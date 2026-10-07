package com.nocountry.communitylab.client;

import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.model.dto.AiBatchRequestDto;
import com.nocountry.communitylab.model.dto.AiInteractionDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.exception.AiServiceUnavailableException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientException;

import java.util.List;

/**
 * Cliente HTTP del microservicio de IA (FastAPI). Usa el {@link RestClient} definido en HttpClientConfig
 * (URL base y timeouts). Nunca devuelve datos simulados: traduce cada fallo a una excepción.
 */
@Slf4j
@Component
public class FastAiClient {

    private static final String ANALYZE_BATCH_PATH = "/api/v1/analyze-batch";

    private final RestClient restClient;

    public FastAiClient(RestClient restClient) {
        this.restClient = restClient;
    }

    /**
     * Envía las interacciones válidas a la IA.
     *
     * @throws AiServiceUnavailableException error de red, timeout o HTTP 5xx (reintentable)
     * @throws AiServiceException            respuesta nula, HTTP 4xx u otro error no reintentable
     */
    public FastAiAnalysisResult analyzeBatch(List<InteractionEntity> validInteractions,
                                            String communitySource, String referencePeriod) {
        AiBatchRequestDto requestDto = toRequest(validInteractions, communitySource, referencePeriod);
        log.info("Sending {} interactions to AI service ({})", validInteractions.size(), ANALYZE_BATCH_PATH);

        FastAiAnalysisResult result;
        try {
            result = restClient.post()
                    .uri(ANALYZE_BATCH_PATH)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(requestDto)
                    .retrieve()
                    .body(FastAiAnalysisResult.class);
        } catch (ResourceAccessException e) {
            // Servidor apagado, conexión rechazada o timeout
            log.warn("AI service unreachable or timed out: {}", e.getMessage());
            throw new AiServiceUnavailableException("AI service unreachable or timed out", e);
        } catch (HttpServerErrorException e) {
            log.warn("AI service returned HTTP {}", e.getStatusCode().value());
            throw new AiServiceUnavailableException(
                    "AI service returned HTTP " + e.getStatusCode().value(), e);
        } catch (HttpClientErrorException e) {
            log.error("AI service rejected the request with HTTP {}", e.getStatusCode().value());
            throw new AiServiceException(
                    "AI service rejected the request with HTTP " + e.getStatusCode().value(), e);
        } catch (RestClientException e) {
            log.error("Unreadable response from AI service", e);
            throw new AiServiceException("Unexpected error calling AI service: " + e.getMessage(), e);
        }

        if (result == null) {
            throw new AiServiceException("AI service returned an empty body");
        }
        return result;
    }

    private AiBatchRequestDto toRequest(List<InteractionEntity> interactions,
                                        String communitySource, String referencePeriod) {
        return AiBatchRequestDto.builder()
                .communitySource(communitySource)
                .referencePeriod(referencePeriod)
                .interactions(interactions.stream().map(this::toAiInteraction).toList())
                .build();
    }

    private AiInteractionDto toAiInteraction(InteractionEntity entity) {
        return AiInteractionDto.builder()
                .id(entity.getId().toString())
                .author(entity.getAuthor())
                .channel(entity.getChannel())
                .type(entity.getType())
                .text(entity.getText())
                .build();
    }
}
