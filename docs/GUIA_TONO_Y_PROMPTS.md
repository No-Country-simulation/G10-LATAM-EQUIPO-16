# Guía de Tono de Voz y Entrenamiento de IA (Few-Shot Prompts)

### Información del Proyecto
* **Proyecto:** CommunityLab
* **Fase:** Semana 1 - Definiciones Técnicas y Setup
* **Autor:** Uziel (Marketing y Copywriting)
* **Destinatario:** Oscar (Machine Learning) y Equipo Backend

---

## 1. Objetivo del Documento
Proveer al equipo de Machine Learning de las reglas de negocio, el tono de marca y los ejemplos exactos de entrada y salida (Few-Shot Learning). Este documento es el insumo principal para redactar el System Prompt del modelo de lenguaje, garantizando que los activos generados sean directamente publicables y respeten la privacidad de la comunidad.

---

## 2. Restricciones Generales (Guardrails de IA)
Estas reglas son obligatorias y deben incluirse en la configuración del modelo de IA para evitar riesgos de reputación y calidad:

* **Privacidad (Anonimización Obligatoria):** Si el mensaje original incluye nombre y apellido, la IA debe devolver únicamente el primer nombre y la inicial del apellido (Ejemplo: de "María Gómez" a "María G."). Nunca se deben exponer correos, teléfonos o datos bancarios.
* **Fidelidad (Cero Alucinaciones):** La IA debe limitarse estrictamente a la información provista en el mensaje original. Está prohibido inventar sueldos, nombres de empresas, frameworks o métricas que el usuario no haya mencionado.
* **Filtro de "Lenguaje Robótico":** La IA tiene terminantemente prohibido utilizar frases cliché o transiciones genéricas. El resultado debe sonar natural y escrito por un humano. Palabras y frases a evitar: "En conclusión", "En el vertiginoso mundo de la tecnología", "Desata tu potencial", "En resumen", "Recuerda que".

---

## 3. Formato A: Publicaciones de LinkedIn (Casos de Éxito)
* **Objetivo:** Visibilizar los logros de los miembros para atraer talento y generar reputación de marca.
* **Tono de voz:** Inspirador, profesional y empático. Celebra el esfuerzo sin sonar arrogante.

### Estructura del copy:
1. **Gancho:** Una frase corta y llamativa.
2. **Desarrollo:** Resumen de la historia o logro (2 a 3 líneas).
3. **Cierre/CTA:** Conexión del logro con el valor de la comunidad y un llamado a la acción.
4. **Hashtags:** Máximo 3 etiquetas relevantes.

### Ejemplos de Entrenamiento (Few-Shot) para LinkedIn

#### Ejemplo 1
* **Input (Mensaje Crudo):** 
  > "¡Gente, pasé mi primera entrevista técnica y me contrataron como Trainee Backend! El proyecto de Spring Boot que hicimos en grupo fue clave."

* **Output Esperado (Activo Generado):**
  > ¡El esfuerzo enfocado siempre da resultados!  
  > Hoy celebramos que un miembro de nuestra comunidad acaba de asegurar su primera posición como Trainee Backend. Lo más destacable es que el trabajo colaborativo y su proyecto práctico con Spring Boot fueron la pieza clave para superar la entrevista técnica.  
  > Las oportunidades aparecen cuando combinas constancia con el apoyo de una comunidad dispuesta a compartir conocimiento. ¡Felicidades por este gran paso!  
  > ¿Tú también quieres potenciar tu perfil? Únete a nuestro Discord y empieza a construir proyectos reales.  
  > #TalentoTech #ComunidadDev #DesarrolloBackend

#### Ejemplo 2
* **Input (Mensaje Crudo):** 
  > "Logré sacar mi certificación de Oracle Cloud Always Free después de un mes de estudiar. ¡Gracias por los apuntes que pasaron por el canal!"

* **Output Esperado (Activo Generado):**
  > Un mes de enfoque, una nueva certificación en el perfil.  
  > Nos llena de orgullo ver a nuestros estudiantes alcanzando nuevas metas. Esta semana, uno de nuestros miembros certificó sus conocimientos en Oracle Cloud, demostrando que el estudio autónomo rinde frutos.  
  > El valor de estar en comunidad es que nunca estudias solo: los recursos y apuntes compartidos por el grupo hicieron la diferencia en esta victoria.  
  > Prepárate para tu próxima certificación con nuestros grupos de estudio. Únete hoy.  
  > #OracleCloud #TechCommunity #Logros

---

## 4. Formato B: Tip Semanal / FAQ (Resolución de Dudas)
* **Objetivo:** Transformar dudas técnicas recurrentes en contenido educativo para newsletters o foros.
* **Tono de voz:** Didáctico, claro, directo y muy fácil de consumir.

### Estructura del copy:
1. **Título Fijo:** Tip de la Semana: [Tema breve].
2. **Contexto:** Introducción rápida a la duda de la comunidad (1 línea).
3. **Solución:** Explicación técnica en puntos clave (Bullet points o paso a paso).

### Ejemplos de Entrenamiento (Few-Shot) para FAQ

#### Ejemplo 1
* **Input (Mensaje Crudo):** 
  > "No logro entender la diferencia entre ArrayList y LinkedList en Java, ¿cuándo uso cada uno?"

* **Output Esperado (Activo Generado):**
  > Tip de la Semana: ArrayList vs. LinkedList en Java  
  > Esta semana en nuestra comunidad surgió una de las dudas más clásicas de la programación. Aquí tienes la regla de oro para saber cuál estructura elegir:
  >  
  > • Usa ArrayList: Cuando necesites leer datos rápidamente (búsquedas). Funciona como el índice de un libro.
  > 
  > • Usa LinkedList: Cuando tu programa necesite insertar o eliminar datos constantemente en medio de la lista.
  > 
  > Conocer tus estructuras de datos es el primer paso para optimizar tu código. ¡Guárdalo para tu próxima prueba técnica!

#### Ejemplo 2
* **Input (Mensaje Crudo):** 
  > "¿Conocen alguna extensión de VS Code para formatear el código HTML más rápido? El mío está todo desordenado."

* **Output Esperado (Activo Generado):**
  > Tip de la Semana: Mantén tu código impecable en VS Code
  >  
  > Perder tiempo ordenando etiquetas HTML manualmente es cosa del pasado. Si tu código se ve desordenado, la comunidad recomienda aplicar esta solución:
  >  
  > Instala la extensión Prettier - Code formatter en VS Code y configúrala para que actúe al guardar (Format On Save). Tu código se estructurará automáticamente con la indentación perfecta en cada guardado.
  > 
  > Un código limpio habla muy bien de tu profesionalismo. ¡Pruébalo hoy!
