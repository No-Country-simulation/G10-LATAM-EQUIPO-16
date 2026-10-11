package com.nocountry.communitylab.service;

import com.oracle.bmc.Region;
import com.oracle.bmc.auth.InstancePrincipalsAuthenticationDetailsProvider;
import com.oracle.bmc.objectstorage.ObjectStorage;
import com.oracle.bmc.objectstorage.ObjectStorageClient;
import com.oracle.bmc.objectstorage.requests.PutObjectRequest;
import com.oracle.bmc.objectstorage.responses.PutObjectResponse;
import org.springframework.stereotype.Service;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

@Service
public class OciObjectStorageService {

    private static final String NAMESPACE = "axfj94golgwj";
    private static final String BUCKET = "communitylab-results";

    public String uploadJson(String json) throws Exception {
        String objectName = "resultados/batch_" + UUID.randomUUID() + ".json";
        byte[] content = json.getBytes(StandardCharsets.UTF_8);

        var provider = InstancePrincipalsAuthenticationDetailsProvider
                .builder()
                .build();

        try (ObjectStorage client = ObjectStorageClient.builder()
                .region(Region.SA_SANTIAGO_1)
                .build(provider)) {

            PutObjectRequest request = PutObjectRequest.builder()
                    .namespaceName(NAMESPACE)
                    .bucketName(BUCKET)
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

            return "oci://" + BUCKET + "/" + objectName;
        }
    }
}
