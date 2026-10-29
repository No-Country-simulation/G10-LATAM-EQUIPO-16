package com.nocountry.communitylab.service.linkedin;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Component;

@Component
public class LinkedInDraftOwner {

    private final LinkedInAuthenticatedIdentity identity;

    public LinkedInDraftOwner(LinkedInAuthenticatedIdentity identity) {
        this.identity = identity;
    }

    public String requireOwner(
            Authentication authentication,
            HttpServletRequest request) {

        String subject = identity.requireSubject(authentication);

        HttpSession session = request.getSession(false);

        if (session == null) {
            throw new SecurityException(
                "Se requiere una sesión HTTP existente."
            );
        }

        String sessionId = session.getId();

        if (sessionId == null || sessionId.isBlank()) {
            throw new SecurityException("Sesión HTTP inválida.");
        }

        return subject.length() + ":" + subject
            + ":" + sessionId.length() + ":" + sessionId;
    }
}
