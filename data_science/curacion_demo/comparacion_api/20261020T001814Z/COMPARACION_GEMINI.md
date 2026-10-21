# Comparación de prompts mediante Gemini API

## Alcance

Ensayo exploratorio de generación: prompt base registrado frente al mismo prompt con un bloque complementario. Se mantienen mensaje, análisis, ejemplos y configuración por pareja. Se evalúa higiene de afirmaciones causales, magnitudes y cuantificación, conservando tono de marketing. No se prueba el endpoint ni el enrutamiento.

| Configuración | Valor |
|---|---|
| modelo_solicitado | gemini-3.5-flash-lite |
| inicio_utc | 2026-10-20T00:18:14.963737+00:00 |
| temperatura | 0.2 |
| max_output_tokens | 2048 |
| repeticiones_por_variante | 2 |
| sdk_google_genai | 2.24.0 |
| version_fuente_prompts | d62dd02ce1a358824b72336a6e4150be1ab81262 |

El prompt base procede de las funciones del PR #38 (d62dd02), capturado en la ejecución 20261018T030127Z_24cd58 del PR #39. Las salidas históricas se muestran como referencia separada. Las respuestas base y extendida de este ensayo son llamadas nuevas con la misma configuración; no se confunden con la ejecución histórica.

## Bloque complementario enviado

````text
Mantén el tono profesional, positivo e inspirador de los ejemplos, sin
presentar una reflexión editorial como evidencia de un resultado.

Conserva quién hizo qué y el alcance del mensaje. Un caso individual no
permite afirmar conducta habitual de toda la comunidad ni eficacia general.

Sin datos o fuentes proporcionados, no atribuyas mejoras medidas, magnitudes,
causalidad demostrada o significación estadística. Evita «significativamente»
cuando no exista respaldo explícito; comunica la valoración como percepción
de quien escribe. Si hay una medición en la entrada, atribúyela a su fuente,
sin presentarla como validación independiente ni inventar citas.

Puedes celebrar el logro y cerrar con una reflexión motivacional vinculada
al mensaje, sin añadir hechos, garantías o promesas. Conserva las instrucciones,
las categorías, los identificadores y el esquema de salida existentes.

````

## Estado de ejecución

Solicitudes registradas: 12. Respuestas con texto: 12. Errores o respuestas vacías: 0.

## Resultados completos por mensaje

### DEMO-001 — linkedin

**Entrada completa**

````text
Conseguí una pasantía de desarrollo frontend después de presentar mi proyecto de React.
````

**Prompt base completo**

````text

Eres un asistente de marketing para una comunidad educativa de tecnología.

Convierte la siguiente interacción en una publicación breve para LinkedIn.

INTERACCIÓN:
Canal: Discord
Mensaje: Conseguí una pasantía de desarrollo frontend después de presentar mi proyecto de React.

ANÁLISIS:
Sentimiento: positivo
Tema: empleabilidad
Tipo: logro
Relevancia: alta
Insight: Los proyectos prácticos impulsan directamente la inserción laboral de los miembros, lo cual puede usarse como caso de éxito en marketing.

EJEMPLOS DE REFERENCIA (muestran la estructura y el tono esperados; no copies sus hechos ni su contenido):
Ejemplo 1
Mensaje: ¡Gente, pasé mi primera entrevista técnica y me contrataron como Trainee Backend! El proyecto de Spring Boot que hicimos en grupo fue clave.
Publicación esperada:
¡El esfuerzo enfocado da resultados!

Una persona de nuestra comunidad acaba de asegurar su primera posición como Trainee Backend. El trabajo colaborativo y la práctica en proyectos de Spring Boot fueron decisivos para superar la entrevista técnica.

Las oportunidades surgen al combinar constancia con aprendizaje aplicado. ¡Felicidades por este logro!

Únete a nuestra comunidad en Discord.

#TalentoTech #ComunidadDev #DesarrolloBackend

Ejemplo 2
Mensaje: Logré sacar mi certificación de Oracle Cloud Always Free después de un mes de estudiar. ¡Gracias por los apuntes que pasaron por el canal!
Publicación esperada:
Un mes de preparación y una nueva certificación alcanzada.

Celebramos que una persona de la comunidad certificó sus conocimientos en Oracle Cloud tras un mes de estudio constante.

Los apuntes compartidos en el canal fueron parte de su preparación para el examen.

Consulta más recursos en la documentación oficial.

#OracleCloud #TechCommunity #Logros

INSTRUCCIONES:
- Escribe en español.
- Usa únicamente los hechos del mensaje de la interacción, nunca los de los ejemplos.
- Mantén un tono profesional, positivo y humano.
- No inventes información que no aparezca en la interacción.
- No agregues apoyo, colaboración, recursos ni otros beneficios de la comunidad que el mensaje no mencione.
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
- Máximo 100 palabras.
- Devuelve únicamente el texto de la publicación.

````

**Respuesta histórica — referencia, no ejecutada de nuevo para esta sección**

````text
¡La práctica se convierte en oportunidades!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. 

Construir proyectos reales es el camino directo para demostrar habilidades técnicas y abrir puertas en el sector tecnológico. ¡Muchas felicidades por este gran paso!

Únete a nuestra comunidad en Discord.

#Frontend #DesarrolloWeb #EmpleabilidadTech
````

#### Repetición 1

**base — respuesta**

Fecha UTC: 2026-10-20T00:18:14.966737+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 1.021 s.

````text
¡Los proyectos prácticos abren puertas!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. 

La práctica y la construcción de proyectos propios son fundamentales para dar el salto al mundo profesional. ¡Muchas felicidades por este gran paso!

Únete a nuestra comunidad en Discord.

#Frontend #DesarrolloWeb #TalentoTech
````

Palabras: 55. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 81, 'prompt_token_count': 762, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 762}], 'total_token_count': 843}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:15.989080+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.793 s.

````text
¡Los proyectos prácticos abren puertas en el mundo tecnológico!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React.

Construir y mostrar proyectos propios es un paso clave para demostrar habilidades técnicas en procesos de selección. ¡Felicidades por este gran logro!

Únete a nuestra comunidad en Discord.

#DesarrolloFrontend #ComunidadDev #EmpleabilidadTech
````

Palabras: 58. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 88, 'prompt_token_count': 960, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 960}], 'total_token_count': 1048}.

#### Repetición 2

**base — respuesta**

Fecha UTC: 2026-10-20T00:18:21.098901+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 1.232 s.

````text
Los proyectos prácticos abren puertas en el mundo laboral.

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. Este logro demuestra cómo la construcción de proyectos propios impacta de forma directa en la empleabilidad.

Construir y mostrar lo que sabes hacer marca la diferencia. ¡Muchas felicidades por este paso!

Únete a nuestra comunidad en Discord.

#Frontend #ComunidadDev #EmpleabilidadTech
````

Palabras: 67. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 95, 'prompt_token_count': 762, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 762}], 'total_token_count': 857}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:20.205991+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.89 s.

````text
¡Los proyectos prácticos abren puertas en el mundo profesional!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. 

Construir y mostrar proyectos propios es una excelente forma de demostrar habilidades técnicas ante los reclutadores. ¡Muchas felicidades por este gran paso!

Únete a nuestra comunidad en Discord.

#Frontend #DesarrolloWeb #ComunidadDev
````

Palabras: 58. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 88, 'prompt_token_count': 960, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 960}], 'total_token_count': 1048}.

### DEMO-002 — linkedin

**Entrada completa**

````text
Terminé mi proyecto de análisis de datos con Python y publiqué el repositorio para que puedan revisarlo.
````

**Prompt base completo**

````text

Eres un asistente de marketing para una comunidad educativa de tecnología.

Convierte la siguiente interacción en una publicación breve para LinkedIn.

INTERACCIÓN:
Canal: Discord
Mensaje: Terminé mi proyecto de análisis de datos con Python y publiqué el repositorio para que puedan revisarlo.

ANÁLISIS:
Sentimiento: positivo
Tema: proyectos prácticos
Tipo: logro
Relevancia: alta
Insight: Los miembros comparten activamente sus proyectos completados, lo que demuestra un alto compromiso y puede ser utilizado para destacar casos de éxito en la comunidad.

EJEMPLOS DE REFERENCIA (muestran la estructura y el tono esperados; no copies sus hechos ni su contenido):
Ejemplo 1
Mensaje: ¡Gente, pasé mi primera entrevista técnica y me contrataron como Trainee Backend! El proyecto de Spring Boot que hicimos en grupo fue clave.
Publicación esperada:
¡El esfuerzo enfocado da resultados!

Una persona de nuestra comunidad acaba de asegurar su primera posición como Trainee Backend. El trabajo colaborativo y la práctica en proyectos de Spring Boot fueron decisivos para superar la entrevista técnica.

Las oportunidades surgen al combinar constancia con aprendizaje aplicado. ¡Felicidades por este logro!

Únete a nuestra comunidad en Discord.

#TalentoTech #ComunidadDev #DesarrolloBackend

Ejemplo 2
Mensaje: Logré sacar mi certificación de Oracle Cloud Always Free después de un mes de estudiar. ¡Gracias por los apuntes que pasaron por el canal!
Publicación esperada:
Un mes de preparación y una nueva certificación alcanzada.

Celebramos que una persona de la comunidad certificó sus conocimientos en Oracle Cloud tras un mes de estudio constante.

Los apuntes compartidos en el canal fueron parte de su preparación para el examen.

Consulta más recursos en la documentación oficial.

#OracleCloud #TechCommunity #Logros

INSTRUCCIONES:
- Escribe en español.
- Usa únicamente los hechos del mensaje de la interacción, nunca los de los ejemplos.
- Mantén un tono profesional, positivo y humano.
- No inventes información que no aparezca en la interacción.
- No agregues apoyo, colaboración, recursos ni otros beneficios de la comunidad que el mensaje no mencione.
- El marcador [AUTOR] representa un nombre anonimizado y nunca debe aparecer en el contenido generado.
- Si aparece [AUTOR] en el mensaje o análisis, reformula la oración de manera natural sin incluir ese marcador ni intentar recuperar el nombre.
- Género de la persona: si el mensaje usa formas femeninas para quien lo escribe (por ejemplo "seleccionada"), respétalas. Si usa formas masculinas o un cargo en masculino (por ejemplo "desarrollador", "contratado"), no copies esa palabra, porque puede ser un masculino genérico: nombra el puesto con un sustantivo neutro ("un puesto de desarrollo backend", "el equipo de desarrollo") y refiérete a la persona como "una persona de la comunidad". Ejemplo: "me contrataron como desarrollador backend" se escribe "una persona de la comunidad se incorporó a un puesto de desarrollo backend". Si el mensaje no marca el género, usa siempre expresiones neutras. Esto aplica a cualquier sustantivo, adjetivo, participio o artículo que describa a la persona, no solo a los ejemplos: no uses una forma masculina para quien escribe a menos que el mensaje lo marque; usa "una persona", "quien" o una construcción impersonal.
- Máximo 100 palabras.
- Devuelve únicamente el texto de la publicación.

````

**Respuesta histórica — referencia, no ejecutada de nuevo para esta sección**

````text
El aprendizaje práctico se ve reflejado en cada proyecto completado.

Quien integra nuestra comunidad terminó un proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

Construir y compartir código fortalece el perfil profesional. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#DataScience #Python #ComunidadTech
````

#### Repetición 1

**base — respuesta**

Fecha UTC: 2026-10-20T00:18:16.783555+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.647 s.

````text
El aprendizaje práctico da resultados visibles.

Una persona de nuestra comunidad terminó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

Compartir los proyectos completados demuestra el compromiso y la constancia en el desarrollo tecnológico. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#DataScience #Python #ComunidadTech
````

Palabras: 57. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 81, 'prompt_token_count': 769, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 769}], 'total_token_count': 850}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:17.432602+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 1.356 s.

````text
De la práctica a la evidencia real.

Un proyecto de análisis de datos con Python ha sido finalizado y su repositorio ya está disponible publicamente para su revisión.

Compartir el código terminado permite visibilizar el aprendizaje práctico y demuestra el compromiso con el desarrollo continuo. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#AnalisisDeDatos #Python #ProyectosTech
````

Palabras: 58. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 84, 'prompt_token_count': 967, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 967}], 'total_token_count': 1051}.

#### Repetición 2

**base — respuesta**

Fecha UTC: 2026-10-20T00:18:23.365114+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.863 s.

````text
Del código al repositorio público.

Una persona de nuestra comunidad finalizó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

La constancia en la práctica y el desarrollo de proyectos propios son claves para fortalecer el perfil técnico en tecnología. 

Únete a nuestra comunidad en Discord para seguir aprendiendo.

#DataScience #Python #ComunidadTech
````

Palabras: 61. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 82, 'prompt_token_count': 769, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 769}], 'total_token_count': 851}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:22.333072+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 1.031 s.

````text
Del código a la práctica real.

Una persona de la comunidad finalizó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

Construir y mostrar proyectos propios es una excelente forma de demostrar lo aprendido y poner manos a la obra. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#DataScience #Python #AnalisisDeDatos
````

Palabras: 62. Hashtags: 3. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 87, 'prompt_token_count': 967, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 967}], 'total_token_count': 1054}.

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

Fecha UTC: 2026-10-20T00:18:18.790528+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.704 s.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones en el mismo lugar, lo que le resulta útil para empezar las pruebas.
````

Palabras: 34. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 37, 'prompt_token_count': 680, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 680}], 'total_token_count': 717}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:19.495881+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.708 s.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones de cada proyecto en el mismo lugar, una organización que le resulta útil para empezar las pruebas. ¡Aprovechar estas herramientas facilita el inicio de nuevos desafíos tecnológicos!
````

Palabras: 48. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 55, 'prompt_token_count': 878, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 878}], 'total_token_count': 933}.

#### Repetición 2

**base — respuesta**

Fecha UTC: 2026-10-20T00:18:24.868928+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.717 s.

````text
Un miembro de la comunidad probó el nuevo panel de proyectos y destacó que encontrar el repositorio y las instrucciones en el mismo lugar resulta útil para empezar las pruebas.
````

Palabras: 30. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 32, 'prompt_token_count': 680, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 680}], 'total_token_count': 712}.

**extendido — respuesta**

Fecha UTC: 2026-10-20T00:18:24.230684+00:00. Modelo devuelto: gemini-3.5-flash-lite. Duración: 0.636 s.

````text
Un miembro de la comunidad destacó que el nuevo panel de proyectos reúne el repositorio y las instrucciones en un mismo lugar, lo que facilita el inicio de las pruebas. Cada avance en la organización de nuestras herramientas impulsa la colaboración y el aprendizaje continuo.
````

Palabras: 45. Hashtags: 0. Finalización: FinishReason.STOP. Uso registrado: {'candidates_token_count': 49, 'prompt_token_count': 878, 'prompt_tokens_details': [{'modality': 'TEXT', 'token_count': 878}], 'total_token_count': 927}.

## Criterios de lectura

- Conservar el hecho principal y un tono publicable; no penalizar por sí sola una reflexión inspiradora.
- Detectar causalidad o eficacia presentadas como demostradas sin respaldo.
- Detectar cifras, magnitudes, comparaciones o validación estadística inexistentes.
- Distinguir percepción atribuida de mejora medida y mantener el alcance del sujeto.
- Comprobar que no se inventan fuentes o citas.
- Revisar también posibles pérdidas de naturalidad y regresiones.

## Limitaciones

Tres mensajes y dos repeticiones por variante. No son una estimación de precisión ni una prueba estadística de superioridad. La generación puede variar aun con temperatura fija. Los ejemplos incluidos en el prompt y el análisis previo se mantienen constantes: este ensayo aísla el efecto del bloque sobre generación, no evalúa una modificación del analizador. Se requieren criterios humanos para juzgar calidad; palabras y hashtags son controles descriptivos, no una puntuación de veracidad.
