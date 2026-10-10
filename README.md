# CommunityLab

## Motor inteligente de transformación y distribución de contenido para comunidades digitales

![Java](https://img.shields.io/badge/Java-21-orange) ![Spring Boot](https://img.shields.io/badge/Spring%20Boot-backend-6DB33F) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-AI%20Engine-009688)
<br>
![LangGraph](https://img.shields.io/badge/LangGraph-routing-1C3C3C) ![Gemini](https://img.shields.io/badge/Google-Gemini%20Flash--Lite-4285F4) ![Oracle](https://img.shields.io/badge/Oracle-Autonomous%20DB-F80000) ![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B) ![Status](https://img.shields.io/badge/status-en%20desarrollo-yellow)

> CommunityLab recibe interacciones de una comunidad digital, las analiza con IA y genera contenido listo para revisar (post de LinkedIn, FAQ y destacado de newsletter), con curaduría humana antes de publicar. Proyecto del equipo 16 de la Hackathon ONE G10 (Oracle Next Education & Alura).

* Última actualización: 9 de octubre de 2026.

## 📑 Tabla de contenidos

<!-- no toc -->
* [Un problema real y con un caso de uso claro](#-un-problema-real-y-con-un-caso-de-uso-claro)
* [Lo que hace CommunityLab](#-lo-que-hace-communitylab)
* [Arquitectura](#-arquitectura)
  * [Pipeline](#pipeline)
  * [Contrato de la API](#contrato-de-la-api)
* [Instalación](#-instalación)
* [Uso](#-uso)
* [Estructura del proyecto](#-estructura-del-proyecto)
* [Roadmap](#-roadmap)
* [Equipo](#-equipo)
* [Licencia](#-licencia)
* [Contribución](#-contribución)

## 🎯 Un problema real y con un caso de uso claro

Las comunidades digitales activas (Discord, Slack, foros) generan a diario testimonios de logros, dudas técnicas recurrentes y proyectos destacados. La mayor parte de ese contenido se pierde en el historial del chat, y los equipos de marketing y gestión de comunidades no tienen tiempo de leer miles de mensajes para encontrar esas historias y convertirlas en contenido publicable.

## 🧩 Lo que hace CommunityLab

Le entregas un lote de interacciones (CSV o JSON, hasta 10 por lote) y CommunityLab:

* **Analiza cada mensaje** → sentimiento, tema, tipo, relevancia e insight, con Gemini.
* **Enruta según el resultado** → logro o testimonio a LinkedIn, pregunta técnica a FAQ, feedback relevante a newsletter, con LangGraph.
* **Genera el activo de contenido** → con prompts por canal (la guía de tono de voz y la anonimización de autores están planificadas, aún no integradas). Por lote se genera un asset por tipo (el de mayor relevancia; ante empate, el primero en llegar). Límites actuales: el FAQ devuelve tema, origen y estado (la pregunta y la respuesta generadas aún no llegan en la respuesta), y el destacado de newsletter todavía no tiene formato definido.
* **Guarda y entrega para curaduría** → una persona aprueba, edita o rechaza antes de publicar (planificado: los endpoints de curaduría aún no existen).

## 🏗️ Arquitectura

CommunityLab está dividido en tres servicios:

| Capa | Tecnología | Qué hace |
| --- | --- | --- |
| Interfaz | Streamlit | Carga del lote (CSV, JSON o JSON pegado) y visualización de la respuesta |
| Backend | Java · Spring Boot · Spring Data JPA | Valida, persiste, filtra, orquesta y devuelve los activos |
| Motor de IA | Python 3.12+ · FastAPI · Uvicorn | Expone `/api/v1/analyze-batch` |
| Análisis | Google Gemini Flash-Lite (GenAI SDK) · Pydantic | Análisis estructurado y validado de cada interacción |
| Enrutamiento | LangGraph | Decide qué activo generar según el análisis |
| Base de datos | Oracle Autonomous Database (mTLS con wallet) | Persistencia de interacciones y lotes |
| Almacenamiento | OCI Object Storage | Guarda los activos generados (simulado por ahora; la subida real está en progreso) |

### Pipeline

```mermaid
graph LR
    A[Frontend<br/>Streamlit] --> B[Backend Java<br/>POST /community/process]
    B --> C[AI Engine<br/>POST /analyze-batch]
    C --> D[Gemini<br/>análisis]
    D --> E[LangGraph<br/>enrutamiento]
    E --> F[Activos: LinkedIn,<br/>FAQ, newsletter]
    F --> B
    B --> G[OCI Object Storage]
    B --> A
```

### Contrato de la API

| Endpoint | Propósito | Estado |
| --- | --- | --- |
| `POST /api/v1/community/process` | Procesa un lote y devuelve resumen y activos generados | ✅ Disponible |
| `GET /api/v1/assets/pending` | Lista activos pendientes de curaduría | ⏳ En progreso |
| `PATCH /api/v1/assets/{id}/curate` | Aprueba, edita o rechaza un activo | ⏳ En progreso |

Errores: `400` (cuerpo inválido; con más de 10 interacciones se rechaza el lote completo), `503` (falla del servicio de IA: el backend convierte cualquier error del AI Engine en 503) y `500` (error interno; responde con el campo `message` y no `mensaje`). Si alguna interacción falla, la respuesta llega con `status: "parcial"`. El AI Engine recibe hasta 10 interacciones por lote y usa el `id` de cada una dentro del lote; por ahora el análisis por interacción no se persiste.

## 🛠️ Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16.git
cd G10-LATAM-EQUIPO-16
```

### AI Engine (Python)

1. Crea y activa un entorno virtual:

```bash
cd ai-engine
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1 (si la política de ejecución lo bloquea: Set-ExecutionPolicy -Scope Process RemoteSigned) | Git Bash: source .venv/Scripts/activate
```

1. Instala las dependencias:

```bash
pip install -r requirements.txt
```

1. Configura tu variable de entorno copiando `.env.example` a `.env`:

   | Variable | Descripción |
   | --- | --- |
   | `GEMINI_API_KEY` | API key de Gemini (obligatoria: el AI Engine no arranca sin ella) |

### Backend (Java)

Requiere JDK 21. Copia `.env.example` de la raíz a `.env` y completa:

| Variable | Descripción |
| --- | --- |
| `ORACLE_DB_USER` | Usuario de Oracle Autonomous Database |
| `ORACLE_DB_PASSWORD` | Contraseña del usuario |
| `ORACLE_WALLET_PATH` | Ruta absoluta a la wallet mTLS |
| `ORACLE_DB_URL` | Cadena de conexión JDBC |
| `AI_SERVICE_URL` | URL del AI Engine (por defecto `http://localhost:8000`; aún no figura en `.env.example`) |

> El archivo `.env` contiene credenciales y no se sube al repositorio.

## ▶️ Uso

Levanta cada servicio en su propia terminal:

```bash
# AI Engine (desde ai-engine/)
uvicorn api:app --reload --host 127.0.0.1 --port 8000

# Backend (desde backend/)
./mvnw spring-boot:run

# Frontend (desde frontend/)
streamlit run app.py
```

* AI Engine: `http://127.0.0.1:8000/docs` (documentación interactiva) y `GET /health`.
* Backend: `http://localhost:8080/api/v1/health`.
* El Frontend apunta fijo a `http://localhost:8080`; la URL configurable está pendiente.

### Ejemplo: procesar un lote

```json
{
  "origen_comunidad": "Discord_Grupo_ONE_G10",
  "periodo_referencia": "Semana_04",
  "interacciones": [
    {
      "autor": "Lucas Albuquerque",
      "canal": "#dudas-langgraph",
      "tipo": "pregunta_tecnica",
      "texto": "Tengo dudas sobre cómo estructurar los nodos condicionales en LangGraph."
    }
  ]
}
```

La respuesta incluye `resumen_comunidad` (total procesado, sentimiento predominante, temas principales) y `activos_distribucion_generados` (post de LinkedIn, destacado de newsletter, sugerencia de FAQ y datos de almacenamiento en OCI).

## 🗂️ Estructura del proyecto

```text
G10-LATAM-EQUIPO-16/
├── ai-engine/          # Servicio Python: análisis y generación de contenido
├── backend/            # API Java Spring Boot: ingesta, persistencia, orquestación, OCI
├── frontend/           # Interfaz Streamlit
├── workflows/          # Automatización de flujos
├── docs/               # Guía de tono y prompts, dataset de prueba
├── .env.example        # Plantilla de variables de entorno
├── LICENSE
└── README.md
```

> No versionados por seguridad (ver `.gitignore`): `.env` y la wallet de Oracle.

## 🗺️ Roadmap

### Core

* [x] Estructura del backend y conexión a Oracle Autonomous Database
* [x] Entidades, repositorios y endpoint `POST /community/process`
* [x] AI Engine con Gemini, LangGraph y `/analyze-batch`
* [x] Integración Backend → AI Engine → Backend (validación extremo a extremo con el AI Engine en OCI pendiente)
* [x] MVP del Frontend en Streamlit y vista de resultados (PR #6 y #11)
* [x] AI Engine desplegado en OCI (pendiente: URL configurable, conexión segura y documentar el despliegue)

### Documentación

* [x] Guía de tono de voz y prompts Few-Shot (pendiente corregir ejemplos con datos inventados antes de integrarlos)
* [x] Dataset inicial de prueba (9 mensajes)

### En progreso

* [ ] Endpoints de curaduría (`/assets/pending` y `/assets/{id}/curate`)
* [ ] Reintentos ante errores temporales de la IA
* [ ] Subida real de los activos a OCI Object Storage
* [ ] Integrar la guía de tono de voz y anonimizar autores antes de enviar el texto a Gemini
* [ ] Dataset de demo balanceado (un mensaje por tipo de activo)
* [ ] Filtro previo de Data Science

## 👥 Equipo

| Rol | Responsable |
| --- | --- |
| Project Management | Gabriela Correa |
| Backend (Java) | Bryan Naragio, Roberto Borja, Alexandra Estupiñan |
| Backend (Python) | Andrea Jaramillo |
| Machine Learning / prompt engineering | Oscar Cruz |
| Data Science | Saul Mendoza |
| Marketing / copywriting / tono de voz | Uziel Green |
| Frontend | Camilo Moroch |

## 📄 Licencia

Revisa el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribución

Este es un proyecto de equipo. Todo cambio entra por rama y pull request hacia `main`, con revisión de al menos otra persona del equipo. Si encuentras un bug, abre un [issue](https://github.com/No-Country-simulation/G10-LATAM-EQUIPO-16/issues).
