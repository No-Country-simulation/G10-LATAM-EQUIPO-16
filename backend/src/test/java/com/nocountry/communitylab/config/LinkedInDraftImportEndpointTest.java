package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.DefaultOidcUser;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.Map;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@TestPropertySource(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
    "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
})
class LinkedInDraftImportEndpointTest {

    @Autowired
    private MockMvc mvc;











    @Test
    void anotherSessionCannotConsumeImportedDraft() throws Exception {
        Instant now = Instant.now();
        OidcIdToken token = new OidcIdToken(
            "session-isolation-token", now, now.plusSeconds(3600),
            Map.of("sub", "same-linkedin-user")
        );
        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"), token
        );
        OAuth2AuthenticationToken auth = new OAuth2AuthenticationToken(
            user, user.getAuthorities(), "linkedin"
        );

        MockHttpSession sessionA = new MockHttpSession();
        MockHttpSession sessionB = new MockHttpSession();

        String html = mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(sessionA).with(authentication(auth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("content", "Borrador privado de sesión A"))
            .andExpect(status().isOk())
            .andReturn().getResponse().getContentAsString();

        var matcher = java.util.regex.Pattern
            .compile("name=\\\"draftId\\\" value=\\\"([^\\\"]+)\\\"")
            .matcher(html);

        org.junit.jupiter.api.Assertions.assertTrue(matcher.find());
        String draftId = matcher.group(1);

        mvc.perform(post("/api/v1/linkedin/drafts/import/review")
                .session(sessionB).with(authentication(auth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("draftId", draftId))
            .andExpect(status().isNotFound());

        mvc.perform(post("/api/v1/linkedin/drafts/import/review")
                .session(sessionA).with(authentication(auth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("draftId", draftId))
            .andExpect(status().isSeeOther());
    }

    @Test
    void anotherLinkedInIdentityCannotConsumeImportedDraft() throws Exception {
        Instant now = Instant.now();
        OidcIdToken token = new OidcIdToken(
            "session-isolation-token", now, now.plusSeconds(3600),
            Map.of("sub", "same-linkedin-user")
        );
        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"), token
        );
        OAuth2AuthenticationToken auth = new OAuth2AuthenticationToken(
            user, user.getAuthorities(), "linkedin"
        );

        MockHttpSession sessionA = new MockHttpSession();
        OidcIdToken otherToken = new OidcIdToken(
            "other-identity-token", now, now.plusSeconds(3600),
            Map.of("sub", "different-linkedin-user")
        );
        OidcUser otherUser = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"), otherToken
        );
        OAuth2AuthenticationToken otherAuth = new OAuth2AuthenticationToken(
            otherUser, otherUser.getAuthorities(), "linkedin"
        );

        String html = mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(sessionA).with(authentication(auth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("content", "Borrador privado de sesión A"))
            .andExpect(status().isOk())
            .andReturn().getResponse().getContentAsString();

        var matcher = java.util.regex.Pattern
            .compile("name=\\\"draftId\\\" value=\\\"([^\\\"]+)\\\"")
            .matcher(html);

        org.junit.jupiter.api.Assertions.assertTrue(matcher.find());
        String draftId = matcher.group(1);

        mvc.perform(post("/api/v1/linkedin/drafts/import/review")
                .session(sessionA).with(authentication(otherAuth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("draftId", draftId))
            .andExpect(status().isNotFound());

        mvc.perform(post("/api/v1/linkedin/drafts/import/review")
                .session(sessionA).with(authentication(auth)).with(csrf())
                .contentType(org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED)
                .param("draftId", draftId))
            .andExpect(status().isSeeOther());
    }

    @Test
    void missingCsrfBlocksContinueToReview() throws Exception {
        mvc.perform(post("/api/v1/linkedin/drafts/import/review")
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("draftId", "test-draft"))
            .andExpect(status().isForbidden());
    }

    @Test
    void consumedDraftCannotBeReviewedTwice() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "single-use-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-single-use-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth = new OAuth2AuthenticationToken(
            user, user.getAuthorities(), "linkedin"
        );

        MockHttpSession session = new MockHttpSession();

        String html = mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(session)
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "Borrador de uso único"))
            .andExpect(status().isOk())
            .andReturn().getResponse().getContentAsString();

        var matcher = java.util.regex.Pattern
            .compile("name=\"draftId\" value=\"([^\"]+)\"")
            .matcher(html);

        org.junit.jupiter.api.Assertions.assertTrue(matcher.find());
        String draftId = matcher.group(1);

        for (int attempt = 1; attempt <= 2; attempt++) {
            var result = mvc.perform(
                post("/api/v1/linkedin/drafts/import/review")
                    .session(session)
                    .with(authentication(auth))
                    .with(csrf())
                    .contentType(
                        org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                    )
                    .param("draftId", draftId)
            );

            if (attempt == 1) {
                result.andExpect(status().isSeeOther());
            } else {
                result.andExpect(status().isNotFound());
            }
        }
    }

    @Test
    void importedDraftCanContinueToPendingReview() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "review-flow-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-review-flow-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        MockHttpSession session = new MockHttpSession();
        String content = "Publicación pendiente de aprobación";

        String html = mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(session)
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", content))
            .andExpect(status().isOk())
            .andReturn()
            .getResponse()
            .getContentAsString();

        java.util.regex.Matcher matcher = java.util.regex.Pattern
            .compile("name=\"draftId\" value=\"([^\"]+)\"")
            .matcher(html);

        org.junit.jupiter.api.Assertions.assertTrue(
            matcher.find(),
            "Debe existir el identificador del borrador"
        );

        String draftId = matcher.group(1);

        String location = mvc.perform(
                post("/api/v1/linkedin/drafts/import/review")
                    .session(session)
                    .with(authentication(auth))
                    .with(csrf())
                    .contentType(
                        org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                    )
                    .param("draftId", draftId))
            .andExpect(status().isSeeOther())
            .andExpect(header().string(
                "Location",
                org.hamcrest.Matchers.matchesPattern(
                    "/api/v1/linkedin/approvals/[^/]+/review"
                )
            ))
            .andReturn()
            .getResponse()
            .getHeader("Location");

        mvc.perform(get(location)
                .session(session)
                .with(authentication(auth)))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(content)
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "Confirmar aprobación"
                )
            ));
    }

    @Test
    void importedDraftOffersSecureReviewForm() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "review-form-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-review-form-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "Contenido pendiente de revisión"))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "Continuar a revisión"
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "name=\"draftId\""
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "name=\"_csrf\""
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "No se ha aprobado ni publicado"
                )
            ));
    }

    @Test
    void importedHtmlIsEscaped() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "html-escape-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-html-escape-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        String maliciousContent = "<script>alert('XSS')</script>";

        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", maliciousContent))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;"
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.not(
                    org.hamcrest.Matchers.containsString(maliciousContent)
                )
            ));
    }

    @Test
    void contentOver3000CharactersIsRejected() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "oversized-content-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-oversized-content-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "A".repeat(3001)))
            .andExpect(status().isBadRequest());
    }

    @Test
    void emptyContentIsRejected() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "empty-content-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-empty-content-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "   "))
            .andExpect(status().isBadRequest());
    }

    @Test
    void authenticatedLinkedInUserCanImportDraft() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "import-post-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-import-post-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth))
                .with(csrf())
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "Mi publicación revisada"))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "Borrador temporal guardado"
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "Mi publicación revisada"
                )
            ));
    }

    @Test
    void missingCsrfBlocksDraftImport() throws Exception {
        mvc.perform(post("/api/v1/linkedin/drafts/import")
                .contentType(
                    org.springframework.http.MediaType.APPLICATION_FORM_URLENCODED
                )
                .param("content", "Borrador de prueba"))
            .andExpect(status().isForbidden());
    }

    @Test
    void anonymousUserCannotAccessImportPage() throws Exception {
        mvc.perform(get("/api/v1/linkedin/drafts/import"))
            .andExpect(status().is3xxRedirection());
    }

    @Test
    void authenticatedLinkedInUserSeesImportForm() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "import-test-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-import-user")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken auth =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        mvc.perform(get("/api/v1/linkedin/drafts/import")
                .session(new MockHttpSession())
                .with(authentication(auth)))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "Importar borrador de LinkedIn"
                )
            ))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "name=\"_csrf\""
                )
            ));
    }
}
