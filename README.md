# CommunityLab
## Motor Inteligente de Transformación y Distribución para Comunidades Digitales

> 🚧 **Proyecto en construcción** — Hackathon ONE G10 (Oracle Next Education & Alura), Semana 1 de 6.
> Este README es un documento vivo: se va completando a medida que el equipo avanza cada semana.

## El problema

Las comunidades digitales activas (Discord, Slack, foros) generan a diario testimonios de
logros, dudas técnicas recurrentes y proyectos destacados, pero la mayor parte de ese
contenido se pierde en el historial del chat. Los equipos de marketing y gestión de
comunidades no tienen tiempo de leer miles de mensajes a mano para encontrar esas historias
y convertirlas en contenido publicable.

## La solución

CommunityLab ingiere un lote de interacciones simuladas de una comunidad (CSV/JSON), las
analiza con un LLM para identificar sentimiento, tema y valor de marketing, y genera
automáticamente activos de distribución listos para publicar (posts de LinkedIn, FAQ,
resúmenes semanales), almacenándolos en OCI Object Storage para su revisión y curaduría.

## Cómo funciona (flujo general)

1. **Ingesta** — se recibe un lote de mensajes simulados de la comunidad.
2. **Persistencia** — cada mensaje se guarda tal cual antes de cualquier procesamiento.
3. **Análisis con IA** — un LLM clasifica sentimiento, tema y relevancia de cada mensaje.
4. **Generación** — se redacta el activo correspondiente (post, FAQ, resumen) con el tono adecuado por canal.
5. **Almacenamiento** — el activo generado se guarda en OCI Object Storage.
6. **Curaduría** — el equipo de marketing revisa antes de publicar de verdad.

## Stack tecnológico

| Componente | Tecnología |
| --- | --- |
| Backend / orquestación | Java (Spring Boot + Spring Data JPA) |
| Procesamiento de IA | Python (LangChain / LangGraph) |
| LLM | Por definir (Groq / Gemini Flash / Claude / GPT — en validación) |
| Base de datos (desarrollo local) | PostgreSQL (Docker Compose) |
| Base de datos (destino final) | Oracle Autonomous Database (Always Free) |
| Almacenamiento de activos | OCI Object Storage (Always Free) |
| Interfaz | Streamlit |

## Estructura del repositorio

```
├── ai-engine/     # Servicio Python — análisis de sentimiento/tema y generación de copy
├── backend/       # API Java Spring Boot — ingesta, persistencia, orquestación, integración OCI
├── frontend/      # Interfaz Streamlit — carga de datos y curaduría de activos generados
├── workflows/     # Automatización de flujos
└── docs/          # Documentación de soporte (dataset de prueba, guía de tono y prompts)
```

## Cómo levantar el entorno local

_Pendiente — en definición durante la Semana 1. Se documentará aquí apenas el equipo de
backend confirme la configuración de Docker Compose y los perfiles de conexión._

## Equipo

| Rol | Responsable |
| --- | --- |
| Project Management | Gabriela Correa |
| Backend (Java) | Bryan Naragio, Roberto Borja, Alexandra Estupiñan |
| Backend (Python) | Andrea Jaramillo |
| Machine Learning / prompt engineering | Oscar Cruz |
| Data Science | Saul Mendoza |
| Marketing / copywriting / tono de voz | Uziel Green |
| Frontend | Camilo Moroch |


## Estado del proyecto

Semana 1 de 6 — definiciones técnicas en curso. Este README se irá actualizando con cada
avance semanal del equipo.
