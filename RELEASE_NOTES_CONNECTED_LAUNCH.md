# NexaFlow v1.0 Connected Launch Notes

## Built Outputs

- Windows installer EXE: `windows-setup/Installers/NexaFlow_Setup.exe`
- Windows direct-share ZIP: `windows-setup/Installers/NexaFlow_v1.0_Setup.zip`
- Android private APK: `mobile-app/Android Installer/NexaFlow_Android_Private.apk`
- Android Google Play AAB: `mobile-app/Android Installer/NexaFlow_Android_Store.aab`
- Chrome extension ZIP: `chrome-extension/dist/NexaFlow_Chrome_Extension_v1.0.zip`

For Chrome developer-mode testing, load the canonical `chrome-extension/` source folder. Packaging uses temporary staging and leaves only the release ZIP in `dist/`.

## Website And Store Pages

- Website landing page: `website/index.html`
- Download center: `website/downloads.html`
- Support page: `website/support.html`
- Privacy policy: `website/privacy.html`

Store buttons are already placed on the website and should be connected to final Google Play and Chrome Web Store URLs after approval.

## Product Updates

- Windows Desktop includes workflow recording, playback, scheduler, event editor, file tools, settings, timezone apply behavior, and consent-based Remote Access.
- Android Companion includes local Wi-Fi / hotspot pairing, saved-workflow playback controls, stable screen monitoring, landscape zoom, settings, theme, and support/privacy links.
- Chrome Companion includes Manifest V3 packaging, browser workflow record/play/export/import, desktop quick controls, and support/privacy links.
- Website direct release includes Windows EXE/ZIP, Android APK, Chrome ZIP, checksums, troubleshooting, support, and privacy pages.

## Connection Modes

NexaFlow connects on the **local network only** — same Wi-Fi or the same phone hotspot. There is no internet/worldwide relay.

### Local Wi-Fi / Hotspot (Android)

1. Open NexaFlow Desktop.
2. Go to Settings > Remote Access.
3. Click Start Remote.
4. On Android, enter the desktop IP/port, tap Pair, and approve the named phone on the desktop.

### Chrome Companion

1. Start Remote Access in NexaFlow Desktop.
2. Load the NexaFlow Chrome extension.
3. Keep host as `127.0.0.1` and port as `8765` when Chrome and NexaFlow Desktop are on the same PC.
4. Request pairing and approve Chrome Companion on the desktop.

## Publishing Requirements

- Google Play uses the AAB and Play Console review.
- Chrome Web Store uses the extension ZIP and extension review.
- Website users can download the Windows setup, Android APK, and Chrome ZIP after the verified GitHub Release assets are uploaded and `RELEASE_BASE` is enabled.
- Windows installer is not code-signed yet; SmartScreen warnings can appear.
- Large downloads are hosted on GitHub Releases and linked from the site (set `RELEASE_BASE` in `website/site-data/releases.js`).

_Scope: v1.0 targets Windows Desktop + Android, with the Chrome companion._
