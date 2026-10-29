package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oauth2Login;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.oidcLogin;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@TestPropertySource(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
    "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
})
class LinkedInIdentityEndpointTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void identidadLinkedInAutenticadaDevuelveSubject() throws Exception {
        mockMvc.perform(get("/api/v1/linkedin/me")
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
                            .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
                            .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
                            .jwkSetUri("https://www.linkedin.com/oauth/openid/jwks")
                            .issuerUri("https://www.linkedin.com/oauth")
                            .userInfoUri("https://api.linkedin.com/v2/userinfo")
                            .userNameAttributeName("sub")
                            .build()
                    )
                    .idToken(token -> token.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.provider").value("linkedin"))
            .andExpect(jsonPath("$.subject").value("linkedin-user-A"))
            .andExpect(jsonPath("$.access_token").doesNotExist());
    }

    @Test
    void otroProveedorOAuth2NoPuedeConsultarIdentidad() throws Exception {
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

        mockMvc.perform(get("/api/v1/linkedin/me")
                .with(oidcLogin()
                    .clientRegistration(otherProvider)
                    .idToken(token -> token.claim("sub", "otro-usuario"))))
            .andExpect(status().isForbidden())
            .andExpect(jsonPath("$.error").value("forbidden"))
            .andExpect(jsonPath("$.message").value(
                "Identidad LinkedIn no autorizada."
            ))
            .andExpect(jsonPath("$.subject").doesNotExist())
            .andExpect(jsonPath("$.access_token").doesNotExist());
    }

    @Test
    void identidadLinkedInConSubjectVacioEsRechazada() throws Exception {
        var oidcUser = org.mockito.Mockito.mock(
            org.springframework.security.oauth2.core.oidc.user.OidcUser.class
        );

        org.mockito.Mockito.when(oidcUser.getSubject())
            .thenReturn(" ");

        org.mockito.Mockito.when(oidcUser.getName())
            .thenReturn("principal-de-prueba");

        var authentication =
            new org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken(
                oidcUser,
                java.util.List.of(
                    new org.springframework.security.core.authority.SimpleGrantedAuthority(
                        "OIDC_USER"
                    )
                ),
                "linkedin"
            );

        mockMvc.perform(get("/api/v1/linkedin/me")
                .with(
                    org.springframework.security.test.web.servlet.request
                        .SecurityMockMvcRequestPostProcessors
                        .authentication(authentication)
                ))
            .andExpect(status().isForbidden())
            .andExpect(jsonPath("$.error").value("forbidden"))
            .andExpect(jsonPath("$.subject").doesNotExist())
            .andExpect(jsonPath("$.access_token").doesNotExist());
    }

    @Test
    void usuarioAnonimoNoPuedeConsultarIdentidad() throws Exception {
        mockMvc.perform(get("/api/v1/linkedin/me"))
            .andExpect(status().is3xxRedirection());
    }
}
