# MiniLM + tres MLP independientes · ONNX INT8

Abrir **MiniLM_3_cabezas_comparacion.ipynb**, ejecutado con outputs reales y cero errores. Muestra hardware, DataFrames/etiquetas, las seis ejecuciones CUDA, exportación, comparación, RAM y traza de inferencia.

Un encoder compartido MiniLM multilingüe L12 (384 dimensiones), afinado previamente en RTX 4070 Ti SUPER y congelado en esta comparación; tres cabezas independientes **384→64→32→16→4→1**, ReLU intermedias y Sigmoid final. Se compararon con 384→16→4→1 usando los mismos embeddings INT8. Se entrenan por separado con RTX: una cabeza, guardar SSD, terminar proceso, siguiente. La caché INT8 se genera en CPU de un mensaje por vez y se lee con mmap. No hay PCA en el paquete final.

FAQ: títulos seleccionados de Stack Exchange=1, comentarios=0. Logro: etiquetas Gemini 0/1. Sentimiento Gemini: negativo=0, neutro/mixto=0.5, positivo=1; un indeterminado en revisión. Datos preparados: FAQ 9782, logro 4782, sentimiento 4781. No se asignan etiquetas inexistentes a títulos. Cada DataFrame tiene su propio target. Se mantienen splits por conversación y se eliminan duplicados.

Resultados del paquete INT8 completo, encoder y cabeza CPU batch 1:

| Cabeza | F1 test batch 1 | Soporte |
|---|---:|---:|
| es_faq | 0.9776 | 903 |
| es_logro | 0.4324 | 418 |
| sentimiento | 0.6578 | 418 |


Sentimiento usa F1 macro de negativo/central/positivo y MAE; FAQ/logro usan F1 de la clase positiva. Los cortes se eligen exclusivamente en validation. Logro tiene 18 positivos test: F1 modesto requiere mejorar y validar en mensajes del dominio real. El score no está calibrado como probabilidad.

RAM de proceso desde arranque: **357.13 MB**; batch 1, primeros 128 tokens, 8000 caracteres, una solicitud simultánea. Latencia local p50 8.26 ms / p95 30.71 ms, 100 muestras tras 4 de calentamiento, mezcla de textos cortos y límite. Se muestrea cada 10 ms y se verifican 5 rechazos de entradas inválidas. Es Windows/Ryzen 8700F, no la VM OCI. El total de 1 GB en OCI incluye SO/API: validar allí; ejemplo cgroup con MemoryMax=700000000 para dejar margen. Los picos PyTorch/Jupyter de entrenamiento local no pertenecen al servicio.

El paquete deploy_mlp_int8 ocupa 135.26 MB en SSD. Incluye un grafo encoder, dos archivos de pesos externos, tokenizer, config y tres cabezas de 36,350 bytes cada una. Conservar todos juntos. INT8 cuantiza MatMul/Gather del encoder y MatMul de cabezas; ReLU/Sigmoid y otras operaciones siguen en punto flotante.

Uso de producción:

```python
from serve_mlp_int8 import Predictor
predictor = Predictor()  # crear UNA vez por worker
salida = predictor({'id_mensaje': 123, 'mensaje': 'Gracias, ya funciona.'}, trace=True)
```

El wrapper solo importa numpy, onnxruntime CPU, tokenizers y psutil. Un encoder vivo, una cabeza cargada/usada/liberada por paso; lock para serializar solicitudes. serve_jsonl.py acepta JSON por línea y mantiene el predictor. No importar runtime.py ni PyTorch para servir. Instalar requirements-serving.txt en Linux; no copiar DLL/wheels Windows. Versiones locales probadas: numpy 2.4.2, tokenizers 0.23.2, psutil 7.2.2, ONNX Runtime 1.30.0. La instalación Linux debe validarse; no se ha desplegado en OCI.

Para repetir entrenamiento local en RTX, instalar requirements-training.txt y PyTorch CUDA adecuado, abrir notebook y activar REENTRENAR=True. RECREAR_CACHE=True regenera embeddings secuencialmente desde el encoder publicado; se usa si cambian datos/tokenizer/encoder/tokens. La caché no se publica ni se utiliza al servir. Para solo verificar la entrega: `python execute_mlp_notebook.py`; termina sin dejar modelos CUDA vivos. El notebook requiere acceso a la RTX local en su celda de hardware. Los archivos antiguos runtime.py/prepare.py y el experimento PCA local son históricos; esta entrega usa los scripts MLP indicados.

Registro histórico 384→1 frente a MLP: artifacts_v2/comparison.json y notebook anterior. Esa etapa afinaba encoder y usaba ventanas; no se mezcla con la comparación controlada actual. La profunda fue elegida por diferencia pequeña y costo mínimo, no por demostrar mayor F1. Ver COMPARACION_MLP_INT8.md y CONTRATO.md.

Procedencia: corpus copiado de 2026-09-30/la-x20/outputs/data/corpus.jsonl, contrastado con 2026-09-27; se conserva original, anotaciones Gemini, IDs, autores, URLs y licencias en data/. Los textos preparados son transformaciones documentadas. Mantener atribución y licencia CC BY-SA aplicable a los posts de Stack Exchange. El checkpoint MiniLM original está identificado por revisión e8f8c211226b894fcb81acc59f3b34ba3efd5f42; su model card indica Apache-2.0.

Fuentes: [ONNX Runtime quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html), [ONNX external data](https://onnx.ai/onnx/api/external_data_helper.html), [OCI shapes](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm).

Publicación GitHub: la copia corpus_original.jsonl tiene un token del cuerpo de una pregunta oculto; original íntegro en SSD local. data/publication.json registra SHA original/publicado y fila modificada. Los DataFrames de entrenamiento no cambian.
