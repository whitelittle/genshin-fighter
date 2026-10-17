$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$items = Get-Content -LiteralPath (Join-Path $root 'download-materials/duplicate-paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($item in $items) {
    $src = Join-Path $root $item.source
    $dst = Join-Path $root $item.path
    if ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() -ne $item.sha256) { throw "Hash mismatch: $src" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
}
Write-Output 'All duplicate paths restored.'
