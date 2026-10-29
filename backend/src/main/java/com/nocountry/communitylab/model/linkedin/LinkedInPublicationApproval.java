package com.nocountry.communitylab.model.linkedin;

import java.time.Instant;
import com.nocountry.communitylab.service.linkedin.LinkedInContentHasher;

public record LinkedInPublicationApproval(
    String approvalId,
    String sessionId,
    String linkedinSubject,
    String content,
    String contentSha256,
    Instant createdAt,
    Instant expiresAt,
    boolean confirmed,
    boolean published,
    LinkedInPublicationStatus status
) {

    public LinkedInPublicationApproval(
            String approvalId,
            String sessionId,
            String content,
            String contentSha256,
            Instant createdAt,
            Instant expiresAt,
            boolean confirmed,
            boolean published,
            LinkedInPublicationStatus status) {

        this(
            approvalId,
            sessionId,
            null,
            content,
            contentSha256,
            createdAt,
            expiresAt,
            confirmed,
            published,
            status
        );
    }

    public LinkedInPublicationApproval(
            String approvalId,
            String sessionId,
            String content,
            String contentSha256,
            Instant createdAt,
            Instant expiresAt,
            boolean confirmed,
            boolean published) {

        this(
            approvalId,
            sessionId,
            null,
            content,
            contentSha256,
            createdAt,
            expiresAt,
            confirmed,
            published,
            published
                ? LinkedInPublicationStatus.PUBLISHED
                : confirmed
                    ? LinkedInPublicationStatus.CONFIRMED
                    : LinkedInPublicationStatus.PENDING
        );
    }

    public boolean isExpired(Instant now) {
        return !now.isBefore(expiresAt);
    }

    public boolean canPublish(
            String currentSessionId,
            String currentLinkedinSubject,
            Instant now) {
        return sessionId != null
            && sessionId.equals(currentSessionId)
            && linkedinSubject != null
            && !linkedinSubject.isBlank()
            && linkedinSubject.equals(currentLinkedinSubject)
            && content != null
            && !content.isBlank()
            && LinkedInContentHasher.matches(content, contentSha256)
            && confirmed
            && !published
            && status == LinkedInPublicationStatus.CONFIRMED
            && !isExpired(now);
    }
}
