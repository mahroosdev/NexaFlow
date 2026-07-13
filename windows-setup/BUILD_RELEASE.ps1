param(
    [string]$GuidePython = $env:NEXAFLOW_GUIDE_PYTHON,
    [switch]$SkipGuides,
    [switch]$SkipChecksums
)

$ErrorActionPreference = 'Stop'
$setupRoot = $PSScriptRoot
$repoRoot = Split-Path -Parent $setupRoot
$distPath = Join-Path $setupRoot 'dist'
$workPath = Join-Path $repoRoot '.nexaflow-build\windows'
$installerPath = Join-Path $setupRoot 'Installers\NexaFlow_Setup.exe'
$zipPath = Join-Path $setupRoot 'Installers\NexaFlow_v1.0_Setup.zip'
$guidePdf = Join-Path $setupRoot 'Installers\NexaFlow_User_Guide.pdf'

if (-not $SkipGuides) {
    if ([string]::IsNullOrWhiteSpace($GuidePython)) {
        $GuidePython = (Get-Command python -ErrorAction Stop).Source
    }
    & $GuidePython -c 'import docx, reportlab' 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'Guide dependencies are missing. Install tools\requirements-guides.txt or set NEXAFLOW_GUIDE_PYTHON.'
    }
    & $GuidePython (Join-Path $repoRoot 'tools\build-user-guides.py')
    if ($LASTEXITCODE -ne 0) { throw 'User-guide generation failed.' }
}

$python = (Get-Command python -ErrorAction Stop).Source
& $python -m PyInstaller --clean --noconfirm --distpath $distPath --workpath $workPath (Join-Path $setupRoot 'nexaflow.spec')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }

$compilerCandidates = @(
    (Join-Path $repoRoot 'tools\Inno Setup 6\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$compiler = $compilerCandidates | Select-Object -First 1
if (-not $compiler) {
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) { $compiler = $command.Source }
}
if (-not $compiler) { throw 'Inno Setup 6 was not found. Run INSTALL_INNO_SETUP.ps1 first.' }

& $compiler (Join-Path $setupRoot 'NexaFlow_Installer.iss')
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $installerPath)) {
    throw 'Inno Setup compilation failed.'
}

$zipStage = Join-Path ([IO.Path]::GetTempPath()) ("NexaFlow-release-" + [guid]::NewGuid().ToString('N'))
try {
    New-Item -ItemType Directory -Path $zipStage | Out-Null
    Copy-Item -LiteralPath $installerPath -Destination (Join-Path $zipStage 'NexaFlow_Setup.exe')
    if (Test-Path -LiteralPath $guidePdf) {
        Copy-Item -LiteralPath $guidePdf -Destination (Join-Path $zipStage 'NexaFlow_User_Guide.pdf')
    }
    Compress-Archive -Path (Join-Path $zipStage '*') -DestinationPath $zipPath -Force
} finally {
    if (Test-Path -LiteralPath $zipStage) {
        Remove-Item -LiteralPath $zipStage -Recurse -Force
    }
}

if (-not $SkipChecksums) {
    & (Join-Path $repoRoot 'tools\sync-release-checksums.ps1')
}

Write-Output "Standalone app: $(Join-Path $distPath 'NexaFlow\NexaFlow.exe')"
Write-Output "Setup installer: $installerPath"
Write-Output "Setup ZIP: $zipPath"
