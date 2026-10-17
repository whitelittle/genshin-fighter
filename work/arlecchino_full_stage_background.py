from pathlib import Path
p=Path('outputs/arlecchino-actions-20261011/player-v2.js');s=p.read_text(encoding='utf-8').replace("createLinearGradient(0,0,0,550)","createLinearGradient(0,0,0,650)").replace('fillRect(0,0,1200,545)','fillRect(0,0,1200,650)');p.write_text(s,encoding='utf-8')
