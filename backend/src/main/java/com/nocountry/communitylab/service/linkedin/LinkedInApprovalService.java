package com.nocountry.communitylab.service.linkedin;

import com.nocountry.communitylab.model.linkedin.LinkedInPublicationApproval;
import com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class LinkedInApprovalService {

    private static final Duration APPROVAL_TTL = Duration.ofMinutes(10);

    private final Map<String, LinkedInPublicationApproval> approvals =
        new ConcurrentHashMap<>();

    private final Clock clock;

    public LinkedInApprovalService(Clock clock) {
        this.clock = clock;
    }

    public LinkedInPublicationApproval create(
            String sessionId,
            String content) {

        return create(sessionId, null, content);
    }

    public LinkedInPublicationApproval create(
            String sessionId,
            String linkedinSubject,
            String content) {

        if (sessionId == null || sessionId.isBlank()) {
            throw new IllegalArgumentException(
                "Se requiere una sesión válida"
            );
        }

        if (content == null || content.isBlank()) {
            throw new IllegalArgumentException(
                "El contenido no puede estar vacío"
            );
        }

        Instant now = clock.instant();

        LinkedInPublicationApproval approval =
            new LinkedInPublicationApproval(
                UUID.randomUUID().toString(),
                sessionId,
                linkedinSubject,
                content,
                LinkedInContentHasher.sha256(content),
                now,
                now.plus(APPROVAL_TTL),
                false,
                false,
                LinkedInPublicationStatus.PENDING
            );

        approvals.put(approval.approvalId(), approval);

        return approval;
    }

    public LinkedInPublicationApproval confirm(
            String approvalId,
            String sessionId) {

        return confirm(approvalId, sessionId, null);
    }

    public LinkedInPublicationApproval confirm(
            String approvalId,
            String sessionId,
            String linkedinSubject) {

        if (approvalId == null || sessionId == null
                || sessionId.isBlank()) {
            return null;
        }

        final LinkedInPublicationApproval[] confirmed = {null};

        approvals.computeIfPresent(approvalId, (id, current) -> {
            if (!sessionId.equals(current.sessionId())
                    || linkedinSubject == null
                    || linkedinSubject.isBlank()
                    || !linkedinSubject.equals(current.linkedinSubject())
                    || current.isExpired(clock.instant())
                    || current.confirmed()
                    || current.published()
                    || current.content() == null
                    || current.content().isBlank()
                    || !LinkedInContentHasher.matches(
                        current.content(), current.contentSha256())) {
                return current;
            }

            LinkedInPublicationApproval updated =
                new LinkedInPublicationApproval(
                    current.approvalId(),
                    current.sessionId(),
                    current.linkedinSubject(),
                    current.content(),
                    current.contentSha256(),
                    current.createdAt(),
                    current.expiresAt(),
                    true,
                    false,
                    LinkedInPublicationStatus.CONFIRMED
                );

            confirmed[0] = updated;
            return updated;
        });

        return confirmed[0];
    }

    public LinkedInPublicationApproval reserveForPublishing(
            String approvalId,
            String sessionId) {

        return reserveForPublishing(approvalId, sessionId, null);
    }

    public LinkedInPublicationApproval reserveForPublishing(
            String approvalId,
            String sessionId,
            String linkedinSubject) {

        if (approvalId == null || sessionId == null
                || sessionId.isBlank()) {
            return null;
        }

        final LinkedInPublicationApproval[] reserved = {null};

        approvals.computeIfPresent(approvalId, (id, current) -> {
            if (!current.canPublish(
                    sessionId,
                    linkedinSubject,
                    clock.instant()
                )) {
                return current;
            }

            LinkedInPublicationApproval updated =
                new LinkedInPublicationApproval(
                    current.approvalId(),
                    current.sessionId(),
                    current.linkedinSubject(),
                    current.content(),
                    current.contentSha256(),
                    current.createdAt(),
                    current.expiresAt(),
                    true,
                    false,
                    LinkedInPublicationStatus.PUBLISHING
                );

            reserved[0] = updated;
            return updated;
        });

        return reserved[0];
    }

    public LinkedInPublicationApproval finishPublishing(
            String approvalId,
            String sessionId,
            LinkedInPublicationStatus resultStatus) {

        return finishPublishing(
            approvalId,
            sessionId,
            null,
            resultStatus
        );
    }

    public LinkedInPublicationApproval finishPublishing(
            String approvalId,
            String sessionId,
            String linkedinSubject,
            LinkedInPublicationStatus resultStatus) {

        if (approvalId == null || sessionId == null
                || sessionId.isBlank()) {
            return null;
        }

        if (resultStatus != LinkedInPublicationStatus.PUBLISHED
                && resultStatus != LinkedInPublicationStatus.UNKNOWN) {
            throw new IllegalArgumentException(
                "Resultado de publicación no permitido"
            );
        }

        final LinkedInPublicationApproval[] finished = {null};

        approvals.computeIfPresent(approvalId, (id, current) -> {
            if (!sessionId.equals(current.sessionId())
                    || linkedinSubject == null
                    || linkedinSubject.isBlank()
                    || !linkedinSubject.equals(current.linkedinSubject())
                    || current.status() != LinkedInPublicationStatus.PUBLISHING) {
                return current;
            }

            LinkedInPublicationApproval updated =
                new LinkedInPublicationApproval(
                    current.approvalId(),
                    current.sessionId(),
                    current.linkedinSubject(),
                    current.content(),
                    current.contentSha256(),
                    current.createdAt(),
                    current.expiresAt(),
                    true,
                    resultStatus == LinkedInPublicationStatus.PUBLISHED,
                    resultStatus
                );

            finished[0] = updated;
            return updated;
        });

        return finished[0];
    }

    public LinkedInPublicationApproval findForSession(
            String approvalId,
            String sessionId) {

        return findForSession(approvalId, sessionId, null);
    }

    public LinkedInPublicationApproval findForSession(
            String approvalId,
            String sessionId,
            String linkedinSubject) {

        if (approvalId == null
                || sessionId == null
                || sessionId.isBlank()
                || linkedinSubject == null
                || linkedinSubject.isBlank()) {
            return null;
        }

        LinkedInPublicationApproval approval = approvals.get(approvalId);

        if (approval == null
                || !sessionId.equals(approval.sessionId())
                || !linkedinSubject.equals(approval.linkedinSubject())
                || approval.isExpired(clock.instant())) {
            return null;
        }

        return approval;
    }
}
