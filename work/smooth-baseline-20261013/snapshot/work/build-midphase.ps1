param([string]$NodePath='',[switch]$Deliver)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if(!$NodePath){$NodePath=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'}
if(!(Test-Path -LiteralPath $NodePath)){throw '请通过 -NodePath 指定可用的 Node.js 运行时'}
function Run-Step([string]$File,[string[]]$Arguments=@()) { & $NodePath $File @Arguments; if($LASTEXITCODE -ne 0){throw "构建停止：$File"} }
$env:GROUP1_OUT='outputs/midphase-final/assembly';$env:FINAL_ROSTER='19';$env:FINAL_ART='1'
$env:REPAIR_INPUT=$env:GROUP1_OUT;$env:REPAIR_OUT='outputs/midphase-final';$env:FINAL_HUD='dots'
$env:STAGE_BUDGET='9000';$env:STAGE_PIXEL_OUT='outputs/stage-pixel-nearest-9000'
$env:DUEL_LOAD_INPUT='outputs/midphase-final/base.save.json';$env:DUEL_LOAD_OUT=$env:REPAIR_OUT;$env:DUEL_LOAD_RUNTIME='work/repair-loading.lua'
Run-Step 'work/build-group1-full.mjs'
Copy-Item -LiteralPath 'outputs/group1-full-test/home-portraits.json' -Destination 'outputs/midphase-final/assembly/home-portraits.json'
Run-Step 'work/restyle-group1-home.mjs'
Run-Step 'work/attach-group1-all.mjs'
Run-Step 'work/build-test-repair.mjs'
Run-Step 'work/build-country-scene-repair.mjs'
Run-Step 'work/final-game-mechanics.mjs'
Run-Step 'work/build-repair-loading.mjs'
Run-Step 'work/build-roster-v2-loading-generated.mjs'
Run-Step 'work/finalize-test-repair.mjs'
Run-Step 'work/fix-selection-input.mjs'
Run-Step 'work/fix-imported-signal-bindings.mjs'
Run-Step 'work/verify-repair-collision.mjs'
Run-Step 'work/verify-repair-loading.mjs'
Run-Step 'work/verify-repair-mobile.mjs'
Run-Step 'work/verify-test-repair.mjs'
if($Deliver){
 $stamp=[TimeZoneInfo]::ConvertTimeFromUtc([DateTime]::UtcNow,[TimeZoneInfo]::FindSystemTimeZoneById('China Standard Time')).ToString('yyyyMMdd_HHmmss')
 Run-Step 'work/deliver-test-repair.mjs' @($stamp)
 Run-Step 'work/write-midphase-install.mjs'
}
