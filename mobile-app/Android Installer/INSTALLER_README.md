# NexaFlow Android Installer

This folder contains the Android release files for NexaFlow Mobile.

## Current Android Files

```text
NexaFlow_Android_Private.apk
NexaFlow_Android_Store.aab
```

- `NexaFlow_Android_Private.apk` is for private/manual install from the website or direct sharing.
- `NexaFlow_Android_Store.aab` is the Google Play Console upload package. Do not publish it as a direct user download.

Debug APKs are developer-only builds and are intentionally excluded from this release folder.

## What The App Does

NexaFlow Mobile is designed for:

- Approval-based pairing with NexaFlow Desktop.
- Local Wi-Fi / hotspot connection by desktop IP and port `8765` (local network only — no internet relay).
- Choosing saved desktop workflows and controlling Start, Pause, Resume, and Stop.
- Monitoring the desktop with stable frames and a landscape pinch-zoom viewer.
- Managing appearance, screen quality, pairing, support, and privacy.

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

Current Android release target SDK: `35`.

## Install On Android

1. Copy or download `NexaFlow_Android_Private.apk` to the Android phone.
2. Open the APK on the phone.
3. If Android asks for permission, allow installation from this browser or file manager.
4. Tap Install.
5. Open NexaFlow after installation finishes.

Android may show a warning because this APK is installed directly instead of from Google Play. This is normal for private APK releases.

## Connect To NexaFlow Desktop

1. Open NexaFlow Desktop on the computer.
2. Start Remote Access in the desktop app.
3. Make sure the phone is on the same Wi-Fi as the PC, or connect the PC to the phone's hotspot.
4. Open NexaFlow Mobile on the Android phone.
5. Enter the desktop IP/port shown by NexaFlow Desktop.
6. Tap Pair, then approve the named phone on NexaFlow Desktop.

Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, and Remote Access can be stopped at any time.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

The address usually looks like:

```text
192.168.1.20:8765
```

## Important Security Note

NexaFlow is designed for local-network use only. Do not expose the NexaFlow desktop remote host directly to the public internet with router port forwarding.

## Troubleshooting

If the phone cannot connect:

- Confirm the desktop and phone are on the same Wi-Fi for Local mode.
- Confirm Remote Access is running in NexaFlow Desktop.
- Confirm the IP address includes port `8765`.
- Submit a new pairing request and approve it within one minute.
- Check that Windows Firewall allows NexaFlow Desktop remote access.

If Android blocks installation:

- Open Android Settings.
- Search for Install unknown apps.
- Allow the browser or file manager used to open the APK.
- Open `NexaFlow_Android_Private.apk` again.

## Folder Contents

- `NexaFlow_Android_Private.apk` - final private installable app.
- `NexaFlow_Android_Store.aab` - Google Play app bundle for Play Console upload.
- `INSTALLER_README.md` - Android setup and user install notes.
