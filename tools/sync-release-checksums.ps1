param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$checksumPath = Join-Path $repoRoot 'release-checksums-sha256.txt'
$websiteChecksumPath = Join-Path $repoRoot 'website\release-checksums-sha256.txt'
$releaseDataPath = Join-Path $repoRoot 'website\site-data\releases.js'

$artifacts = [ordered]@{
    'windows-setup\Installers\NexaFlow_Setup.exe' = $null
    'windows-setup\Installers\NexaFlow_v1.0_Setup.zip' = 'windows'
    'mobile-app\Android Installer\NexaFlow_Android_Private.apk' = 'android'
    'mobile-app\Android Installer\NexaFlow_Android_Store.aab' = $null
    'chrome-extension\dist\NexaFlow_Chrome_Extension_v1.0.zip' = 'chrome'
}

$hashes = [ordered]@{}
foreach ($relativePath in $artifacts.Keys) {
    $absolutePath = Join-Path $repoRoot $relativePath
    if (-not (Test-Path -LiteralPath $absolutePath)) {
        throw "Release artifact is missing: $relativePath"
    }
    $hashes[$relativePath] = (Get-FileHash -LiteralPath $absolutePath -Algorithm SHA256).Hash.ToLowerInvariant()
}

$checksumText = Get-Content -LiteralPath $checksumPath -Raw
$today = Get-Date -Format 'yyyy-MM-dd'
$checksumText = [regex]::Replace(
    $checksumText,
    '(?m)^# Generated .+$',
    "# Generated $today Asia/Riyadh"
)
$checksumText = [regex]::Replace(
    $checksumText,
    '(?m)^# Checksums refreshed .+$',
    "# Checksums refreshed $today after the current release artifacts were rebuilt or verified."
)
foreach ($relativePath in $hashes.Keys) {
    $escapedPath = [regex]::Escape($relativePath)
    $pattern = "(?m)^[0-9a-fA-F]{64}\s{2}$escapedPath$"
    $replacement = "$($hashes[$relativePath])  $relativePath"
    if ([regex]::Matches($checksumText, $pattern).Count -ne 1) {
        throw "Expected one checksum line for: $relativePath"
    }
    $checksumText = [regex]::Replace($checksumText, $pattern, $replacement)
}
Set-Content -LiteralPath $checksumPath -Value $checksumText.TrimEnd() -Encoding ASCII
Copy-Item -LiteralPath $checksumPath -Destination $websiteChecksumPath -Force

$releaseText = Get-Content -LiteralPath $releaseDataPath -Raw
foreach ($relativePath in $artifacts.Keys) {
    $product = $artifacts[$relativePath]
    if (-not $product) { continue }
    $pattern = '(?s)("id"\s*:\s*"' + [regex]::Escape($product) + '".*?"checksum"\s*:\s*")[0-9a-fA-F]{64}("\s*,)'
    if ([regex]::Matches($releaseText, $pattern).Count -ne 1) {
        throw "Expected one website checksum field for product: $product"
    }
    $replacementHash = $hashes[$relativePath]
    $releaseText = [regex]::Replace(
        $releaseText,
        $pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{
            param($match)
            $match.Groups[1].Value + $replacementHash + $match.Groups[2].Value
        }
    )

    $length = (Get-Item -LiteralPath (Join-Path $repoRoot $relativePath)).Length
    if ($product -eq 'chrome') {
        $displaySize = [string]::Format(
            [Globalization.CultureInfo]::InvariantCulture,
            '{0:F2} KiB',
            ($length / 1KB)
        )
    } else {
        $displaySize = [string]::Format(
            [Globalization.CultureInfo]::InvariantCulture,
            '{0:F2} MiB',
            ($length / 1MB)
        )
    }
    $sizePattern = '(?s)("id"\s*:\s*"' + [regex]::Escape($product) + '".*?"size"\s*:\s*")[^"]+(")'
    if ([regex]::Matches($releaseText, $sizePattern).Count -ne 1) {
        throw "Expected one website size field for product: $product"
    }
    $releaseText = [regex]::Replace(
        $releaseText,
        $sizePattern,
        [System.Text.RegularExpressions.MatchEvaluator]{
            param($match)
            $match.Groups[1].Value + $displaySize + $match.Groups[2].Value
        }
    )
}
$releaseText = [regex]::Replace($releaseText, '"generatedAt"\s*:\s*"[^"]+"', "`"generatedAt`": `"$today`"")
$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText(
    $releaseDataPath,
    $releaseText.TrimEnd() + [Environment]::NewLine,
    $utf8WithoutBom
)

Write-Output 'Release checksums and website metadata are synchronized.'
