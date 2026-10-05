# Comparación de MLP y límites de la evidencia

| Arquitectura | Cabeza | Parámetros | Validation macro F1 | Test F1 positivo / macro sentimiento | INT8 bytes |
|---|---|---:|---:|---:|---:|
| small | es_faq | 6233 | 0.9867 | 0.9796 | 11193 |
| small | es_logro | 6233 | 0.7881 | 0.4444 | 11193 |
| small | sentimiento | 6233 | 0.6674 | 0.6770 | 11193 |
| deep | es_faq | 27321 | 0.9877 | 0.9776 | 36350 |
| deep | es_logro | 27321 | 0.8033 | 0.4324 | 36350 |
| deep | sentimiento | 27321 | 0.6435 | 0.6683 | 36350 |

F1 macro medio de validation: {'small': 0.8141036783374632, 'deep': 0.8115164318143839}. Selección: deep. F1 macro medio de validation. Deep si no pierde más de 0.005 frente a small; los pesos siguen siendo pequeños. Test no selecciona.

La profunda pierde aproximadamente 0.0026 de macro F1 medio frente a la pequeña, dentro de la tolerancia predefinida 0.005 y con costo de pesos muy bajo. No mostró una mejora de calidad. La pequeña es una alternativa igualmente razonable; no se midieron varias semillas ni intervalos de confianza.

La tabla compara cabezas sobre cache de UN encoder congelado INT8. Training se hizo en RTX 4070 Ti SUPER, tensores/modelo/targets CUDA; exportación comprobada contra ONNX FP32. Evaluación de la tabla usó bloques hasta 256 embeddings. Como INT8 dinámico depende del batch, el paquete final reajusta cortes solo con validation batch 1 y vuelve a medir todo test end to end; estas son las cifras finales de producción:

| Cabeza | F1 test batch 1 | Soporte |
|---|---:|---:|
| es_faq | 0.9776 | 903 |
| es_logro | 0.4324 | 418 |
| sentimiento | 0.6578 | 418 |

RAM desde arranque 357.13 MB; p50 8.26 ms, p95 30.71 ms en Ryzen/Windows. La prueba usa 104 solicitudes, 4 de calentamiento, no es benchmark de OCI. Error máximo de embeddings frente a cache 0.0.

Logro: test 18 positivos entre 418; 8 TP, 10 FN, 11 FP. Sentimiento: 23 negativos, 346 centrales, 49 positivos; ver matrices por clase en package_evaluation.json. No extrapolar F1 de estos textos técnicos a usuarios finales sin evaluación del dominio. Cortes de sentimientos optimizan macro F1 en validación; MAE reporta el índice continuo.

La comparación anterior lineal/MLP afinaba encoder y usaba otra política de textos; se conserva como histórico. PCA no se usa en este paquete. Reducir la dimensión de la cabeza ahorra pocos KB; INT8 del encoder/runtime ligero y límites de entradas son los cambios de memoria relevantes.
