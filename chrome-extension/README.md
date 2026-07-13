# NexaFlow Chrome Companion

NexaFlow Chrome Companion is a separate browser extension for private/web sharing and Chrome Web Store upload. It connects to NexaFlow Desktop Remote Access and records browser workflows inside Chrome.

This extension is the browser companion for the Windows desktop app and is packaged separately from the Android app.

## Install for testing

1. Open Chrome.
2. Go to `chrome://extensions`.
3. Turn on `Developer mode`.
4. Choose `Load unpacked`.
5. Select the canonical `chrome-extension` folder.

For private sharing, use:

`chrome-extension/dist/NexaFlow_Chrome_Extension_v1.0.zip`

## Pair with NexaFlow Desktop

1. Open NexaFlow Desktop.
2. Go to Settings and start Remote Access.
3. Open the NexaFlow extension.
4. Keep host as `127.0.0.1` and port as `8765` when Chrome and NexaFlow Desktop are on the same PC.
5. Press Pair, then approve Chrome Companion on the desktop.

## Browser workflow controls

- Start Recording captures browser clicks, normal text inputs, selected keys, and the start page.
- Stop saves the workflow in Chrome local storage.
- Play Last replays the latest browser workflow in the active tab.
- Export and Import share browser workflow JSON files privately.

Password fields are skipped/masked by default.

## What It Controls

- Browser workflows are recorded and replayed inside Chrome.
- Desktop quick controls are sent to NexaFlow Desktop after pairing.
- The extension does not silently access the desktop. NexaFlow Desktop Remote Access must be started first.

## Package output

The private extension ZIP should be created at:

`chrome-extension/dist/NexaFlow_Chrome_Extension_v1.0.zip`

## Publishing Status

This v1.0 extension package is ready for private/manual Chrome loading and Chrome Web Store upload. Chrome Web Store publishing still requires listing text, screenshots, the privacy/support URLs, and extension review.
