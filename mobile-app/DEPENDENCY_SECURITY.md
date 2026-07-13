# Mobile Dependency Security

## V1 Decision

NexaFlow Mobile v1.0.0 remains on Expo SDK 51 and React Native 0.74.5 for the first public release.

On 2026-07-23, the non-breaking `npm audit fix` updates were applied. The remaining audit report contains 27 transitive findings: 1 low, 12 moderate, 13 high, and 1 critical. npm's available resolution requires breaking upgrades to Expo 57 and React Native 0.86.

That framework migration is not included in v1.0.0 because it changes the native build and runtime surface and requires a separate physical-device regression cycle. The remaining findings are accepted for this release under the controls below; they are not treated as resolved.

## Exposure and Controls

- The reported dependency paths are in the Expo/React Native CLI, configuration, parsing, and packaging toolchain. NexaFlow does not intentionally process untrusted archives, XML, YAML, CSS source maps, or package metadata during normal Android app use.
- Release builds use the committed lockfile and the official npm registry. Untrusted dependency archives and third-party build scripts must not be introduced.
- Android release files are signed with the existing NexaFlow certificate and verified with `apksigner`.
- Published APK/AAB files are checked against the release SHA-256 list.
- `npm audit fix --force` must not be used on the v1 branch because it performs an unreviewed framework migration.

## Required Follow-up

Upgrade Expo and React Native in a separate release branch, then repeat Android compilation, pairing, playback, screen-viewer, orientation, gesture, startup, and signed-update compatibility tests on a physical device before publishing that upgrade.
