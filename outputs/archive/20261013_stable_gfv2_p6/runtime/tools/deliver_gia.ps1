param([string]$PackageDirectory)
$ErrorActionPreference = 'Stop'
$packageRoot = (Resolve-Path -LiteralPath $PackageDirectory).Path
$manifest = Get-Content -LiteralPath (Join-Path $packageRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$exportTarget = Join-Path ($env:LOCALAPPDATA+'Low') 'miHoYo\原神\BeyondLocal\Beyond_Local_Export'
if (-not (Test-Path -LiteralPath $exportTarget -PathType Container)) { throw '千星导出目录不存在' }
$items = @($manifest.files | Where-Object { $_.filename.EndsWith('.gia') })
foreach ($item in $items) {
 $source = Join-Path $packageRoot $item.filename
 $target = Join-Path $exportTarget $item.filename
 if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw '交付源哈希不一致' }
 if (Test-Path -LiteralPath $target) {
  if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw '同名文件内容不同，停止复制' }
 } else { Copy-Item -LiteralPath $source -Destination $target }
 if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256) { throw '复制后哈希不一致' }
 Write-Output $item.filename
}
Write-Output '三个GIA复制及SHA256核对通过'
