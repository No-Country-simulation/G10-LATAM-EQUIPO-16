# Contrato de API — Curaduría de Activos

Módulo de curaduría humana de los activos generados por la IA (posts de LinkedIn, newsletters y FAQs).

## Convenciones generales

| Aspecto | Valor |
|---|---|
| Ruta base | `/api/v1/assets` |
| Formato | JSON (`Content-Type: application/json`, UTF-8) |
| Nombres de campos | `snake_case` en español (igual que `/api/v1/community/process`) |
| Identificadores | UUID v4 en formato texto |
| Fechas | ISO-8601 sin zona horaria, p. ej. `2026-10-08T14:32:10.123456` |

### Enumeraciones

**`tipo_activo`**

| Valor | Descripción |
|---|---|
| `LINKEDIN_POST` | Publicación para LinkedIn |
| `NEWSLETTER` | Destacado para el newsletter |
| `FAQ` | Pregunta frecuente con su respuesta |

**`estado`**

| Valor | Descripción |
|---|---|
| `PENDING` | Recién generado, esperando curaduría |
| `APPROVED` | Aprobado por el revisor |
| `REJECTED` | Rechazado por el revisor |
| `EDITED` | Editado por el revisor (requiere nuevo contenido) |

### Formato de errores

Todas las respuestas de error comparten la misma estructura:

```json
{
  "error": "Título corto del error",
  "mensaje": "Detalle legible para el usuario"
}
```

---

## 1. Listar activos pendientes

Devuelve los activos en estado `PENDING`, del más antiguo al más reciente.

`GET /api/v1/assets/pending`

### Request

Sin parámetros, query string ni cuerpo.

### Response `200 OK`

Arreglo de activos. Si no hay pendientes devuelve `[]`.

```json
[
  {
    "id": "3f1c9a52-7b1e-4d57-9a3e-5c1d2f8a9b10",
    "lote_id": "a7d2e4c1-5b3f-4e8a-9c6d-1f2b3a4c5d6e",
    "tipo_activo": "LINKEDIN_POST",
    "contenido": "🚀 Esta semana nuestra comunidad desplegó su primera API en la nube. ¡Felicitaciones a todo el equipo! #Java #Comunidad",
    "estado": "PENDING",
    "creado_en": "2026-10-08T14:32:10.123456",
    "actualizado_en": "2026-10-08T14:32:10.123456"
  },
  {
    "id": "9b8e7d6c-1a2b-4c3d-8e4f-0a1b2c3d4e5f",
    "lote_id": "a7d2e4c1-5b3f-4e8a-9c6d-1f2b3a4c5d6e",
    "tipo_activo": "FAQ",
    "contenido": "¿Cómo configuro el wallet de Oracle Autonomous Database? Descarga el wallet desde la consola de OCI y define la ruta en la variable WALLET_DIR.",
    "estado": "PENDING",
    "creado_en": "2026-10-08T14:32:10.456789",
    "actualizado_en": "2026-10-08T14:32:10.456789"
  }
]
```

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador del activo |
| `lote_id` | UUID | Lote de distribución del que proviene |
| `tipo_activo` | enum | `LINKEDIN_POST`, `NEWSLETTER` o `FAQ` |
| `contenido` | string | Texto del activo generado |
| `estado` | enum | Estado actual (siempre `PENDING` en este endpoint) |
| `creado_en` | fecha-hora | Momento de creación |
| `actualizado_en` | fecha-hora | Última modificación |

### Códigos de estado

| Código | Cuándo |
|---|---|
| `200` | Consulta exitosa (la lista puede estar vacía) |
| `500` | Error interno del servidor |

---

## 2. Curar un activo

Actualiza el estado de un activo (y opcionalmente su contenido) y registra la revisión en la auditoría. Ambos cambios se guardan en una sola transacción.

`PATCH /api/v1/assets/{id}/curate`

### Parámetros de ruta

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identificador del activo a curar |

### Request body

```json
{
  "nuevo_estado": "EDITED",
  "contenido": "🚀 Esta semana nuestra comunidad desplegó su primera API en OCI. ¡Felicitaciones al equipo! #Java #Comunidad",
  "notas_revisor": "Ajusté el tono y acorté el texto para LinkedIn."
}
```

| Campo | Tipo | Obligatorio | Validaciones |
|---|---|---|---|
| `nuevo_estado` | enum | Sí | No nulo. Valores permitidos: `APPROVED`, `REJECTED`, `EDITED`. No se acepta `PENDING` |
| `contenido` | string | Condicional | Obligatorio si `nuevo_estado` es `EDITED`. Si se envía, no puede estar vacío. Máximo 20000 caracteres |
| `notas_revisor` | string | Sí | No vacío ni solo espacios. Máximo 1000 caracteres |

**Reglas de negocio**

- Si se envía `contenido`, reemplaza al contenido actual del activo sin importar el nuevo estado.
- Si no se envía `contenido`, el contenido actual no cambia.
- Se permite volver a curar un activo ya curado (por ejemplo `REJECTED` → `APPROVED`); cada revisión queda registrada.

### Response `200 OK`

Devuelve el activo ya actualizado.

```json
{
  "id": "3f1c9a52-7b1e-4d57-9a3e-5c1d2f8a9b10",
  "lote_id": "a7d2e4c1-5b3f-4e8a-9c6d-1f2b3a4c5d6e",
  "tipo_activo": "LINKEDIN_POST",
  "contenido": "🚀 Esta semana nuestra comunidad desplegó su primera API en OCI. ¡Felicitaciones al equipo! #Java #Comunidad",
  "estado": "EDITED",
  "creado_en": "2026-10-08T14:32:10.123456",
  "actualizado_en": "2026-10-08T15:05:41.987654"
}
```

### Respuestas de error

**`400 Bad Request` — validación del cuerpo** (varios mensajes se separan con `; `)

```json
{
  "error": "Solicitud inválida",
  "mensaje": "El nuevo estado es obligatorio; Las notas del revisor son obligatorias"
}
```

**`400 Bad Request` — JSON mal formado, estado desconocido o `id` que no es un UUID**

```json
{
  "error": "Solicitud inválida",
  "mensaje": "Revise el formato del JSON, los valores permitidos de los estados y el formato UUID del id"
}
```

**`404 Not Found` — el activo no existe**

```json
{
  "error": "Activo no encontrado",
  "mensaje": "No se encontró el activo con id: 3f1c9a52-7b1e-4d57-9a3e-5c1d2f8a9b10"
}
```

**`422 Unprocessable Entity` — regla de negocio violada**

```json
{
  "error": "Curaduría no permitida",
  "mensaje": "El estado EDITED requiere enviar el nuevo contenido"
}
```

Mensajes posibles de `422`:

- `El nuevo estado no puede ser PENDING: la curaduría debe aprobar, rechazar o editar el activo`
- `El contenido, si se envía, no puede estar vacío`
- `El estado EDITED requiere enviar el nuevo contenido`

**`500 Internal Server Error`**

```json
{
  "error": "Error interno del servidor",
  "mensaje": "Detalle técnico del error"
}
```

### Códigos de estado

| Código | Cuándo |
|---|---|
| `200` | Activo curado y auditoría registrada |
| `400` | Cuerpo inválido, enum desconocido o UUID mal formado |
| `404` | No existe un activo con ese `id` |
| `422` | La solicitud viola una regla de negocio |
| `500` | Error interno del servidor |

### Ejemplo con cURL

```bash
curl -X PATCH "http://localhost:8080/api/v1/assets/3f1c9a52-7b1e-4d57-9a3e-5c1d2f8a9b10/curate" \
  -H "Content-Type: application/json" \
  -d '{
        "nuevo_estado": "APPROVED",
        "notas_revisor": "Listo para publicar."
      }'
```
