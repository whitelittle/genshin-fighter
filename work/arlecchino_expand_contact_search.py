from pathlib import Path
p=Path('work/arlecchino_pairing_profiles.py');s=p.read_text(encoding='utf-8').replace('base[1]-6','base[1]-10').replace('base[1]+7','base[1]+11').replace('>40:continue','>65:continue').replace("<40))[0]", "<65))[0]");p.write_text(s,encoding='utf-8')
