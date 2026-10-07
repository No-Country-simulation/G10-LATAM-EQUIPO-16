package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.DistributionBatch;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.enums.BatchStatus;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import com.nocountry.communitylab.repository.DistributionBatchRepository;
import com.nocountry.communitylab.repository.InteractionRepository;
import com.nocountry.communitylab.storage.OciObjectStorage;
import lombok.extern.slf4j.Slf4j;
import com.fasterxml.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**Servicio que orquesta el procesamiento de un lote de interacciones de la comunidad.
 * Flujo: staging -> filtro conservador -> envio a IA -> almacenamiento OCI -> respuesta.
 */
@Slf4j
@Service
public class CommunityProcessService {

    private final InteractionRepository interactionRepository;
    private final DistributionBatchRepository batchRepository;
    private final ResilientAiClient resilientAiClient;
    private final OciObjectStorage ociObjectStorage;
    private final ObjectMapper objectMapper;
    private final String ociBucket;

    public CommunityProcessService(InteractionRepository interactionRepository,
                                DistributionBatchRepository batchRepository,
                                ResilientAiClient resilientAiClient,
                                OciObjectStorage ociObjectStorage,
                                ObjectMapper objectMapper,
                                @Value("${oci.bucket:communitylab-bucket}") String ociBucket) {
        this.interactionRepository = interactionRepository;
        this.batchRepository = batchRepository;
        this.resilientAiClient = resilientAiClient;
        this.ociObjectStorage = ociObjectStorage;
        this.objectMapper = objectMapper;
        this.ociBucket = ociBucket;
    }

    /**
     * @throws com.nocountry.communitylab.exception.AiServiceException si la IA falla (tras los reintentos
     *         si era un fallo transitorio); el estado ya fue restaurado a PENDING cuando se relanza
     * @throws IllegalArgumentException si faltan la fuente o el periodo
     */
    public CommunityProcessResponseDto process(CommunityProcessRequestDto request) {
        validate(request);
        String communitySource = request.getCommunitySource();
        String referencePeriod = request.getReferencePeriod();
        log.info("Iniciando procesamiento de lote para origen: {}", communitySource);

        // a) y b) Filtro conservador (vacías -> DISCARDED, válidas -> PENDING) y guardado
        List<InteractionEntity> entities = saveFilteredInteractions(request);

        // c) Las válidas (PENDING) pasan a PROCESSING y se guardan de inmediato
        List<InteractionEntity> validInteractions = markValidAsProcessing(entities);
        if (validInteractions.isEmpty()) {
            log.warn("Ninguna de las {} interacciones recibidas es procesable; no se invoca a la IA", entities.size());
            return CommunityProcessResponseDto.builder().status("DISCARDED").build();
        }

        // d) Lote en PROCESSING
        DistributionBatch batch = batchRepository.save(DistributionBatch.builder()
                .communitySource(communitySource)
                .referencePeriod(referencePeriod)
                .ociBucket(ociBucket)
                .status(BatchStatus.PROCESSING)
                .build());

        // e) y f) Llamada a la IA con reintentos; si falla, fallback y se relanza
        FastAiAnalysisResult aiResult;
        try {
            aiResult = resilientAiClient.analyzeWithRetry(validInteractions, communitySource, referencePeriod);
        } catch (RuntimeException e) { // AiServiceUnavailableException, AiServiceException o cualquier fallo inesperado
            log.error("Lote {}: falló la IA. Restaurando interacciones a PENDING", batch.getId(), e);
            try {
                restoreAfterAiFailure(batch, validInteractions);
            } catch (RuntimeException restoreError) {
                log.error("Lote {}: NO se pudo restaurar el estado; revisar manualmente", batch.getId(), restoreError);
                e.addSuppressed(restoreError);
            }
            throw e;
        }

        // g) Éxito: OCI y estados finales
        return completeBatch(batch, validInteractions, aiResult);
    }

    /** Crea las entidades (PENDING), descarta las vacías y guarda todo. */
    private List<InteractionEntity> saveFilteredInteractions(CommunityProcessRequestDto request) {
        List<InteractionEntity> entities = new ArrayList<>();
        for (InteractionRequestDto dto : request.getInteractions()) {
            InteractionEntity entity = InteractionEntity.builder()
                    .communitySource(request.getCommunitySource())
                    .referencePeriod(request.getReferencePeriod())
                    .author(dto.getAuthor())
                    .channel(dto.getChannel())
                    .type(dto.getType())
                    .text(dto.getText())
                    .receivedAt(LocalDateTime.now())
                    .status(InteractionStatus.PENDING)
                    .build();
            if (entity.isTriviallyEmpty()) {
                entity.markAsDiscarded();
            }
            entities.add(entity);
        }
        return interactionRepository.saveAll(entities);
    }

    private List<InteractionEntity> markValidAsProcessing(List<InteractionEntity> entities) {
        List<InteractionEntity> valid = entities.stream()
                .filter(i -> i.getStatus() == InteractionStatus.PENDING)
                .toList();
        valid.forEach(InteractionEntity::markAsProcessing);
        return interactionRepository.saveAll(valid);
    }

    /** Fallback: PROCESSING -> PENDING para no perder registros; el lote queda en ERROR. */
    private void restoreAfterAiFailure(DistributionBatch batch, List<InteractionEntity> validInteractions) {
        validInteractions.stream()
                .filter(i -> i.getStatus() == InteractionStatus.PROCESSING)
                .forEach(i -> i.setStatus(InteractionStatus.PENDING));
        interactionRepository.saveAll(validInteractions);

        batch.setStatus(BatchStatus.ERROR);
        batchRepository.save(batch);
    }

    /** Sube el JSON a OCI y fija los estados finales. Si OCI falla, lote e interacciones quedan en ERROR. */
    private CommunityProcessResponseDto completeBatch(DistributionBatch batch,
                                                    List<InteractionEntity> validInteractions,
                                                    FastAiAnalysisResult aiResult) {
        String objectRoute = uploadToOci(batch.getId(), aiResult);
        boolean uploaded = objectRoute != null;

        batch.setOciObjectRoute(objectRoute);
        batch.setStatus(uploaded ? BatchStatus.PROCESSED : BatchStatus.ERROR);
        batchRepository.save(batch);

        validInteractions.forEach(i -> {
            if (uploaded) {
                i.markAsProcessed(objectRoute);
            } else {
                i.markAsError();
            }
        });
        interactionRepository.saveAll(validInteractions);

        log.info("Lote {} finalizado en {} ({} interacciones)", batch.getId(), batch.getStatus(), validInteractions.size());
        return CommunityProcessResponseDto.builder()
                .status(aiResult.getStatus() != null ? aiResult.getStatus() : "PROCESSED")
                .summary(aiResult.getSummary())
                .distributionAssets(aiResult.getDistributionAssets())
                .build();
    }

    /** @return la ruta del objeto dentro del bucket, o {@code null} si la subida falló. */
    private String uploadToOci(UUID batchId, FastAiAnalysisResult aiResult) {
        String objectRoute = "activos/" + batchId + "/paquete.json";
        try {
            ociObjectStorage.putObject(ociBucket, objectRoute, objectMapper.writeValueAsBytes(aiResult));
            log.info("Lote {}: resultado guardado en oci://{}/{}", batchId, ociBucket, objectRoute);
            return objectRoute;
        } catch (Exception e) {
            log.error("Lote {}: no se pudo guardar el resultado en OCI", batchId, e);
            return null;
        }
    }

    private void validate(CommunityProcessRequestDto request) {
        if (request.getCommunitySource() == null || request.getCommunitySource().isBlank()
                || request.getReferencePeriod() == null || request.getReferencePeriod().isBlank()
                || request.getInteractions() == null) {
            throw new IllegalArgumentException("origen_comunidad, periodo_referencia e interacciones son obligatorios");
        }
    }
}
