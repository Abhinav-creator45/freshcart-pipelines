"""Run the actual Mage CLI for all five required depth values."""
from pathlib import Path
import subprocess,sys,json,re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
rows=[]
for depth in range(1,6):
    (ROOT/'iris_predictions.csv').unlink(missing_ok=True)
    cmd=[str(Path(sys.executable).with_name('mage')),'run','iris_project','iris_classifier','--test','--runtime-vars',json.dumps({'max_depth':depth})]
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=120)
    log=r.stdout+r.stderr
    (OUT/f'iris-depth-{depth}.txt').write_text(log)
    match=re.search(r'Test accuracy = ([0-9.]+)',log)
    rows.append({'max_depth':depth,'accuracy':float(match.group(1)) if match else None,'passed':r.returncode==0,'csv_created':(ROOT/'iris_predictions.csv').exists()})
    assert rows[-1]['csv_created']==(depth!=1), rows[-1]
print(json.dumps(rows,indent=2))
(OUT/'iris-depths.json').write_text(json.dumps(rows,indent=2)+'\n')
r=subprocess.run([str(Path(sys.executable).with_name('mage')),'run','iris_project','iris_classifier','--test'],cwd=ROOT,capture_output=True,text=True,timeout=120)
(OUT/'iris-default.txt').write_text(r.stdout+r.stderr)
assert r.returncode==0
print('Restored default depth 3 successfully')
