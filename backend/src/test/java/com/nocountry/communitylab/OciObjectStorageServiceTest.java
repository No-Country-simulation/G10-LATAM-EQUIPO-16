package com.nocountry.communitylab;

import com.nocountry.communitylab.service.OciObjectStorageService;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class OciObjectStorageServiceTest {

    @Test
    void mockModeDoesNotRequireOciCredentials() throws Exception {
        OciObjectStorageService service = new OciObjectStorageService();

        ReflectionTestUtils.setField(service, "mode", "mock");
        ReflectionTestUtils.setField(service, "bucket", "communitylab-local");
        ReflectionTestUtils.setField(service, "namespace", "");
        ReflectionTestUtils.setField(service, "region", "");

        // (DEC-11): la ruta viene explícita
        String objectName = "activos/2026-semana-41/paquete-distribucion-test.json";
        String route = service.uploadJson("{\"mensaje\":\"prueba\"}", objectName);

        // (DEC-11): la ruta mock ahora usa el objectName explícito
        assertEquals("mock://communitylab-local/" + objectName, route);
        assertTrue(service.isMockMode());
        assertEquals("communitylab-local", service.getBucket());
    }

    // (DEC-11): test de la construccion de la ruta del paquete
    @Test
    void buildBatchRoute_shouldFollowDec11Convention() {
        OciObjectStorageService service = new OciObjectStorageService();
        UUID loteId = UUID.fromString("11111111-1111-1111-1111-111111111111");

        // Periodo normal
        assertEquals(
                "activos/2026-semana-41/paquete-distribucion-" + loteId + ".json",
                service.buildBatchRoute("2026-semana-41", loteId)
        );

        // Periodo ISO con caracteres inválidos → se sanitiza
        assertEquals(
                "activos/2026-10-18T10_30_00/paquete-distribucion-" + loteId + ".json",
                service.buildBatchRoute("2026-10-18T10:30:00", loteId)
        );

        // Periodo nulo → sin_periodo
        assertEquals(
                "activos/sin_periodo/paquete-distribucion-" + loteId + ".json",
                service.buildBatchRoute(null, loteId)
        );

        // Periodo vacío → sin_periodo
        assertEquals(
                "activos/sin_periodo/paquete-distribucion-" + loteId + ".json",
                service.buildBatchRoute("   ", loteId)
        );
    }
}