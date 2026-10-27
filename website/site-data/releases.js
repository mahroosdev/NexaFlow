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
      "file": "NexaFlow_Windows_v1.0.0.zip",
      "label": "Download Windows package",
      "format": "Setup + PDF guide",
      "size": "16.13 MiB",
      "checksum": "bbd54d12e92088606d43c36e4acb464aa901b7ddf71841275f9026b8af2bcbab",
      "install": [
        "Download and extract the Windows ZIP.",
        "Run NexaFlow_Setup.exe and complete the installation.",
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
      "checksum": "6e1086f12f1d9ce7f694c6fb8bbc27072cff25a59703b1fed26d9d7a6bc2d799",
      "install": [
        "Download the APK on the Android phone.",
        "Allow installation from the browser when Android asks.",
        "Install, enter the desktop address, and approve pairing."
      ]
    }
  ]
};
