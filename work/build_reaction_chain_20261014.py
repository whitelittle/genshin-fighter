from pathlib import Path
import json,os,shutil,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014';B=R/'outputs/three-role-basic-20261013'
wp=json.loads((R/'work/wakeup_chain_20261014_selected.json').read_text(encoding='utf8'))
roots={
 'mavuika':{'unit':.36,'hit':[(325,557),(799,554),(1350,605),(260,1040),(775,956),(1288,962)],'wake':[(470,396),(1140,406),(520,970),(1175,1006)]},
 'neuvillette':{'unit':.42,'hit':[(265,634),(790,628),(290,1235),(795,1188),(300,1440),(780,1430)],'wake':[(500,408),(1210,418),(500,962),(1225,997)]}}
audit=[]
for p in wp:
 role=p['role'];D=O/role;ca.O=D;H=D/'history/reaction-chain-20261014';H.mkdir(parents=True,exist_ok=True)
 for name in ['actions.json','action-data.js','player.js','player.html']:
  if not(H/name).exists():shutil.copy2(D/name,H/name)
 src=D/'sources/wakeup-20261014.png';shutil.copy2(os.path.expandvars(p['generatedPath']),src)
 (D/'prompts/wakeup-20261014.txt').write_text(p['prompt'],encoding='utf8');(D/'prompts/wakeup-unit-revision-20261014.txt').write_text(p['scalePrompt'],encoding='utf8')
 shutil.copy2(os.path.expandvars(p['firstPath']),H/'wakeup-large-low-poses-rejected.png')
 if p.get('elbowPath'):
  shutil.copy2(os.path.expandvars(p['elbowPath']),H/'wakeup-elbow-before-unit-revision.png');(D/'prompts/wakeup-elbow-20261014.txt').write_text(p['elbowPrompt'],encoding='utf8')
 bank=json.loads((D/'actions.json').read_text(encoding='utf8'));unit=roots[role]['unit']
 palette=json.loads((B/role/'palette.json').read_text()) if role=='neuvillette' else json.loads((B/'upstream/mavuika-v10/dist/assets/neutral-rig-v6.json').read_text())['palette']
 for key,path,n,points,durations,phases in [
  ('hit_knockdown',D/'sources/hit-knockdown-20261014.png',6,roots[role]['hit'],[5,6,8,8,8,16],['站立受力','补步失衡','空中受击','侧身下落','肩背落地','同向倒地']),
  ('wakeup',src,4,roots[role]['wake'],[8,8,10,8],['撑肘抬身','收膝撑掌','单膝承重','站起收稳'])]:
  ss=[];fs=[];items,fragments=ca.extract(path,n)
  for i,((im,info),point) in enumerate(zip(items,points)):
   assert not info['fullCanvasContact'],(role,key,i)
   ox,oy=info['sourceOrigin'];anchor=[point[0]-ox+32,point[1]-oy+32];pad=Image.new('RGBA',(im.width+64,im.height+64));pad.alpha_composite(im,(32,32));file=f'frames/{key}-chain-20261014-{i}.png';pad.save(D/file)
   sf={'file':file,'source':path.relative_to(D).as_posix(),'anchor':anchor,'scale':unit,'sourceOrigin':[ox-32,oy-32],'roi':info['roi'],'unitPolicy':'fixed role source drawing unit for this chain; no per-pose bounding box resizing','rootKind':'manual boot/contact or virtual pelvis-relative floor'}
   ff,meta=ca.canonical_fit(pad,anchor,unit,palette,f'{key}-chain-20261014-{i}');ss.append(sf);fs.append(ff);audit.append({'role':role,'key':key,'pose':i,'sourceCanvasContact':False,'unit':unit,'rootSheet':point,'rectangles':ff['rectangles'],'reconstructionExact':True,'artAccepted':False})
  if key=='wakeup':
   ss=[dict(bank['hit_knockdown']['sourceFrames'][-1])]+ss+[dict(bank['idle']['sourceFrames'][0])];fs=[dict(bank['hit_knockdown']['frames'][-1])]+fs+[dict(bank['idle']['frames'][0])];durations=[10]+durations+[6];phases=['共享同向倒地']+phases+['回母版待机']
  bank[key]={'frames':fs,'sourceFrames':ss,'durations':durations,'phases':phases,'events':[],'previewOnly':True,'runtimeIntegrated':False,'artAccepted':False,'status':'2026-10-14新增受击起身身体候选；共享倒地首尾与固定单位，人体/支撑/武器/落地连接仍待美术验收；不是正式战斗受击规则'}
 bank['hit_knockdown']['continuation']={'next':'wakeup','sharedPose':True};bank['wakeup']['continuation']={'next':'idle','sharedPose':True}
 if role=='mavuika':bank['hit_knockdown']['status']+='；当前为无武器身体分支，持剑/骑乘受击的武器/车体过渡另补'
 else:bank['hit_knockdown']['status']+='；手杖握持连续候选，刚性/避穿与遮挡继续复核'
 assert bank['hit_knockdown']['frames'][-1]==bank['wakeup']['frames'][0]
 assert bank['hit_knockdown']['sourceFrames'][-1]==bank['wakeup']['sourceFrames'][0]
 (D/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf8');(D/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf8')
 s=(H/'player.js').read_text(encoding='utf8');s=s.replace('let selected=','let chainMode=false;\nlet selected=')
 s=s.replace("b.onclick=()=>choose(key).catch(error)","b.onclick=()=>{chainMode=false;choose(key).catch(error)}")
 s=s.replace("function tick(now)","const chainButton=document.createElement('button');chainButton.id='chainReplay';chainButton.textContent='受击→倒地→起身连播';chainButton.onclick=()=>{chainMode=true;desiredPlaying=true;choose('hit_knockdown').catch(error)};$('play').parentElement.prepend(chainButton);\nfunction tick(now)")
 s=s.replace("if(time>=total){if($('loop').checked)time%=total;else{time=total-1;playing=desiredPlaying=false}}", "if(time>=total){if(chainMode){const next=active.continuation?.next;time=total-1;playing=false;if(next){if(next==='idle'){chainMode=false;desiredPlaying=false;}choose(next).catch(error)}else{chainMode=false;desiredPlaying=false}}else if($('loop').checked)time%=total;else{time=total-1;playing=desiredPlaying=false}}")
 (D/'player.js').write_text(s,encoding='utf8')
 page=(H/'player.html').read_text(encoding='utf8');page=re.sub(r'本批可播放\d+组新身体小样',f'本批可播放{len(bank)-1}组新身体小样',page);page=page.replace('playable-only-20261014','reaction-chain-20261014');(D/'player.html').write_text(page,encoding='utf8')
 font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
 for key in ['hit_knockdown','wakeup']:
  g=bank[key];card=Image.new('RGBA',(1800,450),(98,112,119,255));dr=ImageDraw.Draw(card)
  for i,f in enumerate(g['frames']):
   im=Image.open(D/f['file']).convert('RGBA');scale=f['scale']*.85;im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);card.alpha_composite(im,(round(155+i*300-f['anchor'][0]*scale),round(403-f['anchor'][1]*scale)));dr.text((i*300+8,10),g['phases'][i],font=font,fill='white')
  dr.line((0,403,1800,403),fill='white');card.convert('RGB').save(D/f'evidence/{key}-chain-20261014.png')
report={'scope':'2 independent body reaction chains, not combat simulation','newGroups':4,'uniqueNewBodies':20,'displayStates':24,'sharedDownBoundaryExact':True,'designDirectionAcceptedByUser':True,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'audit':audit}
(O/'reaction-chain-20261014.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
p=O/'index.html';s=p.read_text(encoding='utf8').replace('火神 · 1组新小样','火神 · 3组新小样').replace('水龙 · 1组新小样','水龙 · 3组新小样').replace('上方播放器仅有4组已制作身体小样','上方播放器现有8组已制作身体小样').replace('本批只有4组身体小样','当前共8组身体小样')
s=s.replace('playable-only-20261014','reaction-chain-20261014');p.write_text(s,encoding='utf8')
cards=json.loads((O/'all-design-cards.json').read_text(encoding='utf8'))
for c in cards:
 c['designDirectionAcceptedByUser']=True
 if c['role'] in ['mavuika','neuvillette'] and c['actionId'] in ['hit_knockdown','wakeup']:
  c['status']='本页新增身体候选可播放；倒地/起身边界共享，正式战斗与美术仍待验';c['bodySampleAvailable']=True
(O/'all-design-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf8')
s=p.read_text(encoding='utf8');s=re.sub(r'const cards=.*?;let role=',lambda m:'const cards='+json.dumps(cards,ensure_ascii=False)+';let role=',s,flags=re.S);p.write_text(s,encoding='utf8')
print('New reaction groups 4, bodies 20; shared down boundary exact; each role 3 playable samples')
