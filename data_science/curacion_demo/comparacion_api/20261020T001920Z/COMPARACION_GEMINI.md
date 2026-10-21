# Comparación de prompts mediante Gemini API

## Alcance

Ensayo exploratorio de generación: prompt base registrado frente al mismo prompt con un bloque complementario. Se mantienen mensaje, análisis, ejemplos y configuración por pareja. Se evalúa higiene de afirmaciones causales, magnitudes y cuantificación, conservando tono de marketing. No se prueba el endpoint ni el enrutamiento.

| Configuración | Valor |
|---|---|
| modelo_solicitado | gemini-3.5-flash-lite |
| inicio_utc | 2026-10-20T00:19:20.877546+00:00 |
| temperatura | 0.2 |
| max_output_tokens | 2048 |
| repeticiones_por_variante | 2 |
| sdk_google_genai | 2.24.0 |
| version_fuente_prompts | d62dd02ce1a358824b72336a6e4150be1ab81262 |

El prompt base procede de las funciones del PR #38 (d62dd02), capturado en la ejecución 20261018T030127Z_24cd58 del PR #39. Las salidas históricas se muestran como referencia separada. Las respuestas base y extendida de este ensayo son llamadas nuevas con la misma configuración; no se confunden con la ejecución histórica.

## Bloque complementario enviado

````text
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

````

## Estado de ejecución

Solicitudes registradas: 4. Respuestas con texto: 4. Errores o respuestas vacías: 0.

## Resultados completos por mensaje

### DEMO-003 — newsletter

**Entrada completa**

````text
Probé el nuevo panel de proyectos de la comunidad: ahora encuentro el repositorio y las instrucciones de cada proyecto en el mismo lugar. Esta organización me resulta útil para empezar las pruebas.
````

**Prompt base completo**

````text

Eres un asistente de marketing para una comunidad educativa de tecnología.

Convierte la siguiente interacción en un destaque breve para el newsletter semanal.

INTERACCIÓN:
Canal: Discord
Mensaje: Probé el nuevo panel de proyectos de la comunidad: ahora encuentro el repositorio y las instrucciones de cada proyecto en el mismo lugar. Esta organización me resulta útil para empezar las pruebas.

ANÁLISIS:
Sentimiento: positivo
Tema: experiencia de usuario
Tipo: feedback
Relevancia: alta
Insight: La reorganización del panel de proyectos mejora la usabilidad y facilita el inicio de pruebas para los usuarios.

EJEMPLOS DE REFERENCIA (muestran la estructura y el tono esperados; no copies sus hechos ni su contenido):
Ejemplo 1
Mensaje: Lanzamos la primera versión de la herramienta de testing para la API. Ya está el repositorio disponible para quien quiera probarlo.
Destaque esperado:
La comunidad publicó la versión inicial de la herramienta de pruebas para la API. El repositorio ya se encuentra disponible para revisión y pruebas colaborativas.

INSTRUCCIONES:
- Escribe en español.
- Usa únicamente los hechos del mensaje de la interacción, nunca los de los ejemplos.
- Resume únicamente los hechos expresados en la interacción.
- Mantén un tono profesional, neutral y humano.
- No inventes información que no aparezca explícitamente en la interacción.
- No afirmes que la organización tomó, está tomando o tomará acciones, medidas o decisiones si eso no aparece explícitamente en la interacción.
- No inventes compromisos, soluciones, mejoras, avances, estados de trabajo ni promesas de la organización.
- No conviertas una sugerencia, queja o dificultad del usuario en una acción confirmada de la organización.
- Puedes reformular el mensaje para hacerlo más claro, pero sin agregar hechos nuevos.
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
- Máximo 80 palabras.
- Devuelve únicamente el texto del destaque.

````

**Respuesta histórica — referencia, no ejecutada de nuevo para esta sección**

````text
Una persona de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones en el mismo lugar, una organización que le resulta útil para empezar las pruebas.
````

#### Repetición 1

**base — respuesta**

Fecha UTC: 2026-10-20T00:19:20.880546+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.63 s.

````text
Un integrante de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones en el mismo lugar, una organización que resulta útil para empezar las pruebas.
````

Palabras: 34. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 37, 'prompt_token_count': 680, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 680}], 'total_token_count': 717}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:19:21.512100+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 1.748 s.

````text
Una persona de la comunidad señaló que el nuevo panel de proyectos resulta útil para empezar las pruebas, ya que ahora el repositorio y las instrucciones se encuentran en el mismo lugar.
````

Palabras: 32. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 34, 'prompt_token_count': 917, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 917}], 'total_token_count': 951}.

#### Repetición 2

**base — respuesta**

Fecha UTC: 2026-10-20T00:19:23.908358+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.451 s.

````text
Un miembro de la comunidad probó el nuevo panel de proyectos y destacó que encontrar el repositorio y las instrucciones en un mismo lugar resulta útil para comenzar las pruebas.
````

Palabras: 30. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 32, 'prompt_token_count': 680, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 680}], 'total_token_count': 712}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:19:23.262094+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.644 s.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y señaló que encontrar el repositorio y las instrucciones en un mismo lugar resulta útil para empezar las pruebas.
````

Palabras: 30. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 32, 'prompt_token_count': 917, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 917}], 'total_token_count': 949}.

## Criterios de lectura

- Conservar el hecho principal y un tono publicable; no penalizar por sí sola una reflexión inspiradora.
- Detectar causalidad o eficacia presentadas como demostradas sin respaldo.
- Detectar cifras, magnitudes, comparaciones o validación estadística inexistentes.
- Distinguir percepción atribuida de mejora medida y mantener el alcance del sujeto.
- Comprobar que no se inventan fuentes o citas.
- Revisar también posibles pérdidas de naturalidad y regresiones.

## Limitaciones

1 mensajes y dos repeticiones por variante. No son una estimación de precisión ni una prueba estadística de superioridad. La generación puede variar aun con temperatura fija. Los ejemplos incluidos en el prompt y el análisis previo se mantienen constantes: este ensayo aísla el efecto del bloque sobre generación, no evalúa una modificación del analizador. Se requieren criterios humanos para juzgar calidad; palabras y hashtags son controles descriptivos, no una puntuación de veracidad.
