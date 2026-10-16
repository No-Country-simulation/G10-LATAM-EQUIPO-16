package com.nocountry.communitylab.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.retry.annotation.EnableRetry;

/**
 * Activa el soporte de {@code @Retryable} / {@code @Recover} (ver ResilientAiClient).
 */
@Configuration
@EnableRetry
public class AppRetryConfig {
}
