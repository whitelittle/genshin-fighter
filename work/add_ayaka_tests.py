from pathlib import Path
p=Path('runtime/tests/run.py');t=p.read_text(encoding='utf-8');a="results['furinaDeliveredTimeline']=True";t=t.replace(a,a+"\n    rt=runtime(ROOT);rt.execute(DUMP);rt.execute((ROOT/'tests/ayaka-timeline.lua').read_text(encoding='utf-8'));results['ayakaDeliveredTimeline']=True")
a="    return {'exactPixelStates':len(receipt['sources']),'bodyPeak':receipt['bodyPeak'],'viewBudgetAndFlash':True}"
b="""    furina_count=len(receipt['sources'])
    receipt=json.loads((ROOT/'ayaka-import.json').read_text(encoding='utf-8'))
    source=REPO/'outputs/v4-one-character-20261010/ayaka-armed-v2'
    for kind in ['bank','script']:
        assert hashlib.sha256((source/receipt['version'][kind]).read_bytes()).hexdigest()==receipt['version'][kind+'Sha256']
    for row in receipt['sources']:
        original=np.array(Image.open(REPO/row['file']).convert('RGBA'));rebuilt=np.zeros_like(original)
        assert hashlib.sha256((REPO/row['file']).read_bytes()).hexdigest()==row['imageSha256']
        img=art.pose('kamisatoayaka','lo',row['pose']);u=row['scale']
        assert abs(img.ax-row['anchor'][0]*u)<1e-8 and abs(img.ay-row['anchor'][1]*u)<1e-8
        for n in range(int(img.n)):
            off=n*5;x,y,w,h=[round(img.bytes[off+i]/u) for i in range(1,5)];col=img.pal[int(img.bytes[off+5])+1]
            rebuilt[y:y+h,x:x+w]=[col[i] for i in range(1,5)]
        assert np.array_equal(original,rebuilt),row['file']
    rt.execute((ROOT/'tests/ayaka-view.lua').read_text(encoding='utf-8'))
    return {'exactPixelStates':furina_count,'ayakaExactPixelStates':len(receipt['sources']),'viewBudgetAndFlash':True}
"""
assert a in t;t=t.replace(a,b);p.write_text(t,encoding='utf-8')
p=Path('runtime/tests/ayaka-view.lua');t=Path('runtime/tests/furina-view.lua').read_text(encoding='utf-8').replace('gf_furina_data','gf_ayaka_data').replace("'furina'","'kamisatoayaka'").replace('R[3],R[3]','R[4],R[4]').replace('Furina','Ayaka');p.write_text(t,encoding='utf-8')
