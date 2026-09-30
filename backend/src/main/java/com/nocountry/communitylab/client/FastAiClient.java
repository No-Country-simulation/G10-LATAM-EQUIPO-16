package com.nocountry.communitylab.client;



import com.nocountry.communitylab.model.dto.AiBatchRequestDto;
import com.nocountry.communitylab.model.dto.AiInteractionDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class FastAiClient {

    private static final Logger log = LoggerFactory.getLogger(FastAiClient.class);

    private final RestClient restClient;

    public FastAiClient(@Value("${ai.service.base-url:http://localhost:8000}") String baseUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .build();
        log.info("FastAiClient initialized with base URL: {}", baseUrl);
    }

    public FastAiAnalysisResult analyzeBatch(List<InteractionEntity> interactions, String communitySource, String referencePeriod) {
        try {
            // Convertir entidades a DTO de IA
            List<AiInteractionDto> aiInteractions = interactions.stream()
                    .map(i -> AiInteractionDto.builder()
                            .id(i.getId().toString())
                            .author(i.getAuthor())
                            .channel(i.getChannel())
                            .type(i.getType())
                            .text(i.getText())
                            .build())
                    .collect(Collectors.toList());

            AiBatchRequestDto request = AiBatchRequestDto.builder()
                    .communitySource(communitySource)
                    .referencePeriod(referencePeriod)
                    .interactions(aiInteractions)
                    .build();

            log.info("Sending {} interactions to AI service", interactions.size());

            FastAiAnalysisResult result = restClient.post()
                    .uri("/api/v1/analyze-batch")
                    .body(request)
                    .retrieve()
                    .body(FastAiAnalysisResult.class);

            if (result == null) {
                log.warn("AI service returned null response, falling back to mock");
                return FastAiAnalysisResult.mock();
            }

            return result;

        } catch (Exception ex) {
            log.warn("AI service call failed ({}), falling back to mock: {}",
                    ex.getClass().getSimpleName(), ex.getMessage());
            return FastAiAnalysisResult.mock();
        }
    }
}
