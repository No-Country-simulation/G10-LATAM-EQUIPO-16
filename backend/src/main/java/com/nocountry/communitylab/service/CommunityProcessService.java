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
import tools.jackson.databind.ObjectMapper;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**Servicio que orquesta el procesamiento de un lote de interacciones de la comunidad.
 * Flujo: staging -> filtro conservador -> envio a IA -> almacenamiento OCI -> respuesta.
 */
@Slf4j
@Service
public class CommunityProcessService {

    private final InteractionRepository interactionRepository;
    private final ResilientAiClient resilientAiClient;
    private final DistributionBatchRepository batchRepository;
    private final OciObjectStorage ociObjectStorage;
    private final ObjectMapper objectMapper;
    private final String ociBucket;

    public CommunityProcessService(InteractionRepository interactionRepository,
        ResilientAiClient resilientAiClient,DistributionBatchRepository batchRepository, OciObjectStorage ociObjectStorage,
        ObjectMapper objectMapper, TransactionTemplate transactionTemplate, @Value("${oci.bucket:communitylab-bucket}") String ociBucket) {
        this.interactionRepository = interactionRepository;
        this.resilientAiClient = resilientAiClient;
        this.batchRepository = batchRepository;
        this.ociObjectStorage = ociObjectStorage;
        this.objectMapper = objectMapper;
        this.ociBucket = ociBucket;
    }

    // @Transactional garantiza que si falla a la mitad, no se guarden datos corruptos
        @Transactional
        public CommunityProcessResponseDto process(CommunityProcessRequestDto request) {
            log.info("Iniciando procesamiento de lote para origen: {}", request.getCommunitySource());

            // 1. Guardar el lote inicial como "PROCESANDO" en la Base de Datos
            DistributionBatch batch = DistributionBatch.builder()
                    .communitySource(request.getCommunitySource())
                    .referencePeriod(request.getReferencePeriod())
                    .status(BatchStatus.PROCESSING)
                    .ociBucket(ociBucket)
                    .build();
            batch = batchRepository.save(batch);

            // 2. Filtrar interacciones vacías y guardar todo en la Base de Datos
            List<InteractionEntity> entities = new ArrayList<>();
            if (request.getInteractions() != null) {
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

                    // Usa las reglas de negocio establecidas por el equipo en la Entidad
                    if (entity.isTriviallyEmpty()) {
                        entity.markAsDiscarded();
                    } else {
                        entity.markAsProcessing();
                    }
                    entities.add(entity);
                }
                interactionRepository.saveAll(entities);
            }

            FastAiAnalysisResult aiResult;
            try {
                // 3. Enviar a la IA usando el cliente con reintentos
                aiResult = resilientAiClient.analyzeWithRetry(request);
            } catch (Exception e) {
                // 4. Si fallan los reintentos, marcar todo como ERROR en BD y cortar el proceso
                log.error("Fallo al procesar lote en la IA tras varios intentos", e);
                batch.setStatus(BatchStatus.ERROR);
                batchRepository.save(batch);

                entities.stream()
                        .filter(i -> i.getStatus() == InteractionStatus.PROCESSING)
                        .forEach(InteractionEntity::markAsError);
                interactionRepository.saveAll(entities);

                return CommunityProcessResponseDto.builder().status("ERROR").build();
            }

            // 5. Si la IA respondió bien, guardar el resultado en OCI Storage
            String objectRoute = "activos/" + batch.getId() + "/paquete.json";
            try {
                byte[] content = objectMapper.writeValueAsBytes(aiResult);
                ociObjectStorage.putObject(ociBucket, objectRoute, content);

                // Actualizar entidades a "PROCESADAS" con la ruta del archivo
                batch.setOciObjectRoute(objectRoute);
                batch.setStatus(BatchStatus.PROCESSED);
                batchRepository.save(batch);

                entities.stream()
                        .filter(i -> i.getStatus() == InteractionStatus.PROCESSING)
                        .forEach(i -> i.markAsProcessed(objectRoute));
                interactionRepository.saveAll(entities);
            } catch (Exception e) {
                log.error("Error al persistir resultado en OCI Storage", e);
                batch.setStatus(BatchStatus.ERROR);
                batchRepository.save(batch);
            }

            // 6. Armar la bandeja (DTO) que se le entregará de vuelta al Controlador
            return CommunityProcessResponseDto.builder()
                    .status(aiResult.getStatus() != null ? aiResult.getStatus() : "PROCESSED")
                    .summary(aiResult.getSummary())
                    .distributionAssets(aiResult.getDistributionAssets())
                    .build();
        }
    }