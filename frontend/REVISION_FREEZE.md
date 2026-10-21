# Revisión de compatibilidad de la interfaz — PR #37

Se continúa el trabajo de Camilo. Estos ajustes alinean la presentación con los contratos Java; no califican el trabajo ni cambian el motor.

## Cambios acotados
- FAQ: presentar pregunta/respuesta cuando existen; admitir ausencia/null.
- Resultados parciales: leer interacciones_fallidas con id/motivo; eliminar deducción por índices locales incompatibles con UUID.
- Mostrar almacenamiento raíz incluso si no hay activos.
- Cinco escenarios explícitos y ficticios; no enviar solicitudes en demo.
- Actualizar expectativas antiguas del fixture FAQ y agregar pruebas reales de UI con Streamlit AppTest.

## Se conserva
Recorte a diez con aviso según revisión posterior de Bryan; metadatos predeterminados; timeout 200 s; manejo HTTP existente. No se refactoriza toda la aplicación durante el freeze.

## Validación antes de integrar
1. Instalar frontend/requirements-dev.txt en .venv.
2. Ejecutar python -m pytest frontend -q.
3. Iniciar iniciar-demo.ps1 y abrir http://127.0.0.1:8502.
4. Pegar contracts/examples/request_valido.json y procesar cada escenario del selector lateral.
5. FAQ completa: pregunta y respuesta visibles.
6. Parcial: exactamente un ID fallido y su motivo; ninguno inventado.
7. OCI: aviso visible y activos conservados.
8. Todos descartados: cero procesados y tres descartados, sin errores de pantalla.

## Pendientes externos y fuera del cambio
Conexión al Backend desplegado, errores HTTP reales, Gemini, Oracle y objetos OCI reales: pendientes. Contratos main no garantizan versión desplegada. Acordar con Camilo la incorporación y con revisores la política de diez mensajes.

La normalización actual colapsa saltos y espacios del texto; se conserva por alcance de freeze y debe confirmarse con el equipo antes de afirmar conservación literal. No se garantiza calidad del contenido por pasar tests de UI. No hay push ni PR automático.

Revisiones de origen:
- https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/pull/37#pullrequestreview-5565738043
- https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/pull/37#pullrequestreview-5580984340
