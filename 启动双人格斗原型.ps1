$fighterOnlineNode = 'C:\Users\Cheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$fighterOnlineServer = 'C:\Users\Cheng\Documents\deepseek-harness\default-workspace\miliastra-beyond-simulator\web\dist\server.js'
& $fighterOnlineNode $fighterOnlineServer --workspace $PSScriptRoot --port 4193 --file 'outputs/demo-online-light/fighter.save.json'
