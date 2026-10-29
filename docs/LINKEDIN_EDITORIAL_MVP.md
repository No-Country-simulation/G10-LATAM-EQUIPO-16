# Aigoraweave — MVP de aprobación editorial con LinkedIn

## 1. Alcance

Este módulo incorpora un flujo experimental de autenticación mediante LinkedIn OpenID Connect y revisión editorial de borradores.

La implementación está desarrollada en una rama de funcionalidad y no representa todavía una integración completa con el flujo principal de CommunityLab.

La aprobación editorial no publica contenido automáticamente en LinkedIn.

## 2. Funcionalidades implementadas

- Configuración de autenticación LinkedIn OAuth2/OIDC.
- Identificación de usuarios autenticados.
- Importación de borradores para revisión.
- Validación de contenido y protección CSRF.
- Aislamiento de operaciones por sesión e identidad.
- Revisión y confirmación explícita de aprobaciones.
- Pruebas automatizadas del flujo de autenticación y aprobación.

Los permisos OAuth solicitados son `openid` y `profile`. No se solicita `w_member_social`.

## 3. Componentes pendientes de integración

El módulo `frontend/linkedin_approval.py` todavía no está conectado a `frontend/app.py`.

`LinkedInPublishRequestDto`, `reserveForPublishing` y `finishPublishing` están preparados para una futura etapa de publicación, pero no forman parte del flujo operativo actual.

La integración completa entre Streamlit y el backend de aprobación sigue pendiente.

## 4. Persistencia y limitaciones del MVP

Los borradores y las aprobaciones del flujo experimental se mantienen en memoria.

Consecuencias:

- Los datos se pierden cuando se reinicia el proceso.
- No existe persistencia durable de aprobaciones.
- Los registros expirados no cuentan todavía con una limpieza automática periódica.
- No debe considerarse este almacenamiento adecuado para producción.

Antes de habilitar el flujo para usuarios reales se deberá incorporar persistencia y una estrategia de expiración y limpieza.

## 5. Seguridad y perfiles

El perfil `linkedin-oauth` habilita la configuración de autenticación con LinkedIn.

El perfil `linkedin-https` configura las protecciones de cookies correspondientes al entorno HTTPS, incluyendo `Secure` y `SameSite`.

Para un futuro despliegue HTTPS del flujo autenticado deben habilitarse conjuntamente ambos perfiles y verificarse la configuración del proxy y la URL de callback.

No se deben incluir credenciales OAuth en el repositorio.

## 6. Entorno de desarrollo y H2

La dependencia H2 está configurada con `scope=test` para que no se empaquete dentro del JAR de producción.

Las pruebas automatizadas pueden utilizar H2.

El perfil `linkedin-dev` mantiene una configuración de base de datos H2 en memoria. Su ejecución independiente fuera del classpath de pruebas requiere un mecanismo específico de desarrollo; no debe asumirse que funcionará directamente con el JAR de producción.

## 7. Comportamiento de curaduría

El cambio en `_guardar_edicion` contempla que editar un activo previamente aprobado o rechazado invalide su decisión editorial anterior.

Esto evita conservar una aprobación o rechazo asociado a una versión del contenido que ya fue modificada.

Este comportamiento debe revisarse y validarse con el equipo antes de integrarse al flujo principal de curaduría.

## 8. Validaciones realizadas

Después de las correcciones del PR:

- Backend: 115 pruebas contabilizadas, 0 fallidas, 0 errores y 1 omitida.
- Compilación y empaquetado Maven: correctos.
- H2: ausente del JAR generado.
- Permiso de publicación `w_member_social`: eliminado.

## 9. Pendientes antes de producción

- Probar OAuth/OIDC con credenciales reales de LinkedIn.
- Validar el callback y la configuración HTTPS.
- Integrar el frontend con el backend.
- Incorporar persistencia durable y limpieza de registros expirados.
- Validar el comportamiento de curaduría con el equipo.
- Realizar una revisión de seguridad y pruebas de integración del despliegue.

Este MVP no debe confundirse con un sistema de publicación automática.
