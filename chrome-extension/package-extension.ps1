$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dist = Join-Path $root "dist"
$staging = Join-Path $root ".package-staging"
$zip = Join-Path $dist "NexaFlow_Chrome_Extension_v1.0.zip"

if (Test-Path $staging) {
  Remove-Item -LiteralPath $staging -Recurse -Force
}

try {
  New-Item -ItemType Directory -Force -Path $dist,$staging | Out-Null
  Copy-Item -LiteralPath (Join-Path $root "manifest.json") -Destination $staging
  Copy-Item -LiteralPath (Join-Path $root "README.md") -Destination $staging
  Copy-Item -LiteralPath (Join-Path $root "src") -Destination $staging -Recurse
  Copy-Item -LiteralPath (Join-Path $root "icons") -Destination $staging -Recurse

  if (Test-Path $zip) {
    Remove-Item -LiteralPath $zip -Force
  }

  Add-Type -AssemblyName System.IO.Compression
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $archive = [IO.Compression.ZipFile]::Open(
    $zip,
    [IO.Compression.ZipArchiveMode]::Create
  )
  try {
    Get-ChildItem -LiteralPath $staging -Recurse -File | ForEach-Object {
      $entryName = $_.FullName.Substring($staging.Length).TrimStart([char[]]"\/").Replace('\', '/')
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
  Write-Host "Created Chrome extension ZIP: $zip"
} finally {
  if (Test-Path $staging) {
    Remove-Item -LiteralPath $staging -Recurse -Force
  }
}
