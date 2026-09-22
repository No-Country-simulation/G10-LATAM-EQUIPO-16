# CommunityLab - Dataset Inicial de Prueba (MVP)

### Resumen y Cobertura

| ID | Tipo de mensaje | Autor simulado | Sentimiento | Tema principal | Caso para Demo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **MSG-001** | Discord | Juan Perez | Positivo | Feedback Producto | Análisis de sentimiento positivo |
| **MSG-002** | Slack | María Gómez | Negativo | Bug/Error | Detección de quejas urgentes |
| **MSG-003** | Telegram | Carlos Ruiz | Neutral | Consulta | Preguntas frecuentes |
| **MSG-004** | Discord | Ana Martinez | Positivo | Feature Request | Ideas para roadmap |
| **MSG-005** | Slack | Pedro Sánchez | Negativo | Facturación | Riesgo de Churn |
| **MSG-006** | Comunidad Web | Laura Torres | Positivo | Agradecimiento | Brand advocates |
| **MSG-007** | Telegram | Diego Lopez | Neutral | Soporte Técnico | Enrutamiento de tickets |
| **MSG-008** | Slack | Sofía Castro | Negativo | Rendimiento | Monitoreo de caídas (Downtime) |
| **MSG-009** | Discord | Roberto Fernández | Neutral | Spam/Irrelevante | Filtro de ruido (Spam) |
| **MSG-010** | Comunidad Web | Elena Vega | Neutral | Integraciones | Uso de API externa |

---

## Mapeo Detallado

#### MSG-001
* **Autor Crudo:** Juan Perez
* **Iniciales:** J.P.
* **Mensaje original:** "¡Me encanta la nueva actualización! La interfaz está súper rápida y fluida."
* **Etiquetas ML:** `[feedback, UI/UX, positivo, fidelización]`

#### MSG-002
* **Autor Crudo:** María Gómez
* **Iniciales:** M.G.
* **Mensaje original:** "El sistema no me deja exportar el PDF. Me tira un error 500 y tengo que presentarlo en 10 minutos."
* **Etiquetas ML:** `[bug, error_500, queja, urgente, negativo]`

#### MSG-003
* **Autor Crudo:** Carlos Ruiz
* **Iniciales:** C.R.
* **Mensaje original:** "¿Alguien sabe cómo se cambia el idioma del dashboard? No encuentro la opción en settings."
* **Etiquetas ML:** `[consulta_general, onboarding, neutral]`

#### MSG-004
* **Autor Crudo:** Ana Martinez
* **Iniciales:** A.M.
* **Mensaje original:** "Sería increíble si pudieran agregar modo oscuro en la próxima versión. ¡Gran trabajo chicos!"
* **Etiquetas ML:** `[feature_request, UI, positivo]`

#### MSG-005
* **Autor Crudo:** Pedro Sánchez
* **Iniciales:** P.S.
* **Mensaje original:** "Me han cobrado dos veces la suscripción este mes. Si no me lo solucionan hoy, cancelo el servicio."
* **Etiquetas ML:** `[facturacion, queja, riesgo_churn, urgente, negativo]`

#### MSG-006
* **Autor Crudo:** Laura Torres
* **Iniciales:** L.T.
* **Mensaje original:** "Gracias al equipo de soporte por ayudarme a migrar mis datos. Excelente atención."
* **Etiquetas ML:** `[agradecimiento, soporte, fidelizacion, positivo]`

#### MSG-007
* **Autor Crudo:** Diego Lopez
* **Iniciales:** D.L.
* **Mensaje original:** "El link para restablecer la contraseña me llega roto."
* **Etiquetas ML:** `[soporte_tecnico, acceso, neutral]`

#### MSG-008
* **Autor Crudo:** Sofía Castro
* **Iniciales:** S.C.
* **Mensaje original:** "La app móvil se queda congelada cada vez que intento subir una imagen. Pésima experiencia."
* **Etiquetas ML:** `[bug, app_movil, rendimiento, queja, negativo]`

#### MSG-009
* **Autor Crudo:** Roberto Fernández
* **Iniciales:** R.F.
* **Mensaje original:** "¡Gana dinero rápido desde casa! Invierte en la nueva criptomoneda y multiplica tus ingresos x10 hoy mismo. Escríbeme al DM."
* **Etiquetas ML:** `[spam, irrelevante, ruido, descartar]`

#### MSG-010
* **Autor Crudo:** Elena Vega
* **Iniciales:** E.V.
* **Mensaje original:** "¿Tienen documentación sobre cómo conectar esto con Zapier u otras herramientas?"
* **Etiquetas ML:** `[integraciones, documentacion, api, neutral]`

---

## Bloque JSON para Ingesta Backend

```json
[
  {
    "id": "MSG-001",
    "tipo_mensaje": "Discord",
    "autor_iniciales": "J.P.",
    "mensaje": "¡Me encanta la nueva actualización! La interfaz está súper rápida y fluida.",
    "sentimiento": "Positivo",
    "tema_principal": "Feedback Producto",
    "etiquetas": ["feedback", "UI/UX", "positivo", "fidelización"]
  },
  {
    "id": "MSG-002",
    "tipo_mensaje": "Slack",
    "autor_iniciales": "M.G.",
    "mensaje": "El sistema no me deja exportar el PDF. Me tira un error 500 y tengo que presentarlo en 10 minutos.",
    "sentimiento": "Negativo",
    "tema_principal": "Bug/Error",
    "etiquetas": ["bug", "error_500", "queja", "urgente", "negativo"]
  },
  {
    "id": "MSG-003",
    "tipo_mensaje": "Telegram",
    "autor_iniciales": "C.R.",
    "mensaje": "¿Alguien sabe cómo se cambia el idioma del dashboard? No encuentro la opción en settings.",
    "sentimiento": "Neutral",
    "tema_principal": "Consulta",
    "etiquetas": ["consulta_general", "onboarding", "neutral"]
  },
  {
    "id": "MSG-004",
    "tipo_mensaje": "Discord",
    "autor_iniciales": "A.M.",
    "mensaje": "Sería increíble si pudieran agregar modo oscuro en la próxima versión. ¡Gran trabajo chicos!",
    "sentimiento": "Positivo",
    "tema_principal": "Feature Request",
    "etiquetas": ["feature_request", "UI", "positivo"]
  },
  {
    "id": "MSG-005",
    "tipo_mensaje": "Slack",
    "autor_iniciales": "P.S.",
    "mensaje": "Me han cobrado dos veces la suscripción este mes. Si no me lo solucionan hoy, cancelo el servicio.",
    "sentimiento": "Negativo",
    "tema_principal": "Facturación",
    "etiquetas": ["facturacion", "queja", "riesgo_churn", "urgente", "negativo"]
  },
  {
    "id": "MSG-006",
    "tipo_mensaje": "Comunidad Web",
    "autor_iniciales": "L.T.",
    "mensaje": "Gracias al equipo de soporte por ayudarme a migrar mis datos. Excelente atención.",
    "sentimiento": "Positivo",
    "tema_principal": "Agradecimiento",
    "etiquetas": ["agradecimiento", "soporte", "fidelizacion", "positivo"]
  },
  {
    "id": "MSG-007",
    "tipo_mensaje": "Telegram",
    "autor_iniciales": "D.L.",
    "mensaje": "El link para restablecer la contraseña me llega roto.",
    "sentimiento": "Neutral",
    "tema_principal": "Soporte Técnico",
    "etiquetas": ["soporte_tecnico", "acceso", "neutral"]
  },
  {
    "id": "MSG-008",
    "tipo_mensaje": "Slack",
    "autor_iniciales": "S.C.",
    "mensaje": "La app móvil se queda congelada cada vez que intento subir una imagen. Pésima experiencia.",
    "sentimiento": "Negativo",
    "tema_principal": "Rendimiento",
    "etiquetas": ["bug", "app_movil", "rendimiento", "queja", "negativo"]
  },
  {
    "id": "MSG-009",
    "tipo_mensaje": "Discord",
    "autor_iniciales": "R.F.",
    "mensaje": "¡Gana dinero rápido desde casa! Invierte en la nueva criptomoneda y multiplica tus ingresos x10 hoy mismo. Escríbeme al DM.",
    "sentimiento": "Neutral",
    "tema_principal": "Spam/Irrelevante",
    "etiquetas": ["spam", "irrelevante", "ruido", "descartar"]
  },
  {
    "id": "MSG-010",
    "tipo_mensaje": "Comunidad Web",
    "autor_iniciales": "E.V.",
    "mensaje": "¿Tienen documentación sobre cómo conectar esto con Zapier u otras herramientas?",
    "sentimiento": "Neutral",
    "tema_principal": "Integraciones",
    "etiquetas": ["integraciones", "documentacion", "api", "neutral"]
  }
]
    "sentimiento": "Neutral",
    "tema_principal": "Integraciones",
    "etiquetas": ["integraciones", "documentacion", "api", "neutral"]
  }
]
