package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@TestPropertySource(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
    "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
})
class LinkedInApprovalEndpointTest {

    @Autowired
    private MockMvc mockMvc;

    private static final String ENDPOINT = "/api/v1/linkedin/approvals";
    private static final String BODY =
        "{\"content\":\"Publicación de prueba de Aigoraweave\"}";

    @Test
    void linkedinConCsrfPuedeCrearAprobacion() throws Exception {
        mockMvc.perform(post(ENDPOINT)
                .with(oidcLogin()
                    .clientRegistration(
                        org.springframework.security.oauth2.client.registration.ClientRegistration
                            .withRegistrationId("linkedin")
                            .clientId("test-client")
                            .clientSecret("test-secret")
                            .authorizationGrantType(
                                org.springframework.security.oauth2.core.AuthorizationGrantType.AUTHORIZATION_CODE
                            )
                            .redirectUri("{baseUrl}/auth/linkedin/callback")
                            .scope("openid", "profile", "w_member_social")
                            .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
                            .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
                            .jwkSetUri("https://www.linkedin.com/oauth/openid/jwks")
                            .issuerUri("https://www.linkedin.com")
                            .build()
                    )
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(BODY))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.approvalId").isNotEmpty())
            .andExpect(jsonPath("$.status").value("PENDING"))
            .andExpect(jsonPath("$.content").value(
                "Publicación de prueba de Aigoraweave"
            ))
            .andExpect(jsonPath("$.sessionId").doesNotExist())
            .andExpect(jsonPath("$.linkedinSubject").doesNotExist());
    }


    @Test
    void contenidoVacioEsRechazado() throws Exception {
        assertContenidoInvalido("");
    }

    @Test
    void contenidoConSoloEspaciosEsRechazado() throws Exception {
        assertContenidoInvalido("   ");
    }

    @Test
    void contenidoDemasiadoLargoEsRechazado() throws Exception {
        assertContenidoInvalido("A".repeat(3001));
    }

    private void assertContenidoInvalido(String content) throws Exception {
        var linkedinRegistration =
            org.springframework.security.oauth2.client.registration.ClientRegistration
                .withRegistrationId("linkedin")
                .clientId("test-client")
                .clientSecret("test-secret")
                .authorizationGrantType(
                    org.springframework.security.oauth2.core.AuthorizationGrantType.AUTHORIZATION_CODE
                )
                .redirectUri("{baseUrl}/auth/linkedin/callback")
                .scope("openid", "profile", "w_member_social")
                .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
                .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
                .jwkSetUri("https://www.linkedin.com/oauth/openid/jwks")
                .issuerUri("https://www.linkedin.com")
                .build();

        String json = """
            {"content":"%s"}
            """.formatted(content);

        mockMvc.perform(post(ENDPOINT)
                .with(oidcLogin()
                    .clientRegistration(linkedinRegistration)
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isBadRequest());
    }

    @Test
    void linkedinSinCsrfEsRechazado() throws Exception {
        mockMvc.perform(post(ENDPOINT)
                .with(oidcLogin())
                .contentType(MediaType.APPLICATION_JSON)
                .content(BODY))
            .andExpect(status().isForbidden());
    }

    @Test
    void otroProveedorOAuth2EsRechazado() throws Exception {
        var otherProvider =
            org.springframework.security.oauth2.client.registration.ClientRegistration
                .withRegistrationId("otro-proveedor")
                .clientId("test-client")
                .clientSecret("test-secret")
                .authorizationGrantType(
                    org.springframework.security.oauth2.core.AuthorizationGrantType.AUTHORIZATION_CODE
                )
                .redirectUri("{baseUrl}/auth/otro/callback")
                .authorizationUri("https://example.com/authorize")
                .tokenUri("https://example.com/token")
                .userInfoUri("https://example.com/userinfo")
                .userNameAttributeName("sub")
                .build();

        mockMvc.perform(post(ENDPOINT)
                .with(oidcLogin().clientRegistration(otherProvider))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(BODY))
            .andExpect(status().isForbidden())
            .andExpect(jsonPath("$.error").value("forbidden"));
    }

    @Test
    void usuarioAnonimoNoPuedeCrearAprobacion() throws Exception {
        mockMvc.perform(post(ENDPOINT)
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(BODY))
            .andExpect(status().is3xxRedirection());
    }
}
