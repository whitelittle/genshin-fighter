"""File/coordinate checks only, never anatomical or device acceptance."""
from pathlib import Path
import json, hashlib, math, base64
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
d=json.loads((O/'actions-size-candidate.json').read_text(encoding='utf-8'))
active=json.loads((O/'actions.json').read_text(encoding='utf-8'))
report=json.loads((O/'uniform-size-report.json').read_text(encoding='utf-8'))
assert hashlib.sha256((O/'actions.json').read_bytes()).hexdigest()==report['activeBankSha256']
assert [f['file'] for f in d['空重']['sourceFrames']]==[f['file'] for f in active['空重']['sourceFrames']]
peak=0;checked=0
for label,action in d.items():
    assert action['durations']==active[label]['durations']
    assert action.get('motion')==active[label].get('motion')
    for source,fitted in zip(action['sourceFrames'],action['frames']):
        assert fitted['scale']==4.5
        assert 'scaleX' not in fitted and 'scaleY' not in fitted
        rec=json.loads((O/Path(fitted['file']).with_suffix('.rects.json')).read_text(encoding='utf-8'))
        target=np.asarray(Image.open(O/fitted['file']).convert('RGBA'))
        rebuilt=np.zeros_like(target)
        for x,y,w,h,c in rec['rects']:rebuilt[y:y+h,x:x+w]=rec['palette'][c][:3]+[255]
        assert np.array_equal(rebuilt,target)
        mask=np.unpackbits(np.frombuffer(base64.b64decode(rec['bodyMaskBits']),dtype='uint8'))[:target.shape[0]*target.shape[1]].reshape(target.shape[:2]).astype(bool)
        assert not (mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any()), 'outline canvas padding missing'
        expanded=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
        assert np.array_equal(target[:,:,3]>0,expanded)
        assert np.all(target[expanded&~mask,:3]==[25,31,79])
        interior=target.copy();interior[~mask]=0
        assert hashlib.sha256(interior.tobytes()).hexdigest()==rec['interiorRgbaSha256']
        im=Image.open(O/source['file']);q=source['scale']/4.5
        expected=[-math.floor(-source['anchor'][0]*q)+1,-math.floor(-source['anchor'][1]*q)+1]
        assert fitted['anchor']==expected
        for point in source.get('anatomy',{}).get('headPoints',[]):
            logical=[(v-a)*q+b for v,a,b in zip(point,source['anchor'],fitted['anchor'])]
            srcworld=[(v-a)*source['scale'] for v,a in zip(point,source['anchor'])]
            fitworld=[(v-a)*4.5 for v,a in zip(logical,fitted['anchor'])]
            assert max(abs(a-b) for a,b in zip(srcworld,fitworld))<1e-8
        checked+=1;peak=max(peak,len(rec['rects']))
for label in ['前冲','后撤']:
    for field in ['sourceFrames','frames']:
        assert d[label][field][0]==d[label][field][-1]==d['待机'][field][0]
for field in ['sourceFrames','frames']:assert d['受击与倒地'][field][-1]==d['起身'][field][0]
assert d['空轻']['airHoverWorld']==d['空重']['airHoverWorld']==100
first=d['败北']['frames'][0];b=Image.open(O/first['file']).getbbox()
idle=d['待机']['frames'][0];ib=Image.open(O/idle['file']).getbbox()
assert abs((b[3]-b[1])*first['scale']-(ib[3]-ib[1])*idle['scale'])<=4.5
for field in ['sourceFrames','frames']:
    assert d['胜利'][field][0]==d['胜利'][field][-1]==d['待机'][field][0]
light=d['轻攻三']['frames'][0];lb=Image.open(O/light['file']).getbbox()
assert abs((lb[3]-lb[1])*light['scale']-(ib[3]-ib[1])*idle['scale'])<=4.5
assert d['胜利']['sourceFrames'][1]['scale']==d['胜利']['sourceFrames'][2]['scale']
for file in ['work/furina_review_app.js','outputs/furina-design-20261010/size-review-app.js']:
    assert 'drawThrowRibbon' not in (R/file).read_text(encoding='utf-8')
print(json.dumps({'fileChecks':'pass','checkedFittedStates':checked,'peakRectangles':peak,'sourceProportionFailures':report['sourceProportionFailures'],'activeBankUnchanged':True,'anatomicalAcceptance':False},ensure_ascii=False))
