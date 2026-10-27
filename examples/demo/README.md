# Escenarios de prueba manual para la demo

Conversaciones ficticias para demostración. No contienen testimonios reales.

## Uso

1. Los escenarios están en esta carpeta, `examples/demo/`.
2. En la aplicación, cargar un archivo JSON a la vez o copiar su contenido completo en Pegar JSON.
3. Procesar el lote y registrar la respuesta observada.

| Archivo | Interacciones | Canales | Propósito |
| --- | --- | --- | --- |
| 01_excel.json | 10 | Discord: 10 | Aprendizaje, dudas y logros; generación de activos. |
| 02_reclutamiento.json | 10 | Discord: 4, LinkedIn: 3, WhatsApp: 3 | Reclutamiento y variación de canales. |
| 03_rutaexpress.json | 10 | Instagram: 4, X: 3, LinkedIn: 3 | Crisis de servicio, sentimiento y descarte de contenido no válido. |

## Observaciones y límites

- En una prueba previa, Excel generó LinkedIn, Newsletter y FAQ; en la ejecución del 26/10/2026 generó LinkedIn y FAQ, con el newsletter vacío. El motor genera un activo por tipo según el análisis, así que el resultado puede variar.
- La interacción final de RutaExpress contiene `"texto": "..."` intencionalmente. Probada por separado, produjo 1 descartada, 0 procesadas y 0 fallidas, con estado Sin contenido válido.
- RutaExpress completo, ejecutado el 26/10/2026 en la demo permanente: 9 procesadas, 1 descartada y 0 fallidas, con sentimiento mixto.
- Las cuatro ejecuciones del 26/10/2026 (estos tres escenarios y el ejemplo del panel) y su verificación en OCI y Oracle están en `docs/EVIDENCIA_ALMACENAMIENTO_OCI.md`. La generación de activos y el sentimiento pueden variar entre ejecuciones.
- Descartada y fallida son estados diferentes. Estos archivos no inducen deliberadamente una falla del servicio.
- Se validó la sintaxis JSON y la estructura de los tres archivos; esto no equivale a ejecutar pruebas automáticas de la aplicación.
