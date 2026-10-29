package com.nocountry.communitylab.service.linkedin;

import org.junit.jupiter.api.Test;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;

import java.time.Clock;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class LinkedInIdentityApprovalIntegrationTest {

    private final LinkedInAuthenticatedIdentity identity =
        new LinkedInAuthenticatedIdentity();

    private final LinkedInApprovalService approvals =
        new LinkedInApprovalService(Clock.systemUTC());

    private OAuth2AuthenticationToken linkedInUser(String subject) {
        OidcUser user = mock(OidcUser.class);
        when(user.getSubject()).thenReturn(subject);

        return new OAuth2AuthenticationToken(
            user,
            List.of(new SimpleGrantedAuthority("OIDC_USER")),
            "linkedin"
        );
    }

    @Test
    void soloLaIdentidadAutenticadaPuedeGestionarSuAprobacion() {
        var authA = linkedInUser("linkedin-A");
        var authB = linkedInUser("linkedin-B");

        String subjectA = identity.requireSubject(authA);
        String subjectB = identity.requireSubject(authB);

        var approval = approvals.create(
            "sesion-compartida",
            subjectA,
            "Publicación protegida de Aigoraweave"
        );

        assertNull(approvals.findForSession(
            approval.approvalId(), "sesion-compartida", subjectB
        ));

        assertNull(approvals.confirm(
            approval.approvalId(), "sesion-compartida", subjectB
        ));

        assertNotNull(approvals.confirm(
            approval.approvalId(), "sesion-compartida", subjectA
        ));

        assertNull(approvals.reserveForPublishing(
            approval.approvalId(), "sesion-compartida", subjectB
        ));

        assertNotNull(approvals.reserveForPublishing(
            approval.approvalId(), "sesion-compartida", subjectA
        ));
    }
}
