import{readFileSync,writeFileSync,mkdirSync}from'node:fs';import{designs}from'./action-probe-design.mjs';
const batch=JSON.parse(readFileSync('outputs/motion-production/batch-plan.json','utf8')).batches[0].roles;
const heights={jean:226,lisa:218,ganyu:214,xiao:209,hutao:212,yaemiko:224,kirara:206,kamisatoayato:229,aratakiitto:237,sangonomiyakokomi:213};
const talents=JSON.parse(readFileSync('assets/roster-v2/talent-index.json','utf8'));
const make=(name,startup,reach,damage,fx)=>({name,startup,active:5,recovery:25,reach,damage,fx,height:'mid',hitCount:1,blockstun:12,hitstun:20,effectExtent:reach+22,notes:'新动作探针候选；实际战斗数值继续分开管理，最终特效待讨论。'});
for(const[key,name]of batch){if(!heights[key])continue;
 const root='outputs/motion-group1/'+key;mkdirSync(root,{recursive:true});const talent=talents.find(t=>t.key===key);
 const source=designs.find(d=>d.key===key);const design=structuredClone(source||{key,name,weapon:'character-specific',color:'#aecbdc',identity:'按原作角色动作意图改编为横版格斗',evidence:'技能名沿用现有talent-index；数值、动作适配为候选。',moves:{A:make('普通攻击',10,145,9,'slash'),E:make(talent?.E||'特殊技',17,220,15,'seal'),Q:make(talent?.Q||'必杀',27,270,32,'seal')}});
 design.moves.Q.hitCount=1;design.moves.Q.support=false;design.moves.Q.effectDuration=0;
 writeFileSync(root+'/role-design.json',JSON.stringify({key,name,height:heights[key],design,notes:['第一批人物动作候选，基础/攻击/连接各16姿势，普攻/E各8张。','角色特效独立；具体最终技能效果待讨论。','状态型技能配套及正式战斗/真机仍需独立验收。']},null,2));
}
