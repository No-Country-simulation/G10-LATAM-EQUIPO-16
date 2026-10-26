# Despliegue de Aigoraweave en Oracle Cloud Infrastructure

## 1. Requisitos
- Oracle Autonomous Database configurada.
- OCI Object Storage con un bucket existente.
- OCI Compute con Java 21.
- Acceso a Oracle Database y permisos IAM para Object Storage.

## 2. Inicialización de Oracle Database
El esquema se encuentra en:
`backend/src/main/resources/db/oracle/V1__initial_schema.sql`

El archivo crea las tablas `interaccion_cruda` y `lote_distribucion`.
Debe ejecutarse manualmente en una base de datos Oracle nueva.
No se utiliza Flyway ni migración automática.
Hibernate utiliza `spring.jpa.hibernate.ddl-auto=validate`.
Por lo tanto, valida las tablas existentes, pero no las crea.

## 3. Variables de entorno

Para utilizar Oracle Database:
- `SPRING_PROFILES_ACTIVE=oracle`
- `ORACLE_DB_URL`: conexión JDBC.
- `ORACLE_DB_USER`: usuario de Oracle.
- `ORACLE_DB_PASSWORD`: contraseña de Oracle.
- `TNS_ADMIN`: directorio privado que contiene la configuración de red
  y el Wallet de Oracle Autonomous Database.

### Configuración del Wallet de Oracle

El Backend utiliza JDBC con el perfil `oracle` para conectarse a
Oracle Autonomous Database.

En el servidor, el directorio indicado por `TNS_ADMIN` debe contener
los archivos necesarios para la conexión, entre ellos:

- `tnsnames.ora`: alias y descriptores de conexión.
- `sqlnet.ora`: configuración de red y ubicación del Wallet.
- `cwallet.sso` y `ewallet.p12`: archivos del Wallet.

El archivo `sqlnet.ora` debe tener configurada la ubicación del Wallet
y la validación del nombre del servidor según el entorno desplegado.

El Wallet debe permanecer fuera del repositorio y contar con permisos
de acceso restringidos. No publicar su contenido, las contraseñas,
la URL JDBC privada ni los valores de las variables de entorno.

### Evidencia de conexión

En la validación del 19/10/2026, el Backend inició con el perfil
`oracle`, estableció una conexión JDBC mediante HikariCP y registró
operaciones de escritura durante el procesamiento de un lote.

Una comprobación posterior mediante un cliente JDBC independiente,
utilizando la configuración del Backend, consultó la tabla
`lote_distribucion` con los filtros `TEST_INTEGRACION_PR26` y
`2026-10`. El resultado fue un lote con estado `PROCESSED`.

Esta consulta confirma la lectura desde Oracle con la misma
configuración de conexión, pero no constituye evidencia de una
lectura realizada por un endpoint del Backend.

Para utilizar OCI Object Storage:
- `OCI_OS_NAMESPACE`: namespace de OCI.
- `OCI_OS_BUCKET`: nombre del bucket.
- `OCI_REGION`: región de OCI.
- `OCI_OS_MODE`: modo de almacenamiento.

No incluir contraseñas, wallets ni credenciales en GitHub.

## 4. Modos de almacenamiento

El modo predeterminado es `mock`, incluso con el perfil Oracle.

- `mock`: simula el almacenamiento y devuelve una ruta `mock://`.
- `real`: utiliza OCI Object Storage mediante Instance Principals y devuelve una ruta `oci://` después de confirmar la carga.

Para producción, establecer explícitamente `OCI_OS_MODE=real`.

## 5. Identidad y permisos IAM

La integración utiliza OCI Instance Principals.
Grupo dinámico: communitylab-vm-dg
Política: communitylab-object-storage-policy

Permisos IAM verificados:
- Allow dynamic-group 'Default'/'communitylab-vm-dg' to read buckets in tenancy where target.bucket.name = 'communitylab-results'
- Allow dynamic-group 'Default'/'communitylab-vm-dg' to manage objects in tenancy where target.bucket.name = 'communitylab-results'

Los permisos están restringidos al bucket communitylab-results.
manage objects también permite eliminar objetos; no equivale a permisos exclusivos de escritura.

## 6. Verificación funcional

Con el backend activo y OCI_OS_MODE=real:

1. Enviar una solicitud POST a /api/v1/community/process.
2. Verificar que la respuesta HTTP sea 200.
3. Confirmar almacenamiento_oci.status = guardado_con_exito.
4. Confirmar que almacenamiento_oci.ruta_objeto comience con oci://.
5. Verificar la existencia del objeto en OCI Object Storage.

Una ruta mock:// indica almacenamiento simulado.

## 7. Consideraciones de despliegue

- El perfil local utiliza PostgreSQL.
- El perfil oracle utiliza Oracle Database.
- Hibernate valida el esquema Oracle existente.
- No subir archivos .env, wallets ni credenciales a GitHub.
- Los nombres de recursos OCI pueden variar entre entornos.
