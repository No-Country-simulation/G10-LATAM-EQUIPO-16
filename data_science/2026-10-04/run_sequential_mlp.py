"""Nunca ejecutar dos cabezas simultáneamente; stdout completo queda en SSD."""
import sys,json,subprocess
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts_mlp_int8';logs=OUT/'logs';logs.mkdir(exist_ok=True)
for architecture in ['small','deep']:
    for task in ['es_faq','es_logro','sentimiento']:
        path=OUT/architecture/task/'report.json'
        if path.exists():print('Reutilizar cabeza ya guardada:',architecture,task,flush=True);continue
        print('INICIAR una cabeza:',architecture,task,flush=True)
        with (logs/f'{architecture}_{task}.log').open('w',encoding='utf-8') as log:
            child=subprocess.Popen([sys.executable,str(ROOT/'train_mlp_head.py'),task,architecture],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
            for line in child.stdout:log.write(line);log.flush();print(line,end='',flush=True)
            code=child.wait()
            if code:raise RuntimeError(f'Fallo {architecture} {task}; exit code {code}; se detiene secuencia.')
        print('PROCESO CERRADO:',architecture,task,flush=True)
reports={architecture:{task:json.loads((OUT/architecture/task/'report.json').read_text(encoding='utf-8')) for task in ['es_faq','es_logro','sentimiento']} for architecture in ['small','deep']}
quality={a:sum(v['validation']['f1_macro'] for v in tasks.values())/3 for a,tasks in reports.items()}
# Arquitectura profunda si está a <=0.005 del mejor score, por la preferencia del usuario y su tamaño pequeño.
selected='deep' if quality['deep']>=quality['small']-.005 else 'small'
summary=dict(architectures=reports,validation_macro_f1=quality,selected=selected,
             selection_rule='F1 macro medio de validation. Deep si no pierde más de 0.005 frente a small; los pesos siguen siendo pequeños. Test no selecciona.')
(OUT/'comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print('SELECCION',selected,quality,flush=True)
