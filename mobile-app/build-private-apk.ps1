param(
  [ValidateSet("apk", "aab", "both")]
  [string]$Target = "apk",
  [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"

$project = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $project
$realBuildRoot = if ([string]::IsNullOrWhiteSpace($env:NEXAFLOW_BUILD_ROOT)) {
  Join-Path $workspaceRoot ".nexaflow-build"
} else {
  $env:NEXAFLOW_BUILD_ROOT
}
$realBuildProject = Join-Path $realBuildRoot "mobile-app"
$installerDir = if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
  Join-Path $project "Android Installer"
} elseif ([System.IO.Path]::IsPathRooted($OutputDirectory)) {
  [System.IO.Path]::GetFullPath($OutputDirectory)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $project $OutputDirectory))
}
$outputApk = Join-Path $installerDir "NexaFlow_Android_Private.apk"
$outputAab = Join-Path $installerDir "NexaFlow_Android_Store.aab"

$substDriveLetters = @(& subst | ForEach-Object {
  if ($_ -match '^\s*([A-Za-z]):\\:') {
    $matches[1].ToUpperInvariant()
  }
})

$driveLetter = if ([string]::IsNullOrWhiteSpace($env:NEXAFLOW_BUILD_DRIVE)) {
  @("N", "P", "Q", "R", "S") |
    Where-Object { !(Test-Path "$_`:") -and $_ -notin $substDriveLetters } |
    Select-Object -First 1
} else {
  $env:NEXAFLOW_BUILD_DRIVE.TrimEnd(":")
}
if ([string]::IsNullOrWhiteSpace($driveLetter)) {
  throw "No free temporary drive letter is available. Set NEXAFLOW_BUILD_DRIVE to a free drive letter."
}
$driveRoot = "$driveLetter`:"

$sdkCandidates = @(
  $env:NEXAFLOW_ANDROID_SDK,
  "C:\AndroidSdk",
  (Join-Path $project ".android-sdk")
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

$sdk = $null
foreach ($candidate in $sdkCandidates) {
  try {
    if (Test-Path -LiteralPath (Join-Path $candidate "platform-tools\adb.exe") -ErrorAction Stop) {
      $sdk = $candidate
      break
    }
  } catch {
    continue
  }
}
if ([string]::IsNullOrWhiteSpace($sdk)) {
  throw "Android SDK was not found. Set NEXAFLOW_ANDROID_SDK to a valid SDK path."
}

$javaCandidates = @(
  $env:JAVA_HOME,
  "C:\Program Files\Java\jdk-17.0.18",
  "C:\Program Files\Android\Android Studio\jbr"
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
$javaHome = $null
foreach ($candidate in $javaCandidates) {
  try {
    if (Test-Path -LiteralPath (Join-Path $candidate "bin\java.exe") -ErrorAction Stop) {
      $javaHome = $candidate
      break
    }
  } catch {
    continue
  }
}
if ([string]::IsNullOrWhiteSpace($javaHome)) {
  throw "JDK 17 was not found. Set JAVA_HOME to a valid JDK 17 path."
}

# The staged build uses an isolated HOME, so copy release-signing values into
# process environment variables before HOME is redirected. Values are never
# printed or copied into the repository/build tree.
$signingNames = @(
  "NEXAFLOW_RELEASE_STORE_FILE",
  "NEXAFLOW_RELEASE_KEY_ALIAS",
  "NEXAFLOW_RELEASE_STORE_PASSWORD",
  "NEXAFLOW_RELEASE_KEY_PASSWORD"
)
$userGradleProperties = Join-Path $HOME ".gradle\gradle.properties"
$userSigning = @{}
if (Test-Path -LiteralPath $userGradleProperties) {
  Get-Content -LiteralPath $userGradleProperties | ForEach-Object {
    if ($_ -match '^([^#][^=]*)=(.*)$') {
      $userSigning[$matches[1].Trim()] = $matches[2].Trim()
    }
  }
}
foreach ($name in $signingNames) {
  $current = [Environment]::GetEnvironmentVariable($name, "Process")
  if ([string]::IsNullOrWhiteSpace($current) -and $userSigning.ContainsKey($name)) {
    [Environment]::SetEnvironmentVariable($name, $userSigning[$name], "Process")
    $current = $userSigning[$name]
  }
  if ([string]::IsNullOrWhiteSpace($current)) {
    throw "Android release signing is not configured. Set $name in the environment or user Gradle properties."
  }
}

New-Item -ItemType Directory -Force -Path $realBuildRoot,$installerDir | Out-Null

if ((Test-Path -LiteralPath $realBuildProject) -and $env:NEXAFLOW_CLEAN_BUILD -eq "1") {
  $resolvedBuildRoot = (Resolve-Path -LiteralPath $realBuildRoot).Path.TrimEnd("\")
  $resolvedBuildProject = (Resolve-Path -LiteralPath $realBuildProject).Path.TrimEnd("\")
  if (!$resolvedBuildProject.StartsWith($resolvedBuildRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove unexpected build path: $resolvedBuildProject"
  }
  Remove-Item -LiteralPath $realBuildProject -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $realBuildProject | Out-Null

$mappedByScript = $false
if (!(Test-Path "$driveRoot\")) {
  & subst $driveRoot $realBuildRoot
  if ($LASTEXITCODE -ne 0 -or !(Test-Path "$driveRoot\")) {
    throw "Could not map temporary build drive $driveRoot to $realBuildRoot."
  }
  $mappedByScript = $true
}

try {
  $buildProject = "$driveRoot\mobile-app"
  $cacheRoot = "$driveRoot\cache"
  $toolHome = "$cacheRoot\home"
  $tmp = "$cacheRoot\tmp"
  $log = "$cacheRoot\build-release.log"
  New-Item -ItemType Directory -Force -Path $cacheRoot,$toolHome,$tmp | Out-Null

  $robocopyArgs = @(
    $project,
    $buildProject,
    "/E",
    "/XD", ".android-sdk", ".android-studio", ".android-tmp", ".expo", ".expo-check", ".expo-polish-check", ".git", "android\build", "android\app\build", "node_modules\expo-modules-core\android\build",
    "/XF", "*.apk", "*.aab", "expo-server.log", "expo-server.err.log",
    "/NFL", "/NDL", "/NJH", "/NJS", "/NP"
  )
  & robocopy @robocopyArgs | Out-Null
  if ($LASTEXITCODE -gt 7) {
    throw "Project copy failed with robocopy exit code $LASTEXITCODE."
  }

  $env:USERPROFILE = $toolHome
  $env:HOME = $toolHome
  $env:APPDATA = Join-Path $toolHome "AppData"
  $env:LOCALAPPDATA = Join-Path $toolHome "LocalAppData"
  $env:TEMP = $tmp
  $env:TMP = $tmp
  $env:GRADLE_OPTS = "-Djava.io.tmpdir=`"$tmp`" -Djava.net.preferIPv4Stack=true"
  $env:npm_config_cache = Join-Path $cacheRoot "npm-cache"
  $env:EXPO_NO_TELEMETRY = "1"
  $env:NODE_ENV = "production"
  $env:JAVA_HOME = $javaHome
  $env:ANDROID_HOME = $sdk
  $env:ANDROID_SDK_ROOT = $sdk
  $env:PATH = "$javaHome\bin;$sdk\cmdline-tools\latest\bin;$sdk\platform-tools;$env:PATH"

  $androidProject = Join-Path $buildProject "android"
  $sdkForProperties = $sdk.Replace("\", "/").Replace(":", "\:")
  Set-Content -Path (Join-Path $androidProject "local.properties") -Value "sdk.dir=$sdkForProperties" -Encoding ASCII

  Set-Location $androidProject
  $gradleTask = if ($Target -eq "aab") { "bundleRelease" } elseif ($Target -eq "both") { "assembleRelease bundleRelease" } else { "assembleRelease" }
  & cmd.exe /d /c "gradlew.bat $gradleTask --no-daemon 2>&1" | Tee-Object -FilePath $log
  $gradleExitCode = $LASTEXITCODE
  if ($gradleExitCode -ne 0) {
    throw "Release APK build failed. Check $log"
  }

  if ($Target -in @("apk", "both")) {
    $releaseApk = Join-Path $androidProject "app\build\outputs\apk\release\app-release.apk"
    if (!(Test-Path -LiteralPath $releaseApk)) {
      throw "Release APK was not created at $releaseApk"
    }
    Copy-Item -LiteralPath $releaseApk -Destination $outputApk -Force
    Write-Output "Private APK built: $outputApk"
  }

  if ($Target -in @("aab", "both")) {
    $releaseAab = Join-Path $androidProject "app\build\outputs\bundle\release\app-release.aab"
    if (!(Test-Path -LiteralPath $releaseAab)) {
      throw "Release AAB was not created at $releaseAab"
    }
    Copy-Item -LiteralPath $releaseAab -Destination $outputAab -Force
    Write-Output "Store AAB built: $outputAab"
  }
} finally {
  if ($mappedByScript) {
    & subst $driveRoot /D
  }
}
