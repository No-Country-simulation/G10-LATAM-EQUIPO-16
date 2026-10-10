package com.nocountry.communitylab.client;


import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.model.dto.AiBatchRequestDto;
import com.nocountry.communitylab.model.dto.AiInteractionDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class FastAiClient {

    private static final Logger log = LoggerFactory.getLogger(FastAiClient.class);

    private final RestClient restClient;

    public FastAiClient(RestClient fastAiRestClient) {
        this.restClient = fastAiRestClient;
        log.info("FastAiClient initialized with injected RestClient");
    }

    public FastAiAnalysisResult analyzeBatch(List<InteractionEntity> interactions, String communitySource, String referencePeriod) {
        try {
            // Convertir entidades a DTO de IA
            List<AiInteractionDto> aiInteractions = interactions.stream().map(i -> AiInteractionDto.builder().id(i.getId().toString()).author(i.getAuthor()).channel(i.getChannel()).type(i.getType()).text(i.getText()).build()).collect(Collectors.toList());

            AiBatchRequestDto request = AiBatchRequestDto.builder().communitySource(communitySource).referencePeriod(referencePeriod).interactions(aiInteractions).build();

            log.info("Sending {} interactions to AI service", interactions.size());

            FastAiAnalysisResult result = restClient.post().uri("/api/v1/analyze-batch").body(request).retrieve().body(FastAiAnalysisResult.class);

            if (result == null) {
                log.error("AI service returned null response");
                throw new AiServiceException("AI service returned null response");
            }

            return result;

        } catch (AiServiceException ex) {
            throw ex;

        } catch (Exception ex) {
            log.error("AI service call failed: {}", ex.getMessage(), ex);
            throw new AiServiceException("AI service call failed: " + ex.getMessage(), ex);
        }
    }
}
