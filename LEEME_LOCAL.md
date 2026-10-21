# Frontend — preparación para freeze

1. Leer frontend/contracts/README.md: contratos y fuentes exactas.
2. Revisar frontend/contracts/examples/ y frontend/demo_scenarios/: solicitudes y respuestas ficticias.
3. Leer frontend/REVISION_FREEZE.md: correcciones y criterios de aceptación.
4. Crear .venv y ejecutar .venv/Scripts/python.exe -m pip install -r frontend/requirements-dev.txt.
5. Ejecutar .venv/Scripts/python.exe -m pytest frontend -q.
6. powershell -ExecutionPolicy Bypass -File ./iniciar-demo.ps1; abrir http://127.0.0.1:8502.

Esta copia es independiente de la demo anterior en 8501. La demo usa respuestas fijas seleccionables: no Gemini, Java ni OCI. No requiere Live Server.
