package com.nocountry.communitylab.client;

import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.model.dto.CommunityProcessRequestDto;
import com.nocountry.communitylab.model.dto.FastAiAnalysisResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.retry.support.RetryTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class ResilientAiClient {

    private final FastAiClient fastAiClient;
    private final RetryTemplate aiRetryTemplate;

    // Envuelve la llamada original con la magia de los reintentos
    public FastAiAnalysisResult analyzeWithRetry(CommunityProcessRequestDto request) throws AiServiceException {
        return aiRetryTemplate.execute(ctx -> {
            log.info("Calling the AI (Attempt {})", ctx.getRetryCount() + 1);
            return fastAiClient.analyzeBatch(request);
        });
    }
}