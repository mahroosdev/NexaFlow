# NexaFlow Mobile

NexaFlow Mobile is the Android companion for NexaFlow Desktop v1.0.

## Current Android Build

- Package: `com.nexaflow.mobile`
- Version: `1.0.0`
- Target SDK: `35`
- Direct install file: `Android Installer/NexaFlow_Android_Private.apk`
- Google Play upload file: `Android Installer/NexaFlow_Android_Store.aab`

## App Features

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

- Connect through local Wi-Fi or a phone hotspot using the desktop address and port `8765`.
- Approve new devices on NexaFlow Desktop; trusted devices reconnect automatically.
- Choose a saved desktop workflow and control Start, Pause, Resume, and Stop.
- Monitor the desktop with stable frame loading, quality presets, and a landscape zoom viewer.
- Manage appearance, screen quality, pairing, support, and privacy.

## Build Android Release Files

Use the local release script:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-private-apk.ps1 -Target both
```

Outputs:

```text
Android Installer/NexaFlow_Android_Private.apk
Android Installer/NexaFlow_Android_Store.aab
```

The APK is for website/private install. The AAB is for Google Play Console upload only.

## Development Run

```powershell
npm install
npm run start:local
```

Use development builds only for internal testing. Do not publish debug APKs.

## Dependency Security

Compatible audit fixes are applied. The remaining Expo SDK 51 toolchain findings and the required post-v1 framework migration are recorded in [`DEPENDENCY_SECURITY.md`](DEPENDENCY_SECURITY.md).

## Remote Access Safety

Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, and Remote Access can be stopped at any time. Do not expose the desktop remote host directly to the public internet with router port forwarding.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

## Platform Scope

Android is the active mobile platform for v1. Existing iOS configuration is preparatory only and is not a supported v1 release channel.
