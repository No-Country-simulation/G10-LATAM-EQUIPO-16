package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oidcLogin;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;

@SpringBootTest(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.datasource.url=jdbc:h2:mem:linkedin_oidc_identity;DB_CLOSE_DELAY=-1",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "oci.os.mode=mock",
    "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
    "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
})
@ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@AutoConfigureMockMvc
class LinkedInOidcIdentityTest {

    @Autowired
    MockMvc mvc;

    @Test
    void usuariosDistintosTienenIdentidadesDistintas() throws Exception {
        var usuarioA = mvc.perform(get("/api/v1/health")
                .with(oidcLogin().idToken(token ->
                    token.claim("sub", "linkedin-user-A"))))
            .andReturn();

        var usuarioB = mvc.perform(get("/api/v1/health")
                .with(oidcLogin().idToken(token ->
                    token.claim("sub", "linkedin-user-B"))))
            .andReturn();

        var contextoA = (org.springframework.security.core.context.SecurityContext)
            usuarioA.getRequest().getSession(false)
                .getAttribute("SPRING_SECURITY_CONTEXT");

        var contextoB = (org.springframework.security.core.context.SecurityContext)
            usuarioB.getRequest().getSession(false)
                .getAttribute("SPRING_SECURITY_CONTEXT");

        assertNotNull(contextoA);
        assertNotNull(contextoB);

        var identidadA = contextoA.getAuthentication();
        var identidadB = contextoB.getAuthentication();

        assertNotNull(identidadA);
        assertNotNull(identidadB);

        assertNotEquals(
            identidadA.getName(),
            identidadB.getName(),
            "Dos cuentas de LinkedIn no deben compartir identidad."
        );

        assertEquals("linkedin-user-A", identidadA.getName());
        assertEquals("linkedin-user-B", identidadB.getName());
    }

    @Test
    void solicitudAnonimaNoTieneIdentidadOidc() throws Exception {
        var respuesta = mvc.perform(get("/api/v1/health"))
            .andReturn();

        var principal = respuesta.getRequest().getUserPrincipal();

        assertNull(
            principal,
            "Una solicitud anónima no debe tener identidad OIDC."
        );
    }
}
