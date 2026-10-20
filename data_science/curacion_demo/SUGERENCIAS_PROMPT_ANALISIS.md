# Sugerencia de bloque complementario — marketing con afirmaciones respaldadas

**Estado:** propuesta de instrucciones adicionales; no implementada en el motor; ensayada de forma exploratoria con Gemini. Su finalidad es mejorar la precisión sin eliminar el tono de marketing, modificar las categorías ni reemplazar los prompts actuales.

## 1. Contraste entre instrucciones y respuestas

El contexto editorial explica las respuestas, pero no convierte toda afirmación en aceptable. La regla de no inventar información se mantiene aunque un ejemplo use lenguaje inspirador.

| Instrucción o referencia enviada | Respuesta registrada | Qué conserva valor | Imprecisión concreta | Mejora buscada |
|---|---|---|---|---|
| `analysis_prompt.txt` pide un hallazgo útil para Marketing y ejemplifica contribución de proyectos a la empleabilidad. `generate_linkedin()` pide tono positivo; el few-shot incluye constancia y aprendizaje aplicado. | «Los proyectos prácticos en React son efectivos para conseguir empleo en el sector.» | El hito profesional y la reflexión sobre aprendizaje aplicado son pertinentes. | Presenta eficacia general a partir de un caso que solo relata una pasantía después de presentar un proyecto. Los ejemplos no aportan evidencia para esa eficacia. | Conservar el hito y el cierre inspirador sin afirmarlo como eficacia demostrada o garantía. |
| El análisis busca una conclusión comunicacional, pero la entrada de DEMO-002 habla de una persona que terminó un proyecto y compartió su repositorio. | «Los miembros comparten activamente sus proyectos completados, lo que demuestra un alto compromiso…» | Reconoce un proyecto terminado y la posibilidad de compartir avances. | Amplía sujeto y frecuencia: un caso no demuestra conducta habitual de varios miembros. Alto compromiso es una interpretación, no un atributo medido. | Mantener el sujeto individual; expresar el valor editorial sin inventar frecuencia o alcance colectivo. |
| La entrada del panel expresa «me resulta útil» y el análisis pide un hallazgo. | «La centralización […] mejora significativamente la usabilidad […] para los usuarios.» | Identifica la organización de recursos y su utilidad relatada. | Añade magnitud y alcance. Significativamente puede sugerir significación estadística, sin prueba, datos ni fuente; incluso en sentido cotidiano intensifica una valoración individual sin respaldo. | Atribuir la utilidad a quien escribe; no afirmar mejora medida, importante o estadísticamente validada. |

Los pasajes anteriores son observaciones sustantivas de precisión y respaldo, no un rechazo global del contenido. El problema no es emplear lenguaje comercial, sino convertir una interpretación editorial en afirmación factual más fuerte que la evidencia disponible.

## 2. Bloque breve sugerido para añadir

```text
Mantén el tono y el formato indicados para cada activo: LinkedIn puede
ser positivo e inspirador; newsletter conserva su síntesis neutral y concisa.
No presentes una reflexión editorial como evidencia de un resultado.

Conserva quién hizo qué y el alcance del mensaje. Un caso individual no
permite afirmar conducta habitual de toda la comunidad ni eficacia general.

Sin datos o fuentes proporcionados, no atribuyas mejoras medidas, magnitudes,
causalidad demostrada o significación estadística. Evita «significativamente»
cuando no exista respaldo explícito; comunica la valoración como percepción
de quien escribe. Si hay una medición en la entrada, atribúyela a su fuente,
sin presentarla como validación independiente ni inventar citas.

En LinkedIn puedes celebrar el logro y cerrar con una reflexión motivacional
vinculada al mensaje, sin añadir hechos, garantías o promesas. En newsletter
no añadas reflexiones o beneficios generales que la entrada no exprese.
Conserva las instrucciones,
las categorías, los identificadores y el esquema de salida existentes.
```

Disponible también en [BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt](BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt). El texto no prohíbe cierres motivacionales: distingue esos recursos de las afirmaciones de hechos, eficacia, causalidad o magnitud.

## 3. Ubicación y compatibilidad

- **Análisis individual:** incorporar el criterio en `ai-engine/prompts/analysis_prompt.txt`. Mantener el esquema JSON y el marcador de entrada existentes.
- **Análisis batch:** incorporar el mismo criterio en `analyze_batch_texts()` de `ai-engine/analyzer.py`. Mantener IDs, categorías y estructura results.
- **Generación:** añadir el bloque junto a las instrucciones de `generate_linkedin()` y `generate_newsletter()` en `ai-engine/generators.py`. LinkedIn conserva su tono inspirador; newsletter conserva su estilo neutral y conciso.
- **Ejemplos existentes:** su función es mostrar tono y estructura, no validar los hechos de una respuesta nueva. Revisar el ejemplo del insight sobre empleabilidad para que no incentive una afirmación general presentada como evidencia. El cierre motivacional puede conservarse sin añadir una garantía o eficacia demostrada.

El generador posterior inspeccionado en main ya pide cierre fiel y limita hashtags. Este bloque concreta el criterio de respaldo para análisis y generación; no se afirma que falten todas las protecciones ni que la versión posterior produzca los mismos pasajes. La evidencia examinada pertenece al commit d62dd02.

## 4. Qué queda fuera de esta corrección

Feedback frente a testimonio sigue siendo una decisión de clasificación, no un orden de importancia. No se impone una categoría para producir newsletter. Tampoco se cambia sentimiento, relevancia, los contratos, el enrutador o los pesos del modelo como parte de esta propuesta.

## 5. Comprobación antes de afirmar una mejora

1. Comparar el prompt anterior y el complementado con el mismo modelo y configuración, reutilizando las respuestas anteriores como referencia.
2. Comprobar que las nuevas salidas mantienen tono y utilidad, conservan hechos y sujetos, y evitan atribuir eficacia general, frecuencia, causalidad o magnitud sin respaldo.
3. Aceptar reflexiones inspiradoras cuando no prometan resultados ni se presenten como demostración. No exigir copia literal del mensaje.
4. Verificar que el modelo no invente datos, fuentes, estudios o citas para justificar las afirmaciones.
5. Añadir casos distintos de los ejemplos usados en el prompt y registrar regresiones. Conservar IDs y formatos; revisar la selección de newsletter por separado.

Se incorporan 16 llamadas nuevas en dos etapas: V1 con tres mensajes y V2 con newsletter. El bloque anterior es V2; solo newsletter se probó con esta versión. Los resultados muestran un contraste causal favorable puntual, una regresión de V1 y el ajuste posterior; no una mejora general medida. Véase [la comparación completa](RESULTADOS_COMPARACION_PROMPTS.md). [La evaluación](EVALUACION_ANALISIS.md) y [la transcripción completa](TRANSCRIPCION_COMPLETA_GEMINI.md) exhiben el contraste que fundamenta el bloque sugerido.
