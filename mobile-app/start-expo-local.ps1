$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$expoHome = Join-Path $projectRoot ".expo-home"
$npmCache = Join-Path $projectRoot ".npm-cache"

New-Item -ItemType Directory -Force -Path $expoHome | Out-Null
New-Item -ItemType Directory -Force -Path $npmCache | Out-Null

$env:USERPROFILE = $expoHome
$env:HOME = $expoHome
$env:npm_config_cache = $npmCache
$env:EXPO_NO_TELEMETRY = "1"

Set-Location $projectRoot
npx expo start --localhost --port 8081 --clear
