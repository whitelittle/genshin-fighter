$ErrorActionPreference='Stop'
$probeRoot=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$probePort=4196
$existingListener=Get-NetTCPConnection -LocalPort $probePort -State Listen -ErrorAction SilentlyContinue
if(-not $existingListener){
    $probePython=(Get-Command python -ErrorAction Stop).Source
    Start-Process -FilePath $probePython -ArgumentList @('-m','http.server',"$probePort",'--bind','127.0.0.1','--directory',('"'+$probeRoot+'"')) -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'server.out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'server.err.log')
}
Write-Host '浏览器打开 http://127.0.0.1:4196/outputs/action-probe/index.html'
