"""Capture a real two-minute experiment with the three required matching drivers."""
import subprocess,sys,time,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
patterns={'Ravi':'bangalore.koramangala.*','Meena':'bangalore.*.food','Control':'bangalore.#'}
processes=[];handles=[]
try:
    for name,pattern in patterns.items():
        handle=(OUT/f'driver-{name}.txt').open('w');handles.append(handle)
        proc=subprocess.Popen([sys.executable,'-u','-m','stream.driver',name,pattern],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT);processes.append(proc)
    for _ in range(60):
        if all((OUT/f'driver-{name}.txt').exists() and 'READY' in (OUT/f'driver-{name}.txt').read_text() for name in patterns):break
        if any(proc.poll() is not None for proc in processes):raise RuntimeError('Driver failed before READY')
        time.sleep(.5)
    else:raise RuntimeError('Drivers not ready')
    run=subprocess.run([sys.executable,'-u','-m','stream.dispatcher'],cwd=ROOT,capture_output=True,text=True,timeout=135)
    (OUT/'dispatcher.txt').write_text(run.stdout+run.stderr);assert run.returncode==0
    time.sleep(1)
finally:
    for proc in processes:
        if proc.poll() is None:proc.terminate()
    for proc in processes:
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:proc.kill()
    for handle in handles:handle.close()
summary={}
for name in patterns:
    text=(OUT/f'driver-{name}.txt').read_text()
    summary[name]={'ack_count':sum(l.startswith('ACK ') for l in text.splitlines()),'discard_count':sum(l.startswith('DISCARD ') for l in text.splitlines()),'probe_food_received':f'ACK {name} probe-food bangalore.koramangala.food' in text}
    assert summary[name]['discard_count']==6
    assert summary[name]['probe_food_received']
assert 'DROPPED probe-drop chennai.whitefield.ride' in run.stdout
assert 'ACK Control probe-short bangalore.koramangala' in (OUT/'driver-Control.txt').read_text()
for name in ['Ravi','Meena']:assert 'probe-short' not in (OUT/f'driver-{name}.txt').read_text()
summary['elapsed_line']=next(l for l in run.stdout.splitlines() if l.startswith('FINISHED'))
(OUT/'stream-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
