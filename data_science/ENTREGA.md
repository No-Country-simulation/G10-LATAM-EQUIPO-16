# Entrega Data Science - Semana 1

27 de septiembre de 2026 (America/Mexico_City).

## Resultado comprobado

| Evidencia | Resultado |
| --- | ---: |
| Registros reales descargados | 10,000 |
| Preguntas de Stack Exchange | 5,000 |
| Comentarios con intención y sentimiento Gemini | 5,000 |
| Comentarios pendientes de etiquetar | 0 |
| Registros por sitio ES / EN | 5,000 / 5,000 |
| Textos únicos tras normalización | 9,782 |
| Repeticiones identificadas | 218 |
| Comentarios elegibles para baseline silver, en todas las particiones | 4,624 |
| Citas no literales, excluidas del baseline recomendado | 160 |
| Registros sintéticos | 0 |
| Etiquetas revisadas por humanos | 0 |

Partición por hilo/grupos de textos duplicados: 8,111 train; 984 validation; 905 test.
No hay solapamiento por hilo ni por texto normalizado exacto. Se resolvieron 1,118 relaciones respuesta-pregunta.

## Cobertura de la tarjeta

- Preguntas técnicas: 5,000 preguntas de origen, más 570 comentarios clasificados como pregunta.
- Testimonios: 172 comentarios con intención principal testimonio; 631 activan el booleano testimonio.
- Logros: 151 comentarios con intención principal logro; 248 activan el booleano logro.
- Casos triviales: 114 comentarios con esa intención principal.
- Ambigüedad: un comentario marcado ambiguo/indeterminado; no constituye un conjunto robusto de ambigüedad.
- CSV/JSON: exportaciones ajustadas a `autor`, `canal`, `tipo`, `texto` y envoltorio del lote del backend.

Los booleanos y la intención principal miden cosas distintas y pueden solaparse. Testimonios/logros se refieren
principalmente a experiencias y soluciones técnicas; no afirmar que sean historias de contratación de estudiantes.
Todas las etiquetas de Gemini son provisionales y requieren revisión antes de evaluar un modelo.

## Pruebas realizadas

`python scripts/validate_dataset.py` pasó con los 10,000 registros:
fidelidad al texto de la API, IDs únicos, hash del texto, procedencia de anotaciones,
evidencia literal señalada correctamente, particiones sin solapamiento de hilos ni duplicados exactos
y equivalencia entre JSON y CSV de ingesta. Se verificó integridad de los ZIP y de su manifiesto SHA-256.

La captura y la anotación se pueden reanudar con los scripts. Los secretos se leen únicamente del entorno.
Se registraron 91 llamadas de anotación exitosas y 875,779 tokens en esas llamadas; el conteo excluye pruebas
de conexión y respuestas rechazadas. No es una estimación de cobro ni incluye tokens de otros servicios.

## Qué sigue

Revisar `exports/revision_humana.jsonl`, ampliar casos ambiguos y testimonios de aprendizaje/empleo,
crear un conjunto de evaluación humano independiente y entrenar el baseline. El uso de Stack Exchange
no demuestra que una pregunta sea frecuente; la recurrencia se validará después con agrupación y revisión.

Este PR entrega datos y preparación para entrenamiento. No afirma completar la generación de activos ni OCI Object Storage.
