package com.nocountry.communitylab.client;



import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.dto.FastAiBatchRequestDto;
import com.nocountry.communitylab.model.dto.FastAiInteractionRequestDto;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import java.util.List;

/**
 * Cliente HTTP hacia el servicio Python de IA (FastAPI / LangGraph).
 * Envia lotes de interacciones al motor de IA y propaga los errores
 * para que puedan ser gestionados por el backend.
 */
@Component
public class FastAiClient {

    private static final Logger log = LoggerFactory.getLogger(FastAiClient.class);

    private static final int MAX_ATTEMPTS = 3;
    private static final long RETRY_DELAY_MS = 2000;

    private final RestClient restClient;

    public FastAiClient(@Value("${ai.service.base-url:http://localhost:8000}") String baseUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .build();
        log.info("FastAiClient initialized with base URL: {}", baseUrl);
    }
    /**
     * EnvIa el lote de interacciones al servicio python y devuelve el analisis consolidado.
     *
     * @param interactions lista de interacciones validas (no descartadas)
     * @return resultado del analisis consolidado del servicio de IA
     */

    public FastAiAnalysisResult analyzeBatch(List<InteractionEntity> interactions) {

        List<FastAiInteractionRequestDto> aiInteractions = interactions.stream()
        .map(interaction -> FastAiInteractionRequestDto.builder()
                .id(interaction.getId().toString())
                .author(interaction.getAuthor())
                .channel(interaction.getChannel())
                .type(interaction.getType())
                .text(interaction.getText())
                .build())
        .toList();

        FastAiBatchRequestDto request = FastAiBatchRequestDto.builder()
                .communitySource(interactions.get(0).getCommunitySource())
                .referencePeriod(interactions.get(0).getReferencePeriod())
                .interactions(aiInteractions)
                .build();
        for (int attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
        log.info("Sending {} interactions to AI service (attempt {}/{})",
                interactions.size(), attempt, MAX_ATTEMPTS);

        FastAiAnalysisResult result = restClient.post()
                .uri("/api/v1/analyze-batch")
                .body(request)
                .retrieve()
                .body(FastAiAnalysisResult.class);

        if (result == null) {
            throw new IllegalStateException("AI service returned null response");
        }

        return result;

    } catch (RestClientResponseException ex) {
        int status = ex.getStatusCode().value();
        boolean transientError = status == 429 || status == 503;

        if (!transientError || attempt == MAX_ATTEMPTS) {
            log.error("AI service call failed with HTTP {}: {}",
                    status, ex.getMessage());
            throw ex;
        }

        log.warn("Transient AI error HTTP {}. Retrying in {} ms (attempt {}/{})",
                status, RETRY_DELAY_MS, attempt + 1, MAX_ATTEMPTS);

        try {
            Thread.sleep(RETRY_DELAY_MS);
        } catch (InterruptedException interrupted) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("AI retry interrupted", interrupted);
        }
    }
}

throw new IllegalStateException("AI service failed after retries");
    }
}
