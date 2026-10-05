$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Users\Cheng\Documents\ChatGPT\原神格斗2027'
$packageDir = Join-Path $projectRoot 'outputs\full-reinstall'
$targetDir = 'C:\Users\Cheng\AppData\LocalLow\miHoYo\原神\BeyondLocal\Beyond_Local_Export'
if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) { throw '千星导出目录不存在' }
$manifest = Get-Content -LiteralPath (Join-Path $packageDir 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$items = @($manifest.files.filename) + @('安装说明.md')
foreach ($fileName in $items) {
 $sourcePath = Join-Path $packageDir $fileName
 $destName = if ($fileName -eq '安装说明.md') { 'gpt_' + $manifest.stamp + '_整套安装说明.md' } else { $fileName }
 $destPath = Join-Path $targetDir $destName
 $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
 if (Test-Path -LiteralPath $destPath) {
  if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "同名不同内容，停止复制：$destPath" }
 } else { Copy-Item -LiteralPath $sourcePath -Destination $destPath }
 if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw '复制后校验失败' }
 Write-Output $destPath
}
