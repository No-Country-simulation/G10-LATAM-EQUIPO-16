package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.DistributionBatch;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import com.nocountry.communitylab.repository.DistributionBatchRepository;
import com.nocountry.communitylab.repository.InteractionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mockito.junit.jupiter.MockitoSettings;
import org.mockito.quality.Strictness;
import tools.jackson.databind.ObjectMapper;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
@MockitoSettings(strictness = Strictness.LENIENT)
class CommunityProcessServiceTest {

    @Mock private InteractionRepository interactionRepository;
    @Mock private DistributionBatchRepository distributionBatchRepository;
    @Mock private ResilientAiClient resilientAiClient;
    @Mock private OciObjectStorageService objectStorageService;
    @Mock private ObjectMapper objectMapper;

    @InjectMocks private CommunityProcessService service;

    /** captuta las entidades que se han guardado para validar su estado persistido. */
    private List<InteractionEntity> savedInteractions;

    @BeforeEach
    void setUp() throws Exception {
        savedInteractions = new ArrayList<>();

        // Simula saveAll: asigna UUIDs y guarda las entidades
        when(interactionRepository.saveAll(anyList()))
                .thenAnswer(inv -> {
                    List<InteractionEntity> input = inv.getArgument(0);
                    List<InteractionEntity> copy = new ArrayList<>(input);
                    for (InteractionEntity e : copy) {
                        if (e.getId() == null) e.setId(UUID.randomUUID());
                        if (!savedInteractions.contains(e)) {
                            savedInteractions.add(e);
                        }
                    }
                    return copy;
                });

        when(distributionBatchRepository.save(any(DistributionBatch.class)))
                .thenAnswer(inv -> {
                    DistributionBatch b = inv.getArgument(0);
                    if (b.getId() == null) b.setId(UUID.randomUUID());
                    return b;
                });

        when(objectStorageService.getBucket()).thenReturn("communitylab-test");
        when(objectStorageService.isMockMode()).thenReturn(true);
        when(objectStorageService.uploadJson(anyString()))
                .thenReturn("mock://bucket/resultados/batch_x.json");

        when(objectMapper.writeValueAsString(any()))
                .thenReturn("{\"status\":\"exito\"}");
    }

    // ==================================================
    // Test 1 — Estado persistido: fallida en ERROR, exitosa en PROCESSED
    // ==================================================
    @Test
    void process_shouldPersistFailedAsErrorAndSuccessAsProcessed() throws Exception {
        // UUIDs predecibles: la primera interacción será la exitosa, la segunda la fallida
        UUID successUuid = UUID.fromString("11111111-1111-1111-1111-111111111111");
        UUID failUuid    = UUID.fromString("22222222-2222-2222-2222-222222222222");

        // forzamos que las entidades creadas por el service reciban los UUIDs ANTES de guardarse
        doAnswer(inv -> {
            List<InteractionEntity> input = inv.getArgument(0);
            // Solo aplicamos en el primer saveAll (staging); los demás conservan sus UUIDs
            if (input.size() == 2 && input.get(0).getId() == null) {
                input.get(0).setId(successUuid);
                input.get(1).setId(failUuid);
            }
            List<InteractionEntity> copy = new ArrayList<>(input);
            for (InteractionEntity e : copy) {
                if (!savedInteractions.contains(e)) savedInteractions.add(e);
            }
            return copy;
        }).when(interactionRepository).saveAll(anyList());

        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "mensaje exitoso"),
                interaction("b@test.com", "mensaje fallido")
        });

        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("positivo")
                        .mainTopics(List.of("empleabilidad"))
                        .build())
                .distributionAssets(DistributionAssetsDto.builder().build())
                .analyzedInteractions(List.of(
                        InteractionAnalysisDto.builder().id(successUuid.toString()).build()
                ))
                .failedInteractions(List.of(
                        InteraccionFallidaDto.builder().id(failUuid.toString()).reason("No procesada").build()
                ))
                .build();

        when(resilientAiClient.analyzeWithRetry(anyList(), anyString(), anyString()))
                .thenReturn(aiResult);

        service.process(request);

        // Verificar estado persistido
        InteractionEntity success = savedInteractions.stream()
                .filter(i -> successUuid.equals(i.getId())).findFirst()
                .orElseThrow(() -> new AssertionError("No se guardó la interacción exitosa con UUID " + successUuid));
        InteractionEntity failed = savedInteractions.stream()
                .filter(i -> failUuid.equals(i.getId())).findFirst()
                .orElseThrow(() -> new AssertionError("No se guardó la interacción fallida con UUID " + failUuid));

        assertEquals(InteractionStatus.PROCESSED, success.getStatus(),
                "La interacción exitosa debe quedar en PROCESSED");
        assertEquals(InteractionStatus.ERROR, failed.getStatus(),
                "La interacción fallida debe quedar en ERROR (no PROCESSED)");
    }

    // ==================================================
    // Test 2 — Normalización de activos
    // ==================================================
    @Test
    void process_shouldNormalizeAssets() throws Exception {
        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "logro conseguido")
        });

        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("POSITIVE")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(DistributionAssetsDto.builder()
                        .linkedInPost(LinkedInPostDto.builder()
                                .title("t").copy("c")
                                .recommendedChannel("LinkedIn")
                                .engagementPotential("high")
                                .build())
                        .build())
                .analyzedInteractions(List.of())
                .failedInteractions(null)
                .build();

        when(resilientAiClient.analyzeWithRetry(anyList(), anyString(), anyString()))
                .thenReturn(aiResult);

        CommunityProcessResponseDto response = service.process(request);

        assertEquals("positivo", response.getSummary().getDominantSentiment());
        assertEquals("LinkedIn Oficial",
                response.getDistributionAssets().getLinkedInPost().getRecommendedChannel());
        assertEquals("Alto",
                response.getDistributionAssets().getLinkedInPost().getEngagementPotential());
    }

    // ==================================================
    // Test 3 — total_descartadas
    // ==================================================
    @Test
    void process_shouldCountDiscardedInteractions() throws Exception {
        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "válido"),
                interaction("b@test.com", ""),
                interaction("c@test.com", "   ")
        });

        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("positivo")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(DistributionAssetsDto.builder().build())
                .analyzedInteractions(List.of())
                .failedInteractions(null)
                .build();

        when(resilientAiClient.analyzeWithRetry(anyList(), anyString(), anyString()))
                .thenReturn(aiResult);

        CommunityProcessResponseDto response = service.process(request);

        assertEquals(2, response.getSummary().getTotalDiscarded());
    }

    // ==================================================
    // Helpers
    // ==================================================

    private CommunityProcessRequestDto buildRequest(InteractionRequestDto[] items) {
        return CommunityProcessRequestDto.builder()
                .communitySource("Discord")
                .referencePeriod("2026-semana-42")
                .interactions(List.of(items))
                .build();
    }

    private InteractionRequestDto interaction(String author, String text) {
        return InteractionRequestDto.builder()
                .author(author).channel("#general").type("mensaje").text(text).build();
    }
}