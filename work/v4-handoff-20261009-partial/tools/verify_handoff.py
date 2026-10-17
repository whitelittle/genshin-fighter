from pathlib import Path
import json, hashlib
r=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((r/'BASELINE_VERIFICATION.json').read_text())['files']
for name,value in base.items():
    assert (r/name).is_file() and sha(r/name)==value, name
m=json.loads((r/'V4/evidence/full-delivery-20261009/ACTUAL_MANIFEST.json').read_text())
good=[x for x in m['records'] if 'output' in x]
assert len(good)==63 and sum(x['visible_pose_count'] for x in good)==252
for x in good:
    assert sha(r/x['output'])==x['sha256'], x['id']
    fit=json.loads((r/x['fit_report']).read_text())
    assert all(f['exact_reconstruction'] for f in fit['frames'])
assert m['game_integrated']==0 and m['accepted']==0 and not m['quota_exhausted']
print('PASS: baseline unchanged; 63 sources / 252 poses; candidate status accurate.')
