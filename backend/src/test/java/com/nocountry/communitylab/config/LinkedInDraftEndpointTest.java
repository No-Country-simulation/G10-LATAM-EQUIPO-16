package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import org.springframework.mock.web.MockHttpSession;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.oauth2.core.oidc.OidcIdToken;
import org.springframework.security.oauth2.core.oidc.user.DefaultOidcUser;
import org.springframework.security.oauth2.core.oidc.user.OidcUser;
import org.springframework.security.core.authority.AuthorityUtils;
import java.time.Instant;
import java.util.Map;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles({"linkedin-dev", "linkedin-oauth"})
@TestPropertySource(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.security.oauth2.client.registration.linkedin.client-id=test-client",
    "spring.security.oauth2.client.registration.linkedin.client-secret=test-secret"
})
class LinkedInDraftEndpointTest {



    @Autowired
    private MockMvc mvc;

    @Test
    void anonymousUserCannotCreateDraft() throws Exception {
        mvc.perform(post("/api/v1/linkedin/drafts")
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"content\":\"Publicación de prueba\"}"))
            .andExpect(status().is3xxRedirection());
    }

    @Test
    void missingCsrfBlocksDraftCreation() throws Exception {
        mvc.perform(post("/api/v1/linkedin/drafts")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"content\":\"Publicación de prueba\"}"))
            .andExpect(status().isForbidden());
    }



    @Test
    void differentLinkedInUserCannotConsumeDraft() throws Exception {
        Instant now = Instant.now();

        OidcIdToken tokenA = new OidcIdToken(
            "token-user-a", now, now.plusSeconds(3600),
            Map.of("sub", "linkedin-user-A")
        );

        OidcIdToken tokenB = new OidcIdToken(
            "token-user-b", now, now.plusSeconds(3600),
            Map.of("sub", "linkedin-user-B")
        );

        OidcUser userA = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"), tokenA
        );

        OidcUser userB = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"), tokenB
        );

        OAuth2AuthenticationToken authA =
            new OAuth2AuthenticationToken(
                userA, userA.getAuthorities(), "linkedin"
            );

        OAuth2AuthenticationToken authB =
            new OAuth2AuthenticationToken(
                userB, userB.getAuthorities(), "linkedin"
            );

        MockHttpSession sharedSession = new MockHttpSession();

        String response = mvc.perform(post("/api/v1/linkedin/drafts")
                .session(sharedSession)
                .with(authentication(authA))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new com.fasterxml.jackson.databind.ObjectMapper()
                    .writeValueAsString(
                        Map.of("content", "Borrador del usuario A")
                    )))
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String draftId = new com.fasterxml.jackson.databind.ObjectMapper()
            .readTree(response)
            .get("draftId")
            .asText();

        mvc.perform(post("/api/v1/linkedin/drafts/{draftId}/consume", draftId)
                .session(sharedSession)
                .with(authentication(authB))
                .with(csrf()))
            .andExpect(status().isNotFound());

        mvc.perform(post("/api/v1/linkedin/drafts/{draftId}/consume", draftId)
                .session(sharedSession)
                .with(authentication(authA))
                .with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content")
                .value("Borrador del usuario A"));
    }


    @Test
    void differentSessionCannotConsumeDraft() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "test-id-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-user-isolation")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken authentication =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        MockHttpSession originalSession = new MockHttpSession();
        MockHttpSession differentSession = new MockHttpSession();

        String response = mvc.perform(post("/api/v1/linkedin/drafts")
                .session(originalSession)
                .with(authentication(authentication))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(Map.of("content", "Borrador privado"))))
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String draftId = new com.fasterxml.jackson.databind.ObjectMapper()
            .readTree(response)
            .get("draftId")
            .asText();

        mvc.perform(post("/api/v1/linkedin/drafts/{draftId}/consume", draftId)
                .session(differentSession)
                .with(authentication(authentication))
                .with(csrf()))
            .andExpect(status().isNotFound());

        mvc.perform(post("/api/v1/linkedin/drafts/{draftId}/consume", draftId)
                .session(originalSession)
                .with(authentication(authentication))
                .with(csrf()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.content").value("Borrador privado"));

        mvc.perform(post("/api/v1/linkedin/drafts/{draftId}/consume", draftId)
                .session(originalSession)
                .with(authentication(authentication))
                .with(csrf()))
            .andExpect(status().isNotFound());
    }


    @Test
    void authenticatedLinkedInUserCanCreateDraft() throws Exception {
        Instant now = Instant.now();

        OidcIdToken token = new OidcIdToken(
            "test-id-token",
            now,
            now.plusSeconds(3600),
            Map.of("sub", "linkedin-user-test")
        );

        OidcUser user = new DefaultOidcUser(
            AuthorityUtils.createAuthorityList("ROLE_USER"),
            token
        );

        OAuth2AuthenticationToken authentication =
            new OAuth2AuthenticationToken(
                user,
                user.getAuthorities(),
                "linkedin"
            );

        MockHttpSession session = new MockHttpSession();

        mvc.perform(post("/api/v1/linkedin/drafts")
                .session(session)
                .with(authentication(authentication))
                .with(csrf())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"content\":\"Publicación de prueba\"}"))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.draftId").isNotEmpty())
            .andExpect(jsonPath("$.content").value("Publicación de prueba"))
            .andExpect(jsonPath("$.expiresAt").isNotEmpty());
    }
}
