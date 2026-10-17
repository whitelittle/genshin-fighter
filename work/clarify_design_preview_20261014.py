from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-redesign-20261014'
for role in ['zhongli','mavuika','neuvillette']:
 D=O/role;bank=json.loads((D/'actions.json').read_text(encoding='utf8'));keys=[k for k in bank if k!='idle'];count=len(keys)
 p=D/'player.js';s=p.read_text(encoding='utf8')
 s=s.replace("idle:'待机'","idle:'母版对照（复用）'")
 s=s.replace(")){const g=document.createElement('div');g.className='group';g.textContent=title;", ")){if(!keys.some(key=>bank[key]))continue;const g=document.createElement('div');g.className='group';g.textContent=title;")
 s=s.replace("for(const key of keys){const b=document.createElement('button');", "for(const key of keys){if(!bank[key])continue;const b=document.createElement('button');")
 s=s.replace("choose('idle').then", "choose(Object.keys(bank).find(key=>key!=='idle')||'idle').then")
 hide="for(const id of ['fx','opponent','enemyModel','branch','movement'])$(id).parentElement.hidden=true;"
 if hide not in s:s=s.replace("function tick(now)",hide+"\nfunction tick(now)")
 p.write_text(s,encoding='utf8')
 p=D/'player.css';css=p.read_text(encoding='utf8')
 if '[hidden]{display:none!important}' not in css:css+='\n[hidden]{display:none!important}\n';p.write_text(css,encoding='utf8')
 p=D/'player.html';s=p.read_text(encoding='utf8');s=s.replace('新设计身体小样 · 全角色动作仍未完成',f'本批可播放{count}组新身体小样；25组文字设计另列，动画未齐')
 s=s.replace('aria-label="选择动作"','aria-label="已制作可播放的小样"')
 if '这里只列已制作' not in s:
  s=s.replace('</header><div id="error"',f'</header><p class="note">这里只列已制作、可播放的小样。母版是历史复用对照，其余动作仍待绘制。查看上级页面下方的25组文字设计卡，不代表25组动画已完成。</p><div id="error"')
 s=re.sub(r'player\.js\?v=[^"\s]+','player.js?v=playable-reaction-v2-20261014',s)
 s=s.replace('href="player.css"','href="player.css?v=playable-reaction-v2-20261014"');p.write_text(s,encoding='utf8')
p=O/'index.html';s=p.read_text(encoding='utf8').replace('完整动作补缺 · 钟离重新设计','文字动作设计与已制作小样').replace('钟离 · 全套重设计','钟离 · 2组新小样').replace('火神 · 18组待补','火神 · 1组新小样').replace('水龙 · 12组待补','水龙 · 1组新小样')
s=s.replace('这里只补全三人75张逐动作设计卡','这里只补全三人75张文字设计卡')
s=s.replace('这里补全三人75张逐动作设计卡，制作仍未完成。','下方是三人75张文字设计卡。上方播放器仅有4组已制作身体小样，整套动画尚未完成。')
s=s.replace('钟离：25组重新设计','钟离：25组文字设计，动画尚未齐全').replace('玛薇卡：25组设计，主预览仍缺18组','玛薇卡：25组文字设计，主预览仍缺18组').replace('那维莱特：25组设计，主预览仍缺12组','那维莱特：25组文字设计，主预览仍缺12组')
s=s.replace('src="zhongli/player.html"','src="zhongli/player.html?v=playable-only-20261014"').replace("role+'/player.html'","role+'/player.html?v=playable-only-20261014'")
p.write_text(s,encoding='utf8')
print('Only available sample buttons are displayed; mother reference is listed separately')
