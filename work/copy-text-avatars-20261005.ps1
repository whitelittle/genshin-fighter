$ErrorActionPreference = 'Stop'
$packageDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\text-avatars-20261005'
$targetDir = Join-Path $env:USERPROFILE 'AppData\LocalLow\miHoYo\原神\BeyondLocal\Beyond_Local_Export'
if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) { throw '千星导入目录不存在' }
$manifest = Get-Content -LiteralPath (Join-Path $packageDir 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$items = @($manifest.primaryFiles) + @([pscustomobject]@{ filename = '加载对照说明.md'; sha256 = (Get-FileHash -LiteralPath (Join-Path $packageDir '加载对照说明.md') -Algorithm SHA256).Hash })
$verified = @()
foreach ($item in $items) {
 $sourcePath = Join-Path $packageDir $item.filename
 $destName = if ($item.filename -eq '加载对照说明.md') { 'gpt_20261005_头像文本对照_说明.md' } else { $item.filename }
 $destPath = Join-Path $targetDir $destName
 $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
 if ($sourceHash -ne $item.sha256) { throw "源文件与清单不一致：$($item.filename)" }
 if (Test-Path -LiteralPath $destPath) {
  if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "同名文件内容不同，未覆盖：$destName" }
 } else { Copy-Item -LiteralPath $sourcePath -Destination $destPath }
 if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "复制后校验失败：$destName" }
 $verified += [pscustomobject]@{filename=$destName;sha256=$sourceHash.ToLowerInvariant()}
 Write-Output "已核对：$destName"
}
$extraFiles = @(
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\native-text-calibration-20261005\gpt_20261005_文字解析校准.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\text-avatars-display-v2-20261005\gpt_20261005_头像显示排错V2_A.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\native-text-length-probe-20261005\gpt_20261005_文字长度缩放校准.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\text-avatars-chunk-v3-20261005\gpt_20261005_头像短文本V3_A.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\original-text-training-v4-20261005\gpt_20261005_原图文字训练室V4_A.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\original-text-training-v4-20261005\gpt_20261005_原图文字训练室V4_尺寸修订_A.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\original-text-training-v5-20261005\gpt_20261005_原图文字训练室V5_头像框_A.gia'),
 (Join-Path (Split-Path -Parent $PSScriptRoot) 'outputs\original-text-training-v5-20261005\gpt_20261005_原图文字训练室V5_头像框修订_A.gia')
)
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'nine-role-hd-latest.json')) {
 $latest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'nine-role-hd-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($latest.out + '/' + $latest.name + '.gia'))
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'native-boot-isolation-latest.json')) {
 $probe = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'native-boot-isolation-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($probe.out + '/' + $probe.name + '.gia'))
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'minimal-native-ui-latest.json')) {
 $minimal = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'minimal-native-ui-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($minimal.out + '/' + $minimal.name + '.gia'))
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'dynamic-text-probe-latest.json')) {
 $dynamic = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dynamic-text-probe-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 foreach ($file in @($dynamic.aName, $dynamic.cName)) {
  $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($dynamic.out + '/' + $file + '.gia'))
 }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'basic-demo-latest.json')) {
 $basic = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'basic-demo-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($basic.out + '/' + $basic.name + '.gia'))
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'menu-art-return-latest.json')) {
 $menuArt = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'menu-art-return-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($menuArt.out + '/' + $menuArt.name + '.gia'))
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'full-art-return-latest.json')) {
 $fullArt = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'full-art-return-latest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($fullArt.out + '/' + $fullArt.name + '.gia'))
 $extraFiles += (Join-Path (Split-Path -Parent $PSScriptRoot) ($fullArt.out + '/实机测试说明.md'))
}
foreach ($sourcePath in $extraFiles) {
 $destName = Split-Path -Leaf $sourcePath
 $destPath = Join-Path $targetDir $destName
 $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
 if (Test-Path -LiteralPath $destPath) {
  if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "Different existing file: $destName" }
 } else { Copy-Item -LiteralPath $sourcePath -Destination $destPath }
 if ((Get-FileHash -LiteralPath $destPath -Algorithm SHA256).Hash -ne $sourceHash) { throw "Copy hash mismatch: $destName" }
 $verified += [pscustomobject]@{filename=$destName;sha256=$sourceHash.ToLowerInvariant()}
 Write-Output "Verified: $destName"
}
[pscustomobject]@{filesCopied=$true;files=$verified;targetDirectory='%USERPROFILE%\AppData\LocalLow\miHoYo\原神\BeyondLocal\Beyond_Local_Export';officialUiImportPerformed=$false;deviceVerified=$false} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $packageDir 'copy-verification.json') -Encoding UTF8


