# Guía de Tono de Voz y Entrenamiento de IA (Few-Shot Prompts)

| Campo | Detalle |
| :-: | :-: |
| **Proyecto** | Aigoraweave |
| **Fase** | Semana 1 - Definiciones Técnicas y Setup |
| **Autor** | Uziel Green (Marketing y Copywriting) |
| **Destinatario** | Machine Learning, Backend y Frontend |

---

## 1. Objetivo del Documento

Proveer al equipo de Machine Learning de las reglas de negocio, el tono de marca y los ejemplos exactos de entrada y salida (Few-Shot Learning). Este documento es el insumo principal para redactar el System Prompt del modelo de lenguaje, garantizando que los activos generados sean directamente publicables, respeten la privacidad y eviten la invención de datos.

> **Nota sobre el dataset:** Los nombres incluidos en el dataset de demostración son ficticios y se utilizan exclusivamente para validar que el sistema elimine la identidad antes de generar los activos.

---

## 2. Restricciones Generales (Guardrails de IA)

Estas reglas son obligatorias y deben incluirse en la configuración del modelo de IA:

1. **Protección de identidad y minimización de datos:** Los activos generados no deben incluir el nombre, apellido ni iniciales del autor. Cuando sea necesario referirse a la persona, se utilizarán expresiones como “una persona de la comunidad” o “un integrante de la comunidad”. Tampoco deben exponerse correos, teléfonos ni otros datos sensibles presentes en el mensaje.
2. **Fidelidad Estricta (Cero Alucinaciones):** La IA debe limitarse estrictamente a la información provista en el mensaje original. Está prohibido inventar sueldos, empresas, métricas o iniciativas (como "grupos de estudio") que el usuario no haya mencionado.
3. **Lista Cerrada de Llamados a la Acción (CTAs Permitidos):** La IA solo puede utilizar uno de los siguientes CTAs al finalizar una publicación:
   - *"Únete a nuestra comunidad en Discord."*
   - *"Consulta más recursos en la documentación oficial."*
   - *"Comparte tus avances en el canal de proyectos."*
4. **Criterio de Descarte para Feedback Negativo:** Si un mensaje contiene quejas, reclamos o críticas de servicio, la IA debe marcarlo para revisión interna y descartar la generación automática de activos públicos (LinkedIn, Tip o Newsletter).
5. **Filtro de Lenguaje Robótico:** Prohibido utilizar clichés como *"En conclusión"*, *"En el vertiginoso mundo de la tecnología"*, *"Desata tu potencial"* o *"Recuerda que"*.

### 🚫 Ejemplo Negativo (Aplicación de Privacidad)
Para garantizar la correcta anonimización, la IA debe evitar filtrar datos como se muestra en este caso:

* **Input Ficticio (Mensaje Crudo):** *"Soy María Gómez y conseguí empleo gracias al programa. Escríbanme a maria@email.com."*
* ❌ **Salida Incorrecta:** *"María G. consiguió empleo gracias al programa..."* (Falla: expone iniciales).
* ✅ **Salida Esperada:** *"Una persona de nuestra comunidad alcanzó una nueva oportunidad profesional gracias al programa..."*

---

## 3. Formato A: Publicaciones de LinkedIn (Casos de Éxito)

* **Objetivo:** Visibilizar los logros de los miembros para atraer talento y generar reputación de marca.
* **Tono de voz:** Inspirador, profesional y empático.
* **Estructura:**
  - **Gancho:** Una frase corta y directa.
  - **Desarrollo:** Resumen del logro basado en los datos reales provistos (2 a 3 líneas).
  - **Cierre/CTA:** Uso exclusivo de la lista de CTAs permitidos.
  - **Hashtags:** Máximo 3 etiquetas relevantes.
  - **Longitud:** 150 a 250 palabras.

### Ejemplos Few-Shot para LinkedIn

#### Ejemplo 1 (Empleo / Contratación)
* **Input (Mensaje Crudo):** *"¡Gente, pasé mi primera entrevista técnica y me contrataron como Trainee Backend! El proyecto de Spring Boot que hicimos en grupo fue clave."*
* **Output Esperado:**
  > ¡El esfuerzo enfocado da resultados!
  > 
  > Un miembro de nuestra comunidad acaba de asegurar su primera posición como Trainee Backend. El trabajo colaborativo y la práctica en proyectos de Spring Boot fueron decisivos para superar la entrevista técnica.
  > 
  > Las oportunidades surgen al combinar constancia con aprendizaje aplicado. ¡Felicidades por este logro!
  > 
  > Únete a nuestra comunidad en Discord.
  > 
  > #TalentoTech #ComunidadDev #DesarrolloBackend

#### Ejemplo 2 (Certificación)
* **Input (Mensaje Crudo):** *"Logré sacar mi certificación de Oracle Cloud Always Free después de un mes de estudiar. ¡Gracias por los apuntes que pasaron por el canal!"*
* **Output Esperado:**
  > Un mes de preparación y una nueva certificación alcanzada.
  > 
  > Celebramos que un integrante de la comunidad certificó sus conocimientos en Oracle Cloud tras cuatro semanas de estudio constante.
  > 
  > El apoyo colaborativo y la revisión de los recursos compartidos en el canal facilitaron la preparación del examen.
  > 
  > Consulta más recursos en la documentación oficial.
  > 
  > #OracleCloud #TechCommunity #Logros

---

## 4. Formato B: Tip de la Semana (Resolución de Dudas / FAQ)

* **Nombre Oficial:** Tip de la Semana
* **Objetivo:** Transformar dudas técnicas recurrentes en contenido educativo rápido.
* **Tono de voz:** Didáctico, directo y estructurado.
* **Estructura:**
  - **Título Fijo:** Tip de la Semana: [Tema breve].
  - **Contexto:** Introducción de 1 línea a la consulta técnica.
  - **Solución:** Pasos o puntos clave en bullets.
  - **Longitud:** 50 a 100 palabras.

### Ejemplos Few-Shot para Tip de la Semana

#### Ejemplo 1 (Duda Conceptual)
* **Input (Mensaje Crudo):** *"No logro entender la diferencia entre ArrayList y LinkedList en Java, ¿cuándo uso cada uno?"*
* **Output Esperado:**
  > **Tip de la Semana: ArrayList vs. LinkedList en Java**
  > 
  > Surgió una duda frecuente sobre estructuras de datos en Java. Aquí la regla clave de uso:
  > 
  > • **ArrayList:** Ideal cuando requieres lecturas y búsquedas rápidas por índice.
  > • **LinkedList:** Recomendado para inserciones o eliminaciones frecuentes de elementos.
  > 
  > Elige la estructura según la operación principal de tu aplicación.

---

## 5. Formato C: Destaque para Newsletter Semanal

* **Objetivo:** Resumir el hito o debate más relevante de la semana para el boletín por correo.
* **Tono de voz:** Informativo, sobrio y conciso.
* **Estructura:**
  - **Titular:** [Categoría] + Tema principal.
  - **Resumen:** Síntesis de 2 líneas sobre la interacción o logro.
  - **Longitud:** 30 a 50 palabras.

### Ejemplo Few-Shot para Newsletter

* **Input (Mensaje Crudo):** *"Lanzamos la primera versión de la herramienta de testing para la API. Ya está el repositorio disponible para quien quiera probarlo."*
* **Output Esperado:**
  > **Destaque Semanal: Herramienta de Testing para API**
  > 
  > La comunidad publicó la versión inicial de la herramienta de pruebas para la API. El repositorio ya se encuentra disponible para revisión y pruebas colaborativas.
