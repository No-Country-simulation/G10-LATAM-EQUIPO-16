package com.nocountry.communitylab.client;

import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.exception.AiServiceUnavailableException;
import com.nocountry.communitylab.model.dto.CommunityProcessRequestDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.http.MediaType;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;

@Slf4j
@Component
public class FastAiClient {

    private static final String ANALYZE_PATH = "/api/v1/analyze";
    private final RestClient restClient;

    public FastAiClient(@Value("${ai.service.base-url:http://localhost:8000}") String baseUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .build();
    }

    // Realiza la petición HTTP real al servicio de Python
    public FastAiAnalysisResult analyzeBatch(CommunityProcessRequestDto request) throws AiServiceException {
        try {
            log.info("Sending {} interactions to AI service", request.getCommunitySource());
            FastAiAnalysisResult result = restClient.post()
                    .uri(ANALYZE_PATH)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(FastAiAnalysisResult.class);

        if (result == null) {
            throw new AiServiceException("AI service returned an empty body");
        }
        return result;        

        } catch (ResourceAccessException e) {
            // Error de red (el servidor está apagado o no hay internet)
            log.warn("AI service unreachable or timed out: {}", e.getMessage());
            throw new AiServiceUnavailableException("AI service unreachable or timed out", e);
        } catch (HttpServerErrorException e) {
            // El servidor respondió, pero con un error 5xx (ej. 500 Internal Server Error)
            log.warn("AI service returned HTTP {}", e.getStatusCode().value());
            throw new AiServiceUnavailableException(
                    "AI service returned HTTP " + e.getStatusCode().value(), e);
        } catch (Exception e) {
            // Cualquier otro error desconocido
            log.error("Non-retryable error calling AI service", e);
            throw new AiServiceException("Unexpected error calling AI service: " + e.getMessage(), e);
        }
    }
}