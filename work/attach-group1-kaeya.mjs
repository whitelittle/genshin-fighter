import{readFileSync,writeFileSync}from'node:fs';
const base='outputs/motion-production',root='outputs/motion-group1/kaeya',r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];r.visualKey='kaeya';r.key='kaeya-group1';r.frames.forEach(f=>f.png='../motion-group1/kaeya/'+f.png);writeFileSync(root+'/addon.js','window.GROUP1_KAEYA='+JSON.stringify(r)+';window.MOTION_PRODUCTION.roles.push(window.GROUP1_KAEYA);');
let page=readFileSync(base+'/index.html','utf8');if(!page.includes('motion-group1/kaeya/addon.js'))page=page.replace('<script src="model.js">','<script src="../motion-group1/kaeya/addon.js"></script><script src="model.js">');writeFileSync(base+'/index.html',page);
let script=readFileSync(base+'/probe.js','utf8');script=script.replace('新旧版本姿势已载入；纳西妲新版本48张。','素材已载入：五位样板、纳西妲新版、第一组凯亚。');writeFileSync(base+'/probe.js',script);
const plan=JSON.parse(readFileSync(base+'/batch-plan.json','utf8'));plan.batches[0].status='started_kaeya_48_pose_candidate_other_13_pending';writeFileSync(base+'/batch-plan.json',JSON.stringify(plan,null,2));
console.log('GROUP1_FIRST_ROLE',r.frames.length,r.pool);
