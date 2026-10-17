"""Preview the audited merge; expose the actually loaded hash for stale-build checks."""
from pathlib import Path
import hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview
SOURCE=preview.REPO/'outputs/tutorial-polish-v12-20261016/genshin_fighter.lua'
class MergedClient(preview.RuntimeClient):
    source=SOURCE
    def __init__(self,**kwargs):
        self.loaded_sha=hashlib.sha256(self.source.read_bytes()).hexdigest()
        super().__init__(**kwargs)
        assert hashlib.sha256(self.source.read_bytes()).hexdigest()==self.loaded_sha
    def stats(self):
        result=super().stats()
        result.update(clientSha256=self.loaded_sha,source=self.source.relative_to(preview.REPO).as_posix())
        return result
preview.preview.Client=MergedClient
if __name__=='__main__':
    if '--scene' not in sys.argv:sys.argv.extend(['--scene','intro'])
    if '--args' not in sys.argv:sys.argv.extend(['--args','{}'])
    if '--canvas' not in sys.argv:sys.argv.extend(['--canvas','1600x900'])
    preview.preview.main()
