package com.nocountry.communitylab.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import tools.jackson.databind.ObjectMapper;
import com.nocountry.communitylab.client.FastAiClient;
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
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Orquesta el procesamiento de un lote de interacciones de la comunidad.
 * Flujo: staging -> filtro conservador -> lote de distribución -> IA (con reintentos) -> OCI -> respuesta.
 *
 * <p><b>Regla de arquitectura:</b> esta clase y {@link #process} NO son {@code @Transactional}.
 * Cada llamada al repositorio es su propia transacción corta, así ninguna conexión de HikariCP
 * queda ocupada mientras esperamos a la IA o a OCI.
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
        log.info("Processing batch: source={}, period={}, interactions={}", request.getCommunitySource(), request.getReferencePeriod(), request.getInteractions() != null ? request.getInteractions().size() : 0);


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

        // 4. Filtrar las válidas para enviar a IA
        List<InteractionEntity> validInteractions = saved.stream().filter(i -> i.getStatus() == InteractionStatus.PENDING).collect(Collectors.toList());

        if (validInteractions.isEmpty()) {
            log.info("No valid interactions to send to AI (all discarded)");
            return buildEmptyResponse(saved);
        }

        // 5. Crear el DistributionBatch (lote_id) con estado PROCESSING
        DistributionBatch batch = distributionBatchRepository.save(DistributionBatch.builder()
                .communitySource(request.getCommunitySource())
                .referencePeriod(request.getReferencePeriod())
                .ociBucket(objectStorageService.getBucket())
                .status(BatchStatus.PROCESSING)
                .build());
        UUID batchId = batch.getId();

        // 6. Marcar como PROCESANDO
        validInteractions.forEach(InteractionEntity::markAsProcessing);
        interactionRepository.saveAll(validInteractions);

        // 7. Llamar a la IA SIN transacción; los reintentos están en ResilientAiClient
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
            return buildErrorResponse(saved, batchId);
        }
            //Guardar realmente el resultado de Gemini en OCI
            String ociRoute = uploadToOci(aiResult, batchId);
            // 11. Si OCI falla: ERROR en BD, pero 200 con los activos generados por la IA (DEC-14)
        if (ociRoute == null) {
            failBatch(batch, validInteractions);
            return buildResponse(request, saved, aiResult, null, batchId);
        }

        // 8. Marcar como PROCESADO con la ruta OCI
        completeBatch(batch, validInteractions, ociRoute);
        log.info("Batch {} processed: {} interactions -> {}", batchId, validInteractions.size(), ociRoute);

        // 9. Construir respuesta
        return buildResponse(request, saved, aiResult, ociRoute, batchId);
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

    // Marca interacciones como PROCESADO y el lote como PROCESSED con su ruta OCI.
    private void completeBatch(DistributionBatch batch, List<InteractionEntity> validInteractions, String ociRoute) {
        validInteractions.forEach(i -> i.markAsProcessed(ociRoute));
        interactionRepository.saveAll(validInteractions);
        // Regla PROCESSED => ociObjectRoute != null. El lote guarda solo el nombre del objeto.
        batch.setOciObjectRoute(toObjectName(ociRoute));
        batch.setStatus(BatchStatus.PROCESSED);
        distributionBatchRepository.save(batch);
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
        if (schemeEnd < 0) {
            return ociRoute;
        }
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
    private CommunityProcessResponseDto buildEmptyResponse(List<InteractionEntity> saved) {
        return CommunityProcessResponseDto.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(saved.size())
                        .dominantSentiment("Sin contenido válido")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(null)
                .build();
    }

    // Respuesta 200 con status "error" para fallos inesperados.
    private CommunityProcessResponseDto buildErrorResponse(List<InteractionEntity> saved, UUID batchId) {
        return CommunityProcessResponseDto.builder()
                .batchId(batchId)
                .status("error")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(saved.size())
                        .dominantSentiment("Error al procesar con IA")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(null)
                .build();
    }

    // ociRoute null => almacenamiento_oci.status = "error_subida" (DEC-14).
    private CommunityProcessResponseDto buildResponse(CommunityProcessRequestDto request,
                                                    List<InteractionEntity> saved,
                                                    FastAiAnalysisResult aiResult,
                                                    String ociRoute,
                                                    UUID batchId) {
        // Si la IA no devolvió resumen, construimos uno por defecto
        CommunitySummaryDto summary = aiResult.getSummary() != null
                ? aiResult.getSummary()
                : CommunitySummaryDto.builder()
                        .totalProcessedInteractions(saved.size())
                        .dominantSentiment("Pendiente de análisis IA")
                        .mainTopics(List.of())
                        .build();

        DistributionAssetsDto assets = aiResult.getDistributionAssets() != null
                ? aiResult.getDistributionAssets()
                : DistributionAssetsDto.builder().build();

        // Estado del almacenamiento: error_subida / simulado (mock) / guardado_con_exito (real)
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
                .status(aiResult.getStatus() != null ? aiResult.getStatus() : "exito")
                .summary(summary)
                .distributionAssets(assets)
                .build();
    }
}
