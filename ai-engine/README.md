# CommunityLab AI Engine

Motor de inteligencia artificial de **CommunityLab**, encargado de analizar interacciones de comunidades digitales y transformarlas en insights y activos de contenido mediante Gemini y LangGraph.

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
- Integrarse con el backend Java de CommunityLab.

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
