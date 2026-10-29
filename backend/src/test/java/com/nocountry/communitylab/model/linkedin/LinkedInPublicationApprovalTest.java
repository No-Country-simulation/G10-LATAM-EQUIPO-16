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

        assertFalse(modificado.canPublish("sesion-A", null, now));
    }

    @Test
    void aprobacionValidaPermitePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), true, false);
        assertFalse(item.canPublish("sesion-A", null, now));
    }

    @Test
    void otraSesionNoPuedePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), true, false);
        assertFalse(item.canPublish("sesion-B", null, now));
    }

    @Test
    void aprobacionExpiradaNoPuedePublicar() {
        var item = approval("sesion-A", now.minusSeconds(1), true, false);
        assertFalse(item.canPublish("sesion-A", null, now));
    }

    @Test
    void contenidoSinConfirmarNoPuedePublicar() {
        var item = approval("sesion-A", now.plusSeconds(300), false, false);
        assertFalse(item.canPublish("sesion-A", null, now));
    }

    @Test
    void contenidoYaPublicadoNoPuedeRepetirse() {
        var item = approval("sesion-A", now.plusSeconds(300), true, true);
        assertFalse(item.canPublish("sesion-A", null, now));
    }

    @Test
    void cuentaLinkedInDistintaNoPuedePublicar() {
        var now = java.time.Instant.parse("2026-10-29T01:00:00Z");
        var content = "Contenido aprobado para LinkedIn A";

        var approval = new LinkedInPublicationApproval(
            "approval-1",
            "sesion-compartida",
            "linkedin-user-A",
            content,
            com.nocountry.communitylab.service.linkedin.LinkedInContentHasher.sha256(content),
            now,
            now.plusSeconds(600),
            true,
            false,
            LinkedInPublicationStatus.CONFIRMED
        );

        assertTrue(
            approval.canPublish(
                "sesion-compartida",
                "linkedin-user-A",
                now
            )
        );

        assertFalse(
            approval.canPublish(
                "sesion-compartida",
                "linkedin-user-B",
                now
            ),
            "La cuenta B no debe publicar contenido aprobado para A."
        );

        assertFalse(
            approval.canPublish(
                "otra-sesion",
                "linkedin-user-A",
                now
            )
        );
    }

}
