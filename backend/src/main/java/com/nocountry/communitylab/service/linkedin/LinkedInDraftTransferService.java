package com.nocountry.communitylab.service.linkedin;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

public class LinkedInDraftTransferService {

    private static final Duration TTL = Duration.ofMinutes(5);
    private static final int MAX_CONTENT_LENGTH = 3000;

    private final ConcurrentMap<String, Draft> drafts =
        new ConcurrentHashMap<>();

    private final Clock clock;

    public LinkedInDraftTransferService(Clock clock) {
        this.clock = clock;
    }

    public record Draft(
        String id,
        String ownerId,
        String content,
        Instant expiresAt
    ) {}

    public Draft create(String ownerId, String content) {
        if (ownerId == null || ownerId.isBlank()) {
            throw new IllegalArgumentException("Propietario inválido.");
        }

        if (content == null || content.isBlank()
                || content.length() > MAX_CONTENT_LENGTH) {
            throw new IllegalArgumentException("Contenido inválido.");
        }

        Instant now = clock.instant();

        Draft draft = new Draft(
            UUID.randomUUID().toString(),
            ownerId,
            content,
            now.plus(TTL)
        );

        drafts.put(draft.id(), draft);
        return draft;
    }

    public Draft consume(String id, String ownerId) {
        if (id == null || id.isBlank()
                || ownerId == null || ownerId.isBlank()) {
            return null;
        }

        final Draft[] consumed = {null};

        drafts.computeIfPresent(id, (key, draft) -> {
            if (!clock.instant().isBefore(draft.expiresAt())) {
                return null;
            }

            if (!ownerId.equals(draft.ownerId())) {
                return draft;
            }

            consumed[0] = draft;
            return null;
        });

        return consumed[0];
    }
}
