"""Read-only candidate gate audit; no anatomical or device acceptance inferred."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent/'v4-handoff-20261009-partial'
V=R/'V4'
batch=json.loads((V/'evidence/codex-batch-20261009/BATCH_MANIFEST.json').read_text(encoding='utf-8'))
overlay=json.loads((V/'design/CODEX_CURRENT_OVERLAY_20261009.json').read_text(encoding='utf-8'))
bad_prefixes=('needs_','requires_','historical','deferred')
checked=0; fitted=0; findings=[]
for rec in batch['records']:
    source=R/rec['source']
    assert source.is_file(),rec['id']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==rec['sha256'],rec['id']
    prompt=V/'prompts/codex-batch-20261009'/f"{rec['id']}.txt"
    assert prompt.is_file() and prompt.read_text(encoding='utf-8').strip(),rec['id']
    checked+=1
    folder=R/rec['evidence_folder'] if rec.get('evidence_folder') else None
    if not folder or not (folder/'fit.json').exists():
        findings.append({'id':rec['id'],'gate':'extraction_missing_or_failed'})
        continue
    report=json.loads((folder/'fit.json').read_text(encoding='utf-8'))
    assert report['source_sha256']==rec['sha256'],rec['id']
    assert report.get('runtime') is False and report.get('accepted') is False,rec['id']
    assert all(f.get('exact_reconstruction') for f in report['frames']),rec['id']
    fitted+=1
    contacts=[f['frame'] for f in report['frames'] if f.get('full_canvas_boundary_contact')]
    if contacts:findings.append({'id':rec['id'],'gate':'canvas_contact_requires_review','frames':contacts})
    findings.append({'id':rec['id'],'gate':'world_anchors_and_four_visual_checks_pending'})
for entry in overlay['entries']:
    assert entry['codex_runtime'] is False and entry['codex_visual_accepted'] is False
    preferred=entry.get('codex_preferred_candidate')
    if preferred:
        rec=next(r for r in entry['codex_sources'] if r['source']==preferred)
        assert rec['offline_fit_passed'] and not rec['status'].startswith(bad_prefixes),entry['actionId']
assert overlay['codex_game_integrated']==0 and overlay['codex_user_accepted']==0
historical=V/'data/codex-candidates-20261009'
receipt=json.loads((historical/'verification.json').read_text(encoding='utf-8'))
assert receipt['assets']==34 and receipt['frames']==169
for name,key in [('candidate-data.json','json_sha256'),('candidate-data.lua','lua_sha256')]:
    assert hashlib.sha256((historical/name).read_bytes()).hexdigest()==receipt[key],name
result={'source_hashes_and_prompts_verified':checked,'fit_reports_verified':fitted,
        'preferred_candidate_exclusion_passed':True,'historical_169_frame_snapshot_unchanged':True,
        'runtime_and_acceptance_false_verified':True,'findings':findings,
        'scope':'file/data gates only; not anatomy, animation continuity, simulation, performance or device validation'}
out=V/'evidence/codex-batch-20261009/CANDIDATE_GATE_AUDIT.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='findings'},ensure_ascii=False))
