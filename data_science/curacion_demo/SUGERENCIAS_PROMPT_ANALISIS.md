# Sugerencias de ajuste del prompt de análisis

**Estado:** propuesta técnica para revisión. Estas instrucciones todavía no se han incorporado al motor ni probado con Gemini. No se afirma una mejora medida ni se atribuye aprobación humana a Saúl o Andrea.

La propuesta corresponde al análisis de sentimiento, tema, tipo, relevancia e insight. Los prompts de generación de LinkedIn/newsletter y el código de enrutamiento se mantienen como asuntos separados.

## 1. Evidencia que motiva cada sugerencia

| Observación en las ejecuciones del PR #39 | Indicación sugerida | Resultado que debe comprobarse |
|---|---|---|
| «Conseguí una pasantía… después de presentar mi proyecto» se resume como eficacia de React para conseguir empleo en el sector. | Conservar el caso individual y separar secuencia temporal de causalidad. | Insight limitado al hecho relatado, sin afirmar eficacia general ni causalidad. |
| Un proyecto publicado por una persona se convierte en conducta activa de varios miembros y alto compromiso. | Mantener sujetos, cantidades y alcance; no añadir atributos no expresados. | Insight referido a una persona y su proyecto, sin conducta colectiva inventada. |
| El panel se clasifica feedback en análisis directo y testimonio en batch. | Definir propósito principal y priorizar feedback cuando el centro sea valorar una función. | Clasificación consistente con la prioridad acordada; no seleccionar etiquetas solo para forzar newsletter. |
| Todos los análisis reciben relevancia alta. | Definir los tres niveles y evitar alta por defecto. | Criterios aplicados al contenido; no exigir repartir artificialmente las clases. |
| Los prompts individual y batch describen de forma diferente los criterios. | Utilizar el mismo bloque de criterios para ambos. | La diferencia de envoltura y presencia de ID no cambia las definiciones. |

Fuentes: [evaluación](EVALUACION_ANALISIS.md), sección 6, y [transcripción de solicitudes y respuestas](TRANSCRIPCION_COMPLETA_GEMINI.md). Los errores observados motivan la propuesta, pero no demuestran que el prompt sea su única causa.

## 2. Indicaciones listas para incorporar, sujetas a revisión

El texto completo está en [BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt](BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt). Se propone utilizarlo como bloque común dentro de los dos prompts actuales, antes del mensaje o lote.

### Fidelidad e insight

```text
El insight resume lo que la persona comunica, conservando sujetos, cantidades
y alcance. No conviertas un caso individual en una conclusión sobre toda la
comunidad. «Después de» no demuestra «gracias a» ni eficacia general.
No añadas compromiso, proactividad, colaboración, apoyo comunitario ni
beneficios que la entrada no mencione. Si el autor afirma una causa, atribuye
esa afirmación al autor; no la presentes como un hecho validado externamente.
```

### Feedback, testimonio y logro

```text
Clasifica por el propósito principal del mensaje.
Si el centro es evaluar una función o experiencia de uso, prioriza feedback
frente a testimonio, aunque esté escrito en primera persona.
Si el centro es anunciar un resultado alcanzado, prioriza logro frente a
testimonio. Reserva testimonio para relatos que no encajen principalmente
como pregunta técnica, feedback o logro.
```

Esta prioridad es una sugerencia de producto: acota el uso actual de testimonio y debe acordarse antes de adoptarla. No se presenta como una definición objetiva universal.

### Sentimiento

```text
positivo: valoración favorable, satisfacción, agradecimiento o celebración.
negativo: queja, insatisfacción o valoración desfavorable.
neutro: descripción o consulta sin valoración emocional clara.
mixto: valoraciones favorables y desfavorables relevantes en el mismo mensaje.
No confundas un hecho favorable con emoción explícita.
```

Esta sugerencia puede cambiar positivo por neutro en relatos factuales de logros. No es una corrección ya aceptada: requiere acordar si la aplicación mide tono o valencia del acontecimiento. Los dos criterios no se deben alternar de forma implícita entre casos.

### Relevancia

```text
alta: hito o aprendizaje concreto claramente pertinente, o feedback específico
sobre el producto de la comunidad que identifique una función y un efecto
observado, con información suficiente para valorar su utilidad.
media: contenido pertinente, pero general, poco detallado o de prioridad incierta.
baja: escasa relación con los objetivos, spam o falta de información útil.
No asignes alta por defecto por mencionar tecnología, ser positivo o aparecer
solo en el lote. No distribuyas artificialmente las categorías.
```

La prioridad debe definirse según el producto. Relevancia alta no equivale a publicación autorizada, sentimiento positivo ni engagement. Una queja puede ser altamente relevante y requerir atención interna.

## 3. Aplicación propuesta en el código existente

| Lugar | Sugerencia | Contrato que se conserva |
|---|---|---|
| `ai-engine/prompts/analysis_prompt.txt`, usado por `analyze_text()` | Incorporar el bloque común y ejemplos contrastivos. Revisar el insight del ejemplo actual, que generaliza sobre empleabilidad. | Objeto con sentimiento, tema, tipo, relevancia e insight; sustitución actual de `{content}`. |
| `analyze_batch_texts()` en `ai-engine/analyzer.py` | Incorporar los mismos criterios y valores de sentimiento, incluido mixto. Mantener la instrucción de preservar IDs y el análisis del lote real. | Objeto results con una entrada por ID; los cinco campos de análisis e id. |
| Carga de criterios compartidos | Si se implementa, una fuente común para evitar divergencia entre ambos prompts. | Sin campos nuevos ni cambio en los DTOs o modelos Pydantic. |

El `.txt` adjunto es material propuesto: el motor actual no lo carga automáticamente. La incorporación requeriría un cambio explícito de Python/plantilla y pruebas posteriores. Este conjunto de documentos no modifica el servicio.

Los criterios deben preceder a los datos y tratar las instrucciones dentro del mensaje como contenido a analizar. Los ejemplos sirven para mostrar la distinción; no añaden hechos al mensaje nuevo.

## 4. Ejemplos de análisis sugeridos

Estas salidas son propuestas ilustrativas; no son respuestas nuevas de Gemini ni etiquetas humanas aprobadas. Las variantes de tema e insight con significado equivalente son aceptables.

### A. Pasantía de desarrollo frontend

**Entrada:**

> Conseguí una pasantía de desarrollo frontend después de presentar mi proyecto de React.

| Campo | Sugerencia |
|---|---|
| Sentimiento | neutro, bajo la regla propuesta de tono explícito: relata un hecho favorable sin expresar emoción. Esta es una sugerencia de criterio, no una corrección ya aprobada. |
| Tema | Pasantía de desarrollo frontend |
| Tipo | logro |
| Relevancia | alta, bajo el objetivo de visibilizar hitos profesionales |
| Insight | Una persona informa que consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. |

**Evitar:** «React es efectivo para conseguir empleo», «el programa consiguió su contratación», «demuestra el impacto de la formación».

### B. Proyecto terminado

**Entrada:**

> Terminé mi proyecto de análisis de datos con Python y publiqué el repositorio para que puedan revisarlo.

| Campo | Sugerencia |
|---|---|
| Sentimiento | neutro, bajo la misma regla propuesta de tono explícito. |
| Tema | Proyecto de análisis de datos con Python |
| Tipo | logro |
| Relevancia | alta, si compartir hitos técnicos es prioritario |
| Insight | Una persona informa que terminó un proyecto de análisis de datos con Python y publicó el repositorio para revisión. |

**Evitar:** «los miembros comparten activamente», «alto compromiso», «fomenta la colaboración» como resultados demostrados por este mensaje.

### C. Valoración del panel

**Entrada:**

> Probé el nuevo panel de proyectos de la comunidad: ahora encuentro el repositorio y las instrucciones de cada proyecto en el mismo lugar. Esta organización me resulta útil para empezar las pruebas.

| Campo | Sugerencia |
|---|---|
| Sentimiento | positivo: «me resulta útil» expresa una valoración favorable |
| Tema | Organización de recursos en el panel de proyectos |
| Tipo | feedback, si se acepta la prioridad de evaluación funcional frente a testimonio |
| Relevancia | alta propuesta: identifica una función concreta del producto y el beneficio observado por quien escribe; no implica un beneficio demostrado para toda la comunidad |
| Insight | Una persona valora que el panel reúne repositorios e instrucciones y señala que esa organización le resulta útil para iniciar pruebas. |

**Evitar:** «mejora significativamente la usabilidad para los usuarios», porque no hay medición ni evidencia de varias personas.

Feedback y relevancia alta producirían newsletter con el enrutador revisado en el snapshot. Feedback y relevancia media producirían general. Ninguna etiqueta debe elegirse únicamente para conseguir una demo de newsletter.

### D. Casos contrastivos adicionales propuestos

| Entrada ficticia | Propósito de revisión | Tipo sugerido | Sentimiento sugerido | Relevancia a acordar |
|---|---|---|---|---|
| «La exportación falla al generar el PDF y necesito ese archivo para entregar mi proyecto.» | Queja o dificultad de producto | feedback | negativo | Puede ser alta aunque no deba publicarse. |
| «¿Cómo agrego una columna a un DataFrame de pandas?» | Consulta explícita | pregunta_tecnica | neutro | Depende de utilidad y recurrencia; no inferir recurrencia no informada. |
| «Muy buena la app.» | Feedback positivo sin detalle | feedback | positivo | media según la rúbrica propuesta |
| «Gana dinero rápido: compra esta moneda y multiplica tus ingresos.» | Promoción ajena a los objetivos | otro | neutro si no expresa una valoración personal | baja |
| «La búsqueda funciona bien, pero la exportación sigue fallando.» | Valoraciones contrapuestas | feedback | mixto | Según prioridad del problema, sin usar sentimiento como relevancia. |

Estos casos no se han enviado a Gemini. Sirven para discutir los criterios y preparar una comparación posterior con casos nuevos.

## 5. Cómo comprobar una implementación posterior

1. Revisar las definiciones propuestas de sentimiento, prioridad feedback/testimonio y relevancia. Los ejemplos A–C aplican esas definiciones de forma explícita; su aceptación humana debe preceder a su adopción como few-shot.
2. Incorporar los mismos criterios a los dos prompts y registrar la nueva versión. Mantener constante el modelo y la configuración al comparar versiones de prompt.
3. Reutilizar las respuestas actuales como referencia anterior. Ejecutar el prompt propuesto con la misma muestra y guardar nuevas respuestas como evidencia separada.
4. Añadir mensajes distintos de los ejemplos incluidos en el prompt. Si los ejemplos A–C se usan como few-shot, su resultado posterior ya no es una validación independiente de generalización.
5. Revisar entrada frente a insight: sujetos, alcance, causalidad, beneficios añadidos y fidelidad. Comparar tipo y relevancia con el criterio humano acordado.
6. Verificar IDs, cantidad de respuestas y contrato en lote. Comprobar que mixto es admisible y se interpreta igual en ambos caminos.
7. Observar la ruta real de DEMO-003 sin forzar etiquetas. Validar aparte las reglas que excluyan quejas de activos públicos: el prompt de análisis no sustituye esa decisión de enrutamiento.
8. Registrar mejora, ausencia de cambio y regresiones; aprobar únicamente lo observado. Un ensayo satisfactorio de tres ejemplos no demuestra precisión general.

## 6. Estado de la entrega

| Elemento | Estado |
|---|---|
| Evidencia anterior desplegada y comparación propuesta | Documentadas en los Markdown de evaluación |
| Instrucciones adicionales listas para incorporar | Propuestas en el .txt adjunto |
| Aplicación al código de producción | No realizada |
| Nuevas pruebas con Gemini | No realizadas |
| Decisiones humanas sobre las alternativas | Pendientes |
| Publicación del nuevo PR | No realizada por esta preparación |

La propuesta documental puede revisarse completa como tal. No debe presentarse como corrección implementada o validada del comportamiento del motor.
