"""Supervisor del proceso de inferencia: pico desde arranque, corte a 1,000 MB."""
import sys,json,subprocess,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts_mlp_int8'

def main():
    report=OUT/'memory.json';log=OUT/'inference.log';peak=0;samples=0;exceeded=False
    command=[sys.executable,'-u',str(ROOT/'serve_mlp_int8.py'),'--report',str(report)]
    print('LLAMADA:',command,flush=True)
    with log.open('w',encoding='utf-8') as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        process=psutil.Process(child.pid)
        while child.poll() is None:
            try:peak=max(peak,process.memory_info().rss);samples+=1
            except psutil.NoSuchProcess:break
            if peak>=1_000_000_000:exceeded=True;child.terminate();break
            time.sleep(.01)
        code=child.wait()
    print(log.read_text(encoding='utf-8'),flush=True)
    if exceeded:raise MemoryError('Supervisor detuvo inferencia: alcanzó 1,000 MB RSS')
    if code:raise RuntimeError(f'Inferencia falló: {code}')
    result=json.loads(report.read_text(encoding='utf-8'))
    result.update(cold_to_hot_peak_rss_mb=peak/1e6,sampling_ms=10,samples=samples,budget_bytes=1_000_000_000,
        under_1000_mb=peak<1_000_000_000,under_700_mb=peak<700_000_000,scope='Proceso Windows local; no incluye SO/API ni comprueba OCI')
    assert not result['imported_heavy_modules']
    assert result['under_1000_mb']
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PICO DE RAM DESDE ARRANQUE MB:',peak/1e6,'<1000:',result['under_1000_mb'],'<700:',result['under_700_mb'],flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
