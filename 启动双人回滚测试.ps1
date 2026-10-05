$fighterRollbackNode = 'C:\Users\Cheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$fighterRollbackServer = 'C:\Users\Cheng\Documents\deepseek-harness\default-workspace\miliastra-beyond-simulator\web\dist\server.js'
& $fighterRollbackNode $fighterRollbackServer --workspace $PSScriptRoot --port 4193 --file 'outputs/demo-online-light-rollback/fighter.save.json'
