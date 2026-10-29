package com.nocountry.communitylab.service.linkedin;

import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.authentication.TestingAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class LinkedInAuthenticatedIdentityTest {

    private final LinkedInAuthenticatedIdentity identity =
        new LinkedInAuthenticatedIdentity();

    private OAuth2AuthenticationToken authentication(
            String registrationId, String subject) {

        OidcUser user = mock(OidcUser.class);
        when(user.getSubject()).thenReturn(subject);

        return new OAuth2AuthenticationToken(
            user,
            List.of(new SimpleGrantedAuthority("OIDC_USER")),
            registrationId
        );
    }

    @Test
    void aceptaIdentidadOidcDeLinkedIn() {
        var auth = authentication("linkedin", "linkedin-user-A");

        assertEquals(
            "linkedin-user-A",
            identity.requireSubject(auth)
        );
    }

    @Test
    void rechazaUsuarioAnonimo() {
        var auth = new AnonymousAuthenticationToken(
            "test-key",
            "anonymousUser",
            List.of(new SimpleGrantedAuthority("ROLE_ANONYMOUS"))
        );

        assertThrows(
            SecurityException.class,
            () -> identity.requireSubject(auth)
        );
    }

    @Test
    void rechazaOtroProveedorOAuth2() {
        var auth = authentication("otro-proveedor", "usuario-A");

        assertThrows(
            SecurityException.class,
            () -> identity.requireSubject(auth)
        );
    }

    @Test
    void rechazaIdentidadOidcVacia() {
        var auth = authentication("linkedin", " ");

        assertThrows(
            SecurityException.class,
            () -> identity.requireSubject(auth)
        );
    }

    @Test
    void rechazaAutenticacionSinOidc() {
        var auth = new TestingAuthenticationToken(
            "usuario",
            "credencial",
            "ROLE_USER"
        );

        assertThrows(
            SecurityException.class,
            () -> identity.requireSubject(auth)
        );
    }
}
