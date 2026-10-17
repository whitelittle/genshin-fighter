from pathlib import Path
import json,re,shutil,io
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from build_zhongli_full import F,O,LABELS,ROOT

def save(im,p,**kw):
 b=io.BytesIO();im.save(b,format=p.suffix[1:].upper().replace('JPG','JPEG'),**kw);p.write_bytes(b.getvalue())
def main():
 bank=json.loads((F/'actions.json').read_text());report=json.loads((F/'pose-report.json').read_text());fits=json.loads((O/'foe-fitted.json').read_text());
 for item in fits.values():shutil.copy(O/item['file'],F/item['file'])
 baseline=ROOT/'outputs/v4-one-character-20261010/baseline-actions'
 for pose in json.loads((baseline/'parameters.json').read_text())['characters']['raidenshogun']['poses']:
  if pose['origin']=='keyframes' and pose['pose'].startswith('guard_'):
   name='foe-fit-'+pose['pose']+'.png';shutil.copy(baseline/pose['file'],F/name);fits[pose['pose']]={'file':name,'ax':pose['ax'],'ay':pose['ay'],'scale':pose['u']*330/336,'rects':pose['rects'],'source':'actual V3 decoded rectangles','sourceSHA256':pose['png_sha256']}
 (F/'foe-fitted.json').write_text(json.dumps(fits));app=(O/'app.js').read_text();
 app=re.sub(r'async function loadFoe\(\).*?\nfunction drawFoe',"async function loadFoe(){const fits=JSON.parse(document.getElementById('foeData').textContent),loaded={};await Promise.all(Object.entries(fits).map(async([key,f])=>loaded[key]=await loadImage(f.file)));foeAtlas={};foeFitted=fits;foeFitImages=loaded}\nfunction drawFoe",app,flags=re.S)
 app=app.replace("if($('material').value==='fit'){const f=foeFitted","if(true){const f=foeFitted")
 app=app.replace("$('material').value==='source'?d.sourceFrames:d.frames","$('material').value==='source'?d.sourceFrames:$('material').value==='initial'?d.initialFrames:d.frames")
 app=app.replace("$('material').value==='fit'?e.fitFrames:e.sourceFrames","$('material').value==='source'?e.sourceFrames:e.fitFrames").replace("$('material').value==='fit'?d.effects?.fitFrames:d.effects?.sourceFrames","$('material').value==='source'?d.effects?.sourceFrames:d.effects?.fitFrames")
 app=app.replace("$('material').value==='fit'?ultimatePortraitFit:ultimatePortrait","$('material').value==='source'?ultimatePortrait:ultimatePortraitFit")
 app=app.replace("fetch('actions.json').then(r=>r.json())","Promise.resolve(JSON.parse(document.getElementById('actionData').textContent))")
 # Throw lock starts at preparation end; source phases 2/3 are pull/release.
 app=app.replace("if(p===0)return [580,550];if(p===1)return [lerp(580,535,u),550];if(p===2)return [535,550]","if(p===0)return [lerp(580,535,u),550];if(p===1)return [535,550];if(p===2)return [535,550]")
 app=app.replace("if(p===0)return [410,550];if(p===1)return [lerp(410,450,u),550];if(p===2)return [450,550]","if(p===0)return [lerp(410,450,u),550];if(p===1)return [450,550];if(p===2)return [450,550]")
 # Independent pillar includes expiration/retract frame, not an infinite hold.
 app=app.replace("(elapsed<5?0:elapsed<12?1:2)","(elapsed<5?0:elapsed<12?1:elapsed<65?2:3)")
 # Airborne registrations use a pelvis root; stage Y must include pelvis height above logical feet.
 app=app.replace("if(!$('stageMove').checked)return [x,y];", "if(selected==='受击与倒地'&&p===2)return [x,385-80*Math.sin(u*Math.PI/2)];if(selected==='受击与倒地'&&p===3)return [x,305+150*u];if((selected==='前冲'||selected==='后撤')&&(p===2||p===3))y=385-25*Math.sin((p-2+u)*Math.PI/2);if(!$('stageMove').checked)return [x,y];")
 app=app.replace("if(p===2||p===3)y-=25*Math.sin((p-2+u)*Math.PI/2)", "")
 app=app.replace("if(p===1)return [450,550];if(p===2)return [450,550]", "if(p===1)return [450,385];if(p===2)return [450,385]")
 app=app.replace("550-60*Math.sin(u*Math.PI/2)","385-60*Math.sin(u*Math.PI/2)").replace("lerp(490,550,u)","lerp(440,550,u)")
 app=app.replace("c.width=240;c.height=190", "c.width=400;c.height=190")
 app=app.replace("const airborne=name==='空轻'||name==='空重'||name==='跳跃'&&i>0&&i<5", "const airborne=d.sourceFrames[i].rootKind?.includes('pelvis')")
 app=app.replace("i,110,airborne?100:175", "i,120,airborne?100:175")

 (F/'app.js').write_text(app)
 page=(O/'index.html').read_text();page=re.sub(r'<link rel="stylesheet" href="action-wrap.css[^>]+>','',page);page=re.sub(r'<header>.*?</header>','<header><h1>钟离 · 全动作素材</h1><span>25组 · 145显示姿 · <a href="size-review.html">三列拟合对照</a> · <a href="checks/all-actions.gif" download>下载全动作动图</a> · <a href="action-cards.json" download>动作卡</a> · <a href="pose-report.json" download>台账</a> · <a href="README.md" download>流程与说明</a></span></header>',page,flags=re.S);page=page.replace('<option value="fit" selected>拟合图</option>','<option value="initial">初始拟合</option><option value="fit" selected>优化拟合</option>');page=page.replace('动作素材候选：25组。尚未接入正式战斗与设备验收。','25组完整素材与展示序列；对手固定使用雷神基线拟合图。正式战斗、模拟器和真机未验收。');page=page.replace('.frame canvas{display:block;width:100%;aspect-ratio:1.3}', '.frame canvas{display:block;width:100%;height:auto;aspect-ratio:400/190}');page=page.replace('<script src="app.js?v=zhongli1"></script>','<script id="actionData" type="application/json">'+json.dumps(bank,ensure_ascii=False).replace('<','\\u003c')+'</script><script id="foeData" type="application/json">'+json.dumps(fits).replace('<','\\u003c')+'</script><script src="app.js"></script>');(F/'index.html').write_text(page)
 # Standalone offline file contains code and JSON; images stay adjacent so PNGs remain downloadable.
 (F/'offline.html').write_text(page.replace('<script src="app.js"></script>','<script>'+app+'</script>'))
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,15)
 cache={f['file']:Image.open(F/f['file']).convert('RGBA') for d in bank.values() for f in d['frames']}
 def paste(canvas,f,x,y,ratio=1):
  im=cache.get(f['file']) or Image.open(F/f['file']).convert('RGBA');scale=f['scale']*ratio;sz=(max(1,round(im.width*scale)),max(1,round(im.height*scale)));im=im.resize(sz,Image.Resampling.NEAREST);canvas.paste(im,(round(x-f['anchor'][0]*scale),round(y-f['anchor'][1]*scale)),im)
 # Fixed-size cells: never shrink a sprite to its individual bounding box.
 overview=[]
 for step in range(60):
  sheet=Image.new('RGB',(2500,1300),(28,31,42));draw=ImageDraw.Draw(sheet)
  for j,(label,d) in enumerate(bank.items()):
   x=j%5*500;y=j//5*260;tick=step/60*sum(d['durations']);i=0
   for i,duration in enumerate(d['durations']):
    if tick<duration:break
    tick-=duration
   key=list(LABELS)[j];draw.text((x+12,y+8),key,font=font,fill=(236,208,147));draw.line((x+5,y+245,x+495,y+245),fill=(89,91,101));f=d['frames'][i];rootY=y+160 if f.get('sourceFrame') and report['poses'][next(k for k,p in enumerate(report['poses']) if p['file']==f['sourceFrame'])]['rootKind']=='pelvis guide' else y+245
   paste(sheet,f,x+210,rootY,.48)
  overview.append(sheet)
 overview[0].save(F/'checks/overview.png');overview[0].save(F/'checks/all-actions.gif',save_all=True,append_images=overview[1:],duration=80,loop=0,optimize=True)
 for key,label in LABELS.items():
  d=bank[label];seq=[];dur=[]
  for i,f in enumerate(d['frames']):
   panel=Image.new('RGB',(1200,450),(28,31,42));draw=ImageDraw.Draw(panel);draw.text((20,15),key+' / '+str(i+1),font=font,fill='white');draw.line((0,410,1200,410),fill=(100,103,115));air=d['sourceFrames'][i].get('rootKind','').startswith('pelvis');paste(panel,f,410,255 if air else 410,.9);seq.append(panel);dur.append(round(d['durations'][i]/60*1000)*3)
  seq[0].save(F/f'checks/{key}-slow.gif',save_all=True,append_images=seq[1:],duration=dur,loop=0,optimize=True)
 from build_zhongli_size_review import main as build_comparison
 build_comparison()
 print({'viewer':'offline.html','gifs':26,'comparison':'size-review.html'})
if __name__=='__main__':main()
