package com.nocountry.communitylab.client;

import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.exception.AiServiceUnavailableException;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import lombok.extern.slf4j.Slf4j;
import org.springframework.retry.RetryContext;
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Recover;
import org.springframework.retry.annotation.Retryable;
import org.springframework.retry.support.RetrySynchronizationManager;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Añade reintentos declarativos con backoff exponencial a {@link FastAiClient}:
 * 3 intentos en total, con esperas de 2 s y 4 s entre ellos.
 * No es transaccional: debe invocarse sin una transacción de BD abierta.
 */
@Slf4j
@Component
public class ResilientAiClient {

    private static final int MAX_ATTEMPTS = 3;

    private final FastAiClient fastAiClient;

    public ResilientAiClient(FastAiClient fastAiClient) {
        this.fastAiClient = fastAiClient;
    }

    @Retryable(retryFor = {AiServiceUnavailableException.class},
            maxAttempts = MAX_ATTEMPTS,
            backoff = @Backoff(delay = 2000, multiplier = 2.0))
    public FastAiAnalysisResult analyzeWithRetry(List<InteractionEntity> validInteractions,
                                                String communitySource, String referencePeriod) {
        RetryContext context = RetrySynchronizationManager.getContext();
        int attempt = context == null ? 1 : context.getRetryCount() + 1;
        log.info("Calling the AI service (attempt {} of {})", attempt, MAX_ATTEMPTS);
        return fastAiClient.analyzeBatch(validInteractions, communitySource, referencePeriod);
    }

    /**
     * Se ejecuta cuando se agotan los {@value #MAX_ATTEMPTS} intentos. Registra el fallo y relanza la
     * excepción para que el orquestador marque el lote como ERROR y el handler responda 503 (DEC-05).
     */
    @Recover
    public FastAiAnalysisResult recover(AiServiceUnavailableException ex,
                                        List<InteractionEntity> validInteractions,
                                        String communitySource, String referencePeriod) {
        log.error("AI service still unavailable after {} attempts ({} interactions, source '{}', period '{}'): {}",
                MAX_ATTEMPTS, validInteractions.size(), communitySource, referencePeriod, ex.getMessage());
        throw ex;
    }

    /**
     * Errores NO reintentables (HTTP 4xx, cuerpo vacío): Spring Retry también busca un @Recover para ellos y,
     * si no lo encuentra, lanza ExhaustedRetryException en lugar de la excepción original.
     */
    @Recover
    public FastAiAnalysisResult recover(AiServiceException ex,
                                        List<InteractionEntity> validInteractions,
                                        String communitySource, String referencePeriod) {
        log.error("Non-retryable AI service error ({} interactions, source '{}', period '{}'): {}",
                validInteractions.size(), communitySource, referencePeriod, ex.getMessage());
        throw ex;
    }
}
