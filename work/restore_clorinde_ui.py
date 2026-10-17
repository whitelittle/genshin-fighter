"""Restore approved V3 action-page layout, retaining Clorinde-specific controls."""
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'
source=(R/'outputs/dual-character-reference-20261011/raiden/index.html').read_text(encoding='utf-8')
style=source.split('<style>',1)[1].split('</style>',1)[0]
style+='\n'+(R/'outputs/dual-character-reference-20261011/action-wrap.css').read_text(encoding='utf-8')
style+='\n#timeline canvas{height:auto}#error[hidden]{display:none}#error:not([hidden]){display:block}.links a{color:var(--gold)}'
(O/'player.css').write_text(style,encoding='utf-8')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#10101c"><title>克洛琳德 · 动作预览</title><link rel="stylesheet" href="player.css"></head><body><main>
<header><h1>克洛琳德 · 动作预览</h1><span>25组动作候选 · <a href="交付说明.md">交付说明</a> · <a href="body-review.html">体型返修对照</a></span></header><div id="error" role="alert" hidden></div>
<div class="layout"><aside id="actions" aria-label="选择动作"></aside><section><div class="stage"><canvas id="cv" width="1200" height="650" aria-label="动作播放画面"></canvas><div class="stage-label"><strong id="actionName">待机</strong><span id="phase">载入素材…</span></div></div>
<div class="controls"><button id="play">暂停</button><button id="restart">重播</button><button id="prev">上一帧</button><button id="next">下一帧</button>
<label>素材<select id="material"><option value="fit">像素拟合</option><option value="source">源图</option></select></label><label>速度<select id="speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option></select></label>
<label><input id="body" type="checkbox" checked>人物</label><label><input id="fx" type="checkbox" checked>特效</label><label><input id="loop" type="checkbox" checked>循环</label><label><input id="opponent" type="checkbox" checked>对手</label><label><input id="movement" type="checkbox" checked>位移</label><label><input id="mirror" type="checkbox">镜像</label><label><input id="anchors" type="checkbox">锚点</label>
<label>背景<select id="background"><option value="dark">深底</option><option value="light">白底</option></select></label><label>Q分支<select id="branch"><option value="hit">命中确认</option><option value="block">防御</option><option value="whiff">空挥</option></select></label></div>
<input id="scrub" type="range" min="0" max="1" value="0" aria-label="动作时间轴"><div class="readout"><span id="clock"></span><span id="pair">动作与双方对照</span></div><div class="timeline" id="timeline"></div><p class="note" id="note">动作候选，尚未接入正式游戏。</p>
<p class="note links"><a id="source" href="#">查看源板</a> · <a href="verification.json">验证记录</a></p></section></div></main><script src="action-data.js"></script><script src="effect-data.js"></script><script src="player.js"></script></body></html>'''
old=O/'index.html'
history=O/'checkpoint-index-before-ui-restore.html'
if old.exists() and not history.exists():history.write_bytes(old.read_bytes())
(O/'player.html').write_text(page,encoding='utf-8');(O/'index.html').write_text(page,encoding='utf-8')
print('Original V3 layout and wrap restored; own action controls retained')
