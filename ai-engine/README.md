# Aigoraweave AI Engine

Motor de inteligencia artificial de **Aigoraweave**, encargado de analizar interacciones de comunidades digitales y transformarlas en insights y activos de contenido mediante Gemini y LangGraph.

## 🤖 Funcionalidades

El AI Engine permite:

- Procesar interacciones de la comunidad por lotes.
- Analizar sentimiento.
- Identificar temas principales.
- Clasificar el tipo de interacción.
- Determinar la relevancia de cada interacción.
- Generar insights mediante Gemini.
- Enrutar automáticamente cada interacción mediante LangGraph.
- Generar contenido para LinkedIn.
- Generar sugerencias de FAQ.
- Generar destacados para newsletter.
- Exponer el motor mediante una API REST con FastAPI.
- Integrarse con el backend Java de Aigoraweave.

## 🧠 Flujo del motor de IA

```text
Backend Java
     │
     ▼
POST /api/v1/analyze-batch
     │
     ▼
FastAPI
     │
     ▼
Gemini
     │
     ├── Sentimiento
     ├── Tema
     ├── Tipo
     ├── Relevancia
     └── Insight
     │
     ▼
LangGraph
     │
     ├── logro / testimonio ─────► LinkedIn
     ├── pregunta_tecnica ───────► FAQ
     ├── feedback relevante ─────► Newsletter
     └── otros ──────────────────► Ruta general
     │
     ▼
Respuesta JSON
     │
     ▼
Backend Java
```

## 🛠️ Tecnologías

- Python
- FastAPI
- Uvicorn
- Google Gemini
- Google GenAI SDK
- LangGraph
- LangChain
- Pydantic
- python-dotenv

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16.git
cd G10-LATAM-EQUIPO-16/ai-engine
```

### 2. Crear un entorno virtual

```bash
python -m venv .venv
```

En Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

## 🔐 Configuración de Gemini

El proyecto utiliza una variable de entorno para acceder a la API de Gemini.

1. Copia el archivo `.env.example` y crea un archivo `.env`.
2. Configura tu API key:

```env
GEMINI_API_KEY=your_api_key_here
```

Reemplaza `your_api_key_here` por tu API key de Gemini.

> ⚠️ El archivo `.env` contiene credenciales y no debe subirse al repositorio. Utiliza `.env.example` únicamente como plantilla.

## ▶️ Ejecutar el servicio

Con el entorno virtual activado y desde la carpeta `ai-engine`, ejecuta:

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

El servicio quedará disponible en:

```text
http://127.0.0.1:8000
```

### Health check

Para comprobar que el servicio está funcionando:

```text
GET /health
```

Ejemplo desde PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

### Documentación interactiva

FastAPI genera automáticamente documentación interactiva de los endpoints:

```text
http://127.0.0.1:8000/docs
```

## 📦 Análisis de interacciones por lote

El endpoint principal del AI Engine permite enviar varias interacciones en una sola solicitud para analizarlas con Gemini y procesarlas mediante LangGraph.

```text
POST /api/v1/analyze-batch
```

### Ejemplo de solicitud

```json
{
  "origen_comunidad": "Discord_Grupo_ONE_G10",
  "periodo_referencia": "Semana_04",
  "interacciones": [
    {
      "id": "uuid-1",
      "autor": "Mariana Souza",
      "canal": "#logros-y-empleos",
      "tipo": "testimonio",
      "texto": "Conseguí mi primer trabajo como desarrolladora de IA gracias a lo aprendido en el curso."
    },
    {
      "id": "uuid-2",
      "autor": "Lucas Albuquerque",
      "canal": "#dudas-langgraph",
      "tipo": "pregunta_tecnica",
      "texto": "Tengo dudas sobre cómo estructurar los nodos condicionales en LangGraph."
    },
    {
      "id": "uuid-3",
      "autor": "Ana Torres",
      "canal": "#general",
      "tipo": "feedback",
      "texto": "Me cuesta encontrar las clases grabadas y eso me frena para continuar con el curso."
    }
  ]
}
```

### Procesamiento

Para cada interacción, el motor obtiene:

- sentimiento
- tema
- tipo
- relevancia
- insight

Después, LangGraph selecciona la ruta correspondiente para generar el activo de contenido.

### Ejemplo de respuesta

```json
{
  "status": "exito",
  "resumen_comunidad": {
    "total_interacciones_procesadas": 3,
    "sentimiento_predominante": "positivo",
    "temas_principales": [
      "Empleabilidad en IA",
      "LangGraph",
      "Usabilidad de la plataforma"
    ]
  },
  "activos_distribucion_generados": {
    "post_linkedin": {
      "titulo": "Empleabilidad en IA",
      "copy": "Contenido generado para LinkedIn...",
      "canal_recomendado": "LinkedIn",
      "potencial_engagement": "alta"
    },
    "destaque_newsletter_semanal": {
      "seccion": "Usabilidad de la plataforma",
      "titular": "Insight generado a partir del feedback.",
      "resumen": "Contenido generado para newsletter..."
    },
    "sugerencia_contenido_faq": {
      "tema": "LangGraph",
      "origen": "#dudas-langgraph",
      "status": "BORRADOR"
    }
  }
}
```

> Los textos generados pueden variar entre ejecuciones porque son producidos dinámicamente por el modelo de IA.

## 🔐 Protección de datos y anonimización

El AI Engine incorpora un mecanismo de anonimización para reducir la exposición de datos personales antes de enviar interacciones a Google Gemini.

### Funcionamiento

* El módulo privacy.py crea una copia anonimizada de cada interacción.
* El nombre del autor se sustituye por Usuario anónimo.
* Las coincidencias del nombre completo del autor dentro del mensaje se reemplazan por [AUTOR].
* Los prompts de LinkedIn, FAQ y newsletter no incluyen el campo autor.
* Los endpoints /analyze y /api/v1/analyze-batch utilizan las interacciones anonimizadas durante el análisis y la generación de contenido.
* Se conserva el identificador original de cada interacción para mantener la trazabilidad.

### Pruebas de privacidad

Se incorporaron pruebas automatizadas para verificar la anonimización y el procesamiento de ambos endpoints, sin realizar llamadas reales a Gemini.

Desde la raíz del repositorio:

```powershell
python ai-engine/test_privacy.py
python ai-engine/test_api_privacy.py
```

### Limitaciones

La implementación actual protege el nombre completo conocido del autor, pero no garantiza la eliminación de nombres parciales, nombres de terceros, correos electrónicos, números telefónicos u otros datos personales incluidos en los mensajes.

Por ello, esta funcionalidad constituye una protección inicial y no una anonimización completa de toda la información personal.

## 🔄 Manejo de errores y reintentos

El AI Engine diferencia entre errores transitorios y errores permanentes durante la comunicación con Gemini.

### Errores transitorios

Situaciones como saturación temporal del servicio o límites de solicitudes pueden generar errores HTTP:

- `429` — Too Many Requests
- `503` — Service Unavailable

El backend Java puede reintentar automáticamente la solicitud ante estos errores. Actualmente se realizan hasta **3 intentos** antes de considerar fallido el procesamiento.

### Errores permanentes

Errores de procesamiento, validación o respuestas inválidas del modelo no se consideran transitorios y no deben provocar reintentos automáticos de la misma solicitud.

Este mecanismo evita reintentos innecesarios y mejora la tolerancia del flujo ante fallos temporales del proveedor de IA.

---

## ☁️ Despliegue en Oracle Cloud Infrastructure (OCI)

### 1. Infraestructura

El AI Engine de Aigoraweave está desplegado en una instancia de Oracle Cloud Infrastructure (OCI).

| Componente | Configuración |
|---|---|
| Proveedor | Oracle Cloud Infrastructure |
| Sistema operativo | Ubuntu Linux |
| IP pública actual | `<IP_PUBLICA>` |
| Usuario SSH | `<USUARIO_SSH>` |
| Directorio del repositorio | `<DIRECTORIO_REPOSITORIO>` |
| Directorio del motor | `<DIRECTORIO_REPOSITORIO>/ai-engine` |
| Framework | FastAPI |
| Servidor ASGI | Uvicorn |
| Puerto interno | `8001` |
| Gestor de servicios | systemd |
| Nombre del servicio | `nocountry-ai.service` |

*Estado:* el servicio funciona en OCI, pero actualmente solo acepta conexiones locales. La integración remota con el backend Java está pendiente.

### 2. Acceso al servidor

Desde un equipo autorizado, conectarse mediante SSH utilizando la clave privada correspondiente:

```bash
ssh -i /ruta/a/clave_privada <USUARIO_SSH>@<IP_PUBLICA>
```

No compartir ni subir claves privadas SSH al repositorio.

### 3. Preparación del entorno

En una instalación nueva de Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

Clonar el repositorio:

```bash
cd <DIRECTORIO_BASE>
git clone https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16.git
cd G10-LATAM-EQUIPO-16/ai-engine
```

Crear el entorno virtual e instalar las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 4. Configuración de Gemini

Crear el archivo `.env` dentro de `ai-engine`, utilizando `.env.example` como referencia.

Configurar la variable:

```env
GEMINI_API_KEY=your_api_key_here
```

Proteger el archivo:

```bash
chmod 600 .env
```

La clave real no debe incluirse en GitHub, registros de ejecución ni documentación pública.

### 5. Ejecución de FastAPI

El servicio desplegado utiliza Uvicorn con la siguiente configuración:

```bash
uvicorn api:app --host 127.0.0.1 --port 8001
```

Se utiliza `127.0.0.1` para restringir el acceso al propio servidor.

En el despliegue permanente, Uvicorn se ejecuta mediante systemd, por lo que no es necesario mantener una terminal abierta.

### 6. Administración con systemd

El servicio está registrado como:

```text
nocountry-ai.service
```

Para consultar su configuración efectiva:

```bash
sudo systemctl cat nocountry-ai
```

Para comprobar su estado:

```bash
sudo systemctl status nocountry-ai
```

Para reiniciarlo:

```bash
sudo systemctl restart nocountry-ai
```

Para habilitar el inicio automático:

```bash
sudo systemctl enable nocountry-ai
```

Para consultar los registros:

```bash
sudo journalctl -u nocountry-ai -n 100 --no-pager
```

La unidad `nocountry-ai.service` utiliza la siguiente configuración. Para reproducirla en otro servidor, reemplazar los valores genéricos según el entorno:

```ini
[Unit]
Description=No Country AI Engine - FastAPI
After=network-online.target
Wants=network-online.target

[Service]
User=<USUARIO_SERVICIO>
Group=<GRUPO_SERVICIO>
WorkingDirectory=<DIRECTORIO_REPOSITORIO>/ai-engine
Environment=PYTHONUNBUFFERED=1
ExecStart=<DIRECTORIO_REPOSITORIO>/ai-engine/.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 8001
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Guardar la configuración en `/etc/systemd/system/nocountry-ai.service` y ejecutar:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nocountry-ai
sudo systemctl status nocountry-ai
```

Los valores `<USUARIO_SERVICIO>`, `<GRUPO_SERVICIO>` y `<DIRECTORIO_REPOSITORIO>` deben adaptarse al servidor.

### 7. Proxy inverso con Nginx

Nginx está instalado y funcionando como proxy inverso del AI Engine.

La configuración actual utiliza el siguiente flujo:

```text
Nginx (127.0.0.1:8080)
          |
          v
FastAPI / Uvicorn (127.0.0.1:8001)
```

Configuración del servidor Nginx:

```nginx
server {
    listen 127.0.0.1:8080;
    server_name localhost;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Para verificar la configuración:

```bash
sudo nginx -t
sudo systemctl status nginx
curl http://127.0.0.1:8080/health
```

**Estado actual:** Nginx solo escucha en la interfaz local. La comunicación desde la instancia Java todavía no está habilitada. Antes de permitir conexiones privadas deben configurarse las reglas de red, la autenticación entre servicios y la protección del transporte.

### 8. Verificación del servicio

Desde la propia instancia OCI:

```bash
curl http://127.0.0.1:8001/health
```

Endpoints disponibles:

- `GET /health`: verificación del servicio.
- `POST /analyze`: análisis individual.
- `POST /api/v1/analyze-batch`: procesamiento de interacciones por lote.

Estos endpoints fueron probados desde la instancia OCI con datos de prueba.

### 9. Actualización del despliegue

Antes de actualizar, confirmar que los cambios estén aprobados y fusionados en la rama de despliegue.

Desde el servidor:

```bash
cd <DIRECTORIO_REPOSITORIO>
git status
git fetch origin
```

Verificar que no existan cambios locales que deban conservarse antes de continuar.

Una vez validado el estado del repositorio y autorizada la actualización:

```bash
git switch main
git pull --ff-only origin main

cd ai-engine
source .venv/bin/activate
python -m pip install -r requirements.txt

sudo systemctl restart nocountry-ai
sudo systemctl status nocountry-ai
curl http://127.0.0.1:8001/health
```

Los cambios deben probarse antes de considerarse desplegados correctamente.

### 10. Integración pendiente con Java

Actualmente FastAPI escucha únicamente en `127.0.0.1:8001`.

Por lo tanto, la IP pública de la instancia no constituye todavía una URL funcional para consumir directamente la API desde otro servidor.

Antes de habilitar la integración remota se requiere:

- Definir la conectividad entre el backend Java y OCI.
- Configurar HTTPS mediante un proxy inverso o una alternativa de conexión privada.
- Implementar autenticación entre servicios.
- Restringir el acceso mediante las reglas de red correspondientes.
- Validar la comunicación de extremo a extremo con Java.

No se recomienda exponer directamente el puerto interno de FastAPI a Internet sin controles de seguridad.

### 11. Estado del despliegue

**Completado:**
- Instalación y configuración del motor en OCI.
- Ejecución persistente mediante systemd.
- Inicio automático del servicio.
- Verificación del health check.
- Pruebas de análisis individual y por lotes.

**Pendiente:**
- Conexión segura con el backend Java.
- Pruebas de integración de extremo a extremo.
- Despliegue de los cambios posteriores a la versión instalada en OCI.

Esta documentación describe la configuración conocida del despliegue y debe mantenerse actualizada cuando cambien la infraestructura o los mecanismos de acceso.

### 12. Actualización pendiente de minimización de datos

La implementación de minimización de datos de autores está incluida en el PR #16:

https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/pull/16

**Estado:** PR #16 fusionado en main. Despliegue y funcionamiento de la anonimización en OCI pendientes de verificación.

Aunque el PR #16 ya fue fusionado en `main`, todavía es necesario verificar si sus cambios están desplegados en OCI. Para ello, se deberá revisar la versión instalada, actualizar el código si corresponde, instalar las dependencias necesarias, reiniciar `nocountry-ai.service` cuando sea necesario y validar los endpoints y la anonimización de datos.

Hasta completar ese procedimiento, no debe considerarse activa en OCI la protección incorporada por el PR #16.
