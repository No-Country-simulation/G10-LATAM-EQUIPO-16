Gracias, Bryan. Revisé los datos de LOGROS y adjunto la evidencia y un script reproducible en `data_science/CABEZAS_V2/auditoria_logros/`.

En las 3792 entradas no encontré textos completos idénticos entre particiones. Sin embargo, con el tokenizer y el límite de 128 tokens de inferencia, dos entradas de validación y tres de test coinciden exactamente con entradas de entrenamiento. Al excluir esas tres de test, el F1 positivo al umbral 0.63 permanece en 0.9079754601226994.

También documenté los IDs 94 y 1374: describen el mismo proyecto WhizChat y comparten enlaces entre train y validation. Esto respalda revisar las familias de publicaciones; no prueba por sí solo un error de etiqueta ni permite cuantificar toda la posible fuga.

Por tanto, el F1 actual debe interpretarse como resultado del split existente. Queda pendiente evaluar una partición agrupada por publicación de origen. El paquete Python de encoder + tres cabezas FP32 sigue disponible para la prueba aislada de inferencia en OCI.
