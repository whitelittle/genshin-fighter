$taskRoot = Join-Path $PSScriptRoot 'work/comment-monitor'
$taskUrl = 'http://127.0.0.1:8807/'
try {
    $null = Invoke-WebRequest ($taskUrl + 'api/state') -UseBasicParsing -TimeoutSec 2
} catch {
    $taskPython = (Get-Command python -ErrorAction Stop).Source
    Start-Process -FilePath $taskPython -ArgumentList @(('"' + (Join-Path $taskRoot 'monitor.py') + '"'), '--serve', '--port', '8807') -WorkingDirectory $taskRoot -WindowStyle Hidden
}
Start-Process $taskUrl
