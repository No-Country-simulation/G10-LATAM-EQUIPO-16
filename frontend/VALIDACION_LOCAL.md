# Validación local

Base frontend: PR #37, 46c7310f599dfba6a74299b636841c62fcd0b8df.
Referencia Backend: main 8cef3b611d0efb22d1f51c7f4726ffc3ad6e12c6.
Entorno: Windows, Python 3.11; versiones exactas en requirements-local-lock.txt.

Comando: .venv/Scripts/python.exe -m pytest frontend -q
Resultado: 64 passed in 2.64s.

Incluye 50 pruebas existentes adaptadas al contrato FAQ actual y 14 nuevas comprobaciones de schema, carga de escenarios y presentación mediante Streamlit AppTest. AppTest verifica los cinco escenarios y comprueba que no se invoque requests.post en demo.

Resultado: FAQ muestra pregunta y respuesta; parcial lista solo el ID fallido declarado; éxito no inventa fallos; error OCI muestra advertencia; descartadas muestra el conteo. Las pruebas no realizan solicitudes a Gemini, Backend, Oracle ni OCI.

Pendiente: revisión visual humana, capturas para PR y prueba con Backend desplegado. No se ha enviado push ni creado PR. El congelamiento de código y la integración se coordinan con Camilo y revisores.
