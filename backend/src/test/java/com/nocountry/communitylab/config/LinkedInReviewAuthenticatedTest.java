package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.oauth2.client.registration.ClientRegistration;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

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
class LinkedInReviewAuthenticatedTest {

    @Autowired
    private MockMvc mvc;

    private static final String BASE = "/api/v1/linkedin/approvals";

    private final ClientRegistration linkedin =
        ClientRegistration.withRegistrationId("linkedin")
            .clientId("test-client")
            .clientSecret("test-secret")
            .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
            .redirectUri("{baseUrl}/auth/linkedin/callback")
            .scope("openid", "profile", "w_member_social")
            .authorizationUri("https://www.linkedin.com/oauth/v2/authorization")
            .tokenUri("https://www.linkedin.com/oauth/v2/accessToken")
            .jwkSetUri("https://www.linkedin.com/oauth/openid/jwks")
            .issuerUri("https://www.linkedin.com")
            .build();

    private String createApproval(
            MockHttpSession session, String content) throws Exception {

        String json = new tools.jackson.databind.ObjectMapper()
            .writeValueAsString(java.util.Map.of("content", content));

        String response = mvc.perform(post(BASE)
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A")))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isCreated())
            .andReturn().getResponse().getContentAsString();

        return new tools.jackson.databind.ObjectMapper()
            .readTree(response).get("approvalId").asText();
    }

    @Test
    void ownerCanReviewWithCsrfForm() throws Exception {
        var session = new MockHttpSession();
        String id = createApproval(session, "Texto de prueba Aigoraweave");

        mvc.perform(get(BASE + "/" + id + "/review")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andExpect(content().contentTypeCompatibleWith(MediaType.TEXT_HTML))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString("Texto de prueba Aigoraweave")))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString("name=\"_csrf\"")))
            .andExpect(header().string("Cache-Control", "no-store"));
    }

    @Test
    void otherSessionCannotReview() throws Exception {
        var original = new MockHttpSession();
        String id = createApproval(original, "Contenido privado");

        mvc.perform(get(BASE + "/" + id + "/review")
                .session(new MockHttpSession())
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isNotFound());
    }

    @Test
    void otherIdentityCannotReview() throws Exception {
        var session = new MockHttpSession();
        String id = createApproval(session, "Contenido privado");

        mvc.perform(get(BASE + "/" + id + "/review")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-B"))))
            .andExpect(status().isNotFound());
    }


    @Test
    void htmlFormCanConfirmApprovalWithItsCsrfToken() throws Exception {
        var session = new MockHttpSession();
        String id = createApproval(session, "Confirmación desde formulario HTML");

        var review = mvc.perform(get(BASE + "/" + id + "/review")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andReturn();

        String html = review.getResponse().getContentAsString();

        var pattern = java.util.regex.Pattern.compile(
            "name=\"([^\"]+)\" value=\"([^\"]+)\""
        );
        var matcher = pattern.matcher(html);

        if (!matcher.find()) {
            throw new AssertionError("El formulario no contiene el token CSRF.");
        }

        String parameterName = matcher.group(1);
        String token = matcher.group(2);

        mvc.perform(post(BASE + "/" + id + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A")))
                .param(parameterName, token))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("CONFIRMED"));
    }


    @Test
    void browserFormRedirectsToProtectedConfirmationPage() throws Exception {
        var session = new MockHttpSession();
        String id = createApproval(session, "Contenido aprobado desde navegador");

        var review = mvc.perform(get(BASE + "/" + id + "/review")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andReturn();

        String html = review.getResponse().getContentAsString();
        var matcher = java.util.regex.Pattern.compile(
            "name=\"([^\"]+)\" value=\"([^\"]+)\""
        ).matcher(html);

        if (!matcher.find()) {
            throw new AssertionError("No se encontró el token CSRF.");
        }

        String confirmedUrl = BASE + "/" + id + "/confirmed";

        mvc.perform(post(BASE + "/" + id + "/confirm")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A")))
                .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                .param(matcher.group(1), matcher.group(2)))
            .andExpect(status().isSeeOther())
            .andExpect(header().string("Location", confirmedUrl));

        mvc.perform(get(confirmedUrl)
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString("Aprobación confirmada")))
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString(
                    "todavía no se ha publicado en LinkedIn")));

        mvc.perform(get(confirmedUrl)
                .session(new MockHttpSession())
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isNotFound());
    }

    @Test
    void htmlContentIsEscaped() throws Exception {
        var session = new MockHttpSession();
        String id = createApproval(session, "<script>alert('x')</script>");

        mvc.perform(get(BASE + "/" + id + "/review")
                .session(session)
                .with(oidcLogin()
                    .clientRegistration(linkedin)
                    .idToken(t -> t.claim("sub", "linkedin-user-A"))))
            .andExpect(status().isOk())
            .andExpect(content().string(
                org.hamcrest.Matchers.containsString("&lt;script&gt;")))
            .andExpect(content().string(
                org.hamcrest.Matchers.not(
                    org.hamcrest.Matchers.containsString("<script>"))));
    }
}
