# Downloads Inno Setup into this workspace so the NexaFlow installer can be
# compiled without relying on an existing Program Files installation.

[CmdletBinding()]
param(
    [string]$InstallDir = ''
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if ([string]::IsNullOrWhiteSpace($InstallDir)) {
    $workspaceRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
    $InstallDir = Join-Path $workspaceRoot.Path 'tools\Inno Setup 6'
}

$toolsDir = Split-Path -Parent $InstallDir
$installer = Join-Path $toolsDir 'innosetup.exe'
$downloadUrl = 'https://jrsoftware.org/download.php/is.exe'

New-Item -ItemType Directory -Force -Path $toolsDir | Out-Null

Write-Host "Downloading Inno Setup compiler..."
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installer

    Write-Host "Installing Inno Setup to:"
    Write-Host "  $InstallDir"

    $arguments = @(
        '/VERYSILENT',
        '/SP-',
        '/SUPPRESSMSGBOXES',
        '/NOCANCEL',
        '/NORESTART',
        '/CURRENTUSER',
        "/DIR=$InstallDir"
    )

    $process = Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Inno Setup installer exited with code $($process.ExitCode)."
    }

    $compiler = Join-Path $InstallDir 'ISCC.exe'
    if (-not (Test-Path $compiler)) {
        throw "Inno Setup installed, but ISCC.exe was not found at $compiler."
    }

    Write-Host "Inno Setup is ready:"
    Write-Host "  $compiler"
} finally {
    if (Test-Path -LiteralPath $installer) {
        Remove-Item -LiteralPath $installer -Force
    }
}
