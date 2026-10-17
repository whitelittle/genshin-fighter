"""Rules and native input integration for the complete teaching candidate."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v11-20261016';E=OUT/'verification';E.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'runtime/tests'));sys.path.insert(0,str(ROOT/'runtime/tools'))
from mock_flow import RuntimeClient,wait
from compact_assets import python_table
RuntimeClient.source=OUT/'genshin_fighter.lua'
if __name__=='__main__':
 c=RuntimeClient()
 result=python_table(c.lua('(function()'+(ROOT/'runtime/tests/teaching_complete_rules.lua').read_text(encoding='utf-8')+' end)()'))
 result['clientSha256']=hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest()
 (E/'complete-rules.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=True))
