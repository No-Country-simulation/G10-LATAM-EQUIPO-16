# Evidencia de almacenamiento en OCI — Aigoraweave

Ejecuciones realizadas el 26 de octubre de 2026, entre las 18:00 y las 19:05 (hora de Bogotá), en la demo permanente (`https://aigoraweave.duckdns.org`), desde el panel de Streamlit, en modo "En vivo" y con el backend "Conectado". Los autores de todos los mensajes son neutros (ejemplo del panel y pruebas ficticias de Marketing).

## Resultados

| # | Prueba | Procesadas | Descartadas | Sentimiento | Activos generados | Lote | Estado OCI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Ejemplo del panel (9 mensajes) | 9 de 9 | 0 | Neutral | LinkedIn, newsletter y FAQ | `3fff2129-d7b9-4c83-ad5d-fb34e01f3254` | `guardado_con_exito` |
| 2 | Excel, gastos (10 mensajes, 1 canal) | 10 de 10 | 0 | Positivo | LinkedIn y FAQ; newsletter vacío en esta ejecución | `ca8359b2-28a7-41f4-b2d3-f0aa4193526a` | `guardado_con_exito` |
| 3 | Reclutamiento (10 mensajes, 3 canales) | 10 de 10 | 0 | Positivo | LinkedIn, newsletter y FAQ | `0d0ea57c-e0f3-46fc-b31c-75794e0dfa3e` | `guardado_con_exito` |
| 4 | RutaExpress (10 mensajes, 3 canales, con un mensaje no válido) | 9 de 10 | 1 | Mixto | LinkedIn, newsletter y FAQ | `67b40d80-421b-49bd-a90b-7429bcb34615` | `guardado_con_exito` |

En las cuatro ejecuciones: `status: exito`, 0 interacciones fallidas y bucket `aigoraweave-pr50-test`. La ruta del objeto sigue el formato `oci://aigoraweave-pr50-test/activos/Semana_01/paquete-distribucion-<lote_id>.json`.

Rutas completas:

1. `oci://aigoraweave-pr50-test/activos/Semana_01/paquete-distribucion-3fff2129-d7b9-4c83-ad5d-fb34e01f3254.json`
2. `oci://aigoraweave-pr50-test/activos/Semana_01/paquete-distribucion-ca8359b2-28a7-41f4-b2d3-f0aa4193526a.json`
3. `oci://aigoraweave-pr50-test/activos/Semana_01/paquete-distribucion-0d0ea57c-e0f3-46fc-b31c-75794e0dfa3e.json`
4. `oci://aigoraweave-pr50-test/activos/Semana_01/paquete-distribucion-67b40d80-421b-49bd-a90b-7429bcb34615.json`

## Qué demuestran

* **Transformación con variedad:** tres temáticas distintas, uno a tres canales y sentimientos neutral, positivo y mixto.
* **Descarte funcional:** en la prueba 4, el mensaje `"..."` se descartó (1 descartada, 9 procesadas, 0 fallidas) sin afectar al resto del lote.
* **Variabilidad del motor:** en la prueba 2 el newsletter quedó vacío; el sistema genera un activo por tipo según el análisis y no siempre hay uno apto.
* **Almacenamiento:** el backend respondió una ruta `oci://` con el estado `guardado_con_exito`, que solo devuelve cuando no está en modo simulado.

## Verificación en la consola de OCI Object Storage

Verificado en la consola de OCI (región Chile Central, Santiago) para la prueba 4 (RutaExpress). Solo se inspeccionó y descargó ese objeto: de las otras tres ejecuciones se registraron las respuestas del backend, las rutas y los registros de Oracle, pero no se abrió cada archivo.

Detalle del objeto de la prueba 4:

* El objeto existe en el bucket `aigoraweave-pr50-test` (namespace `axfj94golgwj`), en `activos/Semana_01/paquete-distribucion-67b40d80-421b-49bd-a90b-7429bcb34615.json`. Almacenamiento: Standard. Tamaño: 5,77 KiB.
* Se descargó el objeto y su contenido corresponde a la ejecución: `lote_id` `67b40d80-421b-49bd-a90b-7429bcb34615`, generado el 27/10/2026 a las 00:03:37 UTC (19:03 en Bogotá), origen `Discord_Grupo_ONE_G10`, periodo `Semana_01`.
* El archivo contiene el resumen de la comunidad (9 procesadas, sentimiento mixto, 5 temas principales), el post de LinkedIn, el destaque de newsletter y la sugerencia de FAQ en estado `BORRADOR`, y el análisis de cada una de las 9 interacciones procesadas (sentimiento, tema, tipo, relevancia e insight). `interacciones_fallidas` está vacío y `total_descartadas` es 1.

Notas sobre el contenido guardado:

* El campo `almacenamiento_oci` va en `null` dentro del archivo, porque el paquete se arma antes de la subida; el estado `guardado_con_exito` solo aparece en la respuesta del backend.
* Dentro de `resumen_comunidad`, `total_descartadas` está en `null`; el valor 1 figura al final del archivo y en la respuesta del backend.

## Verificación en Oracle Autonomous Database

Consultas de solo lectura en Database Actions (SQL), esquema `AIGORAWEAVE_TEST`, el 26 de octubre de 2026.

**Tabla `lote_distribucion`:** los cuatro lotes existen con estado `PROCESSED` y bucket `aigoraweave-pr50-test`; la `ruta_oci` de cada uno coincide con el objeto del bucket.

| Lote | Creado (UTC) | Estado |
| --- | --- | --- |
| `3fff2129-d7b9-4c83-ad5d-fb34e01f3254` | 2026-10-26 23:08:26 | `PROCESSED` |
| `ca8359b2-28a7-41f4-b2d3-f0aa4193526a` | 2026-10-27 00:00:32 | `PROCESSED` |
| `0d0ea57c-e0f3-46fc-b31c-75794e0dfa3e` | 2026-10-27 00:01:48 | `PROCESSED` |
| `67b40d80-421b-49bd-a90b-7429bcb34615` | 2026-10-27 00:03:30 | `PROCESSED` |

**Tabla `interaccion_cruda`**, agrupada por `ruta_oci` y `status`:

* Lote `3fff2129…`: 9 `PROCESSED`.
* Lote `ca8359b2…`: 10 `PROCESSED`.
* Lote `0d0ea57c…`: 10 `PROCESSED`.
* Lote `67b40d80…`: 9 `PROCESSED`.
* Sin `ruta_oci`: 1 `DISCARDED` (canal LinkedIn, texto `...`, creada el 2026-10-27 00:03:29.978 UTC, 25 ms antes del lote `67b40d80…`).

Las interacciones descartadas no se enlazan por `ruta_oci` a un lote, porque no entran al paquete; la asignación al lote `67b40d80…` se deduce por el texto `...` y la hora de creación, que coinciden con la prueba 4 (9 procesadas y 1 descartada).

## Entorno y versión desplegada

Datos confirmados por Óscar el 27 de octubre de 2026, tras revisar la instancia OCI `nocountry-ai-engine` (IP pública `155.181.177.178`, región Chile Central, única instancia del compartimento raíz):

* **Cadena:** dominio público → Nginx → Streamlit (`127.0.0.1:8502`) → backend Spring Boot (`127.0.0.1:8084`).
* **Frontend:** servicio `aigoraweave-pr50-frontend.service`, puerto 8502, directorio `/home/ubuntu/communitylab-pr50-review`. Su variable `BACKEND_URL` apunta a `127.0.0.1:8084`.
* **Backend:** servicio `aigoraweave-pr50.service` (Java, Spring Boot), puerto 8084, carpeta `/home/ubuntu/communitylab-release-test/backend`, JAR `target/communitylab-0.0.1-SNAPSHOT.jar`. Perfil Spring `oracle`, esquema `AIGORAWEAVE_TEST`.
* **Object Storage:** modo `real`, bucket `aigoraweave-pr50-test`, namespace `axfj94golgwj`.
* Ambos servicios los gestiona systemd.

Versiones:

* **Backend:** el HEAD de su carpeta es `4ce1e68` (PR #49, 21/10/2026). Comparado con `main`, el código del backend es idéntico: no hay cambios entre ambos. Reserva: la carpeta tiene cambios locales sin commit y el JAR no registra su commit de compilación, por lo que no es una versión certificada.
* **Frontend:** no se informó su commit. Por comparación entre la interfaz en vivo y el historial del repositorio, corresponde a `ba10ed7` (PR #50): el nombre y el logo de Aigoraweave existen desde ese commit, y la interfaz aún muestra "Enviando a: …", que `ee5c834` reemplazó.
* **AI Engine:** no se confirmó qué servicio usa este backend ni su commit. La instancia tiene además los servicios `nocountry-backend`, `nocountry-ai` y `nocountry-frontend` (puertos 8081, 8001 y 8501), cuyo HEAD es `0105a76` con cambios locales sin commit en el AI Engine. Podría ser el `nocountry-ai`, pero no está verificado.

## Qué falta por verificar

1. El servicio y el commit del AI Engine que usa el backend de la demo.
2. Los objetos de las otras tres ejecuciones; en la lista del bucket aparecen varios archivos `paquete-distribucion-…`, pero solo se abrió el de la prueba 4.

## Observaciones

* El bucket de estas ejecuciones, `aigoraweave-pr50-test`, pertenece a los servicios `aigoraweave-pr50*` (entorno de revisión del PR #50). El `communitylab-results` que documenta `docs/OCI_DEPLOYMENT.md` corresponde a los servicios `nocountry-*`.
* Estas cuatro ejecuciones crearon cuatro lotes reales en la base y cuatro objetos en el bucket de la demo.
