# Sugerencias de precisión editorial — revisión contextual

**Recomendación:** conservar los prompts actuales como punto de partida. La evidencia revisada no justifica una reescritura general ni imponer una síntesis literal a todo contenido de marketing.

## Fundamento

- La plantilla de análisis pide un hallazgo útil para Marketing y ejemplifica contribución de proyectos a la empleabilidad.
- El generador de LinkedIn recibe ese insight, solicita tono positivo y utiliza cierres inspiradores en sus few-shot.
- Los resultados observados son compatibles en términos generales con esa orientación.
- El código local de main revisado ya incorpora cierre fiel, CTA autorizado y límite de hashtags. Las ejecuciones del PR #39 corresponden a una versión anterior; no demuestran fallos del código posterior.

[Evaluación y evidencia](EVALUACION_ANALISIS.md).

## Precisiones opcionales

| Aspecto | Sugerencia proporcionada |
|---|---|
| Generalizaciones de marketing | Aclarar si el insight admite interpretación comunicacional. No tratarlas automáticamente como hechos inventados. |
| Una persona descrita en plural | Preferir singular cuando se quiera conservar el alcance del relato. |
| Significativamente | Puede sugerir significación estadística, no evaluada, o magnitud importante. Utilidad percibida es una alternativa precisa. No se presupone uso estadístico ni fallo general. |
| Feedback/testimonio | Mantener las dos categorías. Acordar prioridad solo si resulta necesaria para el producto; no forzar feedback para obtener newsletter. |
| Relevancia | Documentar alta/media/baja como criterio de evaluación. Tres resultados altos no prueban un defecto. |

## Aclaración breve candidata, solo si se acuerda incorporarla

```text
El insight puede aportar una interpretación comunicacional coherente con
el mensaje y los ejemplos. Distingue esa interpretación de hechos concretos:
no añadas personas, empresas, cifras, logros o compromisos no mencionados.
Conserva el alcance individual cuando corresponda y evita presentar una
valoración como resultado medido o estadísticamente validado.
Mantén las categorías, el esquema de salida y los identificadores existentes.
```

[Texto opcional](BLOQUE_SUGERIDO_PROMPT_ANALISIS.txt). No es un reemplazo del prompt completo ni se carga automáticamente.

## Validación proporcional

La revisión documental puede aceptar la muestra con observaciones y límites. Si se decide modificar el comportamiento, comprobar únicamente ese cambio y sus regresiones con la misma configuración y casos nuevos; las respuestas anteriores ya están disponibles como referencia. Sin cambios acordados de prompt, esta evaluación no exige repetir llamadas ni rehacer el desarrollo.

No se modifica el motor, no se declara mejora medida y no se revoca la aprobación editorial existente. La selección automática newsletter y la corrida integrada siguen su seguimiento específico.
