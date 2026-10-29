package com.nocountry.communitylab.service.linkedin;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.IdTokenClaimNames;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.DefaultOidcUser;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;

import java.time.Instant;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class LinkedInDraftOwnerTest {

    private final LinkedInDraftOwner owner =
        new LinkedInDraftOwner(new LinkedInAuthenticatedIdentity());

    private OAuth2AuthenticationToken linkedinUser(String subject) {
        Instant now = Instant.parse("2026-10-29T03:00:00Z");

        OidcIdToken token = new OidcIdToken(
            "test-token",
            now,
            now.plusSeconds(3600),
            Map.of(IdTokenClaimNames.SUB, subject)
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("OIDC_USER"),
            token
        );

        return new OAuth2AuthenticationToken(
            user,
            user.getAuthorities(),
            "linkedin"
        );
    }

    @Test
    void authenticatedUserWithSessionGetsOwner() {
        var request = new MockHttpServletRequest();
        request.setSession(new MockHttpSession());

        String result = owner.requireOwner(
            linkedinUser("user-A"),
            request
        );

        assertNotNull(result);
        assertFalse(result.isBlank());
    }

    @Test
    void rejectsMissingSession() {
        var request = new MockHttpServletRequest();

        assertThrows(SecurityException.class,
            () -> owner.requireOwner(
                linkedinUser("user-A"),
                request
            ));
    }

    @Test
    void rejectsAnonymousAuthentication() {
        var request = new MockHttpServletRequest();
        request.setSession(new MockHttpSession());

        var anonymous = new AnonymousAuthenticationToken(
            "test-key",
            "anonymousUser",
            AuthorityUtils.createAuthorityList("ROLE_ANONYMOUS")
        );

        assertThrows(SecurityException.class,
            () -> owner.requireOwner(anonymous, request));
    }

    @Test
    void differentLinkedInUsersGetDifferentOwners() {
        var request = new MockHttpServletRequest();
        request.setSession(new MockHttpSession());

        assertNotEquals(
            owner.requireOwner(linkedinUser("user-A"), request),
            owner.requireOwner(linkedinUser("user-B"), request)
        );
    }

    @Test
    void differentSessionsGetDifferentOwners() {
        var requestA = new MockHttpServletRequest();
        requestA.setSession(new MockHttpSession());

        var requestB = new MockHttpServletRequest();
        requestB.setSession(new MockHttpSession());

        assertNotEquals(
            owner.requireOwner(linkedinUser("user-A"), requestA),
            owner.requireOwner(linkedinUser("user-A"), requestB)
        );
    }
}
