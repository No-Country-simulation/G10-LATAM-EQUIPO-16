package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.model.linkedin.LinkedInPublicationApproval;
import com.nocountry.communitylab.model.linkedin.LinkedInPublicationStatus;
import com.nocountry.communitylab.service.linkedin.LinkedInApprovalService;
import com.nocountry.communitylab.service.linkedin.LinkedInAuthenticatedIdentity;
import com.nocountry.communitylab.service.linkedin.LinkedInContentHasher;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class LinkedInReviewController {

    private final LinkedInApprovalService approvals;
    private final LinkedInAuthenticatedIdentity identity;

    public LinkedInReviewController(
            LinkedInApprovalService approvals,
            LinkedInAuthenticatedIdentity identity) {
        this.approvals = approvals;
        this.identity = identity;
    }

    @GetMapping(
        value = "/api/v1/linkedin/approvals/{approvalId}/review",
        produces = MediaType.TEXT_HTML_VALUE
    )
    public ResponseEntity<String> review(
            @PathVariable String approvalId,
            Authentication authentication,
            HttpServletRequest request) {

        String subject;
        try {
            subject = identity.requireSubject(authentication);
        } catch (SecurityException exception) {
            return ResponseEntity.status(403)
                .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
                .body("Identidad LinkedIn no autorizada.");
        }

        var session = request.getSession(false);
        if (session == null) {
            return unavailable();
        }

        LinkedInPublicationApproval approval = approvals.findForSession(
            approvalId, session.getId(), subject
        );

        if (approval == null
                || approval.status() != LinkedInPublicationStatus.PENDING
                || approval.confirmed()
                || !LinkedInContentHasher.matches(
                    approval.content(), approval.contentSha256())) {
            return unavailable();
        }

        CsrfToken csrf = (CsrfToken) request.getAttribute(
            CsrfToken.class.getName()
        );

        if (csrf == null) {
            return ResponseEntity.status(403)
                .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
                .body("Protección CSRF no disponible.");
        }

        String html = """
            <!doctype html>
            <html lang="es">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Revisar publicación de LinkedIn</title>
            </head>
            <body>
              <main>
                <h1>Revisar publicación de LinkedIn</h1>
                <p>Revisa el texto completo antes de confirmar.</p>
                <pre style="white-space:pre-wrap;overflow-wrap:anywhere">%s</pre>
                <p>Esta confirmación no publica contenido en LinkedIn.</p>
                <form method="post" action="/api/v1/linkedin/approvals/%s/confirm">
                  <input type="hidden" name="%s" value="%s">
                  <button type="submit">Confirmar aprobación</button>
                </form>
              </main>
            </body>
            </html>
            """.formatted(
                escapeHtml(approval.content()),
                escapeHtml(approval.approvalId()),
                escapeHtml(csrf.getParameterName()),
                escapeHtml(csrf.getToken())
            );

        return ResponseEntity.ok()
            .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
            .header("Cache-Control", "no-store")
            .header("X-Content-Type-Options", "nosniff")
            .body(html);
    }


    @GetMapping(
        value = "/api/v1/linkedin/approvals/{approvalId}/confirmed",
        produces = MediaType.TEXT_HTML_VALUE
    )
    public ResponseEntity<String> confirmedPage(
            @PathVariable String approvalId,
            Authentication authentication,
            HttpServletRequest request) {

        String subject;

        try {
            subject = identity.requireSubject(authentication);
        } catch (SecurityException exception) {
            return ResponseEntity.status(403)
                .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
                .body("Identidad LinkedIn no autorizada.");
        }

        var session = request.getSession(false);

        if (session == null) {
            return unavailable();
        }

        LinkedInPublicationApproval approval = approvals.findForSession(
            approvalId,
            session.getId(),
            subject
        );

        if (approval == null
                || approval.status() != LinkedInPublicationStatus.CONFIRMED
                || !approval.confirmed()
                || !LinkedInContentHasher.matches(
                    approval.content(),
                    approval.contentSha256()
                )) {
            return unavailable();
        }

        String html = """
            <!doctype html>
            <html lang="es">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Aprobación confirmada</title>
            </head>
            <body>
              <main>
                <h1>Aprobación confirmada</h1>
                <p>Has aprobado el siguiente contenido:</p>
                <pre style="white-space:pre-wrap;overflow-wrap:anywhere">%s</pre>
                <p>El contenido todavía no se ha publicado en LinkedIn.</p>
              </main>
            </body>
            </html>
            """.formatted(escapeHtml(approval.content()));

        return ResponseEntity.ok()
            .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
            .header("Cache-Control", "no-store")
            .header("X-Content-Type-Options", "nosniff")
            .body(html);
    }

    private ResponseEntity<String> unavailable() {
        return ResponseEntity.status(404)
            .contentType(new MediaType(MediaType.TEXT_HTML, java.nio.charset.StandardCharsets.UTF_8))
            .body("Aprobación no disponible.");
    }

    private static String escapeHtml(String value) {
        return value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&#39;");
    }
}
