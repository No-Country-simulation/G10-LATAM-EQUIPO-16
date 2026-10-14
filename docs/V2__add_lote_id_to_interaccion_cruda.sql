-- V2: link each processed interaction to its DistributionBatch (entity field InteractionEntity.batchId).
-- Oracle ADB runs with ddl-auto=validate: apply this BY HAND before starting the app.

-- ===== Oracle =====
ALTER TABLE interaccion_cruda ADD (lote_id RAW(16));
CREATE INDEX idx_interaccion_cruda_lote ON interaccion_cruda (lote_id);
-- Optional FK (check that lote_distribucion.id is RAW(16) first):
-- ALTER TABLE interaccion_cruda ADD CONSTRAINT fk_interaccion_lote
--     FOREIGN KEY (lote_id) REFERENCES lote_distribucion (id);

-- ===== PostgreSQL (default profile) =====
-- ALTER TABLE interaccion_cruda ADD COLUMN IF NOT EXISTS lote_id UUID;
-- CREATE INDEX IF NOT EXISTS idx_interaccion_cruda_lote ON interaccion_cruda (lote_id);
