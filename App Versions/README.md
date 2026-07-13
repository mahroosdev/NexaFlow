# NexaFlow Release Packages

This directory contains the public installation packages prepared for each
NexaFlow release.

## Current Release

Version: 1.0.0

Folder: `App Version 1.0.0`

The release folder contains exactly three files:

1. `NexaFlow_Windows_v1.0.0.zip`
   Windows setup package containing `NexaFlow_Setup.exe` and the PDF user guide.

2. `NexaFlow_Android_v1.0.0.apk`
   Direct-install Android application for phones and tablets.

3. `NexaFlow_Chrome_Extension_v1.0.0.zip`
   Chrome extension package for manual Developer Mode installation.

## Publishing

Upload all three files, without renaming them, to the external release host for
the matching version. The NexaFlow website uses these exact filenames when
generating download links.

After the files are uploaded:

1. Confirm that every filename and SHA-256 checksum matches the release data.
2. Set `published` to `true` in `website/site-data/releases.js`.
3. Regenerate `website.zip`.
4. Deploy the updated website package to Netlify.
5. Test every download before announcing the release.

## Google Play Package

The Android App Bundle is not a public download. It remains at:

`mobile-app/Android Installer/NexaFlow_Android_Store.aab`

Submit the AAB through Google Play Console only. Website users receive the APK,
not the AAB.

## Rebuilding This Folder

Run the release preparation script from the repository root:

```powershell
./tools/prepare-public-release.ps1 -Version 1.0.0
```

The script recreates the version folder from verified release artifacts,
synchronizes checksums and website metadata, and generates the Netlify-ready
`website.zip`.

## Repository Policy

Release binaries in version folders are intentionally excluded from Git history.
Keep source code, signing credentials, Android SDK files, build caches, and
temporary output outside public release uploads.
