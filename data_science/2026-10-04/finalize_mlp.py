"""Documentar resultados reales y construir manifiesto de la entrega, sin cargar modelos."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts_mlp_int8'

def delivery_files():
    names=['.gitignore','.gitattributes','MiniLM_3_cabezas_comparacion.ipynb','MiniLM_3_cabezas_antes_PCA.ipynb',
        'build_mlp_notebook.py','execute_mlp_notebook.py','cache_int8.py','train_mlp_head.py','run_sequential_mlp.py',
        'package_mlp.py','evaluate_mlp_package.py','serve_mlp_int8.py','serve_jsonl.py','probe_mlp_memory.py',
        'finalize_mlp.py','build_delivery.py','requirements-serving.txt','requirements-training.txt','mlp-oci.service.example',
        'README.md','COMPARACION_MLP_INT8.md','CONTRATO.md']
    files=[ROOT/name for name in names]
    files += [p for folder in ['data','deploy_mlp_int8'] for p in (ROOT/folder).rglob('*') if p.is_file()]
    files += [p for p in OUT.rglob('*') if p.is_file() and p.suffix in ['.json','.log','.onnx','.pt']]
    files += [ROOT/'artifacts_v2/comparison.json',ROOT/'artifacts_v2/mlp/training.json',ROOT/'artifacts_v2/linear/training.json']
    return sorted(set(p for p in files if p.exists()))

def main():
    comparison=json.loads((OUT/'comparison.json').read_text(encoding='utf-8'))
    memory=json.loads((OUT/'memory.json').read_text(encoding='utf-8'))
    evaluation=json.loads((OUT/'package_evaluation.json').read_text(encoding='utf-8'))
    config=json.loads((ROOT/'deploy_mlp_int8/config.json').read_text(encoding='utf-8'))
    table='| Cabeza | F1 test batch 1 | Soporte |\n|---|---:|---:|\n'
    for task,r in evaluation['tasks'].items():
        m=r['test_batch1'];table+=f"| {task} | {m.get('f1',m['f1_macro']):.4f} | {m['support']} |\n"
    readme=f'''# MiniLM + tres MLP independientes · ONNX INT8

Abrir **MiniLM_3_cabezas_comparacion.ipynb**, ejecutado con outputs reales y cero errores. Muestra hardware, DataFrames/etiquetas, las seis ejecuciones CUDA, exportación, comparación, RAM y traza de inferencia.

Un encoder compartido MiniLM multilingüe L12 (384 dimensiones), afinado previamente en RTX 4070 Ti SUPER y congelado en esta comparación; tres cabezas independientes **384→64→32→16→4→1**, ReLU intermedias y Sigmoid final. Se compararon con 384→16→4→1 usando los mismos embeddings INT8. Se entrenan por separado con RTX: una cabeza, guardar SSD, terminar proceso, siguiente. La caché INT8 se genera en CPU de un mensaje por vez y se lee con mmap. No hay PCA en el paquete final.

FAQ: títulos seleccionados de Stack Exchange=1, comentarios=0. Logro: etiquetas Gemini 0/1. Sentimiento Gemini: negativo=0, neutro/mixto=0.5, positivo=1; un indeterminado en revisión. Datos preparados: FAQ 9782, logro 4782, sentimiento 4781. No se asignan etiquetas inexistentes a títulos. Cada DataFrame tiene su propio target. Se mantienen splits por conversación y se eliminan duplicados.

Resultados del paquete INT8 completo, encoder y cabeza CPU batch 1:

{table}

Sentimiento usa F1 macro de negativo/central/positivo y MAE; FAQ/logro usan F1 de la clase positiva. Los cortes se eligen exclusivamente en validation. Logro tiene 18 positivos test: F1 modesto requiere mejorar y validar en mensajes del dominio real. El score no está calibrado como probabilidad.

RAM de proceso desde arranque: **{memory['cold_to_hot_peak_rss_mb']:.2f} MB**; batch 1, primeros 128 tokens, 8000 caracteres, una solicitud simultánea. Latencia local p50 {memory['p50_ms']:.2f} ms / p95 {memory['p95_ms']:.2f} ms, 100 muestras tras 4 de calentamiento, mezcla de textos cortos y límite. Se muestrea cada 10 ms y se verifican 5 rechazos de entradas inválidas. Es Windows/Ryzen 8700F, no la VM OCI. El total de 1 GB en OCI incluye SO/API: validar allí; ejemplo cgroup con MemoryMax=700000000 para dejar margen. Los picos PyTorch/Jupyter de entrenamiento local no pertenecen al servicio.

El paquete deploy_mlp_int8 ocupa {sum(v['bytes'] for v in config['files'].values())/1e6:.2f} MB en SSD. Incluye un grafo encoder, dos archivos de pesos externos, tokenizer, config y tres cabezas de 36,350 bytes cada una. Conservar todos juntos. INT8 cuantiza MatMul/Gather del encoder y MatMul de cabezas; ReLU/Sigmoid y otras operaciones siguen en punto flotante.

Uso de producción:

```python
from serve_mlp_int8 import Predictor
predictor = Predictor()  # crear UNA vez por worker
salida = predictor({{'id_mensaje': 123, 'mensaje': 'Gracias, ya funciona.'}}, trace=True)
```

El wrapper solo importa numpy, onnxruntime CPU, tokenizers y psutil. Un encoder vivo, una cabeza cargada/usada/liberada por paso; lock para serializar solicitudes. serve_jsonl.py acepta JSON por línea y mantiene el predictor. No importar runtime.py ni PyTorch para servir. Instalar requirements-serving.txt en Linux; no copiar DLL/wheels Windows. Versiones locales probadas: numpy 2.4.2, tokenizers 0.23.2, psutil 7.2.2, ONNX Runtime 1.30.0. La instalación Linux debe validarse; no se ha desplegado en OCI.

Para repetir entrenamiento local en RTX, instalar requirements-training.txt y PyTorch CUDA adecuado, abrir notebook y activar REENTRENAR=True. RECREAR_CACHE=True regenera embeddings secuencialmente desde el encoder publicado; se usa si cambian datos/tokenizer/encoder/tokens. La caché no se publica ni se utiliza al servir. Para solo verificar la entrega: `python execute_mlp_notebook.py`; termina sin dejar modelos CUDA vivos. El notebook requiere acceso a la RTX local en su celda de hardware. Los archivos antiguos runtime.py/prepare.py y el experimento PCA local son históricos; esta entrega usa los scripts MLP indicados.

Registro histórico 384→1 frente a MLP: artifacts_v2/comparison.json y notebook anterior. Esa etapa afinaba encoder y usaba ventanas; no se mezcla con la comparación controlada actual. La profunda fue elegida por diferencia pequeña y costo mínimo, no por demostrar mayor F1. Ver COMPARACION_MLP_INT8.md y CONTRATO.md.

Procedencia: corpus copiado de 2026-09-30/la-x20/outputs/data/corpus.jsonl, contrastado con 2026-09-27; se conserva original, anotaciones Gemini, IDs, autores, URLs y licencias en data/. Los textos preparados son transformaciones documentadas. Mantener atribución y licencia CC BY-SA aplicable a los posts de Stack Exchange. El checkpoint MiniLM original está identificado por revisión e8f8c211226b894fcb81acc59f3b34ba3efd5f42; su model card indica Apache-2.0.

Fuentes: [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html), [ONNX external data](https://onnx.ai/onnx/api/external_data_helper.html), [OCI shapes](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm).
'''
    if (ROOT/'data/publication.json').exists():
        readme+='\nPublicación GitHub: la copia corpus_original.jsonl tiene un token del cuerpo de una pregunta oculto; original íntegro en SSD local. data/publication.json registra SHA original/publicado y fila modificada. Los DataFrames de entrenamiento no cambian.\n'
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    contract='''# Contrato de inferencia

Entrada exacta:

```json
{"id_mensaje":123,"mensaje":"Gracias, ya funciona."}
```

id_mensaje: entero con signo int64 [-2^63, 2^63-1], no bool. mensaje: string Unicode no vacío ni solo espacios, hasta 8000 caracteres. Se usan primeros 128 tokens (incluidos especiales). Batch siempre 1; una solicitud simultánea. El wrapper rechaza campos adicionales y entradas inválidas con ValueError. JSONL devuelve {"error":"..."} para fallos de entrada; esas respuestas no son predicciones.

Salida exacta: mismo id_mensaje y tres floats finitos entre 0 y 1, sin convertir a etiquetas discretas. es_faq puntúa títulos FAQ frente a comentarios según corpus; es_logro aproxima etiqueta Gemini de logro; sentimiento aproxima negativo=0, central/neutro/mixto=0.5, positivo=1. Los scores no han sido calibrados como probabilidades. Los umbrales en deploy_mlp_int8/config.json solo se usan para evaluación/discretización opcional. La salida permanece continua.

Un solo encoder compartido, 384 dimensiones; tres redes independientes 384→64→32→16→4→1, ReLU oculta y Sigmoid final. INT8 MatMul/Gather seleccionados, salida float. ONNX Runtime CPU, sin Torch, un hilo ORT y un worker. Cada sesión de cabeza termina antes de crear la siguiente. Crear Predictor una vez y reutilizarlo; no crear uno por mensaje. No ejecutar varias copias en una VM de 1 GB.

El proceso consulta RSS antes/después de carga e inferencia y levanta MemoryError al alcanzar 1000 MB. probe_mlp_memory.py observa cada 10 ms y detiene su hijo si alcanza ese valor. Ese muestreo no garantiza detectar un pico más corto; para límite de proceso en Linux integrar MemoryMax=700000000 del ejemplo de servicio. La medición Windows no garantiza RAM total OCI. El SO y API requieren margen y validación adicional allí. Sin despliegue realizado.
'''
    (ROOT/'CONTRATO.md').write_text(contract,encoding='utf-8')
    text='# Comparación de MLP y límites de la evidencia\n\n'
    text+='| Arquitectura | Cabeza | Parámetros | Validation macro F1 | Test F1 positivo / macro sentimiento | INT8 bytes |\n|---|---|---:|---:|---:|---:|\n'
    for arch,tasks in comparison['architectures'].items():
        for task,r in tasks.items():
            text+=f"| {arch} | {task} | {r['parameters']} | {r['validation']['f1_macro']:.4f} | {r['test'].get('f1',r['test']['f1_macro']):.4f} | {(OUT/arch/task/'head_int8.onnx').stat().st_size} |\n"
    text+=f"\nF1 macro medio de validation: {comparison['validation_macro_f1']}. Selección: {comparison['selected']}. {comparison['selection_rule']}\n\n"
    text+='La profunda pierde aproximadamente 0.0026 de macro F1 medio frente a la pequeña, dentro de la tolerancia predefinida 0.005 y con costo de pesos muy bajo. No mostró una mejora de calidad. La pequeña es una alternativa igualmente razonable; no se midieron varias semillas ni intervalos de confianza.\n\n'
    text+='La tabla compara cabezas sobre cache de UN encoder congelado INT8. Training se hizo en RTX 4070 Ti SUPER, tensores/modelo/targets CUDA; exportación comprobada contra ONNX FP32. Evaluación de la tabla usó bloques hasta 256 embeddings. Como INT8 dinámico depende del batch, el paquete final reajusta cortes solo con validation batch 1 y vuelve a medir todo test end to end; estas son las cifras finales de producción:\n\n'+table
    text+=f"\nRAM desde arranque {memory['cold_to_hot_peak_rss_mb']:.2f} MB; p50 {memory['p50_ms']:.2f} ms, p95 {memory['p95_ms']:.2f} ms en Ryzen/Windows. La prueba usa 104 solicitudes, 4 de calentamiento, no es benchmark de OCI. Error máximo de embeddings frente a cache {evaluation['max_embedding_error_vs_cache']}.\n\n"
    text+='Logro: test 18 positivos entre 418; 8 TP, 10 FN, 11 FP. Sentimiento: 23 negativos, 346 centrales, 49 positivos; ver matrices por clase en package_evaluation.json. No extrapolar F1 de estos textos técnicos a usuarios finales sin evaluación del dominio. Cortes de sentimientos optimizan macro F1 en validación; MAE reporta el índice continuo.\n\n'
    text+='La comparación anterior lineal/MLP afinaba encoder y usaba otra política de textos; se conserva como histórico. PCA no se usa en este paquete. Reducir la dimensión de la cabeza ahorra pocos KB; INT8 del encoder/runtime ligero y límites de entradas son los cambios de memoria relevantes.\n'
    (ROOT/'COMPARACION_MLP_INT8.md').write_text(text,encoding='utf-8')
    hashes=[]
    for path in delivery_files():
        with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
        hashes.append(dict(path=str(path.relative_to(ROOT)).replace('\\','/'),bytes=path.stat().st_size,sha256=digest))
    (ROOT/'MANIFEST.sha256.json').write_text(json.dumps(dict(scope='Entrega MLP INT8, excluye cachés/deps/encoder FP32/historial de pesos',files=hashes),indent=2),encoding='utf-8')
    print('Docs y manifiesto:',len(hashes),'archivos',flush=True)

if __name__=='__main__':main()
