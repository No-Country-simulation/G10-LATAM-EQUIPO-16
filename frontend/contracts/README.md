# Contrato de referencia para la interfaz

Orden de trabajo: contrato → ejemplos JSON → presentación → pruebas de pantalla.

Fuente: Backend main 8cef3b611d0efb22d1f51c7f4726ffc3ad6e12c6. Frontend PR #37, 46c7310. Los archivos sources/ conservan los diez DTO Java inspeccionados, sin modificar Backend. Enlace: https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/tree/8cef3b611d0efb22d1f51c7f4726ffc3ad6e12c6/backend/src/main/java/com/nocountry/communitylab/model/dto

## Solicitud
POST /api/v1/community/process. origen_comunidad y periodo_referencia: strings no blancos. interacciones: lista de 1 a 10 objetos. Cada objeto exige autor, canal, tipo y texto no blancos. Java genera los IDs: no inferirlos de la posición local. La pantalla puede completar metadatos faltantes antes de enviar; eso es política de interfaz, no opcionalidad del contrato Java. Mantiene los primeros diez mensajes válidos con aviso, según revisión posterior de Bryan en #37; confirmar con el equipo al cerrar.

## Respuesta
CommunityProcessResponseDto: lote_id (UUID), status, resumen_comunidad, activos_distribucion_generados, interacciones_fallidas, almacenamiento_oci. Los DTO de salida no declaran NotNull: tratar campos ausentes o null sin romper la pantalla. interacciones_analizadas no pertenece al DTO público Java: no usarlo para deducir fallos.

| Objeto | Campos JSON |
| --- | --- |
| resumen_comunidad | total_interacciones_procesadas, total_descartadas, sentimiento_predominante, temas_principales |
| post_linkedin | interaccion_id, titulo, copy, canal_recomendado, potencial_engagement |
| destaque_newsletter_semanal | interaccion_id, seccion, titular, resumen |
| sugerencia_contenido_faq | interaccion_id, tema, origen, pregunta, respuesta, status |
| interacciones_fallidas[] | id, motivo |
| almacenamiento_oci | bucket, ruta_objeto, status |

## Semántica del servicio (no restricciones de tipos del DTO)
status: exito/parcial/error. Fallidas: usar la lista explícita. No llamar fallido a un mensaje solo porque no produjo activo. OCI puede estar en raíz y anidado por compatibilidad; priorizar raíz. Estados OCI conocidos: simulado, guardado_con_exito, error_subida. HTTP 200 puede contener status error/parcial o error_subida: revisar ambos niveles. Sin mensajes que pasen el filtro puede haber exito con cero procesados, descartadas y activos/OCI null. Un activo por tipo/lote, no uno por mensaje.

## Errores HTTP
GlobalExceptionHandler en el mismo commit: 400 validación (timestamp/status/error/mensaje); 502 fallo definitivo IA; 503 indisponibilidad tras reintentos; 500 usa message. El 429 de IA se traduce a 502 en Java. JSON malformado puede recorrer el handler genérico: no garantizar aquí 400 para todo error de parseo. Los ejemplos demo actuales cubren respuestas HTTP 200; no simulan HTTP 400/502/503 ni infraestructura real.

## Schemas y límites
request.schema.json y response.schema.json son traducciones manuales de los DTO, no OpenAPI exportado por Spring. El schema de respuesta permite null/ausencia y campos extra para compatibilidad: no demuestra semántica ni versión desplegada. Las pruebas adicionales verifican campos esenciales de nuestros ejemplos. El patrón no-blanco aproxima NotBlank; diferencias Unicode requieren verificación contra Java.

Los JSON de demo_scenarios son salidas ficticias independientes del texto cargado, no respuestas producidas por IA. mock:// significa simulación; ningún objeto fue guardado. No son evidencia end-to-end ni de calidad del modelo.
