# Validación y curación del dataset de demo

Evaluación del AI Engine de CommunityLab mediante sus funciones de generación y el endpoint batch. Registra respuestas de Gemini para revisión editorial.

## Versión de referencia

- Fuente: PR #38 del repositorio `No-Country-simulation/G10-LATAM-EQUIPO-16`.
- Commit: `d62dd02ce1a358824b72336a6e4150be1ab81262`.
- Importación: `ai-engine/` del repositorio; checkout alternativo mediante `ANDREA_ENGINE_DIR`.
- Modelo predeterminado: `gemini-3.5-flash-lite`.
- Formatos: LinkedIn y newsletter. FAQ sujeto al alcance confirmado del MVP.

## Configuración

La API key se crea en [Google AI Studio — API Keys](https://aistudio.google.com/api-keys), mediante **Create API key**, asociada al proyecto de prueba. Los proyectos existentes se incorporan desde **Dashboard → Projects → Import projects**.

La configuración se carga desde `.env` mediante `python-dotenv`, antes de importar el motor. `.env.example` define las variables y `.gitignore` excluye la configuración local, el entorno virtual y las cachés.

| Variable | Uso |
| --- | --- |
| `GEMINI_API_KEY` | Autenticación con Gemini. |
| `GEMINI_MODEL` | Identificador del modelo. |
| `ANDREA_ENGINE_DIR` | Checkout alternativo de `ai-engine`; vacío utiliza `ai-engine/` del repositorio. |
| `BACKEND_URL` | URL del backend de prueba. |
| `BACKEND_VERSION` | Versión desplegada de Java y del AI Engine, incluido su modelo. |
| `BACKEND_TOKEN` | Bearer token, cuando corresponda. |

Referencia: [Autenticación de Gemini](https://ai.google.dev/gemini-api/docs/api-key). El notebook comprueba disponibilidad del modelo y registra los errores de acceso o cuota por separado.

## Ejecución

Desde la carpeta del paquete, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
.\.venv\Scripts\python.exe -m jupyterlab curacion_demo_andrea.ipynb
```

El notebook se ejecuta en orden con el kernel del entorno instalado: configuración, inspección del código, validación del dataset, solicitudes y persistencia.

| Nivel | Recorrido | Activación |
| --- | --- | --- |
| Generador directo | Análisis Gemini y función seleccionada por formato. | Celda 4, opcional. |
| AI Engine local | Endpoint batch, análisis Gemini, selección, LangGraph y generación. | Celda 5. |
| Diagnóstico | Diez interacciones originales en un lote. | `EJECUTAR_DIAGNOSTICO=True`. |
| Backend integrado | Solicitud HTTP a Java y sus integraciones. | Configuración del backend y `EJECUTAR_BACKEND=True`. |

La prueba directa realiza tres análisis y hasta tres generaciones; la local realiza otros tres análisis batch y hasta tres generaciones. Cada repetición consume nuevas solicitudes. El backend remoto utiliza su propia configuración de Gemini.

## Dataset

- `datos/01_diagnostico_10.json`: diez mensajes ficticios originales; contrato AI Engine.
- `datos/01_diagnostico_10.csv`: versión tabular para inspección.
- `datos/02_demo_empleo.json`, `03_demo_proyecto.json`, `04_demo_feedback.json`: tres candidatos en lotes independientes.
- `datos/*_backend.json`: entradas ajustadas al DTO Java, sin `id`.
- `datos/expectativas.json`: propósito y formato esperado de cada candidato.

El motor selecciona un activo por tipo y lote. La separación permite observar cada candidato. Newsletter requiere clasificación `feedback` y relevancia `alta`. Las expectativas describen el comportamiento buscado; la clasificación y las respuestas efectivas se conservan como evidencia.

## Evidencia

Cada ejecución crea `resultados/FECHA_identificador/`:

| Archivo | Contenido |
| --- | --- |
| `version_probada.json` | Commit, modelo, fecha UTC y dependencias. |
| `evidencia.jsonl` | Entradas, prompts, respuestas, estados HTTP y errores por evento. |
| `resultados_ai_engine.json` | Respuestas del endpoint local. |
| `resultados_backend.json` | Respuestas del backend, cuando se ejecuta. |
| `revision_marketing.csv` | Activos obtenidos y campos para dictamen editorial. |

El notebook conserva las salidas visibles al guardarlo. El CSV exportado inicia con revisión pendiente; una nueva exportación restablece esos campos. El dictamen editorial se conserva en una copia independiente.

## Alcance

La ejecución local cubre el AI Engine con Gemini real, selección y LangGraph. La ejecución del backend añade el recorrido Java y las integraciones configuradas. El snapshot del PR #38 mantiene pendiente la conexión al filtro MiniLM del PR #23.

El endpoint integrado es `/api/v1/community/process`. Su ejecución corresponde al entorno aislado y puede persistir registros y objetos. La versión del despliegue se documenta en `BACKEND_VERSION`.

## Aspectos sujetos a revisión

- El ejemplo LinkedIn transforma primera entrevista en primera posición.
- El ejemplo newsletter atribuye el lanzamiento a la comunidad y añade pruebas colaborativas.
- `decide_route()` selecciona newsletter para feedback de relevancia alta, independientemente del sentimiento.
- La anonimización reemplaza el nombre completo conocido y el marcador interno; su cobertura de datos personales es parcial.

Estos aspectos proceden de la inspección del código y los ejemplos. La evaluación de las respuestas corresponde a la evidencia de cada ejecución.

## Entrega

El PR de curación comprende notebook, helper `curacion.py`, dataset, expectativas, requisitos, documentación y evidencia seleccionada. El motor puede referenciarse mediante `ANDREA_ENGINE_DIR` cuando la versión probada ya esté integrada en el repositorio.

El cierre requiere archivos finales versionados y al menos tres transformaciones identificables del flujo integrado, con entrada, salida, fecha y versión. Los resultados quedan disponibles para revisión editorial y preparación de la demo.

## Estado de ejecución y dependencia

El PR #38 está pendiente de integración. Sus generadores se referencian como dependencia, sin duplicar los módulos del motor.

La evidencia conservada procede de dos ejecuciones del snapshot indicado. Cada una contiene 12 solicitudes/respuestas Gemini y tres solicitudes exitosas al endpoint local. Los tres lotes locales produjeron LinkedIn: DEMO-003 no produjo el newsletter esperado. La evaluación directa ejercita newsletter de forma aislada. Quedan pendientes cobertura automática de newsletter, backend integrado y aprobación editorial.

Las salidas del notebook se conservan desde la ejecución original. La adaptación a la estructura del repositorio cambia la ruta de importación para próximas ejecuciones, no los prompts ni las respuestas registradas.

Para reproducir antes del merge del PR #38, desde la raíz del repositorio:

```powershell
git fetch origin pull/38/head
git worktree add --detach ../communitylab-pr38 FETCH_HEAD
```

`ANDREA_ENGINE_DIR` admite la ruta absoluta a `../communitylab-pr38/ai-engine`. Cuando #38 esté integrado, puede utilizarse directamente `ai-engine/` del repositorio.

## Transcripción completa de Gemini

La sección correspondiente del notebook muestra cada solicitud y cada respuesta persistidas en `resultados/*/evidencia.jsonl`. Incluye los prompts completos de análisis y generación, parámetros y respuestas, identificados por caso, método y fecha UTC. La función `mostrar_intercambios()` imprime el contenido completo de todas las ejecuciones disponibles. La consulta de esta evidencia utiliza archivos locales y puede repetirse sin ejecutar nuevas llamadas al modelo.

## Evaluación del análisis

- [Evaluación campo por campo](EVALUACION_ANALISIS.md): entradas, análisis, textos generados y dictámenes humanos por completar.
- [Transcripción completa de Gemini](TRANSCRIPCION_COMPLETA_GEMINI.md): solicitudes y respuestas de las dos ejecuciones, desplegadas en Markdown.
- [Guía de curación](GUIA_CURACION.md): criterios y registro de decisiones.

Las observaciones propuestas requieren revisión humana. La publicación de esta documentación no cierra por sí sola la tarjeta de evaluación.

## Contraste y bloque complementario de prompt

Las [sugerencias](SUGERENCIAS_PROMPT_ANALISIS.md) contrastan instrucciones, respuestas e imprecisiones de respaldo. El [bloque complementario](BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt) conserva el estilo de marketing y acota afirmaciones de eficacia, magnitud, causalidad y alcance; requiere implementación y validación. Las respuestas originales permanecen íntegras.


## Ensayo del bloque complementario mediante API

[Resultados y 16 respuestas nuevas completas](RESULTADOS_COMPARACION_PROMPTS.md), [notebook ejecutado](comparacion_api_prompts.ipynb) y módulo `comparar_prompts.py`. Se conserva la evidencia de V1 (12 llamadas) y del ajuste V2 de newsletter (4 llamadas), incluidos resultados desfavorables. Los informes por etapa muestran los prompts completos y la configuración. Leer las salidas guardadas no consume API; ejecutar de nuevo las celdas de llamadas genera otras 16 solicitudes. La configuración local utiliza las mismas variables indicadas arriba.

Este ensayo mantiene fijo el análisis y prueba generación; no cambia el motor ni demuestra precisión general. El bloque vigente conserva el tono por formato y limita afirmaciones causales, magnitudes y cuantificación sin respaldo. V2 solo se ensayó en newsletter.


[Resumen de evaluación, observaciones y estado de cierre](CIERRE_EVALUACION.md).
