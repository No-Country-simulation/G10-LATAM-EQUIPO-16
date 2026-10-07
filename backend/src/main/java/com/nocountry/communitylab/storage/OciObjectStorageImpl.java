package com.nocountry.communitylab.storage;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class OciObjectStorageImpl implements OciObjectStorage {
    // Simula la subida de archivos imprimiendo un mensaje en consola
    @Override
    public void putObject(String bucket, String objectRoute, byte[] content) {
        log.info("OCI Mock: {} bytes saved in the ‘{}’ bucket under the path '{}'", 
                content.length, bucket, objectRoute);
    }
}