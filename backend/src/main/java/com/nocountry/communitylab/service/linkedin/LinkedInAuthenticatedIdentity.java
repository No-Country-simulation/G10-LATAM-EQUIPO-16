package com.nocountry.communitylab.service.linkedin;

import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.stereotype.Component;

@Component
public class LinkedInAuthenticatedIdentity {

    public String requireSubject(Authentication authentication) {
        if (!(authentication instanceof OAuth2AuthenticationToken token)) {
            throw new SecurityException("Autenticación OAuth2 requerida.");
        }

        if (!authentication.isAuthenticated()
                || !"linkedin".equals(token.getAuthorizedClientRegistrationId())) {
            throw new SecurityException("Autenticación LinkedIn requerida.");
        }

        if (!(token.getPrincipal() instanceof OidcUser oidcUser)) {
            throw new SecurityException("Identidad OpenID Connect requerida.");
        }

        String subject = oidcUser.getSubject();

        if (subject == null || subject.isBlank()) {
            throw new SecurityException("Identidad LinkedIn inválida.");
        }

        return subject;
    }
}
