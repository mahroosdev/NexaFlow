param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]] $EasArgs
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$cacheRoot = Join-Path (Split-Path -Parent $projectRoot) ".mobile-build-cache"
$toolHome = Join-Path $cacheRoot "eas-home"
$appData = Join-Path $toolHome "AppData"
$localAppData = Join-Path $toolHome "LocalAppData"
$npmCache = if ([string]::IsNullOrWhiteSpace($env:npm_config_cache)) {
  Join-Path $cacheRoot "npm-cache"
} else {
  $env:npm_config_cache
}

New-Item -ItemType Directory -Force -Path $toolHome | Out-Null
New-Item -ItemType Directory -Force -Path $appData | Out-Null
New-Item -ItemType Directory -Force -Path $localAppData | Out-Null
New-Item -ItemType Directory -Force -Path $npmCache | Out-Null

$env:USERPROFILE = $toolHome
$env:HOME = $toolHome
$env:APPDATA = $appData
$env:LOCALAPPDATA = $localAppData
$env:npm_config_cache = $npmCache
$env:EXPO_NO_TELEMETRY = "1"

Set-Location $projectRoot
& npx --yes eas-cli@20.0.0 @EasArgs
