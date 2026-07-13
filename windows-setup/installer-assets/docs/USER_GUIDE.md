# NexaFlow v1 User Guide

Windows desktop automation with local workflow storage and optional Android and Chrome companions.

Version 1.0.0 | Windows and Android v1 scope

## 1. Install and Start

1. Run `NexaFlow_Setup.exe`.
2. Open NexaFlow from the Start Menu or desktop shortcut.
3. Keep Windows and display scaling stable while recording and playing a workflow.
4. Allow Windows Firewall access only when you intend to use a companion on the local network.

NexaFlow stores its configuration, trusted devices, and workflow history locally. It does not require a NexaFlow cloud account.

## 2. Desktop Workspace

The desktop app is organized into these areas:

- Record: capture a new mouse and keyboard workflow.
- Play: load and run a saved workflow.
- Data: configure repeated runs from structured data.
- Files: manage recent workflow files.
- Schedule: prepare time-based workflow runs.
- Events: review and edit recorded events.
- Log: inspect activity and errors.
- Settings: preferences, hotkeys, theme, Remote Access, and support information.

The Focus button opens a smaller playback window. The same NexaFlow lightning icon identifies the main window, Focus window, tray icon, and pairing prompts.

## 3. Record a Workflow

1. Open Record.
2. Enter a workflow name and optional notes.
3. Choose Smart Mode for clicks and keyboard input, or Full Mode when pointer movement is required.
4. Set the countdown.
5. Select Start Recording or press the configured record hotkey.
6. Perform the actions to capture.
7. Stop recording and save the `.nxf` workflow.

Use Smart Mode unless pointer movement itself is important. Short, focused recordings are easier to review and recover than one long recording.

## 4. Play a Workflow

1. Open Play and load a `.nxf` workflow.
2. Select the playback speed and repeat behavior.
3. Review the workflow name and event count.
4. Select Play or use the configured play hotkey.
5. Use Pause/Resume when needed.
6. Use Stop to end the active workflow, or Stop All to cancel all current automation.

Do not move, resize, or replace target windows after recording. Screen coordinates and timing are part of the saved workflow.

## 5. Events, Data, and Scheduling

### Events

Use Events to review recorded actions and timing before playback. Make small changes and test the result on non-critical data first.

### Data

Use Data when a workflow must repeat with changing values. Confirm the selected data source and row order before starting a long run.

### Schedule

Scheduled workflows run only while the Windows user session and NexaFlow are available. Verify the workflow manually before scheduling it.

## 6. Focus Mode

Focus Mode provides compact playback controls without replacing the main app. Closing the Focus window does not delete or change the loaded workflow. Stop automation before leaving the computer unattended.

## 7. Android Companion

NexaFlow Mobile has three sections: Connect, Remote, and Settings. Enter the desktop address once, approve pairing, then choose a saved workflow and control playback while monitoring the desktop screen.

### Connect

1. Put the phone and PC on the same Wi-Fi network or phone hotspot.
2. In desktop Settings, start Remote Access.
3. Enter the desktop address shown by NexaFlow, including port `8765`.
4. Select Pair on the phone.
5. Approve the named phone in the desktop prompt.

The phone attempts one trusted reconnect after startup. New or cleared devices always require desktop approval.

### Remote

- Choose a recent desktop workflow without exposing its file path to the phone.
- Select Once, Repeat, or Loop.
- Set applicable count, delay, speed, and start delay controls.
- Use the fixed primary control for Start, Pause, and Resume.
- Use Stop to cancel playback or an active countdown.
- Monitor countdown, elapsed time, event progress, and loop progress.
- Open the full-screen landscape viewer for pinch zoom, pan, double-tap reset, reset, and close.

The viewer is view-only. Its gestures do not send mouse or keyboard input to Windows. If a frame is delayed, the previous frame remains visible.

### Settings

- Appearance: Light or Dark.
- Screen Quality: Sharp, Balanced, or Battery.
- Pairing: review the paired desktop or clear pairing.
- Support, Privacy, and version information.

Clear Pairing revokes the trusted device when the desktop is reachable and creates a new phone identity. Pair again to reconnect.

## 8. Chrome Companion

The Chrome extension records and replays browser-only workflows and can send approved quick controls to NexaFlow Desktop.

1. Start desktop Remote Access.
2. Load the canonical `chrome-extension` folder in Chrome developer mode, or install the published extension when available.
3. Use host `127.0.0.1` and port `8765` when Chrome and NexaFlow run on the same PC.
4. Pair and approve Chrome Companion on the desktop.

Password fields are excluded from recording labels and stored values. Review exported browser workflows before sharing them.

## 9. Remote Access and Firewall

Remote Access is off by default. Start it manually, or enable **Start Remote when NexaFlow opens** after your first successful setup to start it automatically on future launches. New devices still require desktop approval, and Remote Access can be stopped at any time.

Windows Firewall permission is requested only when the required NexaFlow rule is missing or no longer matches the installed app and port. A verified rule is reused silently on later launches.

Source mode and the installed app use different executable paths, so Windows may require one initial permission for each. A port or installation-path change can also require repair approval.

Remote Access uses unencrypted HTTP on the local network. Use only a private, trusted Wi-Fi network or your own hotspot. Do not expose port `8765` to the public internet or configure router port forwarding.

## 10. Trusted Devices

Use Settings > Remote Access > Trusted Devices to review or revoke remembered companions. A revoked device must request approval again. Stop Remote Access immediately if an unfamiliar request appears.

## 11. Hotkeys

Default bindings may be changed in Settings.

- Record: `F9`
- Play: `F10`
- Stop: `F11`
- Pause/Resume: `F12`
- Stop All: `Esc`

Avoid assigning a shortcut already used by Windows or another foreground application.

## 12. Safety and Privacy

- Test new workflows on non-critical files and accounts.
- Keep a visible Stop All hotkey available.
- Do not record passwords, payment details, recovery codes, or other secrets.
- Review workflows before sharing them; recorded input can contain personal data.
- Treat pairing tokens and trusted-device data as private.
- Stop Remote Access when mobile or Chrome control is not needed.
- Keep important data backed up before running destructive or repetitive automation.

NexaFlow does not provide silent remote access. Pairing requests expire, new devices require approval, and trusted devices can be revoked.

## 13. Troubleshooting

### The phone cannot connect

- Confirm Remote Access is on.
- Confirm both devices use the same Wi-Fi network or hotspot.
- Enter the desktop address shown in NexaFlow, not `127.0.0.1`.
- Confirm port `8765` and the current Windows Firewall rule.
- Temporarily disconnect VPN software that replaces the active local route.

### Pairing remains pending

- Keep the desktop pairing prompt open and select Approve.
- Cancel the phone request and pair again if the request expired.
- Verify that another pairing dialog did not replace the earlier request.

### Playback targets the wrong location

- Restore the same window size, position, display, and scaling used during recording.
- Re-record the affected portion in Smart Mode when possible.
- Reduce playback speed to check whether the target app needs more time.

### The screen viewer refreshes slowly

- Select Balanced or Battery quality.
- Keep the phone close to the Wi-Fi access point or hotspot host.
- Close full-screen view and reopen it after the connection stabilizes.

### Windows asks for firewall permission again

- Confirm the app installation path or Remote Access port did not change.
- Allow the repair only for trusted private networks.
- If the same unchanged installed app asks every launch, open a support issue with the Log details and rule status. Do not include pairing tokens.

## 14. Storage and Removal

NexaFlow configuration and workflow history are stored under the current Windows user profile. Uninstalling the application may leave user-created workflows and local settings so they are not deleted unexpectedly. Remove those files manually only after backing up any workflows you need.

## 15. Support and Policies

- Support: `https://web-nexaflow.netlify.app/support`
- Privacy: `https://web-nexaflow.netlify.app/privacy`
- Repository issues: `https://github.com/mahroosdev/NexaFlow/issues`

Support requests submitted through GitHub may be public. Do not include passwords, pairing tokens, private screenshots, or sensitive workflow data.

Before opening an issue, include only the information needed to reproduce the problem:

- NexaFlow version and platform.
- Windows or Android version.
- Short steps that cause the problem.
- The exact visible error message.
- Whether the desktop app was run from source or installed setup.

Remove names, addresses, account details, workflow contents, tokens, and unrelated log lines before posting.

Official release binaries may be used for personal and internal business purposes under the included proprietary license. The source code and assets remain view-only unless separate written permission is granted. The software is provided without warranty; review the included `LICENSE` file for the complete terms.

This guide applies to NexaFlow v1.0.0. Store availability and download locations can change after publication; use the official repository and Netlify-hosted NexaFlow website for current release information.
