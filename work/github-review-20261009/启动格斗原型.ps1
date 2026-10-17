$fighterNode = 'C:\Users\Cheng\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$fighterServer = 'C:\Users\Cheng\Documents\deepseek-harness\default-workspace\miliastra-beyond-simulator\web\dist\server.js'
& $fighterNode $fighterServer --workspace $PSScriptRoot --port 4192 --file 'outputs/demo-solo-light/fighter.save.json'
