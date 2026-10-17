# CABEZAS_V2

## Inferencia en Python para OCI

El encoder y las tres cabezas **FP32** listos para ejecutar están en
[`inferencia_fp32/`](inferencia_fp32/). Incluye dependencias, un script que
procesa un mensaje y una medición de memoria y latencia para la prueba aislada.

```bash
cd inferencia_fp32
python -m pip install -r requirements.txt
python inferencia.py --texto "Hoy terminé mi diplomado."
python medir_recursos.py
```

Consultar su README para crear el entorno Python y usar `Clasificador` desde
el AI Engine. No modifica el servicio actual ni el flujo de Gemini.

Tres MLP independientes con MiniLM multilingüe congelado: **384→64→32→16→8→4→1**,
ReLU ocultas, Sigmoid final, BCE ponderada y entrenamiento local en RTX 4070 Ti SUPER.

## Entrega

- `CABEZAS_V2.ipynb`: datos, Qwen local, embeddings, entrenamiento, gráficas y exportación FP32.
- `data/`: bases de entrenamiento, etiquetas/respuestas/errores de Qwen y sus prompts.
- `cabezas/`: tres ONNX FP32, checkpoints, curvas, scores test y reportes.
- `train_mlp.py`: proceso independiente por cabeza; `requirements.txt`: dependencias.

Pregunta usa `es_faq.jsonl` sin modificar su target oficial. LOGROS usa `es_logro.jsonl`
con split aleatorio estratificado 80/10/10. Sentimiento usa
`sentimiento_cardiff_binario.jsonl`: EN/ES, negativos=0 y positivos=1, sin neutrales.
`sentimiento.jsonl` conserva la referencia oficial anterior.

| Cabeza | Evaluación de su propio test |
|---|---|
| Pregunta | F1 positivo 0.944 |
| LOGROS | F1 positivo 0.908 |
| Sentimiento Cardiff binario | F1 positivo 0.843 |

Estos tests y etiquetas son diferentes; los F1 no son una comparación directa entre tareas.
LOGROS tiene etiquetas provisionales Qwen. Sentimiento representa polaridad;
0.5 no demuestra neutralidad. Ningún score se declara probabilidad calibrada.

Las cabezas reciben `embedding` float32 `[batch,384]` y devuelven `score`
float32 `[batch,1]`. La diferencia máxima medida frente a PyTorch es menor que
0.000001, usando los embeddings de test. Configuración y validación en `cabezas/`.
La subcarpeta `cabezas/` entrega las cabezas; `inferencia_fp32/` incluye además
el encoder ONNX. El consumo de RAM en OCI debe medirse en la VM de destino.

MiniLM se carga de pesos locales/caché. La carpeta de pesos y la caché de embeddings
no se publican. Las acciones de descarga/entrenamiento están desactivadas al abrir.
Los errores de Qwen documentan respuestas incompletas de lotes; no son targets.
Las respuestas completas permiten inspeccionar cómo se generaron las etiquetas.

## Fuentes y atribución

- Stack Exchange: bases oficiales copiadas de `data_science/2026-10-04/data/`;
  se conservan IDs y URLs. Respetar atribución y CC BY-SA aplicable a los posts.
- Publicaciones: [sanjayram-a](https://huggingface.co/datasets/sanjayram-a/linkedin_posts),
  [BrianClone](https://huggingface.co/datasets/BrianClone/linkedin_posts),
  [NeuML](https://huggingface.co/datasets/NeuML/neuml-linkedin-202501).
  La disponibilidad pública no acredita por sí sola la licencia de cada texto.
- [Cardiff Tweet Sentiment Multilingual](https://huggingface.co/datasets/cardiffnlp/tweet_sentiment_multilingual):
  Francesco Barbieri, Jose Camacho-Collados y Luis Espinosa-Anke,
  XLM-T, LREC 2022. La ficha indica CC BY 3.0 y condiciones de Twitter aplicables.
- [MiniLM multilingüe](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2).


## Reproducibilidad e integración (revisión PR #23)

El entorno de dependencias verificado localmente el 15 de octubre de 2026 está
fijado en `requirements.txt`. Python local: 3.11.9; PyTorch observado:
2.5.1+cu121 (CUDA 12.1); ONNX Runtime CPU: 1.30.0.
Estas son las versiones verificadas ahora en el equipo original, no un freeze
capturado al iniciar cada entrenamiento. Reproducir en otra GPU puede variar
ligeramente los resultados. La RTX 4070 Ti SUPER identifica el hardware histórico;
el código ya acepta cualquier GPU CUDA disponible y mantiene el mismo algoritmo.

`encoder_config.json` identifica MiniLM y su revisión, documentada en la entrega
2026-10-04 de la que se copiaron los pesos base: mean pooling con máscara,
384 dimensiones, máximo 128 tokens y sin normalización L2. No usar el encoder
previamente afinado como sustituto de ese encoder base.

Para disponer del encoder en caché en otro equipo, antes de ejecutar el notebook:

```python
from sentence_transformers import SentenceTransformer
SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    revision="e8f8c211226b894fcb81acc59f3b34ba3efd5f42",
)
```

### Prueba ONNX independiente (CPU)

Desde esta carpeta, sin Jupyter, GPU, PyTorch ni descarga de MiniLM:

```bash
python -m pip install -r requirements-inferencia.txt
python probar_onnx.py
```

La prueba carga los tres `.onnx`, valida `embedding` float32 `[N,384]`,
`score` float32 `[N,1]`, valores finitos en [0,1] y equivalencia entre batch
individual y múltiple. Termina con código 0 si pasa y error si falla.
Los vectores predeterminados son sintéticos: prueba compatibilidad del contrato,
no calidad semántica ni métricas de clasificación. Para usar embeddings reales:

```bash
python probar_onnx.py --embeddings ruta/a/embeddings.npy
```

Esta corrección no modifica pesos, datos ni métricas y no conecta AI Engine,
backend o frontend. La prueba CPU local no certifica integración ni consumo OCI.
