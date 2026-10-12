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

    public String uploadJson(String json) throws Exception {
        String objectName = "resultados/batch_" + UUID.randomUUID() + ".json";
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

        try (ObjectStorage client = ObjectStorageClient.builder()
                .region(Region.fromRegionId(region))
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
