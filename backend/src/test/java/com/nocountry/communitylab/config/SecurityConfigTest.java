package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.security.web.servlet.util.matcher.PathPatternRequestMatcher;

import static org.junit.jupiter.api.Assertions.*;

class SecurityConfigTest {

    @Test
    void verificaCoincidenciaDeRutasPublicas() {
        var health = PathPatternRequestMatcher.withDefaults()
            .matcher(HttpMethod.GET, "/api/v1/health");

        var request = new MockHttpServletRequest(
            "GET", "/api/v1/health"
        );

        assertTrue(health.matches(request));
    }

    @Test
    void verificaQueLinkedInNoEsRutaDeSalud() {
        var health = PathPatternRequestMatcher.withDefaults()
            .matcher(HttpMethod.GET, "/api/v1/health");

        var request = new MockHttpServletRequest(
            "GET", "/api/v1/linkedin/status"
        );

        assertFalse(health.matches(request));
    }
}
