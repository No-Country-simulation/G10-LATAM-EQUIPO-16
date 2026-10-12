# CABEZAS_V2

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
Esta carpeta entrega las cabezas; no incluye el encoder ONNX ni certifica RAM OCI.

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
