/*
  Set published to true only after all three files are uploaded to the matching
  release host. Netlify serves the website; release storage serves the large
  Windows ZIP and APK files.
*/
window.NEXAFLOW_RELEASES = {
  "version": "1.0.0",
  "releasedAt": "2026-07-18",
  "generatedAt": "2026-07-23",
  "published": false,
  "releaseBase": "https://github.com/mahroosdev/NexaFlow/releases/download/v1.0.0/",
  "checksumUrl": "release-checksums-sha256.txt",
  "supportUrl": "https://github.com/mahroosdev/NexaFlow/issues/new",
  "products": [
    {
      "id": "windows",
      "symbol": "WIN",
      "eyebrow": "Desktop application",
      "name": "NexaFlow for Windows",
      "summary": "Record, organize, schedule, and replay desktop workflows from the main NexaFlow control center.",
      "file": "NexaFlow_Windows_v1.0.0.zip",
      "label": "Download Windows package",
      "format": "Setup + PDF guide",
      "size": "14.31 MiB",
      "checksum": "d65d67ac019f2f91fb320ba29f7793e98b54964161cd449714633da2dad760c7",
      "install": [
        "Download and extract the Windows ZIP.",
        "Run NexaFlow_Setup.exe and complete installation.",
        "Keep the included PDF guide for setup and connection help."
      ]
    },
    {
      "id": "android",
      "symbol": "AND",
      "eyebrow": "Mobile companion",
      "name": "NexaFlow for Android",
      "summary": "Pair over the same Wi-Fi or hotspot, monitor the desktop, and control saved workflow playback.",
      "file": "NexaFlow_Android_v1.0.0.apk",
      "label": "Download Android APK",
      "format": "Direct-install APK",
      "size": "60.35 MiB",
      "checksum": "7aaeef13866cf5a2099935da176544ffcc16dff7781c229728fc38ccdc802e29",
      "install": [
        "Download the APK on the Android phone.",
        "Allow installation from the browser when Android asks.",
        "Install, enter the desktop address, and approve pairing."
      ]
    },
    {
      "id": "chrome",
      "symbol": "EXT",
      "eyebrow": "Browser companion",
      "name": "NexaFlow for Chrome",
      "summary": "Record browser workflows and send quick playback controls to the approved NexaFlow desktop.",
      "file": "NexaFlow_Chrome_Extension_v1.0.0.zip",
      "label": "Download extension ZIP",
      "format": "Manual extension package",
      "size": "14.51 KiB",
      "checksum": "315389094f0d323ce51c8fcef0880adf12f2d634979178f1810c7ee87eebeb8a",
      "install": [
        "Download and extract the ZIP.",
        "Open chrome://extensions and enable Developer mode.",
        "Choose Load unpacked and select the extracted folder."
      ]
    }
  ]
};
