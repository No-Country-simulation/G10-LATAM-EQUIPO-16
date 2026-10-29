package com.nocountry.communitylab.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.env.Environment;
import org.springframework.security.config.Customizer;
import org.springframework.security.oauth2.client.web.HttpSessionOAuth2AuthorizedClientRepository;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            Environment environment) throws Exception {

        boolean linkedinOAuthEnabled =
                environment.matchesProfiles("linkedin-oauth");

        http.csrf(csrf -> csrf
            .ignoringRequestMatchers("/api/v1/community/process")
        );

        http.authorizeHttpRequests(auth -> {
            auth.requestMatchers(HttpMethod.GET, "/api/v1/health").permitAll();
            auth.requestMatchers(HttpMethod.POST, "/api/v1/community/process").permitAll();

            if (linkedinOAuthEnabled) {
                auth.requestMatchers(
                    HttpMethod.GET,
                    "/api/v1/linkedin/me",
                    "/api/v1/linkedin/drafts/import"
                ).authenticated();

                auth.requestMatchers(
                    HttpMethod.GET,
                    "/api/v1/linkedin/approvals/*/review",
                    "/api/v1/linkedin/approvals/*/confirmed"
                ).authenticated();

                auth.requestMatchers(
                    HttpMethod.POST,
                    "/api/v1/linkedin/drafts",
                    "/api/v1/linkedin/drafts/import",
                    "/api/v1/linkedin/drafts/import/review",
                    "/api/v1/linkedin/drafts/*/consume"
                ).authenticated();

                auth.requestMatchers(
                    HttpMethod.POST,
                    "/api/v1/linkedin/approvals"
                ).authenticated();

                auth.requestMatchers(
                    HttpMethod.POST,
                    "/api/v1/linkedin/approvals/*/confirm"
                ).authenticated();

                auth.requestMatchers(
                    "/oauth2/authorization/linkedin",
                    "/auth/linkedin/callback"
                ).permitAll();
            }

            auth.anyRequest().denyAll();
        });

        if (linkedinOAuthEnabled) {
            http.oauth2Login(oauth -> oauth
                .redirectionEndpoint(redirection -> redirection
                    .baseUri("/auth/linkedin/callback")
                )
            );

            http.oauth2Client(oauth -> oauth
                .authorizedClientRepository(
                    new HttpSessionOAuth2AuthorizedClientRepository()
                )
            );
        }

        return http.build();
    }
}
