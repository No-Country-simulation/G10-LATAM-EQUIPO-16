# Contrato de inferencia

Entrada exacta:

```json
{"id_mensaje":123,"mensaje":"Gracias, ya funciona."}
```

id_mensaje: entero con signo int64 [-2^63, 2^63-1], no bool. mensaje: string Unicode no vacío ni solo espacios, hasta 8000 caracteres. Se usan primeros 128 tokens (incluidos especiales). Batch siempre 1; una solicitud simultánea. El wrapper rechaza campos adicionales y entradas inválidas con ValueError. JSONL devuelve {"error":"..."} para fallos de entrada; esas respuestas no son predicciones.

Salida exacta: mismo id_mensaje y tres floats finitos entre 0 y 1, sin convertir a etiquetas discretas. es_faq puntúa títulos FAQ frente a comentarios según corpus; es_logro aproxima etiqueta Gemini de logro; sentimiento aproxima negativo=0, central/neutro/mixto=0.5, positivo=1. Los scores no han sido calibrados como probabilidades. Los umbrales en deploy_mlp_int8/config.json solo se usan para evaluación/discretización opcional. La salida permanece continua.

Un solo encoder compartido, 384 dimensiones; tres redes independientes 384→64→32→16→4→1, ReLU oculta y Sigmoid final. INT8 MatMul/Gather seleccionados, salida float. ONNX Runtime CPU, sin Torch, un hilo ORT y un worker. Cada sesión de cabeza termina antes de crear la siguiente. Crear Predictor una vez y reutilizarlo; no crear uno por mensaje. No ejecutar varias copias en una VM de 1 GB.

El proceso consulta RSS antes/después de carga e inferencia y levanta MemoryError al alcanzar 1000 MB. probe_mlp_memory.py observa cada 10 ms y detiene su hijo si alcanza ese valor. Ese muestreo no garantiza detectar un pico más corto; para límite de proceso en Linux integrar MemoryMax=700000000 del ejemplo de servicio. La medición Windows no garantiza RAM total OCI. El SO y API requieren margen y validación adicional allí. Sin despliegue realizado.
