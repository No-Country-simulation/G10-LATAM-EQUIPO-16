# Sugerencia breve de ajuste del prompt de análisis

**Estado:** propuesta documental, no implementada ni probada con Gemini. Sustituye la propuesta extensa como versión recomendada para revisión. Se conservan el contrato y las categorías existentes, sin introducir una nueva definición de sentimiento.

## Qué se propone corregir

| Problema observado | Ajuste mínimo |
|---|---|
| Un relato individual se transforma en una afirmación general o causal. | Resumir hechos conservando alcance y atribución. |
| Una valoración del panel alterna entre feedback y testimonio. | Clasificar por propósito y dar prioridad a feedback para evaluación de uso. |
| Relevancia alta sin criterios explícitos en el prompt. | Describir alta, media y baja de forma breve, separadas del sentimiento. |
| Diferencias entre instrucciones individuales y batch. | Compartir el mismo bloque de criterios. |
| Una valoración individual aparece como mejora «significativa» de usabilidad. | Evitar magnitud no respaldada y posible confusión con significación estadística. |

Fuentes: [evaluación de respuestas](EVALUACION_ANALISIS.md) y [transcripción completa](TRANSCRIPCION_COMPLETA_GEMINI.md). La evidencia muestra imprecisiones con los prompts anteriores, no demuestra que su longitud sea la causa.

## Bloque sugerido

```text
Analiza cada mensaje de la comunidad usando los campos y valores admitidos
por el esquema de salida existente.

1. Resume los hechos del mensaje en el insight. Conserva quién hizo qué y el
   alcance del relato. No conviertas una experiencia individual en una regla
   general ni una secuencia temporal en una causa demostrada.
   Evita calificadores como «significativamente» sin respaldo de magnitud.

2. Clasifica por el propósito principal: logro si comunica un resultado
   alcanzado; feedback si evalúa una función o experiencia de uso; testimonio
   si relata una experiencia personal sin que predomine lo anterior. Ante una
   valoración concreta del producto, prioriza feedback sobre testimonio.
   Conserva pregunta_tecnica y otro para los casos correspondientes.

3. Evalúa relevancia para la comunidad: alta si aporta un hito o información
   concreta de utilidad clara; media si es pertinente pero general o limitada;
   baja si aporta poca información útil o está fuera de los objetivos.
   Relevancia y sentimiento son independientes.

4. Aplica los mismos criterios en análisis individual y por lote. Conserva
   los IDs recibidos cuando el contrato los incluya y devuelve únicamente
   el JSON solicitado, sin campos adicionales.
```

Texto disponible también en [BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt](BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt).

## Dos referencias para explicar fidelidad

**Entrada:** «Conseguí una pasantía de desarrollo frontend después de presentar mi proyecto de React».

- Resultado observado: «Los proyectos prácticos en React son efectivos para conseguir empleo en el sector».
- Insight sugerido: «Una persona informa que consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React».

**Entrada:** «Terminé mi proyecto de análisis de datos con Python y publiqué el repositorio para que puedan revisarlo».

- Resultado observado en una ejecución: «Los miembros comparten activamente sus proyectos completados, lo que demuestra un alto compromiso…».
- Insight sugerido: «Una persona terminó un proyecto de análisis de datos con Python y publicó el repositorio para revisión».

Las alternativas son propuestas de síntesis, no nuevas respuestas del modelo. Estos ejemplos pueden servir para discutir el criterio o como few-shot; si se incorporan al prompt, no deben contarse después como evaluación independiente.

## Observación sobre «significativamente»

En DEMO-003, Gemini afirmó que el panel «mejora significativamente la usabilidad». En un contexto técnico puede confundirse con significación estadística, que no se evaluó. Incluso en su sentido cotidiano de «considerablemente», atribuye una magnitud no respaldada: la entrada solo expresa utilidad percibida por una persona. Se sugiere conservar esa atribución individual, sin calificativos de magnitud. El término no es exclusivo de la estadística.

## Decisión de producto que requiere acuerdo

La prioridad feedback sobre testimonio es una sugerencia, no una verdad lingüística. El mensaje del panel admite ambas lecturas; la propuesta privilegia su valoración de una función. La categoría y la relevancia se eligen por el mensaje, no para forzar newsletter.

Un feedback negativo puede ser relevante y requerir gestión interna. Esta propuesta de análisis no sustituye las reglas de enrutamiento o revisión de quejas.

## Incorporación y comprobación

- Incorporar el bloque común en `ai-engine/prompts/analysis_prompt.txt` y en el prompt de `analyze_batch_texts()` de `ai-engine/analyzer.py`, manteniendo sus envolturas y esquemas actuales. El .txt adjunto no se carga automáticamente.
- Revisar que ambos prompts admitan los valores del contrato, incluido mixto; el bloque breve no redefine esas categorías.
- Mantener modelo y configuración al comparar el prompt anterior y el propuesto. Reutilizar las respuestas anteriores como referencia y guardar las nuevas por separado.
- Revisar fidelidad del insight, tipo, relevancia y IDs, incluyendo casos nuevos y posibles regresiones. Las decisiones humanas quedan registradas en la evaluación.

**No se afirma eficacia equivalente ni superior:** la versión breve es una candidata más simple. Su efecto debe medirse después de implementarla. No se modificó el motor ni se ejecutaron nuevas llamadas a Gemini como parte de esta propuesta.

Referencia de diseño: [Google — estrategias de prompting](https://ai.google.dev/gemini-api/docs/prompting-strategies): claridad, ejemplos y refinamiento iterativo.
