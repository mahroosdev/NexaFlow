/*
  Set published to true only after both release files are uploaded to the matching
  release host. Netlify serves the website; GitHub Releases serves the installer
  EXE and Android APK.
*/
window.NEXAFLOW_RELEASES = {
  "version": "1.0.0",
  "releasedAt": "2026-07-18",
  "generatedAt": "2026-10-27",
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
      "file": "NexaFlow_Setup.exe",
      "label": "Download Windows installer",
      "format": "Windows setup installer",
      "size": "16.60 MiB",
      "checksum": "709b890a4c790c2fd17e4f3a164295e4dabffc5076387d7f029e9e1727ae947e",
      "install": [
        "Download and run NexaFlow_Setup.exe.",
        "Complete the Windows installation wizard.",
        "Open the installed app and follow the connection setup."
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
      "checksum": "6e1086f12f1d9ce7f694c6fb8bbc27072cff25a59703b1fed26d9d7a6bc2d799",
      "install": [
        "Download the APK on the Android phone.",
        "Allow installation from the browser when Android asks.",
        "Install, enter the desktop address, and approve pairing."
      ]
    }
  ]
};
