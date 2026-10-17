param([ValidateSet('build','smoke','deliver')][string]$Mode='build')
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent $PSScriptRoot
$taskNode=Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
if(-not(Test-Path -LiteralPath $taskNode)){ $taskNode=(Get-Command node -ErrorAction Stop).Source }
function Invoke-TaskNode([string]$Entry){ & $taskNode $Entry; if($LASTEXITCODE -ne 0){throw "Failed: $Entry ($LASTEXITCODE)"} }
$oldOut=$env:DUEL_LOAD_OUT;$oldInput=$env:DUEL_LOAD_INPUT;$oldRuntime=$env:DUEL_LOAD_RUNTIME
Push-Location -LiteralPath $taskRoot
try{
 Invoke-TaskNode 'work/build-roster-v2.mjs'
 Invoke-TaskNode 'work/build-roster-v2-loading.mjs'
 $env:DUEL_LOAD_OUT='outputs/roster-v2';$env:DUEL_LOAD_INPUT='outputs/roster-v2/base.save.json';$env:DUEL_LOAD_RUNTIME='work/v2-loading-generated.lua'
 Invoke-TaskNode 'work/build-roster-v2-loading-generated.mjs'
 if($Mode -ne 'build'){
  Invoke-TaskNode 'work/verify-roster-v2.mjs'
  Invoke-TaskNode 'work/verify-roster-v2-mobile.mjs'
 }
 Invoke-TaskNode 'work/roster-v2-resource-index.mjs'
 if($Mode -eq 'deliver'){ Invoke-TaskNode 'work/deliver-roster-v2.mjs' }
}finally{
 $env:DUEL_LOAD_OUT=$oldOut;$env:DUEL_LOAD_INPUT=$oldInput;$env:DUEL_LOAD_RUNTIME=$oldRuntime
 Pop-Location
}
