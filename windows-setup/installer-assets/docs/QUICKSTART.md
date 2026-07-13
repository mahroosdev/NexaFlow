# NexaFlow Quick Start

## Install

1. Run `NexaFlow_Setup.exe`.
2. Follow the Windows setup wizard.
3. Launch `NexaFlow` from the Desktop shortcut or Start Menu.

## Standalone App

For direct testing before creating the installer, run:

```text
windows-setup\dist\NexaFlow\NexaFlow.exe
```

## Basic Use

1. Open the Record tab and click **Start Recording**.
2. Perform the actions you want to automate.
3. Stop recording.
4. Open the Play tab and click **Play**.

## Focus Mode

Click **Focus** in the main window to open the compact control window.

Use the gear button inside Focus Mode to adjust Focus transparency and playback visibility behavior.

## Safety

In Settings, enable **Stop play on user input** if you want playback to stop when you touch the mouse or keyboard.

## Remote Access

1. Open Settings.
2. Go to Remote Access.
3. Click **Start Remote**.
4. Request pairing from Android or Chrome, then approve the named device on the desktop.

Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, and Remote Access can be stopped at any time.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

Local Wi-Fi mobile pairing uses the desktop IP and port `8765`. Chrome pairing on the same PC uses `127.0.0.1:8765`.

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

iOS is planned for a later Apple/TestFlight release and is not part of the current public website launch.
