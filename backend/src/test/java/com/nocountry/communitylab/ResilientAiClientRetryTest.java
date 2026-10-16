package com.nocountry.communitylab;

import com.nocountry.communitylab.client.FastAiClient;
import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.config.AppRetryConfig;
import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.exception.AiServiceUnavailableException;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.reset;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Verifica que el proxy de {@code @Retryable} esté activo con Spring Boot 4 y que la política sea la acordada:
 * solo los errores transitorios (AiServiceUnavailableException) se reintentan, hasta 3 intentos en total
 * (esperas de 2 s y 4 s); los permanentes (AiServiceException) fallan al primer intento.
 */
@SpringJUnitConfig(classes = {AppRetryConfig.class, ResilientAiClient.class})
class ResilientAiClientRetryTest {

    @MockitoBean
    private FastAiClient fastAiClient;

    @Autowired
    private ResilientAiClient resilientAiClient;

    private final List<InteractionEntity> interactions = List.of();

    @BeforeEach
    void resetMock() {
        reset(fastAiClient);
    }

    @Test
    void transientErrorIsRetriedUntilThreeAttemptsAndThenRethrown() {
        when(fastAiClient.analyzeBatch(any(), any(), any()))
                .thenThrow(new AiServiceUnavailableException("AI service returned HTTP 503", 503));

        assertThrows(AiServiceUnavailableException.class,
                () -> resilientAiClient.analyzeWithRetry(interactions, "Discord", "Semana_04"));

        verify(fastAiClient, times(3)).analyzeBatch(any(), any(), any());
    }

    @Test
    void transientErrorThatRecoversStopsRetrying() {
        FastAiAnalysisResult ok = new FastAiAnalysisResult();
        when(fastAiClient.analyzeBatch(any(), any(), any()))
                .thenThrow(new AiServiceUnavailableException("timeout", new RuntimeException("timeout")))
                .thenReturn(ok);

        FastAiAnalysisResult result = resilientAiClient.analyzeWithRetry(interactions, "Discord", "Semana_04");

        assertEquals(ok, result);
        verify(fastAiClient, times(2)).analyzeBatch(any(), any(), any());
    }

    @Test
    void permanentErrorIsNotRetried() {
        when(fastAiClient.analyzeBatch(any(), any(), any()))
                .thenThrow(new AiServiceException("AI service rejected the request: HTTP 422"));

        assertThrows(AiServiceException.class,
                () -> resilientAiClient.analyzeWithRetry(interactions, "Discord", "Semana_04"));

        verify(fastAiClient, times(1)).analyzeBatch(any(), any(), any());
    }
}
