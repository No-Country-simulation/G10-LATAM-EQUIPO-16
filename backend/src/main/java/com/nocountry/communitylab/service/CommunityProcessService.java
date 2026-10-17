package com.nocountry.communitylab.service;

import tools.jackson.databind.ObjectMapper;
import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.entity.DistributionBatch;
import com.nocountry.communitylab.model.enums.BatchStatus;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import com.nocountry.communitylab.repository.DistributionBatchRepository;
import com.nocountry.communitylab.repository.InteractionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Orquesta el procesamiento de un lote de interacciones de la comunidad.
 * Flujo: staging -> filtro conservador -> lote de distribución -> IA (con reintentos) -> OCI -> respuesta.
 *
 * <p><b>Regla de arquitectura:</b> esta clase y {@link #process} NO son {@code @Transactional}.
 * Cada llamada al repositorio es su propia transacción corta, así ninguna conexión de HikariCP
 * queda ocupada mientras esperamos a la IA o a OCI.
 *
 * <p><b>Contrato con IA (tarjeta C):</b>
 * <ul>
 *   <li>{@code total_interacciones_procesadas} viene del motor IA (solo exitosas).</li>
 *   <li>{@code total_descartadas} lo calcula el backend (interacciones filtradas por emojis/símbolos).</li>
 *   <li>{@code interacciones_fallidas} viene del motor IA; se reenvía al Frontend.</li>
 *   <li>{@code status: "parcial"} si hay fallidas o si la IA no devuelve resumen.</li>
 * </ul>
 *
 * <p><b>Nota sobre {@code tipo} de entrada:</b> se envía y persiste, pero no condiciona el análisis.
 * La IA reclasifica por su cuenta (DEC-02).
 */
@Service
public class CommunityProcessService {

    private static final Logger log = LoggerFactory.getLogger(CommunityProcessService.class);

    private final InteractionRepository interactionRepository;
    private final DistributionBatchRepository distributionBatchRepository;
    private final ResilientAiClient resilientAiClient;
    private final OciObjectStorageService objectStorageService;
    private final ObjectMapper objectMapper;

    public CommunityProcessService(
            InteractionRepository interactionRepository,
            DistributionBatchRepository distributionBatchRepository,
            ResilientAiClient resilientAiClient,
            OciObjectStorageService objectStorageService,
            ObjectMapper objectMapper) {
        this.interactionRepository = interactionRepository;
        this.distributionBatchRepository = distributionBatchRepository;
        this.resilientAiClient = resilientAiClient;
        this.objectStorageService = objectStorageService;
        this.objectMapper = objectMapper;
    }

    // NO @Transactional (ver Javadoc de la clase).
    public CommunityProcessResponseDto process(CommunityProcessRequestDto request) {
        log.info("Processing batch: source={}, period={}, interactions={}",
                request.getCommunitySource(), request.getReferencePeriod(),
                request.getInteractions() != null ? request.getInteractions().size() : 0);

        // 1. Convertir DTOs a entidades de dominio
        List<InteractionEntity> interactions = toEntities(request);

        // 2. Aplicar filtro conservador
        for (InteractionEntity interaction : interactions) {
            if (interaction.isTriviallyEmpty()) {
                interaction.markAsDiscarded();
            } else {
                interaction.setStatus(InteractionStatus.PENDING);
            }
        }

        // 3. Guardar todas en BD (staging)
        List<InteractionEntity> saved = interactionRepository.saveAll(interactions);

        // 4. Contar descartadas (responsabilidad del backend, no de IA - DEC-06)
        long discardedCount = saved.stream()
                .filter(i -> i.getStatus() == InteractionStatus.DISCARDED)
                .count();

        // 5. Filtrar las válidas para enviar a IA
        List<InteractionEntity> validInteractions = saved.stream()
                .filter(i -> i.getStatus() == InteractionStatus.PENDING)
                .collect(Collectors.toList());

        if (validInteractions.isEmpty()) {
            log.info("No valid interactions to send to AI (all discarded)");
            return buildEmptyResponse(saved, discardedCount);
        }

        // 6. Crear el DistributionBatch (lote_id) con estado PROCESSING
        DistributionBatch batch = distributionBatchRepository.save(DistributionBatch.builder()
                .communitySource(request.getCommunitySource())
                .referencePeriod(request.getReferencePeriod())
                .ociBucket(objectStorageService.getBucket())
                .status(BatchStatus.PROCESSING)
                .build());
        UUID batchId = batch.getId();

        // 7. Marcar como PROCESANDO
        validInteractions.forEach(InteractionEntity::markAsProcessing);
        interactionRepository.saveAll(validInteractions);

        // 8. Llamar a la IA SIN transacción; los reintentos están en ResilientAiClient
        FastAiAnalysisResult aiResult;
        try {
            aiResult = resilientAiClient.analyzeWithRetry(
                    validInteractions, request.getCommunitySource(), request.getReferencePeriod());
        } catch (AiServiceException ex) {
            // Fallo del servicio IA: marcar interacciones como ERROR y PROPAGAR para que el
            // GlobalExceptionHandler responda 503/502 y el frontend pueda reintentar.
            log.error("AI service failed for batch {}, marking interactions as ERROR: {}", batchId, ex.getMessage(), ex);
            failBatch(batch, validInteractions);
            throw ex;
        } catch (RuntimeException ex) {
            // Otros errores inesperados (BD, NPE, etc.): se reportan como 200 + status "error"
            log.error("Unexpected error processing batch {}, marking interactions as ERROR", batchId, ex);
            failBatch(batch, validInteractions);
            return buildErrorResponse(saved, batchId, discardedCount);
        }

        // 9. Cruzar IDs: los fallidos o ausentes pasan a ERROR (GRUPO C)
        reconcileInteractions(validInteractions, aiResult);

        // 10. Guardar realmente el resultado de Gemini en OCI
        String ociRoute = uploadToOci(aiResult, batchId);

        // 11. Si OCI falla: ERROR en BD, pero 200 con los activos generados por la IA (DEC-14)
        if (ociRoute == null) {
            failBatch(batch, validInteractions);
            return buildResponse(saved, aiResult, null, batchId, discardedCount);
        }

        // 12. Marcar como PROCESADO con la ruta OCI
        completeBatch(batch, validInteractions, ociRoute);
        log.info("Batch {} processed: {} interactions -> {}", batchId, validInteractions.size(), ociRoute);

        // 13. Construir respuesta
        return buildResponse(saved, aiResult, ociRoute, batchId, discardedCount);
    }

    // ---------------------------------------------------------------- persistencia

    // Marca interacciones y lote como ERROR. Si la propia BD falla, solo se registra
    // para no tapar la excepción original.
    private void failBatch(DistributionBatch batch, List<InteractionEntity> validInteractions) {
        try {
            validInteractions.forEach(InteractionEntity::markAsError);
            interactionRepository.saveAll(validInteractions);
            batch.setStatus(BatchStatus.ERROR);
            distributionBatchRepository.save(batch);
        } catch (RuntimeException dbEx) {
            log.error("Could not persist ERROR state for batch {}", batch.getId(), dbEx);
        }
    }

    // Marca como PROCESADO solo las que no quedaron en ERROR, y guarda todas.
    // Las que reconcileInteractions ya marcó como ERROR se mantienen en ERROR.
    private void completeBatch(DistributionBatch batch, List<InteractionEntity> validInteractions, String ociRoute) {
        validInteractions.forEach(i -> {
            if (i.getStatus() != InteractionStatus.ERROR) {
                i.markAsProcessed(ociRoute);
            }
        });
        interactionRepository.saveAll(validInteractions);
        // Regla PROCESSED => ociObjectRoute != null. El lote guarda solo el nombre del objeto.
        batch.setOciObjectRoute(toObjectName(ociRoute));
        batch.setStatus(BatchStatus.PROCESSED);
        distributionBatchRepository.save(batch);
    }

    /**
     * Cruza los IDs enviados con los analizados devueltos por la IA.
     * Los que no aparecen en {@code interacciones_analizadas} se marcan como ERROR,
     * cubriendo dos casos:
     * <ul>
     *   <li>El motor los reportó explícitamente en {@code interacciones_fallidas}.</li>
     *   <li>El motor los omitió (no aparecen en ninguna de las dos listas).</li>
     * </ul>
     * <p>
     * Si la IA no devuelve ni {@code analyzedInteractions} ni {@code failedInteractions},
     * no hay información para reconciliar y se asume que todo fue exitoso.
     */
    private void reconcileInteractions(List<InteractionEntity> validInteractions, FastAiAnalysisResult aiResult) {
        if (aiResult.getAnalyzedInteractions() == null && aiResult.getFailedInteractions() == null) {
            return;
        }

        Set<String> successfulIds = new HashSet<>();
        if (aiResult.getAnalyzedInteractions() != null) {
            aiResult.getAnalyzedInteractions().forEach(a -> successfulIds.add(a.getId()));
        }

        validInteractions.forEach(i -> {
            String id = i.getId().toString();
            // Condicion : si el ID no aparece como exitoso, se marca como ERROR.
            // Cubre dos casos:
            //   - El motor lo reportó explícitamente en interacciones_fallidas.
            //   - El motor no lo reportó en interacciones_analizadas (ausente).
            if (!successfulIds.contains(id)) {
                i.markAsError();
                log.warn("Interaction {} marked as ERROR (failed or absent in AI response)", id);
            }
        });
    }

    // ---------------------------------------------------------------- OCI

    // Devuelve la ruta del objeto, o null si la subida falló (no interrumpe el flujo).
    private String uploadToOci(FastAiAnalysisResult aiResult, UUID batchId) {
        try {
            return objectStorageService.uploadJson(objectMapper.writeValueAsString(aiResult));
        } catch (Exception ex) {
            log.error("OCI upload failed for batch {}", batchId, ex);
            return null;
        }
    }

    // "oci://bucket/resultados/batch_x.json" -> "resultados/batch_x.json"
    private String toObjectName(String ociRoute) {
        int schemeEnd = ociRoute.indexOf("://");
        if (schemeEnd < 0) return ociRoute;
        int bucketEnd = ociRoute.indexOf('/', schemeEnd + 3);
        return bucketEnd < 0 ? ociRoute : ociRoute.substring(bucketEnd + 1);
    }

    // ---------------------------------------------------------------- mapeo y respuestas

    // Convierte cada DTO de entrada en una entidad, con la fuente y el periodo del lote.
    private List<InteractionEntity> toEntities(CommunityProcessRequestDto request) {
        return request.getInteractions().stream()
                .map(dto -> InteractionEntity.builder()
                        .communitySource(request.getCommunitySource())
                        .referencePeriod(request.getReferencePeriod())
                        .author(dto.getAuthor())
                        .channel(dto.getChannel())
                        .type(dto.getType())
                        .text(dto.getText())
                        .receivedAt(LocalDateTime.now())
                        .build())
                .collect(Collectors.toList());
    }

    // Respuesta cuando todas las interacciones fueron descartadas por el filtro.
    private CommunityProcessResponseDto buildEmptyResponse(List<InteractionEntity> saved, long discardedCount) {
        return CommunityProcessResponseDto.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(0)
                        .totalDiscarded((int) discardedCount)
                        .dominantSentiment("Sin contenido válido")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(null)
                .failedInteractions(List.of())
                .build();
    }

    // Respuesta 200 con status "error" para fallos inesperados.
    private CommunityProcessResponseDto buildErrorResponse(List<InteractionEntity> saved, UUID batchId, long discardedCount) {
        return CommunityProcessResponseDto.builder()
                .batchId(batchId)
                .status("error")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(0)
                        .totalDiscarded((int) discardedCount)
                        .dominantSentiment("Error al procesar con IA")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(null)
                .failedInteractions(List.of())
                .build();
    }

    // ociRoute null => almacenamiento_oci.status = "error_subida" (DEC-14).
    // status "parcial" => hay fallidas o la IA no devolvió resumen (GRUPO C).
    private CommunityProcessResponseDto buildResponse(List<InteractionEntity> saved,
                                                      FastAiAnalysisResult aiResult,
                                                      String ociRoute,
                                                      UUID batchId,
                                                      long discardedCount) {
        // 1. Determinar status: "parcial" si hay fallidos o si la IA no devolvió resumen
        boolean hasFailed = aiResult.getFailedInteractions() != null
                && !aiResult.getFailedInteractions().isEmpty();
        boolean hasSummary = aiResult.getSummary() != null;

        String status;
        if (hasFailed || !hasSummary) {
            status = "parcial";
        } else {
            status = aiResult.getStatus() != null ? aiResult.getStatus() : "exito";
        }

        // 2. Construir resumen con normalización
        CommunitySummaryDto summary = hasSummary
                ? aiResult.getSummary()
                : CommunitySummaryDto.builder()
                .totalProcessedInteractions(0)
                .dominantSentiment("pendiente")
                .mainTopics(List.of())
                .build();

        // Normalizar sentimiento + total_descartadas
        summary = CommunitySummaryDto.builder()
                .totalProcessedInteractions(summary.getTotalProcessedInteractions())
                .totalDiscarded((int) discardedCount)
                .dominantSentiment(normalizeSentiment(summary.getDominantSentiment()))
                .mainTopics(summary.getMainTopics())
                .build();

        // 3. Construir activos con normalización
        DistributionAssetsDto assets = aiResult.getDistributionAssets() != null
                ? aiResult.getDistributionAssets()
                : DistributionAssetsDto.builder().build();
        normalizeAssets(assets);

        // 4. Estado del almacenamiento: error_subida / simulado (mock) / guardado_con_exito (real)
        String storageStatus;
        if (ociRoute == null) {
            storageStatus = "error_subida";
        } else if (objectStorageService.isMockMode()) {
            storageStatus = "simulado";
        } else {
            storageStatus = "guardado_con_exito";
        }

        // Sobrescribir la info de OCI con la ruta real generada
        assets.setOciStorage(OciStorageInfoDto.builder()
                .bucket(objectStorageService.getBucket())
                .objectRoute(ociRoute)
                .status(storageStatus)
                .build());

        return CommunityProcessResponseDto.builder()
                .batchId(batchId)
                .status(status)
                .summary(summary)
                .distributionAssets(assets)
                .failedInteractions(aiResult.getFailedInteractions() != null
                        ? aiResult.getFailedInteractions()
                        : List.of())
                .build();
    }

    // ---------------------------------------------------------------- normalización (GRUPO C)

    /**
     * Normaliza el sentimiento a valores aceptados por el contrato:
     * positivo, negativo, neutral, mixto (minúsculas).
     */
    private String normalizeSentiment(String sentiment) {
        if (sentiment == null) return "neutral";
        String s = sentiment.trim().toLowerCase();
        return switch (s) {
            case "positivo", "positive" -> "positivo";
            case "negativo", "negative" -> "negativo";
            case "mixto", "mixed" -> "mixto";
            case "neutro", "neutral" -> "neutral";
            case "sin_datos", "sin datos", "no_data" -> "sin_datos";
            default -> {
                log.warn("Valor de sentimiento inesperado: '{}'. Se normaliza a 'neutral'", sentiment);
                yield "neutral";
            }
        };
    }

    /**
     * Normaliza los valores de los activos:
     * canal_recomendado → "LinkedIn Oficial" (si es LinkedIn).
     * potencial_engagement → "Alto" / "Medio" / "Bajo".
     * status FAQ → "BORRADOR".
     */
    private void normalizeAssets(DistributionAssetsDto assets) {
        if (assets.getLinkedInPost() != null) {
            LinkedInPostDto li = assets.getLinkedInPost();
            li.setRecommendedChannel(normalizeChannel(li.getRecommendedChannel()));
            li.setEngagementPotential(normalizeEngagement(li.getEngagementPotential()));
        }

        if (assets.getFaqSuggestion() != null) {
            FaqSuggestionDto faq = assets.getFaqSuggestion();
            if (faq.getStatus() == null || faq.getStatus().isBlank()) {
                faq.setStatus("BORRADOR");
            }
        }
    }

    private String normalizeChannel(String channel) {
        if (channel == null || channel.isBlank()) return "LinkedIn Oficial";
        String c = channel.trim();
        if (c.toLowerCase().contains("linkedin")) return "LinkedIn Oficial";
        return c;
    }

    private String normalizeEngagement(String engagement) {
        if (engagement == null || engagement.isBlank()) return "Medio";
        String e = engagement.trim().toLowerCase();
        return switch (e) {
            case "alto", "high" -> "Alto";
            case "bajo", "low" -> "Bajo";
            case "medio", "medium" -> "Medio";
            default -> {
                log.warn("Valor de potencial_engagement inesperado: '{}'. Se normaliza a 'Medio'", engagement);
                yield "Medio";
            }
        };
    }
}
