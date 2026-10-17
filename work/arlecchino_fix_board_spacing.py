from pathlib import Path
p=Path('work/arlecchino_world_current.py');s=p.read_text(encoding='utf-8');s=s.replace('(len(items)+11)//12','(len(items)+8)//9').replace('(1600,1200)','(1950,1200)').replace('items[page*12:(page+1)*12]','items[page*9:(page+1)*9]').replace('x=j%4*400;y=j//4*400','x=j%3*650;y=j//3*400').replace('x+200','x+270').replace('x+400','x+650');p.write_text(s,encoding='utf-8')
