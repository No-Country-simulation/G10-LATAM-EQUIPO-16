package com.nocountry.communitylab.service.linkedin;

import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.junit.jupiter.api.Assertions.*;

class LinkedInDraftTransferServiceTest {

    private static final Instant NOW =
        Instant.parse("2026-10-29T03:00:00Z");

    private LinkedInDraftTransferService service() {
        return new LinkedInDraftTransferService(
            Clock.fixed(NOW, ZoneOffset.UTC)
        );
    }

    @Test
    void createsDraftWithOriginalContent() {
        var draft = service().create("owner-A", "Publicación de Aigoraweave");

        assertNotNull(draft.id());
        assertEquals("Publicación de Aigoraweave", draft.content());
        assertEquals(NOW.plusSeconds(300), draft.expiresAt());
    }

    @Test
    void draftCanOnlyBeConsumedOnce() {
        var drafts = service();
        var draft = drafts.create("owner-A", "Contenido privado");

        assertNotNull(drafts.consume(draft.id(), "owner-A"));
        assertNull(drafts.consume(draft.id(), "owner-A"));
    }

    @Test
    void rejectsEmptyOrOversizedContent() {
        var drafts = service();

        assertThrows(IllegalArgumentException.class,
            () -> drafts.create("owner-A", "   "));

        assertThrows(IllegalArgumentException.class,
            () -> drafts.create("owner-A", "x".repeat(3001)));
    }

    @Test
    void expiredDraftCannotBeConsumed() {
        var currentTime = new java.util.concurrent.atomic.AtomicReference<>(NOW);

        Clock adjustableClock = new Clock() {
            @Override
            public ZoneOffset getZone() {
                return ZoneOffset.UTC;
            }

            @Override
            public Clock withZone(java.time.ZoneId zone) {
                return this;
            }

            @Override
            public Instant instant() {
                return currentTime.get();
            }
        };

        var drafts = new LinkedInDraftTransferService(adjustableClock);
        var draft = drafts.create("owner-A", "Contenido temporal");

        currentTime.set(NOW.plusSeconds(360));

        assertNull(drafts.consume(draft.id(), "owner-A"));
        assertNull(drafts.consume(draft.id(), "owner-A"));
    }

    @Test
    void anotherOwnerCannotConsumeDraft() {
        var drafts = service();

        var draft = drafts.create(
            "streamlit-session-A",
            "Contenido privado de Aigoraweave"
        );

        assertNull(drafts.consume(
            draft.id(),
            "streamlit-session-B"
        ));

        assertNotNull(drafts.consume(
            draft.id(),
            "streamlit-session-A"
        ));

        assertNull(drafts.consume(
            draft.id(),
            "streamlit-session-A"
        ));
    }

    @Test
    void sameLinkedInUserWithDifferentSessionCannotConsumeDraft() {
        var drafts = service();

        String ownerA = "linkedin-user-A:session-1";
        String ownerB = "linkedin-user-A:session-2";

        var draft = drafts.create(
            ownerA,
            "Publicación privada de Aigoraweave"
        );

        assertNull(drafts.consume(draft.id(), ownerB));

        assertNotNull(drafts.consume(draft.id(), ownerA));

        assertNull(drafts.consume(draft.id(), ownerA));
    }

    @Test
    void unknownDraftCannotBeConsumed() {
        assertNull(service().consume("identificador-inexistente", "owner-A"));
    }
}
