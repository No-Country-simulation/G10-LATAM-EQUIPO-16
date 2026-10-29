package com.nocountry.communitylab.service.linkedin;

import org.junit.jupiter.api.Test;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.junit.jupiter.api.Assertions.*;

class LinkedInApprovalServiceTest {

    private final Instant now =
        Instant.parse("2026-10-29T00:00:00Z");

    private final Clock clock =
        Clock.fixed(now, ZoneOffset.UTC);

    @Test
    void creaAprobacionPendienteConHashCorrecto() {
        var service = new LinkedInApprovalService(clock);

        var approval = service.create("sesion-A", "linkedin-A", "Contenido para LinkedIn");

        assertNotNull(approval.approvalId());
        assertEquals("sesion-A", approval.sessionId());
        assertFalse(approval.confirmed());
        assertFalse(approval.published());
        assertTrue(LinkedInContentHasher.matches(
            approval.content(), approval.contentSha256()
        ));
        assertEquals(now.plusSeconds(600), approval.expiresAt());
    }

    @Test
    void recuperaAprobacionDesdeSesionCorrecta() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto aprobado");

        assertNotNull(service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A"));
    }

    @Test
    void otraSesionNoPuedeRecuperarAprobacion() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto privado");

        assertNull(service.findForSession(approval.approvalId(), "sesion-B", "linkedin-A"));
    }

    @Test
    void aprobacionExpiradaNoPuedeRecuperarse() {
        var adjustableClock = new AdjustableClock(now);
        var service = new LinkedInApprovalService(adjustableClock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto temporal");

        assertNotNull(service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A"));

        adjustableClock.advanceSeconds(601);

        assertNull(service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A"));
    }

    @Test
    void sesionCorrectaPuedeConfirmar() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto original");

        var confirmed = service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        );

        assertNotNull(confirmed);
        assertTrue(confirmed.confirmed());
        assertFalse(confirmed.published());
    }

    @Test
    void otraSesionNoPuedeConfirmar() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto privado");

        assertNull(service.confirm(
            approval.approvalId(), "sesion-B", "linkedin-A"
        ));

        assertFalse(service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A").confirmed());
    }

    @Test
    void noPuedeConfirmarseDosVeces() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto único");

        assertNotNull(service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));

        assertNull(service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));
    }

    @Test
    void aprobacionExpiradaNoPuedeConfirmarse() {
        var adjustableClock = new AdjustableClock(now);
        var service = new LinkedInApprovalService(adjustableClock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto temporal");

        adjustableClock.advanceSeconds(601);

        assertNull(service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));
    }

    @Test
    void confirmacionConservaContenidoYHash() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto aprobado");

        var confirmed = service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        );

        assertNotNull(confirmed);
        assertEquals(approval.content(), confirmed.content());
        assertEquals(
            approval.contentSha256(),
            confirmed.contentSha256()
        );
        assertFalse(confirmed.canPublish("sesion-A", null, now));
        assertFalse(confirmed.canPublish("sesion-B", null, now));
    }

    @Test
    void cambioDeCuentaLinkedInNoAutorizaPublicacion() {
        var service = new LinkedInApprovalService(clock);

        var approval = service.create(
            "sesion-A",
            "linkedin-A",
            "Publicación protegida por identidad"
        );

        // Misma sesión HTTP, pero otra cuenta de LinkedIn.
        assertNull(service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-B"
        ));

        // La cuenta original sí puede confirmar.
        assertNotNull(service.confirm(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));

        // La segunda cuenta no puede reservar.
        assertNull(service.reserveForPublishing(
            approval.approvalId(), "sesion-A", "linkedin-B"
        ));

        // La cuenta original puede reservar una sola vez.
        assertNotNull(service.reserveForPublishing(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));

        // La segunda cuenta no puede finalizar.
        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-B",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));

        // La cuenta original sí puede finalizar.
        assertNotNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));
    }

    @Test
    void otraCuentaLinkedInNoPuedeConsultarAprobacion() {
        var service = new LinkedInApprovalService(clock);

        var approval = service.create(
            "sesion-A",
            "linkedin-A",
            "Contenido privado de LinkedIn A"
        );

        // La cuenta original puede consultar su aprobación.
        assertNotNull(service.findForSession(
            approval.approvalId(), "sesion-A", "linkedin-A"
        ));

        // Otra cuenta no puede consultar, aunque comparta sesión.
        assertNull(service.findForSession(
            approval.approvalId(), "sesion-A", "linkedin-B"
        ));

        // Otra sesión tampoco puede consultar.
        assertNull(service.findForSession(
            approval.approvalId(), "sesion-B", "linkedin-A"
        ));

        // La firma antigua sin identidad debe permanecer bloqueada.
        assertNull(service.findForSession(
            approval.approvalId(), "sesion-A"
        ));
    }

    @Test
    void soloUnaSolicitudPuedeReservarPublicacion() throws Exception {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Publicación única de Aigoraweave");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));

        var ready = new java.util.concurrent.CountDownLatch(2);
        var start = new java.util.concurrent.CountDownLatch(1);

        var executor = java.util.concurrent.Executors.newFixedThreadPool(2);

        try {
            java.util.concurrent.Callable<Boolean> attempt = () -> {
                ready.countDown();

                if (!start.await(5, java.util.concurrent.TimeUnit.SECONDS)) {
                    throw new IllegalStateException("Tiempo de espera agotado");
                }

                return service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A") != null;
            };

            var first = executor.submit(attempt);
            var second = executor.submit(attempt);

            assertTrue(ready.await(
                5, java.util.concurrent.TimeUnit.SECONDS
            ));

            start.countDown();

            int successfulReservations =
                (first.get(5, java.util.concurrent.TimeUnit.SECONDS) ? 1 : 0)
                + (second.get(5, java.util.concurrent.TimeUnit.SECONDS) ? 1 : 0);

            assertEquals(1, successfulReservations);

            var stored = service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A");

            assertNotNull(stored);
            assertEquals(
                com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHING,
                stored.status()
            );

        } finally {
            start.countDown();
            executor.shutdownNow();
        }
    }

    @Test
    void otraSesionNoPuedeReservarPublicacion() {
        var service = new LinkedInApprovalService(clock);

        var approval = service.create("sesion-A", "linkedin-A", "Contenido aprobado por el usuario A");

        assertNotNull(
            service.confirm(approval.approvalId(), "sesion-A", "linkedin-A")
        );

        assertNull(
            service.reserveForPublishing(approval.approvalId(), "sesion-B", "linkedin-A"),
            "La sesión B no debe reservar publicaciones de A."
        );

        assertNotNull(
            service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"),
            "La sesión A debe conservar su derecho a publicar."
        );
    }

    @Test
    void reservaNoPuedeRepetirse() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto único");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));

        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));

        assertNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));
    }


    @Test
    void publicacionExitosaNoPuedeReservarseNuevamente() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Publicación exitosa");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));

        var finished = service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        );

        assertNotNull(finished);
        assertTrue(finished.published());
        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED,
            finished.status()
        );
        assertNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));
    }

    @Test
    void resultadoDesconocidoNoPuedeReintentarseAutomaticamente() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Publicación incierta");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));

        var finished = service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.UNKNOWN
        );

        assertNotNull(finished);
        assertFalse(finished.published());
        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.UNKNOWN,
            finished.status()
        );
        assertNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));
    }

    @Test
    void otraSesionNoPuedeFinalizarPublicacion() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto protegido");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-B",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));

        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHING,
            service.findForSession(approval.approvalId(), "sesion-A", "linkedin-A").status()
        );
    }

    @Test
    void noPuedeFinalizarSinReserva() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto pendiente");

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));
    }

    @Test
    void publicacionFinalizadaNoPuedeFinalizarseDosVeces() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "linkedin-A", "Texto definitivo");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A", "linkedin-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A", "linkedin-A"));

        assertNotNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            "linkedin-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.UNKNOWN
        ));
    }

    private static final class AdjustableClock extends Clock {
        private Instant current;

        AdjustableClock(Instant initial) {
            this.current = initial;
        }

        void advanceSeconds(long seconds) {
            current = current.plusSeconds(seconds);
        }

        @Override
        public ZoneOffset getZone() {
            return ZoneOffset.UTC;
        }

        @Override
        public Clock withZone(java.time.ZoneId zone) {
            return Clock.fixed(current, zone);
        }

        @Override
        public Instant instant() {
            return current;
        }
    }

    @Test
    void rechazaSesionOContenidoVacio() {
        var service = new LinkedInApprovalService(clock);

        assertThrows(IllegalArgumentException.class,
            () -> service.create("", "Texto"));

        assertThrows(IllegalArgumentException.class,
            () -> service.create("sesion-A", "linkedin-A", "   "));
    }
}
