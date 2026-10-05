import{readFileSync,writeFileSync}from'node:fs';
const base='outputs/motion-production';
// Klee v2 rejected by user for chibi ratio; do not silently reattach it on rebuild.
for(const key of['yanfei']){
 const root=`outputs/motion-group1/${key}`,r=JSON.parse(readFileSync(root+'/manifest.json','utf8')).roles[0];
 r.visualKey=key;r.key=key+'-group1-v2';r.frames.forEach(f=>f.png=`../motion-group1/${key}/`+f.png);
 writeFileSync(root+'/addon.js',`window.MOTION_PRODUCTION.roles.push(${JSON.stringify(r)});`);
 let page=readFileSync(base+'/index.html','utf8');const src=`../motion-group1/${key}/addon.js`;if(!page.includes(src))page=page.replace('<script src="model.js">',`<script src="${src}"></script><script src="model.js">`);writeFileSync(base+'/index.html',page);
}
let script=readFileSync(base+'/probe.js','utf8');script=script.replace("r.key==='nahida-normal-v2'?120:100","(r.key==='nahida-normal-v2'||r.key==='klee-group1-v2')?120:100");script=script.replace('素材已载入：五位样板、纳西妲新版、第一组凯亚。','素材已载入：五位样板、納西妲新版，第一组凯亚、可莉、烟绯。');writeFileSync(base+'/probe.js',script);
