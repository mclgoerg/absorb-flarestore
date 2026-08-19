# Absorb FlareStore / Feather Source

Automatically generated AltStore-compatible source for the iOS IPA files published by [pounat/absorb](https://github.com/pounat/absorb/releases).

## Source URL

Once this repository is **public**, add this URL to FlareStore or Feather:

```text
https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/apps.json
```

Feather URL scheme:

```text
feather://source/https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/apps.json
```

## How it works

The GitHub Actions workflow runs every three hours and can also be started manually. It:

1. Reads releases from `pounat/absorb`.
2. Finds release assets ending in `.ipa`.
3. Reads the actual bundle identifier from the newest IPA's `Info.plist`.
4. Generates `apps.json` with the available IPA versions, download URLs, sizes, dates, and release notes.
5. Commits `apps.json` when upstream releases have changed.

The source includes prereleases as well as stable releases so new Absorb iOS builds become available automatically.

> This is an unofficial source. Absorb and its release files are maintained by the upstream project.
