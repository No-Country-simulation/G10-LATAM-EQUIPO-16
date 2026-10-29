package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.service.linkedin.LinkedInAuthenticatedIdentity;
import org.springframework.security.core.Authentication;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/linkedin")
public class LinkedInIdentityController {

    private final LinkedInAuthenticatedIdentity identity;

    public LinkedInIdentityController(
            LinkedInAuthenticatedIdentity identity) {
        this.identity = identity;
    }

    @ExceptionHandler(SecurityException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public Map<String, String> handleInvalidIdentity(
            SecurityException exception) {

        return Map.of(
            "error", "forbidden",
            "message", "Identidad LinkedIn no autorizada."
        );
    }

    @GetMapping("/me")
    public Map<String, String> currentIdentity(
            Authentication authentication) {

        String subject = identity.requireSubject(authentication);

        return Map.of(
            "provider", "linkedin",
            "subject", subject
        );
    }
}
