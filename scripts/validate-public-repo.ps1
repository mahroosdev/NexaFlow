param(
  [switch]$SkipArtifactHashes
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root

$errors = [System.Collections.Generic.List[string]]::new()

try {
  $tracked = @(git ls-files)
  $generatedPattern = '(?i)(^|/)(node_modules|\.android-sdk|\.gradle|\.expo-check|\.expo-polish-check|build|dist|_REMOVED_review)(/|$)|\.(apk|aab|exe|zip|keystore|jks|p12|pfx|pyc|log)$'
  foreach ($path in $tracked) {
    if ($path -match $generatedPattern) {
      $errors.Add("Tracked generated or private file: $path")
    }
  }

  $signingAssignments = @(git grep -n -E '^NEXAFLOW_RELEASE_(STORE_FILE|KEY_ALIAS|STORE_PASSWORD|KEY_PASSWORD)=' -- ':!scripts/validate-public-repo.ps1' 2>$null)
  foreach ($match in $signingAssignments) {
    $errors.Add("Tracked Android signing assignment: $match")
  }

  $forbidden = @(git grep -n -I -i -E 'nexaflow\.app|mahroosdev\.github\.io|OWNER/REPO|pairing code|pair code|desktop code|EmailJS|placeholder license|dist/unpacked|CodexSandboxOffline|C:\\Users\\Nexus Pulse' -- ':!scripts/validate-public-repo.ps1' 2>$null)
  foreach ($match in $forbidden) {
    $errors.Add("Stale or unrelated public reference: $match")
  }

  $appJson = Get-Content -Raw -LiteralPath 'mobile-app\app.json' | ConvertFrom-Json
  $expectedVersionCode = [int]$appJson.expo.android.versionCode
  $nativeText = Get-Content -Raw -LiteralPath 'mobile-app\android\app\build.gradle'
  if ($nativeText -notmatch 'versionCode\s+(\d+)') {
    $errors.Add('Native Android versionCode was not found.')
  } elseif ([int]$matches[1] -ne $expectedVersionCode) {
    $errors.Add("Android versionCode mismatch: app.json=$expectedVersionCode native=$($matches[1])")
  }

  $extensionManifest = Get-Content -Raw -LiteralPath 'chrome-extension\manifest.json' | ConvertFrom-Json
  $extensionIconPaths = @($extensionManifest.icons.PSObject.Properties.Value)
  if ($extensionManifest.action.default_icon -is [string]) {
    $extensionIconPaths += $extensionManifest.action.default_icon
  } else {
    $extensionIconPaths += @($extensionManifest.action.default_icon.PSObject.Properties.Value)
  }
  foreach ($iconPath in $extensionIconPaths) {
    if ($iconPath -match '(?i)\.svg$') {
      $errors.Add("Chrome manifest must use PNG extension icons: $iconPath")
    } elseif (-not (Test-Path -LiteralPath (Join-Path 'chrome-extension' $iconPath))) {
      $errors.Add("Chrome manifest icon is missing: $iconPath")
    }
  }

  $remoteHostText = Get-Content -Raw -LiteralPath 'remote_host.py'
  if ($remoteHostText -match 'Access-Control-Allow-Origin.{0,20}["'']\*["'']') {
    $errors.Add('Remote host must not allow wildcard browser origins.')
  }

  if (-not $SkipArtifactHashes) {
    $checksumPath = 'release-checksums-sha256.txt'
    $websiteChecksumPath = 'website\release-checksums-sha256.txt'
    if ((Get-Content -Raw -LiteralPath $checksumPath) -ne (Get-Content -Raw -LiteralPath $websiteChecksumPath)) {
      $errors.Add('Root and website checksum files differ.')
    }

    $expectedWebsiteHashes = @{}
    foreach ($line in Get-Content -LiteralPath $checksumPath) {
      if ($line -notmatch '^([0-9a-fA-F]{64})\s{2}(.+)$') { continue }
      $expected = $matches[1].ToLowerInvariant()
      $path = $matches[2] -replace '\\', [IO.Path]::DirectorySeparatorChar
      if ($path -like '*NexaFlow_v1.0_Setup.zip') { $expectedWebsiteHashes.windows = $expected }
      if ($path -like '*NexaFlow_Android_Private.apk') { $expectedWebsiteHashes.android = $expected }
      if ($path -like '*NexaFlow_Chrome_Extension_v1.0.zip') { $expectedWebsiteHashes.chrome = $expected }
      if (-not (Test-Path -LiteralPath $path)) {
        $errors.Add("Release artifact is missing: $path")
        continue
      }
      $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
      if ($actual -ne $expected) {
        $errors.Add("Release hash mismatch: $path")
      }
    }

    $releaseData = Get-Content -Raw -LiteralPath 'website\site-data\releases.js'
    foreach ($product in @('windows', 'android', 'chrome')) {
      $pattern = '(?s)"id"\s*:\s*"' + $product + '".*?"checksum"\s*:\s*"([0-9a-fA-F]{64})"'
      $match = [regex]::Match($releaseData, $pattern)
      if (-not $match.Success) {
        $errors.Add("Website checksum is missing for: $product")
      } elseif ($match.Groups[1].Value.ToLowerInvariant() -ne $expectedWebsiteHashes[$product]) {
        $errors.Add("Website checksum mismatch for: $product")
      }
    }
  }

  if ($errors.Count) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
  }

  Write-Host 'Public repository validation passed.'
} finally {
  Pop-Location
}

exit 0
