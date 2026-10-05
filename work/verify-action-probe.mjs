import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {designs} from './action-probe-design.mjs';
await import('./action-probe/model.js');
const M=globalThis.ProbeModel,get=(key,action)=>designs.find(r=>r.key===key).moves[action];
const checks=[];function check(name,fn){fn();checks.push(name);}
check('短剑与大剑距离有差异，而非统一普攻判定',()=>{assert.equal(M.trace(get('keqing','A'),100,140,'stand').events.length,0);assert.equal(M.trace(get('diluc','A'),100,140,'stand').events.length,1);});
check('剑影仅一次命中，不因五帧有效重复伤害',()=>{const t=M.trace(get('keqing','Q'),100,240,'stand');assert.equal(t.events.length,1);assert.equal(t.damage,36);});
check('喷水六次接触，每十帧一次，总伤害36',()=>{const t=M.trace(get('neuvillette','Q'),200,240,'stand');assert.equal(t.events.length,6);assert.equal(t.damage,36);assert.ok(t.events.slice(1).every((e,i)=>e.frame-t.events[i].frame===10));});
check('跳跃可越过水平喷水，持续防守不计示意伤害',()=>{assert.equal(M.trace(get('neuvillette','Q'),200,240,'jump').damage,0);assert.equal(M.trace(get('neuvillette','Q'),200,240,'guard').damage,0);});
check('火鸟离体，远处接触晚于角色收招，超过射程空挥',()=>{const m=get('diluc','Q'),end=m.startup+m.active+m.recovery,t=M.trace(m,200,535,'stand');assert.equal(t.events.length,1);assert.ok(t.events[0].frame>end);assert.equal(M.trace(m,200,600,'stand').events.length,0);assert.equal(M.stateAt(m,end+1),'投射物飞行');});
check('纳西妲领域零命中，角色收招后仍持续',()=>{const m=get('nahida','Q');assert.equal(M.trace(m,200,150,'stand').events.length,0);assert.equal(M.stateAt(m,70),'领域持续');assert.equal(M.hitboxes(m,70).length,0);});
check('雷楔第一帧未造成追斩，瞬移不叠加攻击最远距离',()=>{const m=get('keqing','E');assert.equal(M.hitboxes(m,m.startup+1).length,0);assert.equal(M.actorOffset(m,m.startup+2),180);assert.ok(M.hitboxes(m,m.startup+2).every(b=>b.x+b.w<=m.reach));});
check('投弹判定与弧线高度一致；落地前下降',()=>{const m=get('klee','A'),first=M.hitboxes(m,m.startup+1)[0],mid=M.hitboxes(m,m.startup+14)[0],end=M.hitboxes(m,m.startup+28)[0];assert.ok(mid.y>first.y+100);assert.ok(end.y<mid.y-100);});
check('所有研究招式最远判定不超出声明射程，结束不残留伤害',()=>{for(const r of designs)for(const m of Object.values(r.moves)){for(let f=0;f<=M.duration(m);f++)for(const b of M.hitboxes(m,f)){assert.ok(b.x+b.w<=m.reach+.001,r.key+' '+m.name);assert.ok(b.w>0&&b.h>0);}assert.equal(M.hitboxes(m,M.duration(m)+1).length,0);}});
check('模型只接受当前动作、公开帧、距离及假人状态，无玩家输入读取',()=>{const s=readFileSync('work/action-probe/model.js','utf8');assert.ok(!/keyboard|keyDown|network|fetch\(/i.test(s));assert.equal(M.sample(get('keqing','A'),7,90,'ai').guarded,false);assert.equal(M.sample(get('neuvillette','Q'),37,200,'ai').guarded,true);});
const report={date:new Date().toISOString(),checks,passed:true,roles:designs.length,moves:designs.length*3,evidence:'local deterministic design model; not production battle or real device',productionCombatChanged:false};
writeFileSync('outputs/action-probe/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
