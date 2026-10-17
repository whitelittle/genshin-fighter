"""Read-only source integrity and diagnostic gates; never implies acceptance."""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image

V = Path(__file__).resolve().parents[1]
R = V.parent
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    queue = json.loads((V/'design/ACTION_QUEUE_20261009.json').read_text())
    locks = json.loads((V/'design/IDENTITY_REFERENCE_LOCK.json').read_text())
    refs = []
    for lock in locks['references']:
        path = R/lock['path']
        refs.append({'character': lock['character'], 'exists': path.exists(),
                     'hash_matches': path.exists() and sha(path) == lock['sha256'],
                     'accepted': False})
    reports = []
    for spec in queue['generation_specs']:
        if not spec.get('output'):
            continue
        path = R/spec['output']
        report = {'id': spec['id'], 'exists': path.exists(),
                  'hash_matches': path.exists() and sha(path) == spec['sha256']}
        if not report['hash_matches']:
            reports.append(report)
            continue
        with Image.open(path) as im:
            report['mode'] = im.mode
            rgba = np.asarray(im.convert('RGBA'))
        alpha = rgba[:,:,3]
        report['transparent_fraction'] = round(float((alpha == 0).mean()), 6)
        report['has_real_alpha'] = im.mode == 'RGBA' and bool((alpha == 0).any())
        cols, rows = spec['grid']
        h,w = alpha.shape
        cells = []
        for n in range(cols*rows):
            a=alpha[n//cols*h//rows:(n//cols+1)*h//rows,
                    n%cols*w//cols:(n%cols+1)*w//cols]
            y,x=np.where(a>32)
            bbox = [int(x.min()),int(y.min()),int(x.max()),int(y.max())] if len(x) else None
            edges = [int((a[0]>32).sum()),int((a[-1]>32).sum()),
                     int((a[:,0]>32).sum()),int((a[:,-1]>32).sum())]
            cells.append({'pose': n+1, 'alpha32_bbox': bbox,
                          'edge_pixels_top_bottom_left_right': edges,
                          'edge_clear': not any(edges)})
        report['cells'] = cells
        report['all_cells_edge_clear'] = all(c['edge_clear'] for c in cells)
        report['source_gate'] = ('candidate_requires_visual_review' if
            report['has_real_alpha'] and report['all_cells_edge_clear'] else 'needs_correction')
        report['anchors_measured'] = False
        report['accepted'] = False
        reports.append(report)
    result={'identity_references': refs, 'sources': reports,
            'limitations': ['Alpha and hashes cannot prove anatomy, motion or costume consistency.',
                           'Diagnostic fit is not V3 painter or runtime validation.']}
    out=V/'evidence/resume-20261009/source-audit.json'
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'references':len(refs), 'reference_hashes_valid':all(x['hash_matches'] for x in refs),
                      'sources':len(reports), 'source_hashes_valid':all(x['hash_matches'] for x in reports),
                      'report':str(out.relative_to(R))},ensure_ascii=False))
if __name__ == '__main__':
    main()
