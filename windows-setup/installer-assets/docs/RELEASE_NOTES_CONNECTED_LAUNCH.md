# NexaFlow v1.0 Connected Launch Notes

## Built Outputs

- Windows installer EXE: `windows-setup/Installers/NexaFlow_Setup.exe`
- Windows direct-share ZIP: `windows-setup/Installers/NexaFlow_v1.0_Setup.zip`
- Android private APK: `mobile-app/Android Installer/NexaFlow_Android_Private.apk`
- Android store AAB: `mobile-app/Android Installer/NexaFlow_Android_Store.aab`
- Chrome extension ZIP: `chrome-extension/dist/NexaFlow_Chrome_Extension_v1.0.zip`

For Chrome developer-mode testing, load the canonical `chrome-extension/` source folder. Packaging uses temporary staging and leaves only the release ZIP in `dist/`.

## Website And Store Pages

- Website home page: `index.html`
- Downloads page: `downloads.html`
- Support page: `support.html`
- Privacy page: `privacy.html`

Store links are prepared as pending links until the Google Play and Chrome Web Store listings are approved.

## Product Updates

- Windows Desktop includes workflow recording, playback, scheduling, event and file tools, settings, and consent-based Remote Access.
- Android Companion includes approval pairing, saved-workflow playback, stable screen monitoring, landscape zoom, settings, theme, and support/privacy links.
- Chrome Companion includes browser workflow record/play/export/import and approved desktop quick controls.

## Connection Modes

### Local Wi-Fi

1. Open NexaFlow Desktop.
2. Go to Settings > Remote Access.
3. Click Start Remote.
4. On Android, enter the desktop IP/port, tap Pair, and approve the named phone on the desktop.

### Chrome Companion

1. Start Remote Access in NexaFlow Desktop.
2. Load the NexaFlow Chrome extension.
3. Keep host as `127.0.0.1` and port as `8765` when Chrome and NexaFlow Desktop are on the same PC.
4. Press Pair and approve Chrome Companion on the desktop.

Android connects on the local network only (trusted Wi-Fi or a phone hotspot). Chrome connects through loopback on the same Windows PC. There is no internet/worldwide relay.

Remote Access is off by default. The desktop user can start it manually or enable **Start Remote when NexaFlow opens** for future launches. New devices still require desktop approval, and Remote Access can be stopped at any time.

## Publishing Requirements

- Android Play release uses the AAB and final Play signing setup.
- Chrome Web Store release uses the Chrome extension ZIP, privacy page, and listing assets.
- Website downloads activate after the verified GitHub Release assets are uploaded and `RELEASE_BASE` is enabled.
- Windows installer is not code-signed yet; SmartScreen warnings can appear.

_Scope: v1.0 targets Windows Desktop and Android, with the Chrome companion._
