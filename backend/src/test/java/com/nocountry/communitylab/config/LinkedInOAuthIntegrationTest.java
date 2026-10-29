package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(
    properties = {
        "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
        "spring.datasource.url=jdbc:h2:mem:linkedin_oauth_test;DB_CLOSE_DELAY=-1",
        "spring.datasource.driver-class-name=org.h2.Driver",
        "spring.datasource.username=sa",
        "spring.datasource.password=",
        "spring.jpa.hibernate.ddl-auto=create-drop",
        "oci.os.mode=mock",
        "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
        "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
    }
)
@org.springframework.test.context.ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@AutoConfigureMockMvc
class LinkedInOAuthIntegrationTest {

    @Autowired
    MockMvc mvc;

    @Test
    void callbackSinAutorizacionPreviaNoEsAceptado() throws Exception {
        mvc.perform(get("/auth/linkedin/callback")
                .secure(true)
                .with(request -> {
                    request.setServerName("aigoraweave.duckdns.org");
                    request.setServerPort(443);
                    return request;
                })
                .param("code", "codigo-ficticio")
                .param("state", "estado-ficticio"))
            .andExpect(result -> {
                int status = result.getResponse().getStatus();
                assertTrue(status >= 400 && status < 500,
                    "El callback sin sesión OAuth previa debe rechazarse. HTTP: " + status);
            });
    }

    @Test
    void callbackConStateIncorrectoNoEsAceptado() throws Exception {
        var inicio = mvc.perform(get("/oauth2/authorization/linkedin"))
            .andExpect(status().is3xxRedirection())
            .andReturn();

        var session = inicio.getRequest().getSession(false);
        assertNotNull(session, "OAuth debe crear una sesión.");

        var callback = mvc.perform(get("/auth/linkedin/callback")
                .session((org.springframework.mock.web.MockHttpSession) session)
                .secure(true)
                .with(request -> {
                    request.setServerName("aigoraweave.duckdns.org");
                    request.setServerPort(443);
                    return request;
                })
                .param("code", "codigo-ficticio")
                .param("state", "estado-incorrecto"))
            .andReturn();

        int status = callback.getResponse().getStatus();

        assertTrue(status >= 400 && status < 500,
            "Un state incorrecto debe rechazarse. HTTP: " + status);
    }

    @Test
    void publicarSinAutorizacionConOAuthActivoEsRechazado() throws Exception {
        mvc.perform(post("/api/v1/linkedin/publish")
                .contentType("application/json")
                .content("{\\\"text\\\":\\\"Publicación de prueba\\\"}"))
            .andExpect(status().isForbidden());
    }

    @Test
    void inicioOAuthRedirigeALinkedIn() throws Exception {
        mvc.perform(get("/oauth2/authorization/linkedin"))
            .andExpect(status().is3xxRedirection())
            .andExpect(result -> {
                String location = result.getResponse().getHeader("Location");
                assertNotNull(location);
                assertTrue(location.startsWith(
                    "https://www.linkedin.com/oauth/v2/authorization?"));
                assertTrue(location.contains("state="));
                assertTrue(location.contains("w_member_social"));
            });
    }
}
