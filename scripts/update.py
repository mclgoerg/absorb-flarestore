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
SOURCE_URL = f"https://raw.githubusercontent.com/{SOURCE_REPO}/main/apps.json"
ICON_URL = "https://raw.githubusercontent.com/pounat/absorb/main/assets/icon/app_icon.png"
API = f"https://api.github.com/repos/{UPSTREAM}/releases?per_page=100"


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


def parsed_version(tag: str, asset_name: str):
    value = tag.removeprefix("v")

    # Beta tags use forms such as v1.9.3-240.
    match = re.fullmatch(r"(.+?)-(\d+)", value)
    if match:
        return match.group(1), match.group(2)

    # Stable tags such as v1.9.2 do not contain the build number, but the
    # published IPA does (for example absorb-1.9.2-217.ipa).
    build_match = re.search(r"-(\d+)(?:-[^.]+)?\.ipa$", asset_name, re.IGNORECASE)
    if build_match:
        return value, build_match.group(1)

    return value, value


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

        version, build_version = parsed_version(release["tag_name"], ipa["name"])
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
    latest = versions[0]

    source = {
        "name": "Absorb",
        "identifier": "com.mclgoerg.absorb-flarestore",
        "sourceURL": SOURCE_URL,
        "apps": [
            {
                "name": "Absorb",
                "bundleIdentifier": metadata["bundleIdentifier"],
                "developerName": "Nathan Poulson",
                "subtitle": "Audiobookshelf client for iOS",
                "localizedDescription": "A modern cross-platform Audiobookshelf client. This unofficial source tracks IPA files published by the upstream Absorb GitHub releases.",
                "iconURL": ICON_URL,
                "version": latest["version"],
                "buildVersion": latest["buildVersion"],
                "downloadURL": latest["downloadURL"],
                "versions": versions,
            }
        ],
    }

    Path("apps.json").write_text(
        json.dumps(source, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Generated apps.json with {len(versions)} IPA release(s); "
        f"latest {latest['version']} ({latest['buildVersion']}), "
        f"bundle {metadata['bundleIdentifier']}"
    )


if __name__ == "__main__":
    main()
