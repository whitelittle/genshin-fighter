from pathlib import Path
import json
p=Path('outputs/arlecchino-actions-20261011');f=p/'source-calibration.json';c=json.loads(f.read_text(encoding='utf-8'));c.update({'forwarddash-v1':{'supportY':[494,494,959,985]},'backdash-v1':{'supportY':[500,510,747+175/.52,998]},'victory-v1':{'supportY':[734,734,1495,1495]},'defeat-v1':{'supportY':[536,513,992,992]}});f.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
f=p/'additional-body-plans.json';plans=json.loads(f.read_text(encoding='utf-8'));new=[
 {'key':'forwarddash','label':'前冲','source':'source/forwarddash-v1.png','group':'forwarddash-v1','n':4,'unit':.55,'hips':[465,1195,589,1220],'durations':[4,4,6,6],'phases':['压低蓄脚','蹬地','滑入','落地制动'],'motion':{'kind':'dash','distance':140,'beginTick':4,'endTick':24,'height':0},'appendIdlePrefix':True,'appendIdle':True},
 {'key':'backdash','label':'后撤','source':'source/backdash-v1.png','group':'backdash-v1','n':4,'unit':.52,'hips':[452,1220,450,1220],'durations':[4,4,6,6],'phases':['前脚蓄力','蹬退','短离地','后脚制动'],'motion':{'kind':'dash','distance':-95,'beginTick':4,'endTick':24,'height':22},'appendIdlePrefix':True,'appendIdle':True},
 {'key':'victory','label':'胜利','source':'source/victory-v1.png','group':'victory-v1','n':4,'unit':.42,'hips':[307,814,324,818],'durations':[12,18,18,16],'phases':['平复','致意','收手','静立'],'appendIdlePrefix':True,'appendIdle':True},
 {'key':'defeat','label':'败北','source':'source/defeat-v1.png','group':'defeat-v1','n':4,'unit':.60,'hips':[448,1135,515,1170],'durations':[8,8,12,20],'phases':['失力','跪下','低头','停留']}]
for x in new:x['weaponLayer']='none';x['status']='新空手动作候选；尺度/支撑/衔接待复核'
plans=[x for x in plans if x['key'] not in {y['key'] for y in new}]+new;f.write_text(json.dumps(plans,ensure_ascii=False,indent=2),encoding='utf-8')
