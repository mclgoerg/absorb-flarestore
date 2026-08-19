#!/usr/bin/env python3
import json
import os
import plistlib
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path

UPSTREAM = "pounat/absorb"
SOURCE_REPO = "mclgoerg/absorb-flarestore"
RAW_BASE = f"https://raw.githubusercontent.com/{SOURCE_REPO}/main"
SOURCE_URL = f"{RAW_BASE}/apps.json"
ICON_URL = "https://raw.githubusercontent.com/pounat/absorb/main/assets/icon/app_icon.png"
API = f"https://api.github.com/repos/{UPSTREAM}/releases?per_page=100"
ROLLBACK_COUNT = 3


def request_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "absorb-flarestore-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def download(url: str, destination: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "absorb-flarestore-updater"})
    with urllib.request.urlopen(req, timeout=180) as response, destination.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            output.write(chunk)


def inspect_ipa(url: str):
    with tempfile.TemporaryDirectory() as tmp:
        ipa_path = Path(tmp) / "Absorb.ipa"
        download(url, ipa_path)
        with zipfile.ZipFile(ipa_path) as archive:
            info_names = [
                name for name in archive.namelist()
                if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", name)
            ]
            if not info_names:
                raise RuntimeError("Could not find Payload/*.app/Info.plist in latest IPA")
            info = plistlib.loads(archive.read(info_names[0]))
            return {
                "bundleIdentifier": info["CFBundleIdentifier"],
                "version": str(info.get("CFBundleShortVersionString", "")),
                "buildVersion": str(info.get("CFBundleVersion", "")),
            }


def parsed_version(tag: str):
    value = tag.removeprefix("v")
    match = re.fullmatch(r"(.+?)-(\d+)", value)
    if match:
        return match.group(1), match.group(2)
    return value, value


def app_entry(bundle_id: str, versions: list[dict], description: str):
    current = versions[0]
    return {
        "name": "Absorb",
        "bundleIdentifier": bundle_id,
        "developerName": "Nathan Poulson",
        "subtitle": "Audiobookshelf client for iOS",
        "localizedDescription": description,
        "iconURL": ICON_URL,
        "version": current["version"],
        "buildVersion": current["buildVersion"],
        "downloadURL": current["downloadURL"],
        "versions": versions,
    }


def write_source(path: str, name: str, identifier: str, source_url: str, app: dict):
    source = {
        "name": name,
        "identifier": identifier,
        "sourceURL": source_url,
        "apps": [app],
    }
    Path(path).write_text(
        json.dumps(source, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    releases = request_json(API)
    versions = []
    latest_ipa_url = None

    for release in releases:
        if release.get("draft"):
            continue

        ipa_assets = [
            asset for asset in release.get("assets", [])
            if asset.get("name", "").lower().endswith(".ipa")
        ]
        if not ipa_assets:
            continue

        ipa = next(
            (asset for asset in ipa_assets if "absorb" in asset.get("name", "").lower()),
            ipa_assets[0],
        )

        version, build_version = parsed_version(release["tag_name"])
        versions.append({
            "version": version,
            "buildVersion": build_version,
            "date": release["published_at"],
            "downloadURL": ipa["browser_download_url"],
            "size": ipa["size"],
            "localizedDescription": (release.get("body") or "").strip(),
        })

        if latest_ipa_url is None:
            latest_ipa_url = ipa["browser_download_url"]

    if not versions or latest_ipa_url is None:
        raise RuntimeError("No Absorb GitHub release containing an IPA was found")

    metadata = inspect_ipa(latest_ipa_url)
    bundle_id = metadata["bundleIdentifier"]
    latest = versions[0]

    write_source(
        "apps.json",
        "Absorb",
        "com.mclgoerg.absorb-flarestore",
        SOURCE_URL,
        app_entry(
            bundle_id,
            versions,
            "A modern cross-platform Audiobookshelf client. This unofficial source tracks IPA files published by the upstream Absorb GitHub releases.",
        ),
    )

    # AltStore-compatible sources cannot contain duplicate bundle identifiers.
    # Generate separate one-app rollback sources for the three previous IPA builds.
    rollback_versions = versions[1 : 1 + ROLLBACK_COUNT]
    for index, rollback in enumerate(rollback_versions, start=1):
        filename = f"rollback-{index}.json"
        rollback_url = f"{RAW_BASE}/{filename}"
        write_source(
            filename,
            f"Absorb Rollback {index}",
            f"com.mclgoerg.absorb-flarestore.rollback-{index}",
            rollback_url,
            app_entry(
                bundle_id,
                [rollback],
                f"Pinned rollback source for Absorb {rollback['version']} (build {rollback['buildVersion']}). Add this source temporarily when you want to install this older build.",
            ),
        )

    # Remove stale rollback files if fewer than three prior IPA releases exist.
    for index in range(len(rollback_versions) + 1, ROLLBACK_COUNT + 1):
        Path(f"rollback-{index}.json").unlink(missing_ok=True)

    print(
        f"Generated apps.json with {len(versions)} IPA release(s); "
        f"latest {latest['version']} ({latest['buildVersion']}), "
        f"bundle {bundle_id}; generated {len(rollback_versions)} rollback source(s)"
    )


if __name__ == "__main__":
    main()
