# Auditoría de LOGROS

Se revisaron 3792 entradas. No se encontraron textos completos idénticos entre particiones, tampoco tras normalizar mayúsculas y espacios.

Con el tokenizer de inferencia y el límite de 128 tokens, hay 5 grupos compartidos entre particiones (12 filas). Dos entradas de validación y tres de test tienen la misma entrada tokenizada que una entrada de entrenamiento.

Al excluir esas tres entradas de test, el F1 positivo con el umbral de decisión existente permanece sin cambios. Los valores históricos se conservan en los archivos JSON de la auditoría como evidencia técnica; no se presentan aquí como una estimación validada de generalización. Este análisis cuantifica esas coincidencias exactas, pero no determina el impacto de todas las posibles reformulaciones.

Los IDs 94 y 1374 describen WhizChat y comparten enlaces, estando en train y validation. Sus etiquetas difieren; esto requiere revisión contextual y no demuestra por sí solo un error de etiquetado.

## Reproducir desde la raíz del repositorio

```powershell
python -m pip install -r data_science/CABEZAS_V2/auditoria_logros/requirements.txt
python data_science/CABEZAS_V2/auditoria_logros/auditar.py
```

Genera `resultado_reproducido.json`. No requiere descargar datos, entrenar ni cargar pesos. Usa los datos, tokenizer y scores existentes en el repositorio.

`auditoria.json` conserva la exploración inicial. Su conteo de 30 pares con URL compartida usa un emparejamiento exploratorio entre las dos mitades del CSV de origen; no equivale a 30 familias de publicaciones demostradas. El script reproducible se limita a las coincidencias exactas y al ejemplo concreto documentado.

Queda pendiente una evaluación agrupada por publicación de origen para cuantificar la generalización entre familias. Esta auditoría no modifica el encoder ni las tres cabezas FP32.
