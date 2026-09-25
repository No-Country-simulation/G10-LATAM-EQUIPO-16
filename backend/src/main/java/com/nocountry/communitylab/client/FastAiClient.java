package com.nocountry.communitylab.client;



import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteraccionCruda;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;

/**
 * Cliente HTTP hacia el servicio Python de IA (FastAPI / LangChain).
 * Mientras el equipo de IA termina el servicio, este cliente retorna un mock
 * de respaldo si la llamada HTTP falla.
 */
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
    /**
     * EnvIa el lote de interacciones al servicio python y devuelve el analisis consolidado.
     *
     * @param interactions lista de interacciones validas (no descartadas)
     * @return resultado del analisis (real o mock si el servicio no esta disponible)
     */

    public FastAiAnalysisResult analyzeBatch(List<InteraccionCruda> interactions) {
        try {
            log.info("Sending {} interactions to AI service", interactions.size());
            FastAiAnalysisResult result = restClient.post()
                    .uri("/api/v1/analyze")
                    .body(interactions)
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
