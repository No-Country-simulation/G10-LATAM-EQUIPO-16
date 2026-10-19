# Guía de curación del análisis

## Archivos

- EVALUACION_ANALISIS.md: entradas, doce análisis, doce textos generados, criterios y decisiones propuestas.
- TRANSCRIPCION_COMPLETA_GEMINI.md: veinticuatro solicitudes y veinticuatro respuestas completas.
- generar_evaluacion.py: reconstrucción desde los registros locales; archivo de preparación, innecesario para leer la evaluación. Reejecutarlo reemplaza los Markdown y reinicia los campos de dictamen; las decisiones humanas se conservan editando los documentos sin regenerarlos.

## Revisión

1. Revisar los criterios de la sección 3 del informe. Acordar sentimiento favorable frente a emoción explícita y prioridad de feedback/testimonio.
2. Leer la entrada completa de cada ficha de la sección 6.
3. Comparar ID, sentimiento, tema, tipo, relevancia e insight. Completar cada Dictamen humano: Correcto, Ajustar, Discutible o No evaluable.
4. Señalar palabras concretas del insight que añaden causalidad, generalizan a otros usuarios o atribuyen beneficios no demostrados. Las alternativas sugeridas pueden editarse.
5. En DEMO-003 decidir qué categoría debe prevalecer y por qué. Alta no equivale automáticamente a newsletter; también se requiere feedback.
6. Completar revisor, fecha y justificación. Conservar la respuesta original; registrar cambios en el dictamen, no en la evidencia.
7. Revisar con Andrea D-01 a D-05 y registrar resolución, responsable y fecha acordados o limitación aceptada.
8. Actualizar la sección 7 y enlazar la evaluación mediante un nuevo PR hacia main. El PR #39 ya fue fusionado.

Las observaciones propuestas se prepararon con asistencia de IA. La revisión se atribuye a Saúl/Andrea únicamente después de que registren sus decisiones. No se necesitan nuevas llamadas a Gemini.
