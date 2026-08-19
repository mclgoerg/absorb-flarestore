# Absorb FlareStore / Feather Source

Automatically generated AltStore-compatible source for the iOS IPA files published by [pounat/absorb](https://github.com/pounat/absorb/releases).

## Main source

Add this URL to FlareStore or Feather:

```text
https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/apps.json
```

Feather URL scheme:

```text
feather://source/https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/apps.json
```

The main source always points to the newest IPA and keeps the full available version history.

## Rollback sources

Because AltStore-compatible sources cannot contain multiple app entries with the same bundle identifier, the updater also generates three separate rollback sources. Each contains one pinned previous Absorb build.

```text
https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/rollback-1.json
https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/rollback-2.json
https://raw.githubusercontent.com/mclgoerg/absorb-flarestore/main/rollback-3.json
```

`rollback-1.json` is the immediately previous IPA release, `rollback-2.json` is the one before that, and `rollback-3.json` is the third previous release. These move forward automatically whenever upstream publishes a new IPA.

Use a rollback source temporarily when you want to replace the currently installed Absorb build with an older one. All of them use Absorb's real bundle identifier, so they are intended as replacement/downgrade installs rather than side-by-side copies.

## How it works

The GitHub Actions workflow runs every three hours and can also be started manually. It:

1. Reads releases from `pounat/absorb`.
2. Finds release assets ending in `.ipa`.
3. Reads the actual bundle identifier from the newest IPA's `Info.plist`.
4. Generates `apps.json` with all available IPA versions, download URLs, sizes, dates, and release notes.
5. Generates `rollback-1.json`, `rollback-2.json`, and `rollback-3.json` for the three previous IPA releases.
6. Commits the generated source files whenever upstream releases change.

The source includes prereleases as well as stable releases so new Absorb iOS builds become available automatically.

> This is an unofficial source. Absorb and its release files are maintained by the upstream project.
