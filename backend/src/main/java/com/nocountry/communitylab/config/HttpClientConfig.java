package com.nocountry.communitylab.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;


@Configuration
public class HttpClientConfig {

    @Bean
    public RestClient fastAiRestClient(
            @Value("${ai.service.base-url:http://localhost:8000}") String baseUrl,
            @Value("${ai.service.connect-timeout:10}") int connectTimeoutSeconds,
            @Value("${ai.service.read-timeout:60}") int readTimeoutSeconds) {

        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(connectTimeoutSeconds * 1000);
        requestFactory.setReadTimeout(readTimeoutSeconds * 1000);

        return RestClient.builder()
                .baseUrl(baseUrl)
                .requestFactory(requestFactory)
                .build();
    }
}
