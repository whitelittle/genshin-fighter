from pathlib import Path
p=Path('runtime/source/render/gf_fview.lua');t=p.read_text(encoding='utf-8').replace("a.key=='furina' and self.key~='furina'", "a.key=='furina' and not Registry.provider(self.key)");p.write_text(t,encoding='utf-8')
p=Path('runtime/tests/mock_flow.py');t=p.read_text(encoding='utf-8').replace("scene.built==4 and not GF_APP().poolNext", "scene.built==4 and not GF_APP().poolNext and not GF_APP().trans");p.write_text(t,encoding='utf-8')
