"""Interactive local preview using the existing mock client and canvas UI."""
from pathlib import Path
import importlib.util,sys,json
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
sys.path.insert(0,str(ROOT/'tests'))
from mock_flow import RuntimeClient
spec=importlib.util.spec_from_file_location('runtime_preview',REPO/'game/tools/preview/server.py')
preview=importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
preview.Client=RuntimeClient
preview.HERE=ROOT/'tools'
if __name__=='__main__':
    if '--scene' not in sys.argv:sys.argv.extend(['--scene','intro'])
    if '--device' not in sys.argv:sys.argv.extend(['--device','Mobile'])
    if '--canvas' not in sys.argv:sys.argv.extend(['--canvas','2832x1280'])
    preview.main()
