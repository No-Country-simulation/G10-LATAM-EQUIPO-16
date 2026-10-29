package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.model.linkedin.LinkedInPublicationApproval;
import com.nocountry.communitylab.service.linkedin.LinkedInApprovalService;
import com.nocountry.communitylab.service.linkedin.LinkedInAuthenticatedIdentity;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.Instant;

@RestController
@RequestMapping("/api/v1/linkedin/approvals")
public class LinkedInApprovalController {

    private final LinkedInApprovalService approvals;
    private final LinkedInAuthenticatedIdentity identity;

    public LinkedInApprovalController(
            LinkedInApprovalService approvals,
            LinkedInAuthenticatedIdentity identity) {
        this.approvals = approvals;
        this.identity = identity;
    }

    public record CreateApprovalRequest(
        @NotBlank
        @Size(max = 3000)
        String content
    ) {}

    public record ApprovalResponse(
        String approvalId,
        String content,
        String contentSha256,
        Instant expiresAt,
        String status
    ) {}

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApprovalResponse create(
            @Valid @RequestBody CreateApprovalRequest body,
            Authentication authentication,
            HttpServletRequest request) {

        String subject = identity.requireSubject(authentication);

        String sessionId = request.getSession(true).getId();

        LinkedInPublicationApproval approval = approvals.create(
            sessionId,
            subject,
            body.content()
        );

        return new ApprovalResponse(
            approval.approvalId(),
            approval.content(),
            approval.contentSha256(),
            approval.expiresAt(),
            approval.status().name()
        );
    }


    @PostMapping("/{approvalId}/confirm")
    public org.springframework.http.ResponseEntity<?> confirmApproval(
            @PathVariable String approvalId,
            Authentication authentication,
            HttpServletRequest request) {

        String subject = identity.requireSubject(authentication);

        var session = request.getSession(false);

        if (session == null) {
            throw new org.springframework.web.server.ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Aprobación no disponible."
            );
        }

        LinkedInPublicationApproval approval = approvals.confirm(
            approvalId,
            session.getId(),
            subject
        );

        if (approval == null) {
            throw new org.springframework.web.server.ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Aprobación no disponible."
            );
        }

        ApprovalResponse response = new ApprovalResponse(
            approval.approvalId(),
            approval.content(),
            approval.contentSha256(),
            approval.expiresAt(),
            approval.status().name()
        );

        String contentType = request.getContentType();

        if (contentType != null &&
                contentType.toLowerCase(java.util.Locale.ROOT)
                    .startsWith("application/x-www-form-urlencoded")) {
            String location = "/api/v1/linkedin/approvals/"
                + approval.approvalId() + "/confirmed";

            return org.springframework.http.ResponseEntity
                .status(HttpStatus.SEE_OTHER)
                .header("Location", location)
                .build();
        }

        return org.springframework.http.ResponseEntity.ok(response);
    }


    @ExceptionHandler(
        org.springframework.web.server.ResponseStatusException.class
    )
    public org.springframework.http.ResponseEntity<java.util.Map<String, String>>
            handleApprovalStatusException(
                org.springframework.web.server.ResponseStatusException exception) {

        return org.springframework.http.ResponseEntity
            .status(exception.getStatusCode())
            .body(java.util.Map.of(
                "error", "approval_unavailable",
                "message", "Aprobación no disponible."
            ));
    }

    @ExceptionHandler(SecurityException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public java.util.Map<String, String> handleInvalidIdentity(
            SecurityException exception) {
        return java.util.Map.of(
            "error", "forbidden",
            "message", "Identidad LinkedIn no autorizada."
        );
    }
}
