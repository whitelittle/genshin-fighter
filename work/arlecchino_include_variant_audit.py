from pathlib import Path
p=Path('work/check_arlecchino_ownership.py');s=p.read_text(encoding='utf-8').replace('for action in d.values():','for action in [a for main in d.values() for a in [main]+[{**main,**v} for v in main.get(\'variants\',{}).values()]]:');p.write_text(s,encoding='utf-8')
