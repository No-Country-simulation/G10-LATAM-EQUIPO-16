package com.nocountry.communitylab;

import com.nocountry.communitylab.service.OciObjectStorageService;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;

class OciObjectStorageServiceTest {

    @Test
    void mockModeDoesNotRequireOciCredentials() throws Exception {
        OciObjectStorageService service = new OciObjectStorageService();

        ReflectionTestUtils.setField(service, "mode", "mock");
        ReflectionTestUtils.setField(service, "bucket", "communitylab-local");
        ReflectionTestUtils.setField(service, "namespace", "");
        ReflectionTestUtils.setField(service, "region", "");

        String route = service.uploadJson("{\"mensaje\":\"prueba\"}");

        assertTrue(route.startsWith(
                "mock://communitylab-local/resultados/batch_"
        ));
        assertTrue(route.endsWith(".json"));
        assertTrue(service.isMockMode());
        assertEquals("communitylab-local", service.getBucket());
    }
}
