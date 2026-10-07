-- =====================================================================
-- Auditoría E2E de CommunityLab tras ejecutar el lote test-dataset-30.json
-- Compatible con PostgreSQL y Oracle (SQL estándar, sin funciones propietarias).
--
-- NOTA: las tablas y columnas son las reales de las entidades JPA:
--   interaccion_cruda  (InteractionEntity)     lote_distribucion (DistributionBatch)
-- y los estados se guardan como texto con el nombre del enum en INGLÉS:
--   PENDING, PROCESSING, PROCESSED, ERROR, DISCARDED
-- (no existen valores PROCESADO / DESCARTADO / PENDIENTE / PROCESANDO en la BD).
--
-- Resultado esperado con el dataset (4 vacías + 2 mensajes con saltos de línea):
--   * Con isTriviallyEmpty() ACTUAL:     DISCARDED = 6, PROCESSED = 24
--   * Con isTriviallyEmpty() CORREGIDO:  DISCARDED = 4, PROCESSED = 26
--   (PROCESSED asume IA y OCI disponibles; si fallan, verás PENDING o ERROR)
-- =====================================================================


-- 1. Conteo de interacciones por estado (solo el dataset de prueba)
--    Los estados con 0 filas no aparecen en el resultado.
SELECT status, COUNT(*) AS total
FROM interaccion_cruda
WHERE fuente_comunidad = 'Discord/Slack'
  AND periodo_referencia = '2026-semana-41'
GROUP BY status
ORDER BY status;


-- 2. Conteo global por estado (todas las ejecuciones)
SELECT status, COUNT(*) AS total
FROM interaccion_cruda
GROUP BY status
ORDER BY status;


-- 3. Relación lote <-> ruta guardada en OCI Object Storage
SELECT id, status, oci_bucket, ruta_oci, created_at, updated_at
FROM lote_distribucion
ORDER BY created_at DESC;


-- 4. Regla del pipeline: PROCESSED => ruta_oci NOT NULL
--    Debe devolver 0 filas.
SELECT id, status, created_at
FROM lote_distribucion
WHERE status = 'PROCESSED'
  AND ruta_oci IS NULL;


-- 5. Interacciones procesadas por lote (no hay FK: el vínculo es la ruta OCI compartida)
SELECT l.id AS lote_id,
       l.status,
       l.ruta_oci,
       COUNT(i.id) AS interacciones_procesadas
FROM lote_distribucion l
LEFT JOIN interaccion_cruda i
       ON i.ruta_oci = l.ruta_oci
      AND i.status = 'PROCESSED'
GROUP BY l.id, l.status, l.ruta_oci, l.created_at
ORDER BY l.created_at DESC;


-- 6. Interacciones atascadas: tras terminar el lote no debe haber ninguna en PROCESSING.
--    Debe devolver 0 filas.
SELECT id, fuente_comunidad, status, updated_at
FROM interaccion_cruda
WHERE status = 'PROCESSING';


-- 7. Auditoría de curaduría (después de usar PATCH /api/v1/assets/{id}/curate)
SELECT c.curado_en, c.activo_id, c.estado_anterior, c.estado_nuevo, c.notas_revisor
FROM curaduria_activo c
ORDER BY c.curado_en DESC;
