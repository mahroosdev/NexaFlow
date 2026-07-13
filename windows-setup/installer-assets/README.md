# NexaFlow

NexaFlow v1.0 is a Windows desktop automation app with Android and Chrome companion control for recording, replaying, scheduling, editing, and managing workflows.

## Windows Install

Use the professional setup file created from:

```text
windows-setup\NexaFlow_Installer.iss
```

The installer packages the current fast-start app folder:

```text
windows-setup\dist\NexaFlow\NexaFlow.exe
```

## Included App Features

- Record and replay mouse and keyboard workflows
- Focus Mode compact control window
- Data Loop for repeating workflows with list data
- Files tools for rename, copy, move, organize, and delete
- Scheduler and Events editor
- Logs, hotkeys, theme, timezone, and playback safety settings
- Android companion pairing over local Wi-Fi
- Chrome extension companion pairing on the same PC
- Local-only companion control over the same Wi-Fi network or phone hotspot

## Android Pairing Quick Start

1. Open NexaFlow Desktop.
2. Go to Settings > Remote Access.
3. Click Start Remote.
4. Open the Android app.
5. Enter the desktop IP/port, tap Pair, and approve the named phone on the desktop.

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, and Remote Access can be stopped at any time.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

## Chrome Companion Quick Start

1. Extract the Chrome extension ZIP and load the extracted folder in Chrome developer mode.
2. Start Remote Access in NexaFlow Desktop.
3. In the extension, keep host as `127.0.0.1` and port as `8765`.
4. Press Pair and approve Chrome Companion on the desktop.
5. Use browser workflow record/play or desktop quick controls.

## User Data

NexaFlow stores settings and workflows locally on the user device. No cloud account is required.

Common local folders:

```text
%USERPROFILE%\.nexaflow
%USERPROFILE%\NexaFlow_Screenshots
```

## Support Files

- `docs\QUICKSTART.md`
- `docs\USER_GUIDE.md`
- `PRIVACY.md`
- `SUPPORT.md`
- `CHANGELOG.md`

## Launch Channels

- Website direct downloads: Windows Setup, Android APK, Chrome extension ZIP.
- Google Play: Android AAB upload package.
- Chrome Web Store: Chrome extension ZIP upload package.
