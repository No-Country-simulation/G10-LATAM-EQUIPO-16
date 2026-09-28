# CommunityLab - dataset real de Stack Exchange

Entrega de Data Science, Semana 1. Responsable: Saul Mendoza.

**10,000 registros reales descargados de la API pública: 5,000 preguntas y 5,000 comentarios.**
Cada sitio aporta 2,500 preguntas y 2,500 comentarios: Stack Overflow en español y Stack Overflow en inglés.
No se generaron mensajes sintéticos, no se tradujeron textos y no se entrenó ningún modelo en esta entrega.


## Prueba pequeña de ingesta (sin descargar los ZIP)

Backend puede usar directamente [exports/demo_ingesta.json](exports/demo_ingesta.json),
con **9 mensajes reales**, y consultar su procedencia en
[exports/demo_fuentes.jsonl](exports/demo_fuentes.jsonl).
Para probar el LLM usar este demo o un subconjunto pequeño de `ingesta.json`;
**no enviar los 10,000 mensajes completos**, para evitar agotar la cuota.
Las etiquetas siguen siendo automáticas provisionales, no un gold set humano.

## Empezar

Descargar [el dataset](https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/releases/download/dataset-v1.0/CommunityLab_Dataset.zip) y [las fuentes originales](https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/releases/download/dataset-v1.0/StackExchange_Fuentes.zip) y extraer ambos en la misma carpeta.
El primero contiene CSV/JSON, etiquetas y scripts; el segundo contiene las respuestas originales de la API.
Ambos se combinan bajo `CommunityLab_Dataset/`. Los ZIP se distribuyen como assets del [Release dataset-v1.0](https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/releases/tag/dataset-v1.0), fuera del historial Git. El Release incluye sus hashes SHA-256.
Los scripts usan Python 3.10+ y solamente la biblioteca estándar.

Resultado de esta captura: 5,000 comentarios anotados, cero pendientes; 4,624 pasan los filtros de calidad
para un futuro baseline sobre etiquetas automáticas. Hay 160 citas de evidencia no literales, marcadas para revisión.
Los 5,000 sentimientos de las preguntas se dejan nulos, sin asignarles neutralidad por defecto.

```bash
cd CommunityLab_Dataset
python scripts/validate_dataset.py
```

| Archivo dentro del paquete | Uso |
| --- | --- |
| `exports/corpus.jsonl` | Maestro con texto íntegro normalizado, procedencia, licencia, etiquetas y partición |
| `exports/corpus.csv` | La misma colección en CSV para inspección y entrenamiento posterior |
| `exports/ingesta.json` | Contrato de lote del backend: origen_comunidad, periodo_referencia, interacciones |
| `exports/ingesta.csv` | Columnas exactas del cargador Python del equipo: autor, canal, tipo, texto |
| `exports/ingesta_index.json` | ID de origen de cada fila de ingesta, en el mismo orden |
| `exports/demo_ingesta.json` | Lote pequeño, real y listo para probar la ingesta |
| `exports/demo_fuentes.jsonl` | Procedencia y etiquetas del lote de demostración |
| `exports/train_index.jsonl`, `validation_index.jsonl`, `test_index.jsonl` | IDs de particiones fijas para uso posterior |
| `exports/revision_humana.jsonl` | Muestra estratificada con campos vacíos para que el equipo revise las etiquetas |
| `reports/quality_report.json` | Conteos exactos de etiquetas, pendientes, duplicados, idiomas y consumo registrado |
| `reports/validation.json` | Resultado de comprobaciones reproducibles |
| `data/raw/` (ZIP de fuentes) | Respuestas originales de Stack Exchange con URL y fecha de descarga |
| `data/annotations/` | Anotaciones persistidas de Gemini y consumo por lote |
| `MANIFEST.sha256.json` | Integridad de los archivos del paquete |

Los CSV están en UTF-8. En Excel, importar como texto/datos y no evaluar fórmulas de contenido de terceros.
El JSONL es la fuente recomendada para ML. Los campos con saltos de línea se conservan correctamente en CSV.

## Qué significan las etiquetas

- `source_label=pregunta_tecnica`: procedencia del endpoint de preguntas. No es una etiqueta semántica validada por humanos.
- `faq_candidate=true`: pregunta utilizable para explorar FAQ; **no demuestra recurrencia** ni que tenga una respuesta correcta.
- Las etiquetas originales `tags` son temas técnicos asignados en Stack Exchange; no son etiquetas de sentimiento.
- Gemini 3.1 Flash-Lite clasifica **el texto completo de los comentarios** en intención, sentimiento, testimonio y logro.
- `annotation_status=silver_unreviewed`: etiqueta automática provisional, pendiente de revisión humana.
- `source_only`: pregunta con etiqueta de origen; sentimiento/testimonio/logro permanecen nulos.
- `pending`: comentario todavía sin anotación. Un nulo no significa neutro ni negativo.
- `evidence_verified` comprueba que la cita devuelta por el modelo existe literalmente en el mensaje.
- `eligible_silver_training` excluye duplicados, evidencia no literal, confianza menor a 0.8 y salidas ambiguas/indeterminadas.
  El umbral es un filtro operativo; la confianza del LLM **no está calibrada**.

Vocabulario de intención: pregunta_tecnica, respuesta_tecnica, solicitud_aclaracion, agradecimiento,
testimonio, logro, feedback, conversacion_trivial, moderacion, otro, ambiguo.
Sentimiento: positivo, negativo, neutro, mixto, indeterminado.
Testimonio y logro son booleanos independientes: un mensaje puede activar ambos.
Resolver un problema técnico puede contar como un logro; no equivale a contratación o éxito profesional.

## Uso para entrenar después

Usar **solo `texto` como entrada del modelo** y la etiqueta seleccionada como objetivo. Excluir de las variables
predictoras ID, sitio, autor, tags, URL, tipo, evidencia, confianza y metadatos de anotación para evitar atajos.
Filtrar por `split=train`, `eligible_silver_training=true` para un baseline sobre etiquetas automáticas.
Las preguntas pueden alimentar un corpus de candidatas FAQ; no sirven como negativos automáticos de testimonio/logro.

Las particiones 80/10/10 se asignan con hash estable a grupos de hilos. Se resolvieron los IDs de respuestas
para reunir sus comentarios con la pregunta original. Los textos duplicados tras normalizar espacios, caja y Unicode
conectan también sus hilos al mismo grupo. No hay solapamiento por hilo ni por texto normalizado exacto.
No se garantiza independencia por autor ni por similitud semántica; los grupos de comentarios sobre posts eliminados
pueden conservar solo el ID del post directo. La proporción final por filas puede diferir de 80/10/10.

Las etiquetas de validation/test también son automáticas: **no son un gold set**. Revisar una muestra independiente
antes de reportar precisión, recall o F1. No se reportan métricas de entrenamiento en esta entrega.

## Reproducir y reanudar

```bash
python scripts/download_stackexchange.py --pages 25
python scripts/prepare_dataset.py
python scripts/resolve_threads.py
# Configurar GEMINI_API_KEY fuera del repositorio, mediante una variable de entorno.
python scripts/label_gemini.py --model gemini-3.1-flash-lite --max-calls 100
python scripts/export_dataset.py
python scripts/validate_dataset.py
```

La descarga reutiliza páginas guardadas y fija `todate` para mantener el corte. Respeta `backoff`, cuotas y reintentos
acotados. La API anónima admite hasta 25 páginas por consulta. Para un corte nuevo, utilizar otra carpeta de datos.
El anotador no vuelve a consumir tokens para IDs ya persistidos. Ante cuota/autenticación/modelo no disponible
se detiene y deja los pendientes explícitos. No incluir claves ni archivos `.env` en commits.
Las muestras devueltas con IDs ausentes/duplicados se guardan solo si son inequívocas; el resto queda pendiente.

## Contrato comprobado

La exportación sigue `InteractionRequestDto` y `CommunityProcessRequestDto` de
`feature/roberto-endpoint-process`, y `Interaction`/`load_csv` de `feature/ml-analysis`.
Las ramas se inspeccionaron, sin fusionarlas ni cambiar el servicio del equipo.
`tipo` se mapea a testimonio, pregunta_tecnica, feedback, logro u otro. Los metadatos de anotación
quedan fuera del JSON de entrada. Esta comprobación es estructural: no se ejecutó el backend Java remoto.

## Alcance y límites

Se revisaron las bases de CommunityLab y la persistencia anterior: 179 preguntas previamente descargadas,
el subconjunto de 118 del experimento FAQ y el experimento de testimonios con 61 reales + 32 controles sintéticos.
Se preservó ese trabajo; la colección nueva contiene únicamente la nueva captura real de Stack Exchange.

La muestra es por recencia, no aleatoria ni representativa de ONE, Discord o Slack. El mismo número de registros
cubre periodos diferentes por sitio; consultar `site_date_ranges`. Stack Exchange modera mensajes triviales,
por lo que esa clase puede ser minoritaria. Los testimonios son principalmente experiencias técnicas.

Esta entrega cubre adquisición, persistencia local, limpieza, anotación y exportación. Las bases del MVP completo
también requieren generación de dos formatos de activos, tres demostraciones de transformación e integración activa
con OCI Object Storage Always Free. Eso no se implementó ni se declara cumplido con este dataset.

## Atribución y licencia

Los textos pertenecen a sus autores en Stack Exchange. Se conserva autor, perfil cuando existe, enlace permanente,
fecha y licencia por registro. La API puede omitir `content_license`; en esos casos se conserva `license_api=null`
y se deriva CC BY-SA 4.0 de la fecha de publicación posterior al 2 de mayo de 2018, marcando
`license_method=publication_date_and_site_policy`. Ver [política de licencia](https://stackoverflow.com/help/licensing)
y [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Transformaciones: decodificación de entidades HTML, eliminación de etiquetas conservando texto/código y título
antepuesto al cuerpo en preguntas. Se preserva el HTML original en raw. Las anotaciones automáticas son añadidos
del proyecto. Los textos del dataset no pasan a ser MIT por estar dentro del repositorio.

Referencias: [API de preguntas](https://api.stackexchange.com/docs/questions),
[API de comentarios](https://api.stackexchange.com/docs/comments),
[límites de la API](https://api.stackexchange.com/docs/throttle),
[salida estructurada de Gemini](https://ai.google.dev/gemini-api/docs/structured-output).
