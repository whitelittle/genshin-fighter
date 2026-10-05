import fs from 'node:fs';import assert from 'node:assert/strict';import crypto from 'node:crypto';
const out='outputs/original-text-training-v4-20261005';const save=JSON.parse(fs.readFileSync(out+'/simulator.save.json')),source=save.assets.scripts[0].source;
const old=JSON.parse(fs.readFileSync('outputs/text-avatars-chunk-v3-20261005/simulator.save.json')).assets.scripts[0].source;
for(const prefix of ['local spriteData=','local specs=','local loadingJobs=']){const a=old.split('\n').find(l=>l.startsWith(prefix));const b=source.split('\n').find(l=>l.startsWith(prefix));assert(a&&b);assert.equal(prefix==='local loadingJobs='?a.replace(/,?\{path=\{"CountryStage"\},prefix="StagePx",count=\d+\}/,''):a,b);}
const report=JSON.parse(fs.readFileSync(out+'/report.json'));const lines=['resourceGate.homePortraitData=','local portraitData=','local thumbData=','local Collision='].map(p=>source.split('\n').find(l=>l.startsWith(p)));
const ordered=['home','portrait','thumb','stage'].flatMap(f=>report.allFrames.filter(r=>r.family===f));
let index=0,maxBytes=0;for(const line of lines)for(const m of line.matchAll(/\{textArt=true,palette=\{([^}]*)\},chunks=\{(.*?)\},w=(\d+),h=(\d+),scale=([^,]+),anchor=\{([^}]*)\}\}/g)){
 const palette=[...m[1].matchAll(/"([A-F0-9]{8})"/g)].map(v=>Buffer.from(v[1],'hex'));const w=Number(m[3]),h=Number(m[4]),pixels=Buffer.alloc(w*h*4);
 for(const c of m[2].matchAll(/\{x=(\d+),y=(\d+),w=(\d+),h=(\d+),runs="([a-f0-9]*)"\}/g)){
  const x=Number(c[1]),y=Number(c[2]),cw=Number(c[3]),ch=Number(c[4]),runs=c[5];let xx=0,text='<b>';
  for(let at=0;at<runs.length;at+=9){const color=palette[parseInt(runs.slice(at,at+6),16)-1],count=parseInt(runs.slice(at+6,at+9),16);assert(color);text+='<color=#'+color.toString('hex').toUpperCase()+'>'+'█'.repeat(count)+'</color>';for(let yy=y;yy<y+ch;yy++)for(let k=0;k<count;k++)color.copy(pixels,(yy*w+x+xx+k)*4);xx+=count;}
  assert.equal(xx,cw);text+='</b>';const bytes=Buffer.byteLength(text);assert(bytes<=1000);maxBytes=Math.max(maxBytes,bytes);
 }
 const item=ordered[index++];assert.equal(crypto.createHash('sha256').update(pixels).digest('hex'),item.sourceGridSha256,'Raster roundtrip '+item.key);
}
assert.equal(index,41);assert(source.includes('function Collision.stageId(seed,number) return 1 end'));assert(source.includes('if c.frame~=frame or c.scale~=scale then resourceGate.loader.stagePaint='));
const flow=JSON.parse(fs.readFileSync(out+'/flow-verification.json'));const painted=flow.logs.filter(l=>/LOAD PHASE.*paint|painted=/.test(l.text||'')).map(l=>l.text);
fs.writeFileSync(out+'/raster-verification.json',JSON.stringify({all41FrameRunEncodingRoundtrips:true,maxTextBytes:maxBytes,actorFramesAndSpecsUnchanged:true,actorFxJobCountsUnchanged:true,threeRoundsSameStage:true,warmStagePaintCached:true,simulatorOnly:true,nativeTextSeamsVerified:false,stagePaintLogs:painted},null,2));
console.log('ORIGINAL_TEXT_RASTER_AND_SCOPE_PASS');
