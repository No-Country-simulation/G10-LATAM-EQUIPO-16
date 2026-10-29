package com.nocountry.communitylab.model.linkedin;

import org.junit.jupiter.api.Test;
import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

class LinkedInPublicationApprovalTest {

    private final Instant now = Instant.parse("2026-10-29T00:00:00Z");

    private LinkedInPublicationApproval approval(
            String sessionId,
            Instant expiresAt,
            boolean confirmed,
            boolean published) {

        return new LinkedInPublicationApproval(
            "approval-123",
            sessionId,
            "Contenido aprobado para LinkedIn",
            com.nocountry.communitylab.service.linkedin.LinkedInContentHasher.sha256("Contenido aprobado para LinkedIn"),
            now.minusSeconds(60),
            expiresAt,
            confirmed,
            published
        );
    }

    @Test
    void contenidoModificadoNoPuedePublicarse() {
        var original = approval("sesion-A", now.plusSeconds(300), true, false);

        var modificado = new LinkedInPublicationApproval(
            original.approvalId(),
            original.sessionId(),
            "Contenido alterado sin autorización",
            original.contentSha256(),
            original.createdAt(),
            original.expiresAt(),
            original.confirmed(),
            original.published()
        );

        assertFalse(modificado.canPublish("sesion-A", now));
    }

    @Test
    void aprobacionValidaPermitePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), true, false);
        assertTrue(item.canPublish("sesion-A", now));
    }

    @Test
    void otraSesionNoPuedePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), true, false);
        assertFalse(item.canPublish("sesion-B", now));
    }

    @Test
    void aprobacionExpiradaNoPuedePublicar() {
        var item = approval("sesion-A", now.minusSeconds(1), true, false);
        assertFalse(item.canPublish("sesion-A", now));
    }

    @Test
    void contenidoSinConfirmarNoPuedePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), false, false);
        assertFalse(item.canPublish("sesion-A", now));
    }

    @Test
    void contenidoYaPublicadoNoPuedeRepetirse() {
        var item = approval("sesion-A", now.plusSeconds(300), true, true);
        assertFalse(item.canPublish("sesion-A", now));
    }
}
