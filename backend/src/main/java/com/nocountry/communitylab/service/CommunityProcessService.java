package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.FastAiClient;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.InteraccionCruda;
import com.nocountry.communitylab.model.enums.EstadoInteraccion;
import com.nocountry.communitylab.repository.InteraccionCrudaRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

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

    private final InteraccionCrudaRepository interactionRepository;
    private final FastAiClient fastAiClient;

    public CommunityProcessService(InteraccionCrudaRepository interactionRepository,
                                   FastAiClient fastAiClient) {
        this.interactionRepository = interactionRepository;
        this.fastAiClient = fastAiClient;
    }

    @Transactional
    public CommunityProcessResponseDto process(CommunityProcessRequestDto request) {
        log.info("Processing batch: source={}, period={}, interactions={}",
                request.getCommunitySource(),
                request.getReferencePeriod(),
                request.getInteractions() != null ? request.getInteractions().size() : 0);

        // 1. Convertir DTOs a entidades de dominio
        List<InteraccionCruda> interactions = toEntities(request);

        // 2. Aplicar filtro conservador (marcar DESCARTADO si es trivialmente vacía)
        for (InteraccionCruda interaction : interactions) {
            if (interaction.esTrivialmenteVacia()) {
                interaction.marcarComoDescartada();
            } else {
                interaction.setStatus(EstadoInteraccion.PENDIENTE);
            }
        }

        // 3. Guardar todas en BD (staging)
        List<InteraccionCruda> saved = interactionRepository.saveAll(interactions);

        // 4. Filtrar las válidas para enviar a IA
        List<InteraccionCruda> validInteractions = saved.stream()
                .filter(i -> i.getStatus() == EstadoInteraccion.PENDIENTE)
                .collect(Collectors.toList());

        if (validInteractions.isEmpty()) {
            log.info("No valid interactions to send to AI (all discarded)");
            return buildEmptyResponse(saved);
        }

        // 5. Marcar como PROCESANDO
        validInteractions.forEach(InteraccionCruda::marcarComoProcesando);
        interactionRepository.saveAll(validInteractions);

        // 6. Llamar a la IA
        FastAiAnalysisResult aiResult;
        try {
            aiResult = fastAiClient.analyzeBatch(validInteractions);

            // 7. Simular almacenamiento en OCI (por ahora)
            String ociRoute = "oci://community-bucket/batch_" + UUID.randomUUID() + ".json";

            // 8. Marcar como PROCESADO
            validInteractions.forEach(i -> i.marcarComoProcesada(ociRoute));
            interactionRepository.saveAll(validInteractions);

            log.info("Batch processed successfully: {} interactions -> {}", validInteractions.size(), ociRoute);

            // 9. Construir respuesta
            return buildResponse(request, saved, aiResult, ociRoute);

        } catch (Exception ex) {
            log.error("Error processing batch, marking interactions as ERROR", ex);
            validInteractions.forEach(InteraccionCruda::marcarComoError);
            interactionRepository.saveAll(validInteractions);
            throw new RuntimeException("Error processing community batch", ex);
        }
    }


    // helpers

    private List<InteraccionCruda> toEntities(CommunityProcessRequestDto request) {
        return request.getInteractions().stream()
                .map(dto -> InteraccionCruda.builder()
                        .id(UUID.randomUUID())
                        .communitySource(request.getCommunitySource())
                        .referencePeriod(request.getReferencePeriod())
                        .autor(dto.getAuthor())
                        .canal(dto.getChannel())
                        .tipo(dto.getType())
                        .text(dto.getText())
                        .receivedAt(LocalDateTime.now())
                        .build())
                .collect(Collectors.toList());
    }

    private CommunityProcessResponseDto buildEmptyResponse(List<InteraccionCruda> saved) {
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

    private CommunityProcessResponseDto buildResponse(CommunityProcessRequestDto request,
                                                      List<InteraccionCruda> saved,
                                                      FastAiAnalysisResult aiResult,
                                                      String ociRoute) {
        // Si la IA devuelve mock, construimos una respuesta con valores por defecto
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

        // Sobrescribir la info de OCI con la ruta real generada
        assets.setOciStorage(OciStorageInfoDto.builder()
                .bucket("community-bucket")
                .objectRoute(ociRoute)
                .status("guardado_con_exito")
                .build());

        return CommunityProcessResponseDto.builder()
                .status(aiResult.getStatus() != null ? aiResult.getStatus() : "exito")
                .summary(summary)
                .distributionAssets(assets)
                .build();
    }
}
