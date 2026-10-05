$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Users\Cheng\Documents\ChatGPT\原神格斗2027'
$targetDir = 'C:\Users\Cheng\AppData\LocalLow\miHoYo\原神\BeyondLocal\Beyond_Local_Export'
if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) { throw '千星导出目录不存在' }
$sources = @(
 (Join-Path $projectRoot 'outputs\midphase-final\gpt_20261004_191454_A_实机信号绑定修复.gia'),
 (Join-Path $projectRoot 'outputs\network-import-fix\gpt_20261004_191546_联机节点_常量修复_引用现有信号.gia')
)
foreach ($sourcePath in $sources) {
 $destPath = Join-Path $targetDir ([System.IO.Path]::GetFileName($sourcePath))
 $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
 if (Test-Path -LiteralPath $destPath) {
  if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "同名不同内容，停止复制：$destPath" }
 } else { Copy-Item -LiteralPath $sourcePath -Destination $destPath }
 if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw '复制后校验失败' }
 Write-Output $destPath
}
