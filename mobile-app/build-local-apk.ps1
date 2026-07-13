$ErrorActionPreference = "Stop"

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$cacheRoot = Join-Path (Split-Path -Parent $project) ".mobile-build-cache"
$sdk = if ([string]::IsNullOrWhiteSpace($env:NEXAFLOW_ANDROID_SDK)) {
  Join-Path $project ".android-sdk"
} else {
  $env:NEXAFLOW_ANDROID_SDK
}
$toolHome = Join-Path $cacheRoot "local-build-home"
$tmp = Join-Path $cacheRoot "tmp"
$log = Join-Path $toolHome "build-debug.log"

New-Item -ItemType Directory -Force -Path $toolHome,$tmp | Out-Null

$env:USERPROFILE = $toolHome
$env:HOME = $toolHome
$env:APPDATA = Join-Path $toolHome "AppData"
$env:LOCALAPPDATA = Join-Path $toolHome "LocalAppData"
$env:TEMP = $tmp
$env:TMP = $tmp
$env:GRADLE_OPTS = "-Djava.io.tmpdir=`"$tmp`" -Djava.net.preferIPv4Stack=true"
$env:npm_config_cache = Join-Path $cacheRoot "npm-cache-build"
$env:EXPO_NO_TELEMETRY = "1"
$env:NODE_ENV = "development"
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17.0.18"
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:PATH = "$env:JAVA_HOME\bin;$sdk\cmdline-tools\latest\bin;$sdk\platform-tools;$env:PATH"

$androidProject = Join-Path $project "android"
$sdkForProperties = $sdk.Replace("\", "/").Replace(":", "\:")
Set-Content -Path (Join-Path $androidProject "local.properties") -Value "sdk.dir=$sdkForProperties" -Encoding ASCII

Set-Location $androidProject
& .\gradlew.bat assembleDebug --no-daemon *>&1 | Tee-Object -FilePath $log
