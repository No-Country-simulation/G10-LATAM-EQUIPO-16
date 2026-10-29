package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.service.linkedin.LinkedInApprovalService;
import com.nocountry.communitylab.service.linkedin.LinkedInAuthenticatedIdentity;
import com.nocountry.communitylab.service.linkedin.LinkedInDraftOwner;
import com.nocountry.communitylab.service.linkedin.LinkedInDraftTransferService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.web.csrf.CsrfToken;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.nio.charset.StandardCharsets;

@RestController
public class LinkedInDraftImportController {

    private final LinkedInDraftOwner owner;
    private final LinkedInDraftTransferService drafts;
    private final LinkedInApprovalService approvals;
    private final LinkedInAuthenticatedIdentity identity;

    public LinkedInDraftImportController(
            LinkedInDraftOwner owner,
            LinkedInDraftTransferService drafts,
            LinkedInApprovalService approvals,
            LinkedInAuthenticatedIdentity identity) {
        this.owner = owner;
        this.drafts = drafts;
        this.approvals = approvals;
        this.identity = identity;
    }

    @GetMapping(
        value = "/api/v1/linkedin/drafts/import",
        produces = MediaType.TEXT_HTML_VALUE
    )
    public ResponseEntity<String> importPage(
            Authentication authentication,
            HttpServletRequest request) {

        try {
            owner.requireOwner(authentication, request);
        } catch (SecurityException exception) {
            return ResponseEntity.status(403)
                .contentType(new MediaType(MediaType.TEXT_HTML, StandardCharsets.UTF_8))
                .body("Identidad LinkedIn no autorizada.");
        }

        CsrfToken csrf = (CsrfToken) request.getAttribute(
            CsrfToken.class.getName()
        );

        if (csrf == null) {
            return ResponseEntity.status(403)
                .body("Protección CSRF no disponible.");
        }

        String html = """
            <!doctype html>
            <html lang="es">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Importar borrador - Aigoraweave</title>
            </head>
            <body>
              <main>
                <h1>Importar borrador de LinkedIn</h1>
                <p>Pega el texto que revisaste en Aigoraweave.</p>
                <p>Importar no publica contenido en LinkedIn.</p>
                <form method="post" action="/api/v1/linkedin/drafts/import">
                  <textarea name="content" rows="12" maxlength="3000"
                            required style="width:100%%"></textarea>
                  <input type="hidden" name="%s" value="%s">
                  <button type="submit">Guardar borrador temporal</button>
                </form>
              </main>
            </body>
            </html>
            """.formatted(
                escapeHtml(csrf.getParameterName()),
                escapeHtml(csrf.getToken())
            );

        return ResponseEntity.ok()
            .contentType(new MediaType(MediaType.TEXT_HTML, StandardCharsets.UTF_8))
            .header("Cache-Control", "no-store")
            .header("X-Content-Type-Options", "nosniff")
            .body(html);
    }

    @PostMapping(
        value = "/api/v1/linkedin/drafts/import",
        consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE,
        produces = MediaType.TEXT_HTML_VALUE
    )
    public ResponseEntity<String> saveImportedDraft(
            @RequestParam("content") String content,
            Authentication authentication,
            HttpServletRequest request) {

        String ownerId;
        try {
            ownerId = owner.requireOwner(authentication, request);
        } catch (SecurityException exception) {
            return ResponseEntity.status(403)
                .contentType(new MediaType(MediaType.TEXT_HTML, StandardCharsets.UTF_8))
                .body("Identidad LinkedIn no autorizada.");
        }

        if (content.isBlank() || content.length() > 3000) {
            return ResponseEntity.badRequest()
                .contentType(new MediaType(MediaType.TEXT_HTML, StandardCharsets.UTF_8))
                .body("El texto debe contener entre 1 y 3000 caracteres.");
        }

        CsrfToken csrf = (CsrfToken) request.getAttribute(
            CsrfToken.class.getName()
        );

        if (csrf == null) {
            return ResponseEntity.status(403)
                .body("Protección CSRF no disponible.");
        }

        var draft = drafts.create(ownerId, content);

        String html = """
            <!doctype html>
            <html lang="es">
            <head><meta charset="utf-8"><title>Borrador guardado</title></head>
            <body>
              <main>
                <h1>Borrador temporal guardado</h1>
                <p>Este borrador caduca en cinco minutos.</p>
                <p>No se ha aprobado ni publicado contenido en LinkedIn.</p>
                <pre style="white-space:pre-wrap;overflow-wrap:anywhere">%s</pre>
                <form method="post" action="/api/v1/linkedin/drafts/import/review">
                  <input type="hidden" name="draftId" value="%s">
                  <input type="hidden" name="%s" value="%s">
                  <button type="submit">Continuar a revisión</button>
                </form>
              </main>
            </body>
            </html>
            """.formatted(
                escapeHtml(draft.content()),
                escapeHtml(draft.id()),
                escapeHtml(csrf.getParameterName()),
                escapeHtml(csrf.getToken())
            );

        return ResponseEntity.ok()
            .contentType(new MediaType(MediaType.TEXT_HTML, StandardCharsets.UTF_8))
            .header("Cache-Control", "no-store")
            .header("X-Content-Type-Options", "nosniff")
            .body(html);
    }

    @PostMapping(
        value = "/api/v1/linkedin/drafts/import/review",
        consumes = MediaType.APPLICATION_FORM_URLENCODED_VALUE
    )
    public ResponseEntity<String> continueToReview(
            @RequestParam("draftId") String draftId,
            Authentication authentication,
            HttpServletRequest request) {

        String ownerId;
        String subject;

        try {
            ownerId = owner.requireOwner(authentication, request);
            subject = identity.requireSubject(authentication);
        } catch (SecurityException exception) {
            return ResponseEntity.status(403)
                .body("Identidad LinkedIn no autorizada.");
        }

        var session = request.getSession(false);
        if (session == null) {
            return ResponseEntity.status(403)
                .body("Sesión no disponible.");
        }

        var draft = drafts.consume(draftId, ownerId);
        if (draft == null) {
            return ResponseEntity.status(404)
                .body("Borrador no disponible.");
        }

        var approval = approvals.create(
            session.getId(),
            subject,
            draft.content()
        );

        return ResponseEntity.status(303)
            .header(
                "Location",
                "/api/v1/linkedin/approvals/"
                    + approval.approvalId() + "/review"
            )
            .header("Cache-Control", "no-store")
            .body("");
    }

    private static String escapeHtml(String value) {
        return value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&#39;");
    }
}
