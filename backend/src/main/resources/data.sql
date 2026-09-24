-- Datos semilla para pruebas iniciales
INSERT INTO interaccion_cruda (id, origen_comunidad, periodo_referencia, autor, canal, tipo, texto, fecha_recibido, estado) 
VALUES (gen_random_uuid(), 'Discord_Grupo_ONE_G10', 'Semana_04', 'Usuario_Prueba', '#general', 'pregunta_tecnica', 'Prueba de conexión a BD', CURRENT_TIMESTAMP, 'PENDIENTE')
ON CONFLICT DO NOTHING;