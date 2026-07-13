param(
  [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$versionRoot = Join-Path $root "App Versions"
$versionDirectory = Join-Path $versionRoot "App Version $Version"

& (Join-Path $PSScriptRoot "sync-release-checksums.ps1")

$packages = @(
  @{
    Source = "windows-setup\Installers\NexaFlow_v1.0_Setup.zip"
    Target = "NexaFlow_Windows_v$Version.zip"
  },
  @{
    Source = "mobile-app\Android Installer\NexaFlow_Android_Private.apk"
    Target = "NexaFlow_Android_v$Version.apk"
  },
  @{
    Source = "chrome-extension\dist\NexaFlow_Chrome_Extension_v1.0.zip"
    Target = "NexaFlow_Chrome_Extension_v$Version.zip"
  }
)

New-Item -ItemType Directory -Force -Path $versionDirectory | Out-Null
Get-ChildItem -LiteralPath $versionDirectory -File | Remove-Item -Force

foreach ($package in $packages) {
  $source = Join-Path $root $package.Source
  if (-not (Test-Path -LiteralPath $source)) {
    throw "Release artifact is missing: $($package.Source)"
  }
  Copy-Item -LiteralPath $source -Destination (Join-Path $versionDirectory $package.Target) -Force
}

$websiteArchive = Join-Path $root "website.zip"
if (Test-Path -LiteralPath $websiteArchive) {
  Remove-Item -LiteralPath $websiteArchive -Force
}
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$websiteSource = Join-Path $root "website"
$archive = [IO.Compression.ZipFile]::Open(
  $websiteArchive,
  [IO.Compression.ZipArchiveMode]::Create
)
try {
  Get-ChildItem -LiteralPath $websiteSource -Recurse -File | ForEach-Object {
    $entryName = $_.FullName.Substring($websiteSource.Length).TrimStart([char[]]"\/").Replace('\', '/')
    [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
      $archive,
      $_.FullName,
      $entryName,
      [IO.Compression.CompressionLevel]::Optimal
    ) | Out-Null
  }
} finally {
  $archive.Dispose()
}

Write-Output "Version folder: $versionDirectory"
Get-ChildItem -LiteralPath $versionDirectory -File | ForEach-Object {
  $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
  Write-Output "$hash  $($_.Name)"
}
Write-Output "Netlify website package: $websiteArchive"
