import fs from 'node:fs';
import assert from 'node:assert/strict';
const root='C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator';
const source=fs.readFileSync(root+'/studio/play/pixi-renderer.js','utf8');
// Native text-art rows use only bold full-block glyphs with RGBA color tags.
// Preview projects those glyph cells directly; no PNG replacement or game data change.
export function blockTextRuns(value) {
 const body=String(value).replace(/^<b>/i,'').replace(/<\/b>$/i,'');
 const pattern=/<color=#([0-9a-f]{8})>(█+)<\/color>/ig;
 const runs=[];let end=0;
 for(const match of body.matchAll(pattern)){
  if(match.index!==end)return null;
  const rgba=match[1];runs.push({count:match[2].length,color:parseInt(rgba.slice(0,6),16),alpha:parseInt(rgba.slice(6),16)/255});end=match.index+match[0].length;
 }
 return runs.length&&end===body.length?runs:null;
}
assert.deepEqual(blockTextRuns('<b><color=#FF0000FF>██</color><color=#00FF0080>█</color></b>'),[{count:2,color:0xff0000,alpha:1},{count:1,color:0x00ff00,alpha:128/255}]);
assert.equal(blockTextRuns('<color=#FF0000FF>█</color>oops'),null);
assert.equal(blockTextRuns('ordinary title'),null);
assert.equal(blockTextRuns('<color=#112233FF>███</color>')[0].count,3);
const start=source.indexOf('      const text = new Text({');
const finish=source.indexOf('      visual.addChild(clip, text)',start)+'      visual.addChild(clip, text)'.length;
assert(start>0&&finish>start);
const old=source.slice(start,finish);
const replacement=`      const blockRuns = blockTextRuns(item.text)
      if (blockRuns) {
        const cells = new Graphics()
        let x = -width / 2 + 2
        const y = -height / 2
        for (const run of blockRuns) {
          cells.rect(x, y, run.count * font, font).fill({color: run.color, alpha: run.alpha})
          x += run.count * font
        }
        const clip = new Graphics().rect(-width / 2, -height / 2, width, height).fill({color:0xffffff,alpha:1})
        cells.mask = clip
        visual.addChild(clip, cells)
      } else {
${old}
      }`;
const helper=blockTextRuns.toString().replace('function blockTextRuns','function blockTextRuns');
const patched=source.slice(0,start)+replacement+source.slice(finish);
fs.writeFileSync('work/simulator-pixi-renderer-text-preview.js',patched.replace('export class PixiPlayRenderer',helper+'\n\nexport class PixiPlayRenderer'));
fs.writeFileSync('work/simulator-text-preview-check.json',JSON.stringify({rgbaOrder:true,runLengths:true,transparentAlpha:true,invalidAndOrdinaryTextFallback:true,gameAssetsChanged:false,pngReplacement:false},null,2));
console.log('BLOCK_TEXT_PREVIEW_CHECK_PASS');
