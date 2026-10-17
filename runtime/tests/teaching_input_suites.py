"""Run existing teaching suites against the isolated input repair."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
suite=sys.argv[1]
target=sys.argv[2] if len(sys.argv)>2 else 'outputs/tutorial-input-v15-20261016'
source=ROOT/'runtime/tests/teaching_walk.py'
code=source.read_text(encoding='utf-8').replace("OUT=ROOT/'outputs/tutorial-walk-v14-20261016'",f"OUT=ROOT/'{target}'")
# Nested confirmation recipe also needs the repaired output path.
code=code.replace('"OUT=ROOT/\'outputs/tutorial-walk-v14-20261016\'"',f'"OUT=ROOT/\'{target}\'"')
sys.argv=[str(source),suite]
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
