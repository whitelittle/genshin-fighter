"""Run the isolated two-role gameplay prototype in the existing gf_ui simulator."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview
preview.RuntimeClient.source=preview.REPO/'outputs/nahida-raiden-rework-20261015/candidate.lua'
if __name__=='__main__':preview.preview.main()
