# NexaFlow v1.0

NexaFlow is a local-first desktop automation product with Android and Chrome companion control.

**v1.0 scope: Windows Desktop + Android**, plus the Chrome extension companion.

## Launch Channels

- Website: direct-download links for the Windows setup-and-guide ZIP, Android APK, and Chrome Extension ZIP after release hosting is enabled.
- Google Play: Android App Bundle prepared for Play Console upload.
- Chrome Web Store: Manifest V3 extension package prepared for store upload.

## Release Files

- `windows-setup/Installers/NexaFlow_Setup.exe`
- `windows-setup/Installers/NexaFlow_v1.0_Setup.zip`
- `mobile-app/Android Installer/NexaFlow_Android_Private.apk`
- `mobile-app/Android Installer/NexaFlow_Android_Store.aab`
- `chrome-extension/dist/NexaFlow_Chrome_Extension_v1.0.zip`
- `App Versions/App Version 1.0.0/` - three canonical user-facing packages for release upload.
- `release-checksums-sha256.txt`

## Repository Layout

- `nexaflow.py`, `recorder_core.py`, `remote_host.py`, `remote_access.py` - Windows desktop application and local companion server.
- `mobile-app/` - Expo/React Native Android companion and native Android project.
- `chrome-extension/` - canonical Manifest V3 extension source and packaging script.
- `windows-setup/` - PyInstaller/Inno Setup definitions, bundled documentation, and final Windows release files.
- `website/` - static Netlify site, support page, privacy policy, and release metadata.
- `tests/` - desktop protocol, firewall, address-selection, and playback tests.
- `scripts/` - public-repository validation.
- `tools/` - repeatable release/document helpers; downloaded compilers remain ignored.

Generated dependencies, SDKs, build caches, signing keys, and release binaries are intentionally ignored. They remain local or are uploaded as release/store assets.

## Website (`website/`)

The deployable website lives entirely in `website/` — the only folder published to hosting.
App source and the large release binaries stay outside it and are **not** deployed.

- `website/index.html` - product landing page.
- `website/downloads.html` - download page (data-driven from `site-data/releases.js`).
- `website/support.html` - GitHub Issues support helper with no public support email.
- `website/privacy.html` - privacy policy for website, Google Play, and Chrome Web Store review.
- `mobile-app/DEPENDENCY_SECURITY.md` - accepted Expo SDK 51 dependency risk and the required post-v1 upgrade gate.
- `website/assets/` - CSS, JS, and hero images.
- `website/site-data/releases.js` - release/version data and download URLs.

### Hosting: Netlify + external release files

Netlify publishes the static `website/` directory through `netlify.toml`. Large installers are linked from external release storage instead of being committed to the repository or uploaded with the Netlify site.

1. **Prepare the packages.** Run `./tools/prepare-public-release.ps1 -Version 1.0.0`.
2. **Upload the three user packages.** Create a GitHub Release tagged `v1.0.0` and upload the contents of `App Versions/App Version 1.0.0/`.
3. **Enable the links.** In `website/site-data/releases.js`, set `published` to `true` only after every uploaded filename matches the release data.
4. **Deploy the website.** Connect the repository to Netlify or upload the generated `website.zip`.

Until `published` is enabled, download buttons show **Release upload pending**, preventing broken public links.

## Remote Access

Remote access is consent-based. Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, requests expire, trusted devices can be revoked, and Remote Access can be stopped at any time.

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

NexaFlow works on your **local network only** (like a home remote-desktop tool) — the phone and PC must be on the same Wi-Fi or the same phone hotspot. There is no worldwide/internet relay.

Supported connection paths:

- Local Wi-Fi / hotspot: Android connects to the desktop IP and port `8765`.
- Local Chrome companion: Chrome extension connects to `127.0.0.1:8765`.

## Store Publishing Notes

- Upload the AAB to Google Play; do not publish the AAB as a public download.
- Upload the Chrome ZIP to Chrome Web Store; website users can still manually install the ZIP if needed.
- Windows website installer is not code-signed yet, so SmartScreen may warn until signing is added.
- Replace pending Google Play and Chrome Web Store buttons after those listings are approved.

## Important Documents

- `V1_LAUNCH_CHECKLIST.md`
- `RELEASE_NOTES_CONNECTED_LAUNCH.md`
- `release-checksums-sha256.txt`
- `chrome-extension/README.md`

## Rebuilding the Android app

`Android Installer/NexaFlow_Android_Private.apk` and `..._Store.aab` are current builds
with the local-only + cleartext-LAN fixes applied (verified in the compiled manifest and
checksummed above). To rebuild again after future source changes, run from `mobile-app/`:

```
./build-private-apk.ps1 -Target both
```

`node_modules/` and `.android-sdk/` are kept locally in `mobile-app/` for this. After building,
regenerate `release-checksums-sha256.txt` (root and `website/` copies).

## Public repository validation

Run `./scripts/validate-public-repo.ps1` before publishing. It rejects tracked signing
credentials, private/generated files, obsolete connection instructions, unrelated public URLs,
Android version mismatches, and release checksum mismatches.
