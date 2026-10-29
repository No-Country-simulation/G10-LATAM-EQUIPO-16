package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.client.web.HttpSessionOAuth2AuthorizedClientRepository;
import org.springframework.security.oauth2.core.OAuth2AccessToken;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

class LinkedInSessionIsolationTest {

    @Test
    void dosSesionesNoCompartenAutorizaciones() {
        var repository = new HttpSessionOAuth2AuthorizedClientRepository();

        var registration = ClientRegistration.withRegistrationId("linkedin")
            .clientId("test-client")
            .clientSecret("test-secret")
            .authorizationGrantType(
                org.springframework.security.oauth2.core.AuthorizationGrantType.AUTHORIZATION_CODE
            )
            .redirectUri("https://aigoraweave.duckdns.org/auth/linkedin/callback")
            .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
            .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
            .build();

        var token = new OAuth2AccessToken(
            OAuth2AccessToken.TokenType.BEARER,
            "token-ficticio-usuario-A",
            Instant.now(),
            Instant.now().plusSeconds(3600)
        );

        var authorizedClient = new OAuth2AuthorizedClient(
            registration, "anonymousUser", token
        );

        var requestA = new MockHttpServletRequest();
        var responseA = new MockHttpServletResponse();

        var requestB = new MockHttpServletRequest();

        repository.saveAuthorizedClient(
            authorizedClient, null, requestA, responseA
        );

        assertNotNull(
            repository.loadAuthorizedClient("linkedin", null, requestA),
            "La sesión A debe recuperar su autorización."
        );

        assertNull(
            repository.loadAuthorizedClient("linkedin", null, requestB),
            "La sesión B no debe acceder a la autorización de A."
        );
    }
}
