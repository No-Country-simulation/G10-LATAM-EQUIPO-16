package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
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
class LinkedInConfirmationEndpointTest {

    @Autowired
    private MockMvc mockMvc;

    private static final String BASE = "/api/v1/linkedin/approvals";

    private final ClientRegistration linkedin =
        ClientRegistration.withRegistrationId("linkedin")
            .clientId("test-client")
            .clientSecret("test-secret")
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .redirectUri("{baseUrl}/auth/linkedin/callback")
            .scope("openid", "profile", "w_member_social")
            .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
            .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
            .jwkSetUri("https://www.linkedin.com/oauth/openid/jwks")
            .issuerUri("https://www.linkedin.com")
            .build();

    private String createApproval(MockHttpSession session) throws Exception {
        String response = mockMvc.perform(post(BASE)
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"content":"Publicación de prueba de Aigoraweave"}
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.status").value("PENDING"))
            .andReturn()
            .getResponse()
            .getContentAsString();

        return new tools.jackson.databind.ObjectMapper()
            .readTree(response)
            .get("approvalId")
            .asText();
    }

    @Test
    void mismaSesionPuedeConfirmarSoloUnaVez() throws Exception {
        MockHttpSession session = new MockHttpSession();
        String approvalId = createApproval(session);

        mockMvc.perform(post(BASE + "/" + approvalId + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("CONFIRMED"));

        mockMvc.perform(post(BASE + "/" + approvalId + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf()))
            .andExpect(status().isNotFound());
    }

    @Test
    void otraSesionNoPuedeConfirmar() throws Exception {
        MockHttpSession original = new MockHttpSession();
        String approvalId = createApproval(original);

        mockMvc.perform(post(BASE + "/" + approvalId + "/confirm")
                .session(new MockHttpSession())
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-A")))
                .with(csrf()))
            .andExpect(status().isNotFound());
    }

    @Test
    void otraIdentidadNoPuedeConfirmar() throws Exception {
        MockHttpSession session = new MockHttpSession();
        String approvalId = createApproval(session);

        mockMvc.perform(post(BASE + "/" + approvalId + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-B")))
                .with(csrf()))
            .andExpect(status().isNotFound());
    }

    @Test
    void confirmacionSinCsrfEsRechazada() throws Exception {
        MockHttpSession session = new MockHttpSession();
        String approvalId = createApproval(session);

        mockMvc.perform(post(BASE + "/" + approvalId + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(token -> token.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isForbidden());
    }
}
