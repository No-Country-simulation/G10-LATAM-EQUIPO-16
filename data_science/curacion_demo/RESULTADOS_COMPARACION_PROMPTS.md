# Comparación del bloque complementario con Gemini

Se realizaron **16 llamadas reales**, todas con respuesta, el 20 de octubre de 2026 UTC (19 de octubre en Ciudad de México). Se compara cada prompt base con el mismo prompt extendido: modelo solicitado `gemini-3.5-flash-lite`, temperatura 0.2, máximo 2048 tokens y dos repeticiones por variante.

El objetivo es conservar un marketing útil e inspirador evitando atribuciones causales injustificadas, cuantificación inexistente y magnitudes sin respaldo. Una reflexión editorial no equivale a evidencia de eficacia. «Significativamente» admite un uso cotidiano, pero puede comunicar magnitud o validación estadística que la entrada no aporta.

## Método y alcance

Se reutilizan los prompts completos capturados de los generadores del commit `d62dd02ce1a358824b72336a6e4150be1ab81262` del PR #38, conservados por #39. Se mantienen constantes entrada, análisis y ejemplos. Las respuestas base de esta comparación son nuevas; las históricas se identifican aparte en los informes completos. Se alternó el orden base/extendido entre repeticiones.

La primera versión se probó con dos casos LinkedIn y uno newsletter (12 llamadas). Al observar una regresión en newsletter, se ajustó el bloque y se repitió únicamente ese caso (4 llamadas). Cada carpeta conserva el bloque exacto probado, los prompts y las respuestas. El notebook exhibe los pasos y las salidas completas.

## Hallazgos y límites

- **Atribución causal:** en DEMO-001, repetición 2, la base afirmó que un caso «demuestra cómo la construcción de proyectos propios impacta de forma directa en la empleabilidad». La extendida conservó la celebración sin esa afirmación causal. Es un contraste puntual, no una demostración de superioridad general.
- **Regresión conservada:** V1 extendió las dos respuestas de newsletter con reflexiones generales sobre desafíos, colaboración o aprendizaje. Esto contradice su síntesis neutral. No se descarta esa evidencia.
- **Ajuste compatible:** V2 distingue el tono de LinkedIn del newsletter. Sus dos respuestas extendidas conservaron la valoración individual del panel sin añadir esos beneficios generales. Las bases de esta segunda prueba también fueron sobrias.
- **Imprecisiones residuales:** V1 no eliminó todas las inferencias. DEMO-002 todavía incluyó «demuestra el compromiso con el desarrollo continuo» y calificó un repositorio de público. Publicar un repositorio para revisión no establece necesariamente acceso público. Estos pasajes requieren criterio editorial.
- **Cuantificación:** ninguna variante de esta pequeña prueba inventó cifras ni empleó «significativamente». Por tanto, el ensayo no permite afirmar que el bloque reduzca esos errores. Esa prevención es una intención de diseño que requiere casos adicionales.
- **Cobertura:** V2 solo se probó en newsletter; no se ha probado V2 en LinkedIn. No se reejecutaron análisis, selección de activos, endpoint ni backend. No se modificó el motor. Dos repeticiones sobre tres entradas no estiman precisión general ni significación estadística.

La propuesta queda disponible para revisión e integración; estos resultados no equivalen a aprobación editorial ni al cierre de la prueba integrada.

## Entradas y respuestas completas

### Entrada DEMO-001 — linkedin

> Conseguí una pasantía de desarrollo frontend después de presentar mi proyecto de React.

### Entrada DEMO-002 — linkedin

> Terminé mi proyecto de análisis de datos con Python y publiqué el repositorio para que puedan revisarlo.

### Entrada DEMO-003 — newsletter

> Probé el nuevo panel de proyectos de la comunidad: ahora encuentro el repositorio y las instrucciones de cada proyecto en el mismo lugar. Esta organización me resulta útil para empezar las pruebas.

## V1: tres mensajes, 12 llamadas

[Prompts, configuración y comparación completos](comparacion_api/20261020T001814Z/COMPARACION_GEMINI.md).

### DEMO-001_r1_base

Fecha de solicitud UTC: 2026-10-20T00:18:14.966737+00:00. Estado: respuesta.

````text
¡Los proyectos prácticos abren puertas!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. 

La práctica y la construcción de proyectos propios son fundamentales para dar el salto al mundo profesional. ¡Muchas felicidades por este gran paso!

Únete a nuestra comunidad en Discord.

#Frontend #DesarrolloWeb #TalentoTech
````

### DEMO-001_r1_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:15.989080+00:00. Estado: respuesta.

````text
¡Los proyectos prácticos abren puertas en el mundo tecnológico!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React.

Construir y mostrar proyectos propios es un paso clave para demostrar habilidades técnicas en procesos de selección. ¡Felicidades por este gran logro!

Únete a nuestra comunidad en Discord.

#DesarrolloFrontend #ComunidadDev #EmpleabilidadTech
````

### DEMO-001_r2_base

Fecha de solicitud UTC: 2026-10-20T00:18:21.098901+00:00. Estado: respuesta.

````text
Los proyectos prácticos abren puertas en el mundo laboral.

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. Este logro demuestra cómo la construcción de proyectos propios impacta de forma directa en la empleabilidad.

Construir y mostrar lo que sabes hacer marca la diferencia. ¡Muchas felicidades por este paso!

Únete a nuestra comunidad en Discord.

#Frontend #ComunidadDev #EmpleabilidadTech
````

### DEMO-001_r2_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:20.205991+00:00. Estado: respuesta.

````text
¡Los proyectos prácticos abren puertas en el mundo profesional!

Una persona de nuestra comunidad consiguió una pasantía de desarrollo frontend después de presentar su proyecto de React. 

Construir y mostrar proyectos propios es una excelente forma de demostrar habilidades técnicas ante los reclutadores. ¡Muchas felicidades por este gran paso!

Únete a nuestra comunidad en Discord.

#Frontend #DesarrolloWeb #ComunidadDev
````

### DEMO-002_r1_base

Fecha de solicitud UTC: 2026-10-20T00:18:16.783555+00:00. Estado: respuesta.

````text
El aprendizaje práctico da resultados visibles.

Una persona de nuestra comunidad terminó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

Compartir los proyectos completados demuestra el compromiso y la constancia en el desarrollo tecnológico. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#DataScience #Python #ComunidadTech
````

### DEMO-002_r1_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:17.432602+00:00. Estado: respuesta.

````text
De la práctica a la evidencia real.

Un proyecto de análisis de datos con Python ha sido finalizado y su repositorio ya está disponible publicamente para su revisión.

Compartir el código terminado permite visibilizar el aprendizaje práctico y demuestra el compromiso con el desarrollo continuo. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#AnalisisDeDatos #Python #ProyectosTech
````

### DEMO-002_r2_base

Fecha de solicitud UTC: 2026-10-20T00:18:23.365114+00:00. Estado: respuesta.

````text
Del código al repositorio público.

Una persona de nuestra comunidad finalizó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

La constancia en la práctica y el desarrollo de proyectos propios son claves para fortalecer el perfil técnico en tecnología. 

Únete a nuestra comunidad en Discord para seguir aprendiendo.

#DataScience #Python #ComunidadTech
````

### DEMO-002_r2_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:22.333072+00:00. Estado: respuesta.

````text
Del código a la práctica real.

Una persona de la comunidad finalizó su proyecto de análisis de datos con Python y ya publicó el repositorio para que pueda ser revisado. 

Construir y mostrar proyectos propios es una excelente forma de demostrar lo aprendido y poner manos a la obra. ¡Felicitaciones por este logro!

Únete a nuestra comunidad en Discord.

#DataScience #Python #AnalisisDeDatos
````

### DEMO-003_r1_base

Fecha de solicitud UTC: 2026-10-20T00:18:18.790528+00:00. Estado: respuesta.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones en el mismo lugar, lo que le resulta útil para empezar las pruebas.
````

### DEMO-003_r1_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:19.495881+00:00. Estado: respuesta.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones de cada proyecto en el mismo lugar, una organización que le resulta útil para empezar las pruebas. ¡Aprovechar estas herramientas facilita el inicio de nuevos desafíos tecnológicos!
````

### DEMO-003_r2_base

Fecha de solicitud UTC: 2026-10-20T00:18:24.868928+00:00. Estado: respuesta.

````text
Un miembro de la comunidad probó el nuevo panel de proyectos y destacó que encontrar el repositorio y las instrucciones en el mismo lugar resulta útil para empezar las pruebas.
````

### DEMO-003_r2_extendido

Fecha de solicitud UTC: 2026-10-20T00:18:24.230684+00:00. Estado: respuesta.

````text
Un miembro de la comunidad destacó que el nuevo panel de proyectos reúne el repositorio y las instrucciones en un mismo lugar, lo que facilita el inicio de las pruebas. Cada avance en la organización de nuestras herramientas impulsa la colaboración y el aprendizaje continuo.
````

## V2: ajuste de newsletter, 4 llamadas

[Prompts, configuración y comparación completos](comparacion_api/20261020T001920Z/COMPARACION_GEMINI.md).

### DEMO-003_r1_base

Fecha de solicitud UTC: 2026-10-20T00:19:20.880546+00:00. Estado: respuesta.

````text
Un integrante de la comunidad probó el nuevo panel de proyectos y destacó que ahora encuentra el repositorio y las instrucciones en el mismo lugar, una organización que resulta útil para empezar las pruebas.
````

### DEMO-003_r1_extendido

Fecha de solicitud UTC: 2026-10-20T00:19:21.512100+00:00. Estado: respuesta.

````text
Una persona de la comunidad señaló que el nuevo panel de proyectos resulta útil para empezar las pruebas, ya que ahora el repositorio y las instrucciones se encuentran en el mismo lugar.
````

### DEMO-003_r2_base

Fecha de solicitud UTC: 2026-10-20T00:19:23.908358+00:00. Estado: respuesta.

````text
Un miembro de la comunidad probó el nuevo panel de proyectos y destacó que encontrar el repositorio y las instrucciones en un mismo lugar resulta útil para comenzar las pruebas.
````

### DEMO-003_r2_extendido

Fecha de solicitud UTC: 2026-10-20T00:19:23.262094+00:00. Estado: respuesta.

````text
Una persona de la comunidad probó el nuevo panel de proyectos y señaló que encontrar el repositorio y las instrucciones en un mismo lugar resulta útil para empezar las pruebas.
````
