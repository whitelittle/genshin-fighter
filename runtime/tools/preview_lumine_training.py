"""Native gf_ui simulator, isolated Lumine/Lawachurl training candidate."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview
import preview_tutorial_v15 as merged
preview.preview.Client=merged.MergedClient
if __name__=='__main__':
    if '--scene' not in sys.argv:sys.argv.extend(['--scene','intro'])
    if '--args' not in sys.argv:sys.argv.extend(['--args','{}'])
    if '--device' not in sys.argv:sys.argv.extend(['--device','KeyboardAndMouse'])
    if '--canvas' not in sys.argv:sys.argv.extend(['--canvas','1600x900'])
    preview.preview.main()
