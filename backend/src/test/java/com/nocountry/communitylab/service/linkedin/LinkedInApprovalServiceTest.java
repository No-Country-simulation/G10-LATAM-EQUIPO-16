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

        var approval = service.create(
            "sesion-A", "Contenido para LinkedIn"
        );

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
        var approval = service.create("sesion-A", "Texto aprobado");

        assertNotNull(service.findForSession(
            approval.approvalId(), "sesion-A"
        ));
    }

    @Test
    void otraSesionNoPuedeRecuperarAprobacion() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto privado");

        assertNull(service.findForSession(
            approval.approvalId(), "sesion-B"
        ));
    }

    @Test
    void aprobacionExpiradaNoPuedeRecuperarse() {
        var adjustableClock = new AdjustableClock(now);
        var service = new LinkedInApprovalService(adjustableClock);
        var approval = service.create("sesion-A", "Texto temporal");

        assertNotNull(service.findForSession(
            approval.approvalId(), "sesion-A"
        ));

        adjustableClock.advanceSeconds(601);

        assertNull(service.findForSession(
            approval.approvalId(), "sesion-A"
        ));
    }

    @Test
    void sesionCorrectaPuedeConfirmar() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto original");

        var confirmed = service.confirm(
            approval.approvalId(), "sesion-A"
        );

        assertNotNull(confirmed);
        assertTrue(confirmed.confirmed());
        assertFalse(confirmed.published());
    }

    @Test
    void otraSesionNoPuedeConfirmar() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto privado");

        assertNull(service.confirm(
            approval.approvalId(), "sesion-B"
        ));

        assertFalse(service.findForSession(
            approval.approvalId(), "sesion-A"
        ).confirmed());
    }

    @Test
    void noPuedeConfirmarseDosVeces() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto único");

        assertNotNull(service.confirm(
            approval.approvalId(), "sesion-A"
        ));

        assertNull(service.confirm(
            approval.approvalId(), "sesion-A"
        ));
    }

    @Test
    void aprobacionExpiradaNoPuedeConfirmarse() {
        var adjustableClock = new AdjustableClock(now);
        var service = new LinkedInApprovalService(adjustableClock);
        var approval = service.create("sesion-A", "Texto temporal");

        adjustableClock.advanceSeconds(601);

        assertNull(service.confirm(
            approval.approvalId(), "sesion-A"
        ));
    }

    @Test
    void confirmacionConservaContenidoYHash() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto aprobado");

        var confirmed = service.confirm(
            approval.approvalId(), "sesion-A"
        );

        assertNotNull(confirmed);
        assertEquals(approval.content(), confirmed.content());
        assertEquals(
            approval.contentSha256(),
            confirmed.contentSha256()
        );
        assertTrue(confirmed.canPublish("sesion-A", now));
        assertFalse(confirmed.canPublish("sesion-B", now));
    }

    @Test
    void soloUnaSolicitudPuedeReservarPublicacion() throws Exception {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create(
            "sesion-A", "Publicación única de Aigoraweave"
        );

        assertNotNull(service.confirm(
            approval.approvalId(), "sesion-A"
        ));

        var ready = new java.util.concurrent.CountDownLatch(2);
        var start = new java.util.concurrent.CountDownLatch(1);

        var executor = java.util.concurrent.Executors.newFixedThreadPool(2);

        try {
            java.util.concurrent.Callable<Boolean> attempt = () -> {
                ready.countDown();

                if (!start.await(5, java.util.concurrent.TimeUnit.SECONDS)) {
                    throw new IllegalStateException("Tiempo de espera agotado");
                }

                return service.reserveForPublishing(
                    approval.approvalId(), "sesion-A"
                ) != null;
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

            var stored = service.findForSession(
                approval.approvalId(), "sesion-A"
            );

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
    void reservaNoPuedeRepetirse() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto único");

        assertNotNull(service.confirm(
            approval.approvalId(), "sesion-A"
        ));

        assertNotNull(service.reserveForPublishing(
            approval.approvalId(), "sesion-A"
        ));

        assertNull(service.reserveForPublishing(
            approval.approvalId(), "sesion-A"
        ));
    }


    @Test
    void publicacionExitosaNoPuedeReservarseNuevamente() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Publicación exitosa");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));

        var finished = service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        );

        assertNotNull(finished);
        assertTrue(finished.published());
        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED,
            finished.status()
        );
        assertNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));
    }

    @Test
    void resultadoDesconocidoNoPuedeReintentarseAutomaticamente() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Publicación incierta");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));

        var finished = service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.UNKNOWN
        );

        assertNotNull(finished);
        assertFalse(finished.published());
        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.UNKNOWN,
            finished.status()
        );
        assertNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));
    }

    @Test
    void otraSesionNoPuedeFinalizarPublicacion() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto protegido");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-B",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));

        assertEquals(
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHING,
            service.findForSession(approval.approvalId(), "sesion-A").status()
        );
    }

    @Test
    void noPuedeFinalizarSinReserva() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto pendiente");

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));
    }

    @Test
    void publicacionFinalizadaNoPuedeFinalizarseDosVeces() {
        var service = new LinkedInApprovalService(clock);
        var approval = service.create("sesion-A", "Texto definitivo");

        assertNotNull(service.confirm(approval.approvalId(), "sesion-A"));
        assertNotNull(service.reserveForPublishing(approval.approvalId(), "sesion-A"));

        assertNotNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
            com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus.PUBLISHED
        ));

        assertNull(service.finishPublishing(
            approval.approvalId(),
            "sesion-A",
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
            () -> service.create("sesion-A", "   "));
    }
}
