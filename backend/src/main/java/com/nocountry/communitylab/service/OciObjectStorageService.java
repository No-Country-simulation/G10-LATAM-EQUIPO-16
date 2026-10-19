package com.nocountry.communitylab.service;

import com.oracle.bmc.Region;
import com.oracle.bmc.auth.InstancePrincipalsAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorage;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import com.oracle.bmc.objectstorage.responses.PutObjectResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

@Service
public class OciObjectStorageService {

    @Value("${oci.os.mode:mock}")
    private String mode;

    @Value("${oci.os.namespace:}")
    private String namespace;

    @Value("${oci.os.bucket:communitylab-local}")
    private String bucket;

    @Value("${oci.os.region:}")
    private String region;

    public String getBucket() {
        return bucket;
    }

    public boolean isMockMode() {
        return "mock".equalsIgnoreCase(mode);
    }

    // ==========================================================
    // NUEVO (DEC-11): ruta del paquete con convención del roadmap
    // ==========================================================

    /**
     * Construye la ruta del paquete según DEC-11:
     * {@code activos/<periodo_sanitizado>/paquete-distribucion-<lote_id>.json}.
     *
     * <p>El {@code periodo_sanitizado} reemplaza cualquier carácter que no sea
     * {@code [A-Za-z0-9_-]} por {@code _}. Si el periodo es nulo o vacío,
     * se usa {@code sin_periodo}.
     */
    public String buildBatchRoute(String referencePeriod, UUID batchId) {
        String sanitized = sanitizePeriodo(referencePeriod);
        return "activos/" + sanitized + "/paquete-distribucion-" + batchId + ".json";
    }

    private String sanitizePeriodo(String periodo) {
        if (periodo == null || periodo.isBlank()) {
            return "sin_periodo";
        }
        // limitamos a 100 caracteres para no exceder varchar(255) en ruta_oci.
        // Ruta final: activos/<sanitized>/paquete-distribucion-<uuid>.json
        String sanitized = periodo.replaceAll("[^A-Za-z0-9_-]", "_");
        return sanitized.length() > 100 ? sanitized.substring(0, 100) : sanitized;
    }

    // ==========================================================
    // CAMBIO (DEC-11): uploadJson ahora recibe la ruta explícita
    // ==========================================================

    /**
     * Sube un JSON al bucket OCI en la ruta indicada.
     *
     * @param json       Contenido JSON a subir.
     * @param objectName Ruta relativa dentro del bucket
     *                   (ej. {@code activos/2026-semana-41/paquete-distribucion-xxx.json}).
     * @return URL {@code oci://bucket/ruta} en modo real, {@code mock://bucket/ruta} en modo mock.
     */
    public String uploadJson(String json, String objectName) throws Exception {
        // CAMBIO (DEC-11): antes se hardcodeaba resultados/batch_<uuid>.json.
        // Ahora la ruta viene explícita desde el service.
        if ("mock".equalsIgnoreCase(mode)) {
            return "mock://" + bucket + "/" + objectName;
        }

        if (!"real".equalsIgnoreCase(mode)) {
            throw new IllegalStateException(
                    "Modo de almacenamiento no válido: " + mode
            );
        }

        if (namespace.isBlank() || region.isBlank()) {
            throw new IllegalStateException(
                    "Falta configurar OCI_OS_NAMESPACE o OCI_REGION"
            );
        }

        byte[] content = json.getBytes(StandardCharsets.UTF_8);

        var provider = InstancePrincipalsAuthenticationDetailsProvider
                .builder()
                .build();

        Region ociRegion;
        try {
            ociRegion = Region.fromRegionId(region);
        } catch (IllegalArgumentException ex) {
            throw new IllegalStateException(
                    "Región OCI inválida: " + region, ex
            );
        }

        try (ObjectStorage client = ObjectStorageClient.builder()
                .region(ociRegion)
                .build(provider)) {

            PutObjectRequest request = PutObjectRequest.builder()
                    .namespaceName(namespace)
                    .bucketName(bucket)
                    .objectName(objectName)
                    .contentLength((long) content.length)
                    .putObjectBody(new ByteArrayInputStream(content))
                    .contentType("application/json")
                    .build();

            PutObjectResponse response = client.putObject(request);

            if (response.getETag() == null) {
                throw new IllegalStateException(
                        "OCI no confirmó el almacenamiento del objeto"
                );
            }

            return "oci://" + bucket + "/" + objectName;
        }
    }
}
