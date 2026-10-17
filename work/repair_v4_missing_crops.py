"""Re-create three diagnostic PNG crops from the intact, hash-verified source sheet."""
from pathlib import Path
import hashlib, json
from PIL import Image

R=Path(__file__).resolve().parent/'v4-handoff-20261009-partial'
NAME='tartaglia-crouchheavy-body-full-v1'
folder=R/'V4/evidence/full-delivery-20261009'/NAME
fit=json.loads((folder/'fit.json').read_text(encoding='utf-8'))
job=next(j for j in json.loads((R/'V4/design/FULL_PRODUCTION_JOBS_20261009.json').read_text(encoding='utf-8'))['jobs'] if j['id']==NAME)
source=R/'V4/assets/full-delivery-20261009'/f'{NAME}.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==fit['source_sha256']
im=Image.open(source).convert('RGBA');w,h=im.size;cols,rows=job['grid']
def crop(n):
    box=(n%cols*w//cols,n//cols*h//rows,(n%cols+1)*w//cols,(n//cols+1)*h//rows)
    return im.crop(box),box
control,_=crop(3)
assert control.tobytes()==Image.open(folder/'source-3.png').convert('RGBA').tobytes()
records=[]
for n in range(3):
    path=folder/f'source-{n}.png'
    assert not path.exists(),'Refuse to overwrite an existing diagnostic crop'
    frame,box=crop(n);frame.save(path)
    assert Image.open(path).convert('RGBA').tobytes()==frame.tobytes()
    records.append({'path':path.relative_to(R).as_posix(),'crop_box':box,
                    'archive_png_sha256':fit['frames'][n]['source_sha256'],
                    'recreated_png_sha256':sha(path),'byte_identical':sha(path)==fit['frames'][n]['source_sha256'],
                    'status':'regenerated diagnostic crop, not recovered original compressed PNG bytes'})
report={'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),
        'method':'Original process_full_production.py nominal grid cropping; unchanged fourth crop used as pixel control',
        'files':records,'archive_missing_shard':'V4_1M_0448.part','archive_original_sha256_restored':False}
(R/'LOCAL_CROP_REGENERATION.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
