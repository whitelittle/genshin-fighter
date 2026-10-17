"""Repair the existing full-action viewer without changing source art or combat data."""
from pathlib import Path
import argparse
import re


def repair(folder):
    app = folder / 'app.js'
    text = app.read_text(encoding='utf-8')
    if 'function drawCurrentBody(' not in text:
        text = text.replace('let frames=[],images=[],', 'let neutralFrames=[],neutralImages=[],frames=[],images=[],', 1)
        marker = '\nasync function loadFoe()'
        addition = """
function isNeutralTail(){return selected==='E · 地心'&&time>=bank[selected].bodyActionTicks}
function drawCurrentBody(x,y){
 if(!isNeutralTail()){const i=phase();drawPose(ctx,i,x,y,frames[i].scale);return}
 const idle=bank['待机'],elapsed=(time-bank[selected].bodyActionTicks)%idle.durations.reduce((a,b)=>a+b,0);
 let remain=elapsed,index=0;while(index<idle.durations.length-1&&remain>=idle.durations[index])remain-=idle.durations[index++];
 const f=neutralFrames[index],im=neutralImages[index];if(!f||!im)return;
 ctx.imageSmoothingEnabled=false;ctx.drawImage(im,x-f.anchor[0]*f.scale,y-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);
}
"""
        assert marker in text
        text = text.replace(marker, addition + marker, 1)
        old = "if($('body').checked&&frames.length)drawPose(ctx,phase(),x,y,frames[phase()].scale)"
        assert old in text
        text = text.replace(old, "if($('body').checked&&frames.length)drawCurrentBody(x,y)", 1)
        text = text.replace("$('phase').textContent=phases[phase()]||''", "$('phase').textContent=isNeutralTail()?'待机／岩脊独立存续与消散':phases[phase()]||''", 1)
        # Preload the idle bank with the selected material before atomically switching.
        old = "const [loaded,effects]=await Promise.all([Promise.all(chosen.map(f=>loadImage(f.file))),Promise.all((list||[]).map(f=>loadImage(f.file)))]);"
        new = "const idle=bank['待机'],neutralChosen=$('material').value==='source'?idle.sourceFrames:$('material').value==='initial'?idle.initialFrames:idle.frames;const [loaded,effects,neutralLoaded]=await Promise.all([Promise.all(chosen.map(f=>loadImage(f.file))),Promise.all((list||[]).map(f=>loadImage(f.file))),Promise.all(neutralChosen.map(f=>loadImage(f.file)))]);"
        assert old in text
        text = text.replace(old, new, 1)
        text = text.replace('frames=chosen;images=loaded;', 'neutralFrames=neutralChosen;neutralImages=neutralLoaded;frames=chosen;images=loaded;', 1)
    app.write_text(text, encoding='utf-8')
    page = folder / 'offline.html'
    html = page.read_text(encoding='utf-8')
    html, count = re.subn(r'<script>.*?</script>', lambda _: '<script>'+text+'</script>', html, flags=re.S)
    assert count == 1, 'Expected exactly one inline viewer script'
    page.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('full_actions', type=Path)
    repair(parser.parse_args().full_actions)
