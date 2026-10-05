package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.FastAiClient;
import com.nocountry.communitylab.exception.AiServiceException;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import com.nocountry.communitylab.repository.InteractionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Servicio que orquesta el procesamiento de un lote de interacciones de la comunidad.
 * Flujo: staging -> filtro conservador -> envio a IA -> almacenamiento OCI -> respuesta.
 */

@Service
public class CommunityProcessService {

    private static final Logger log = LoggerFactory.getLogger(CommunityProcessService.class);

    private final InteractionRepository interactionRepository;
    private final FastAiClient fastAiClient;

    public CommunityProcessService(InteractionRepository interactionRepository, FastAiClient fastAiClient) {
        this.interactionRepository = interactionRepository;
        this.fastAiClient = fastAiClient;
    }


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

        // 5. Marcar como PROCESANDO
        validInteractions.forEach(InteractionEntity::markAsProcessing);
        interactionRepository.saveAll(validInteractions);

        // 6. Llamar a la IA
        FastAiAnalysisResult aiResult;
        try {
            aiResult = fastAiClient.analyzeBatch(
                    validInteractions,
                    request.getCommunitySource(),
                    request.getReferencePeriod()
            );
        } catch (AiServiceException ex) {
            // Fallo del servicio IA: marcar interacciones como ERROR y PROPAGAR para que el
            // GlobalExceptionHandler responda 503 y el frontend pueda reintentar.
            log.error("AI service failed, marking interactions as ERROR: {}", ex.getMessage(), ex);
            validInteractions.forEach(InteractionEntity::markAsError);
            interactionRepository.saveAll(validInteractions);
            throw ex;
        } catch (Exception ex) {
            // Otros errores inesperados (BD, NPE, etc.): se reportan como 200 + status "error"
            log.error("Unexpected error processing batch, marking interactions as ERROR", ex);
            validInteractions.forEach(InteractionEntity::markAsError);
            interactionRepository.saveAll(validInteractions);
            return buildErrorResponse(saved);
        }
            // 7. Simular almacenamiento en OCI (por ahora)
            String ociRoute = "oci://community-bucket/batch_" + UUID.randomUUID() + ".json";

            // 8. Marcar como PROCESADO
            validInteractions.forEach(i -> i.markAsProcessed(ociRoute));
            interactionRepository.saveAll(validInteractions);

            log.info("Batch processed successfully: {} interactions -> {}", validInteractions.size(), ociRoute);

            // 9. Construir respuesta
            return buildResponse(request, saved, aiResult, ociRoute);
    }

    // helpers
    private List<InteractionEntity> toEntities(CommunityProcessRequestDto request) {
        return request.getInteractions().stream().map(dto -> InteractionEntity.builder().id(UUID.randomUUID()).communitySource(request.getCommunitySource()).referencePeriod(request.getReferencePeriod()).author(dto.getAuthor()).channel(dto.getChannel()).type(dto.getType()).text(dto.getText()).receivedAt(LocalDateTime.now()).build()).collect(Collectors.toList());
    }

    private CommunityProcessResponseDto buildEmptyResponse(List<InteractionEntity> saved) {
        return CommunityProcessResponseDto.builder().status("exito").summary(CommunitySummaryDto.builder().totalProcessedInteractions(saved.size()).dominantSentiment("Sin contenido válido").mainTopics(List.of()).build()).distributionAssets(null).build();
    }

    private CommunityProcessResponseDto buildErrorResponse(List<InteractionEntity> saved) {
        return CommunityProcessResponseDto.builder().status("error").summary(CommunitySummaryDto.builder().totalProcessedInteractions(saved.size()).dominantSentiment("Error al procesar con IA").mainTopics(List.of()).build()).distributionAssets(null).build();
    }

    private CommunityProcessResponseDto buildResponse(CommunityProcessRequestDto request, List<InteractionEntity> saved, FastAiAnalysisResult aiResult, String ociRoute) {
        // Si la IA devuelve mock, construimos una respuesta con valores por defecto
        CommunitySummaryDto summary = aiResult.getSummary() != null ? aiResult.getSummary() : CommunitySummaryDto.builder().totalProcessedInteractions(saved.size()).dominantSentiment("Pendiente de análisis IA").mainTopics(List.of()).build();

        DistributionAssetsDto assets = aiResult.getDistributionAssets() != null ? aiResult.getDistributionAssets() : DistributionAssetsDto.builder().build();

        // Sobrescribir la info de OCI con la ruta real generada
        assets.setOciStorage(OciStorageInfoDto.builder().bucket("community-bucket").objectRoute(ociRoute).status("guardado_con_exito").build());

        return CommunityProcessResponseDto.builder().status(aiResult.getStatus() != null ? aiResult.getStatus() : "exito").summary(summary).distributionAssets(assets).build();
    }
}
