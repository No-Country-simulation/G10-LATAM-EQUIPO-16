"""Notebook explícito y ejecutable: datos, CUDA, tres entrenamientos, ONNX, RSS, inferencia."""
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
cells=[]
def md(text):cells.append(dict(cell_type='markdown',metadata={},source=text))
def code(text):
    ast.parse(text);cells.append(dict(cell_type='code',metadata={},execution_count=None,outputs=[],source=text))

md('''# MiniLM compartido + tres MLP independientes · RTX 4070 Ti SUPER · ONNX INT8

Flujo: **ver datos y etiquetas → una cabeza en CUDA → guardar en SSD → cerrar proceso → siguiente cabeza → exportar → validar → medir RAM → inferir**.

Cada tarea tiene su propio DataFrame y un único target. FAQ usa los títulos seleccionados de Stack Exchange como 1 y los comentarios como 0. Logro y sentimiento usan las respuestas de Gemini existentes. Sentimiento: negativo=0, neutro=0.5, mixto=0.5, positivo=1. El indeterminado queda en revisión.

Comparación controlada de cabezas: `384→16→4→1` frente a `384→64→32→16→4→1`. ReLU tras cada capa oculta, Sigmoid al salir. Se comparan sobre los mismos embeddings INT8 y splits.

**Un solo encoder:** MiniLM multilingüe L12, salida 384. Se reutiliza el encoder afinado de la etapa v2 en esta misma RTX. En esta comparación se congela y se entrenan únicamente las cabezas, por separado. La caché se calcula con el encoder INT8 CPU para coincidir con producción. Los tres entrenamientos no duplican ni modifican el encoder. El entrenamiento anterior del encoder está registrado en `artifacts_v2/mlp/training.json`.

El límite de 1,000 MB corresponde al proceso de inferencia. PyTorch de entrenamiento y Jupyter se ejecutan en la PC de 64 GB y no forman parte del servicio OCI. El paquete de producción no importa Torch/pandas/sklearn.
''')
code(r'''from pathlib import Path
import os,sys,json,gc,subprocess
from IPython.display import display,Code
ROOT=Path.cwd()
if not (ROOT/'train_mlp_head.py').exists():ROOT=ROOT/'2026-10-04'
assert (ROOT/'train_mlp_head.py').exists(),ROOT
OUT=ROOT/'artifacts_mlp_int8'
DEPLOY=ROOT/'deploy_mlp_int8'
TASKS=('es_faq','es_logro','sentimiento')
REENTRENAR=False
RECREAR_CACHE=False
REVALIDAR=False
print('PASO 0 · carpeta:',ROOT)
print('REENTRENAR=',REENTRENAR,'RECREAR_CACHE=',RECREAR_CACHE,'REVALIDAR=',REVALIDAR)

def execute_step(arguments):
    cmd=[sys.executable,'-u',*map(str,arguments)]
    print('LLAMADA EXPLÍCITA:',cmd,flush=True)
    process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
    for line in process.stdout:print(line,end='',flush=True)
    status=process.wait()
    if status:raise RuntimeError(f'Paso fallido ({status}); se detiene la secuencia.')
    print('Proceso terminado; sus modelos y memoria quedaron liberados.',flush=True)

def show_source(name):
    print('IMPLEMENTACIÓN:',name)
    display(Code((ROOT/name).read_text(encoding='utf-8-sig'),language='python'))
''')
md('''## 1. Encontrar y comprobar la RTX, CPU y RAM
Se llama a `nvidia-smi` y luego se comprueba CUDA con PyTorch **en otro proceso**. No se permite continuar un entrenamiento con CPU de forma silenciosa. El script de cada cabeza vuelve a comprobar GPU y muestra el dispositivo de modelo, embeddings y target.
''')
code(r'''import psutil
gpu=subprocess.run(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],capture_output=True,text=True,check=True).stdout.strip()
print('RTX ENCONTRADA:',gpu)
assert '4070 Ti SUPER' in gpu,gpu
if os.name=='nt':
    import winreg
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
        print('CPU:',winreg.QueryValueEx(key,'ProcessorNameString')[0])
print('Hilos lógicos:',psutil.cpu_count(),'RAM instalada GiB:',round(psutil.virtual_memory().total/2**30,2))
cuda_code="import torch; print('PyTorch:',torch.__version__,'CUDA:',torch.version.cuda); assert torch.cuda.is_available(); gpu=torch.cuda.get_device_name(0); print('GPU CUDA:',gpu); assert '4070 Ti SUPER' in gpu; x=torch.ones((1,384),device='cuda'); print('Tensor real:',x.shape,x.device); print('VRAM GiB:',torch.cuda.get_device_properties(0).total_memory/2**30)"
execute_step(['-c',cuda_code])
print('Kernel Jupyter sin PyTorch:', 'torch' not in sys.modules)
''')
md('''## 2. DataFrames y etiquetas antes de entrenar
Se abre, muestra y libera un DataFrame por vez. Se conservan los IDs, URLs y `split_group` de procedencia. Los splits originales se agrupan por conversación y se quitan duplicados. Los títulos solo supervisan FAQ; los comentarios etiquetados por Gemini supervisan logro/sentimiento. No se inventan targets de logro/sentimiento para los títulos.
''')
code('''def show_dataframe(task):
    import pandas as pd
    pd.set_option('display.max_colwidth',None)
    df=pd.read_json(ROOT/'data'/f'{task}.jsonl',lines=True)
    cols=['id_mensaje','id_original','mensaje',task,'split','url']
    gemini=task+'_gemini'
    if gemini in df:cols.insert(4,gemini)
    print('ABRIR DF:',task,'filas/columnas:',df.shape)
    print('HEAD del DataFrame que entrena esta cabeza:')
    display(df[cols].head())
    print('CONTEO DE ETIQUETAS:');display(df[task].value_counts().sort_index().rename('filas').to_frame())
    print('SPLITS Y ETIQUETAS:');display(pd.crosstab(df['split'],df[task]))
    assert df.id_mensaje.is_unique
    assert df.groupby('split_group')['split'].nunique().max()==1,'Conversación repetida entre splits'
    assert set(df[task].unique()) <= ({0,.5,1} if task=='sentimiento' else {0,1})
    for value in sorted(df[task].unique()):
        print('EJEMPLOS target=',value)
        display(df.loc[df[task].eq(value),cols].head(3))
    if task=='sentimiento':
        print('ETIQUETAS ORIGINALES GEMINI:');display(df.sentimiento_gemini.value_counts().to_frame())
        print('EJEMPLOS MIXTOS, target 0.5:');display(df.loc[df.sentimiento_gemini.eq('mixto'),cols].head(3))
    del df;gc.collect()
    print('DataFrame liberado antes de abrir el siguiente.')
''')
for task in ('es_faq','es_logro','sentimiento'):code(f"print('PASO 2 · {task}')\nshow_dataframe('{task}')")
code('''print('PROCEDENCIA Y TRANSFORMACIONES:')
display(json.loads((ROOT/'data/provenance.json').read_text(encoding='utf-8')))
print('Sentimiento indeterminado: se conserva en sentimiento_revision.jsonl, fuera del entrenamiento.')
print('Un target diferente y un entrenamiento separado por cabeza.')
''')
md('''## 3. Encoder afinado, exportación y caché en SSD
El encoder v2 fue afinado con CUDA. Esta etapa usa sus pesos congelados. El pooling es media ponderada por `attention_mask`: produce 384 valores por mensaje, sin normalización adicional. En serving se procesan los **primeros 128 tokens**, batch 1, hasta 8,000 caracteres.

El encoder se exportó a FP32 (470.22 MB) y se cuantizó con `quantize_dynamic`, QInt8, `MatMul` y `Gather`, resultando en 118.05 MB. `Gather` permite reducir la tabla multilingüe. La representación final del mismo encoder usa pesos externos en SSD. INT8 aplica a pesos y operaciones seleccionadas: ReLU/Sigmoid y otras operaciones conservan valores flotantes.

La caché `.npy` se escribe de un mensaje por vez. `mmap` lee solamente los bloques usados por una cabeza. La caché no es necesaria para servir. Si cambia encoder, tokenizer, datos o política de tokens, hay que regenerarla antes de reentrenar.
''')
code('''print('REGISTRO REAL DEL AFINADO ANTERIOR DEL ENCODER:')
prior=ROOT/'artifacts_v2/mlp/training.json'
if prior.exists():
    history=json.loads(prior.read_text(encoding='utf-8'))
    display({k:v for k,v in history.items() if k in ['hardware','epochs','batch_size','history']})
    del history
show_source('cache_int8.py')
if RECREAR_CACHE or not (OUT/'embeddings_int8.npy').exists():execute_step([ROOT/'cache_int8.py'])
else:print('REUTILIZAR caché INT8 existente en SSD:',OUT/'embeddings_int8.npy')
print('Tamaño caché MB:',(OUT/'embeddings_int8.npy').stat().st_size/1e6)
cache_metadata=json.loads((OUT/'embeddings_index.json').read_text(encoding='utf-8'))
print('Filas:',len(cache_metadata['ids']),'dimensiones:',384,'precisión:',cache_metadata['precision'],'tokens:',cache_metadata['max_tokens'])
del cache_metadata;gc.collect()
''')
md('''## 4. Definir y entrenar tres cabezas en RTX, por separado
Arquitecturas: pequeña `[384,16,4,1]`, profunda `[384,64,32,16,4,1]`. Cada cabeza tiene su propio optimizador, target y checkpoint. ReLU tras cada capa oculta. Durante el entrenamiento se usa BCEWithLogitsLoss para estabilidad; la sigmoide se aplica en evaluación y queda en ONNX.

AdamW: lr=0.001, weight_decay=0.001; batches=128; seed=42; hasta 100 épocas; parada tras 15 sin mejorar BCE de validation. Solo train ajusta pesos. Cada proceso muestra `features cuda:0`, `target cuda:0` y `head cuda:0`, guarda el mejor checkpoint y exporta su cabeza FP32 y después INT8, y termina antes de la próxima.

Con REENTRENAR=False se muestran los registros **de entrenamientos realmente ejecutados**. Con True se repiten las seis ejecuciones de forma secuencial. El proceso PyTorch puede superar 1 GB en la PC local; no se carga en el runtime OCI.
''')
code("show_source('train_mlp_head.py')")
code('''def one_head(architecture,task):
    path=OUT/architecture/task/'report.json'
    print('CABEZAS SECUENCIALES ·',architecture,task)
    if REENTRENAR or not path.exists():execute_step([ROOT/'train_mlp_head.py',task,architecture])
    else:
        print('Cabeza ya entrenada; registro guardado:',path)
        logfile=OUT/'logs'/f'{architecture}_{task}.log'
        if logfile.exists():
            text=logfile.read_text(encoding='utf-8')
            if '[9] FIN.' in text:print(text)
            else:print('El log conserva el intento interrumpido. El reintento completó; abajo se muestra su report.json y toda su historia.')
    report=json.loads(path.read_text(encoding='utf-8'))
    print('RTX realmente usada:',report['gpu'],'CHECK CUDA:',report['cuda_checks'])
    print('Dimensiones:',report['dims'],'parámetros:',report['parameters'],'VRAM pico MB:',report['peak_training_vram_mb'])
    print('Tiempo segundos:',report['train_seconds'],'épocas:',report['epochs'])
    print('TODAS LAS ÉPOCAS:');display(report['history'])
    print('VALIDATION:');display(report['validation'])
    print('TEST INT8:');display(report['test'])
    print('Error CUDA / ONNX FP32:',report['fp32_parity_error'])
    print('Cortes elegidos SOLO en validation:',report['threshold'])
    print('ONNX INT8 en SSD:',path.parent/'head_int8.onnx','bytes:',(path.parent/'head_int8.onnx').stat().st_size)
    del report;gc.collect()
    print('FIN DE CABEZA. No hay modelo de entrenamiento vivo en el kernel.')
''')
for arch in ('small','deep'):
    for task in ('es_faq','es_logro','sentimiento'):
        code(f"one_head('{arch}','{task}')")
md('''## 5. Comparar y documentar la decisión
Se usa el F1 macro medio de las tres tareas en validation. La regla acepta la profunda si pierde como máximo 0.005 frente a la pequeña, conforme a la preferencia por la profunda cuando la diferencia es pequeña y el costo mínimo. Test informa el resultado y no elige arquitectura.

La profunda no demostró superioridad en esta prueba: ambas están próximas y la pequeña también es válida. El costo extra de estas tres cabezas es aproximadamente 75 KB. La RAM del encoder/runtime es mucho más relevante.

Para FAQ y logro se informa F1 positivo; sentimiento se agrupa en negativo/central/positivo y se informa macro F1 y MAE. Neutro/mixto comparten la clase central. Los cortes de predicción se ajustan solo en validation; los targets 0/0.5/1 no se alteran.
''')
code('''execute_step([ROOT/'run_sequential_mlp.py'])
summary=json.loads((OUT/'comparison.json').read_text(encoding='utf-8'))
import pandas as pd
rows=[]
for architecture,tasks in summary['architectures'].items():
    for task,r in tasks.items():
        rows.append(dict(arquitectura=architecture,tarea=task,dimensiones=str(r['dims']),parametros=r['parameters'],
                         validation_macro_f1=r['validation']['f1_macro'],test_f1=r['test'].get('f1',r['test']['f1_macro']),
                         segundos=r['train_seconds'],onnx_int8_bytes=(OUT/architecture/task/'head_int8.onnx').stat().st_size))
display(pd.DataFrame(rows))
print('F1 macro promedio validation:',summary['validation_macro_f1'])
print('SELECCIÓN:',summary['selected'],summary['selection_rule'])
del rows,summary;gc.collect()
''')
md('''## 6. Guardar paquete ONNX portable y comprobar operadores
Un encoder compartido, tokenizer y tres archivos de cabezas. Los pesos externos ONNX se dividen en archivos de menos de 100 MB para GitHub; deben permanecer junto al grafo encoder.onnx. No se duplican los pesos por cabeza. El código conserva ReLU intermedias y Sigmoid final y comprueba presencia de operaciones enteras.
''')
code('''show_source('package_mlp.py')
if REENTRENAR or not (DEPLOY/'config.json').exists():execute_step([ROOT/'package_mlp.py'])
else:print('Paquete final ya escrito en SSD:',DEPLOY)
config=json.loads((DEPLOY/'config.json').read_text(encoding='utf-8'))
print('Arquitectura final:',config['dims'],'precisión:',config['precision'])
display(pd.DataFrame([dict(archivo=k,bytes=v['bytes']) for k,v in config['files'].items()]))
print('Total MB en SSD:',sum(v['bytes'] for v in config['files'].values())/1e6)
del config;gc.collect()
''')
md('''## 7. F1 del paquete real, batch 1 y límites del contrato
Se evalúa el encoder INT8 portable y cada cabeza INT8 de una en una con todos los ejemplos test. Se compara el embedding contra la caché. La cuantización dinámica puede depender del batch: se reajustan los cortes usando exclusivamente validation con batch 1 y se miden después los ejemplos test con el mismo batch de producción.

El score de sentimiento sigue siendo un índice continuo entre 0 y 1. Sus cortes solo permiten calcular F1 de tres clases; no cambian el JSON de salida ni garantizan calibración de probabilidades. La cabeza logro tiene pocos positivos: se muestran soporte y matriz de confusión para interpretar F1.
''')
code('''show_source('evaluate_mlp_package.py')
if REVALIDAR or REENTRENAR or not (OUT/'package_evaluation.json').exists():execute_step([ROOT/'evaluate_mlp_package.py'])
evaluation=json.loads((OUT/'package_evaluation.json').read_text(encoding='utf-8'))
print('Máximo error embedding caché / paquete:',evaluation['max_embedding_error_vs_cache'])
print('Alcance:',evaluation['scope'])
for task,record in evaluation['tasks'].items():
    print('TAREA:',task,'cortes validation batch 1:',record['threshold'])
    print('VALIDATION:');display(record['validation_batch1'])
    print('TEST:');display(record['test_batch1'])
    print('Truncados test:',record['truncated_test'],'rechazados test:',record['rejected_test'])
del evaluation;gc.collect()
''')
md('''## 8. Inferencia paso a paso y RAM desde el arranque
El wrapper valida entrada, tokeniza, llama a un solo encoder, obtiene `(1,384)`, carga una cabeza, ejecuta su MLP, guarda el float y libera esa sesión antes de cargar otra. Las solicitudes se serializan con un lock. Se rechaza exceso de caracteres y no se admiten lotes externos.

El supervisor muestrea RSS cada 10 ms desde antes de importar ONNX. Prueba 104 solicitudes, incluidas 8,000 caracteres y truncación a 128 tokens; verifica entradas inválidas. Si observa 1,000 MB, termina el hijo. Se busca además estar bajo 700 MB para dejar margen al SO.

Esta medida corresponde a Windows/Ryzen. La VM OCI completa incluye SO/API/otros servicios y todavía no se ha probado allí. En Linux se incluye un ejemplo de `MemoryMax=700000000` para aplicar un límite al proceso mediante cgroup; hay que integrarlo con el servidor real y repetir la medida. Un worker, batch 1, 128 tokens, 8,000 caracteres.
''')
code("show_source('serve_mlp_int8.py')\nshow_source('probe_mlp_memory.py')")
code('''execute_step([ROOT/'probe_mlp_memory.py'])
memory=json.loads((OUT/'memory.json').read_text(encoding='utf-8'))
print('PICO desde arranque MB:',memory['cold_to_hot_peak_rss_mb'])
print('¿Debajo de 1,000 MB?',memory['under_1000_mb'],'¿Debajo de 700 MB?',memory['under_700_mb'])
print('RAM por etapa MB:',memory['stages_mb'])
print('Latencia p50 / p95 ms:',memory['p50_ms'],memory['p95_ms'])
print('Checks de rechazo:',memory['boundary_checks'],'imports de librerías pesadas:',memory['imported_heavy_modules'])
print('SALIDA REAL del wrapper:');display(memory['example'])
assert memory['under_1000_mb'] and not memory['imported_heavy_modules']
del memory;gc.collect()
''')
md('''## 9. Contrato y uso del wrapper
Entrada exacta: `{id_mensaje: int64, mensaje: string}`. ID se conserva; máximo 8,000 caracteres Unicode, texto no vacío, primeros 128 tokens. Salida exacta: `{id_mensaje: int64, es_faq: float[0,1], es_logro: float[0,1], sentimiento: float[0,1]}`.

`serve_mlp_int8.Predictor()` se instancia una vez por proceso. `predictor(entrada, trace=True)` muestra pasos. En OCI no se importa runtime.py ni los scripts de entrenamiento. `serve_jsonl.py` ofrece entrada/salida JSON por línea con el mismo predictor persistente. Los errores de validación se devuelven aparte de las respuestas exitosas.

Instalar dependencias CPU Linux usando requirements-serving.txt; los wheels/DLL de Windows en deps/ no se suben ni se copian a OCI. Conservar encoder.onnx, weights-*.bin, tokenizer.json, heads/ y config.json juntos.
''')
code("show_source('serve_jsonl.py')\nprint((ROOT/'mlp-oci.service.example').read_text(encoding='utf-8'))")
md('''## 10. Registros anteriores y conclusión
La comparación original `384→1` frente a `384→16→4→1` se conserva en `artifacts_v2/comparison.json` y en el notebook anterior. Usó el afinado del encoder y una política de ventanas distinta; no debe mezclarse con esta comparación controlada sobre el mismo encoder INT8 congelado. PCA fue un experimento anterior y no forma parte del paquete final.

La profunda cumple el diseño pedido y cuesta poco; no ofrece una mejora de F1 demostrada sobre la pequeña. El encoder INT8 y un runtime CPU liviano son los cambios principales para RAM. FAQ funciona bien en estos datos; logro y sentimiento todavía tienen errores visibles y requieren validación con mensajes del dominio real. No se afirma que el proceso completo en OCI ya esté validado.

Fuentes técnicas: [cuantización ONNX Runtime](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html), [pesos externos ONNX](https://onnx.ai/onnx/api/external_data_helper.html), [shapes OCI](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm).
''')
for i,c in enumerate(cells):c['id']=f'mlp-int8-{i:02d}'
notebook=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),language_info=dict(name='python',version='3.11')),nbformat=4,nbformat_minor=5)
(ROOT/'MiniLM_3_cabezas_comparacion.ipynb').write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding='utf-8')
print('Notebook MLP creado:',len(cells),'celdas.')
