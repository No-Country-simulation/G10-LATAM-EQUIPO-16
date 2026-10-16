package com.nocountry.communitylab.client;

import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.exception.AiServiceUnavailableException;
import com.nocountry.communitylab.model.dto.AiBatchRequestDto;
import com.nocountry.communitylab.model.dto.AiInteractionDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientResponseException;

import java.util.List;
import java.util.stream.Collectors;


/**
 * Cliente HTTP del microservicio de IA (FastAPI). Usa el {@link RestClient} definido en HttpClientConfig
 * (URL base y timeouts). Nunca devuelve datos simulados: traduce cada fallo a una excepción.
 */
@Slf4j
@Component
public class FastAiClient {

    private static final String ANALYZE_BATCH_PATH = "/api/v1/analyze-batch";

    private final RestClient restClient;

    public FastAiClient(RestClient fastAiRestClient) {
        this.restClient = fastAiRestClient;
        log.info("FastAiClient initialized with injected RestClient");
    }

    public FastAiAnalysisResult analyzeBatch(List<InteractionEntity> interactions, String communitySource, String referencePeriod) {
            // 1. Convertir entidades a DTO de IA (fuera del try: un error aquí no es un fallo de la IA)
            List<AiInteractionDto> aiInteractions = interactions.stream().map(i -> AiInteractionDto.builder().id(i.getId().toString()).author(i.getAuthor()).channel(i.getChannel()).type(i.getType()).text(i.getText()).build()).collect(Collectors.toList());

            // 2. Armar el envelope del lote
            AiBatchRequestDto request = AiBatchRequestDto.builder().communitySource(communitySource).referencePeriod(referencePeriod).interactions(aiInteractions).build();

            log.info("Sending {} interactions to AI service", interactions.size());

            // 3. Llamar al servicio de IA y clasificar los errores
            FastAiAnalysisResult result;
            try {
                result = restClient.post().uri("/api/v1/analyze-batch").body(request).retrieve().body(FastAiAnalysisResult.class);

            } catch (ResourceAccessException ex) {
            // Conexión rechazada o timeout: transitorio, se reintenta
            log.warn("AI service unreachable or timed out: {}", ex.getMessage());
            throw new AiServiceUnavailableException("AI service unreachable or timed out", ex);
            
            } catch (HttpServerErrorException ex) {
                int status = ex.getStatusCode().value();
                if (ex.getStatusCode() == HttpStatus.INTERNAL_SERVER_ERROR) {
                    // 4. DEC-04: un 500 del ML es error de lógica o modelo; reintentar no lo arregla.
                    // Para tratarlo también como transitorio, elimina este bloque.
                    log.error("AI service returned HTTP 500 (permanent, not retried)");
                    throw new AiServiceException("AI service returned HTTP 500", ex);
                }

                // 5. Otros 5xx (503...): transitorios, se reintentan
                log.warn("AI service returned HTTP {} (transient)", status);
                throw new AiServiceUnavailableException("AI service returned HTTP " + status, status);
            
            } catch (RestClientResponseException ex) {
                // 6. 4xx (400, 422...): la petición está mal, reintentar no sirve
                log.error("AI service rejected the request: HTTP {}", ex.getStatusCode().value());
                throw new AiServiceException("AI service rejected the request: HTTP "
                        + ex.getStatusCode().value(), ex);
            
            } catch (RestClientException ex) {
                // 7. Error de deserialización u otro problema del cliente: permanente
                log.error("Invalid response from AI service: {}", ex.getMessage());
                throw new AiServiceException("Invalid response from AI service: " + ex.getMessage(), ex);
            }

            // 8. Cuerpo vacío: error permanente
            if (result == null) {
                log.error("AI service returned an empty body");
                throw new AiServiceException("AI service returned an empty body");
            }

            // 9. Devolver el resultado
            return result;
    }
}
