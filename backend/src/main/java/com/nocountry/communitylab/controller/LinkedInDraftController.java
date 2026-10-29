package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.service.linkedin.LinkedInDraftOwner;
import com.nocountry.communitylab.service.linkedin.LinkedInDraftTransferService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;

@RestController
@RequestMapping("/api/v1/linkedin/drafts")
public class LinkedInDraftController {

    private final LinkedInDraftTransferService drafts;
    private final LinkedInDraftOwner owner;

    public LinkedInDraftController(
            LinkedInDraftTransferService drafts,
            LinkedInDraftOwner owner) {
        this.drafts = drafts;
        this.owner = owner;
    }

    public record CreateDraftRequest(
        @NotBlank
        @Size(max = 3000)
        String content
    ) {}

    public record DraftResponse(
        String draftId,
        String content,
        Instant expiresAt
    ) {}

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public DraftResponse create(
            @Valid @RequestBody CreateDraftRequest body,
            Authentication authentication,
            HttpServletRequest request) {

        String ownerId = owner.requireOwner(authentication, request);

        var draft = drafts.create(ownerId, body.content());

        return new DraftResponse(
            draft.id(),
            draft.content(),
            draft.expiresAt()
        );
    }

    @PostMapping("/{draftId}/consume")
    public DraftResponse consume(
            @PathVariable String draftId,
            Authentication authentication,
            HttpServletRequest request) {

        String ownerId = owner.requireOwner(authentication, request);

        var draft = drafts.consume(draftId, ownerId);

        if (draft == null) {
            throw new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Borrador no disponible."
            );
        }

        return new DraftResponse(
            draft.id(),
            draft.content(),
            draft.expiresAt()
        );
    }

    @ExceptionHandler(ResponseStatusException.class)
    public org.springframework.http.ResponseEntity<java.util.Map<String, String>>
            handleDraftStatusException(ResponseStatusException exception) {

        return org.springframework.http.ResponseEntity
            .status(exception.getStatusCode())
            .body(java.util.Map.of(
                "error", "draft_unavailable",
                "message", "Borrador no disponible."
            ));
    }

    @ExceptionHandler(SecurityException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public java.util.Map<String, String> invalidIdentity() {
        return java.util.Map.of(
            "error", "forbidden",
            "message", "Identidad LinkedIn no autorizada."
        );
    }
}
