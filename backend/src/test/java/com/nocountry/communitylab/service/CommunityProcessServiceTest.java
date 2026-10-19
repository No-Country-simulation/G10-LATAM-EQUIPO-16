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

    private List<InteractionEntity> savedInteractions;

    @BeforeEach
    void setUp() throws Exception {
        savedInteractions = new ArrayList<>();

        when(interactionRepository.saveAll(anyList()))
                .thenAnswer(inv -> {
                    List<InteractionEntity> input = inv.getArgument(0);
                    List<InteractionEntity> copy = new ArrayList<>(input);
                    for (InteractionEntity e : copy) {
                        if (e.getId() == null) e.setId(UUID.randomUUID());
                        if (!savedInteractions.contains(e)) savedInteractions.add(e);
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

        when(objectStorageService.buildBatchRoute(anyString(), any(UUID.class)))
                .thenReturn("activos/2026-semana-42/paquete-distribucion-test.json");

        when(objectStorageService.uploadJson(anyString(), anyString()))
                .thenReturn("mock://bucket/activos/2026-semana-42/paquete-distribucion-test.json");

        when(objectMapper.writeValueAsString(any()))
                .thenReturn("{\"status\":\"exito\"}");
    }

    // ==================================================
    // Test 1 — Estado persistido: fallida en ERROR, exitosa en PROCESSED
    // ==================================================
    @Test
    void process_shouldPersistFailedAsErrorAndSuccessAsProcessed() throws Exception {
        UUID successUuid = UUID.fromString("11111111-1111-1111-1111-111111111111");
        UUID failUuid    = UUID.fromString("22222222-2222-2222-2222-222222222222");

        doAnswer(inv -> {
            List<InteractionEntity> input = inv.getArgument(0);
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

        InteractionEntity success = savedInteractions.stream()
                .filter(i -> successUuid.equals(i.getId())).findFirst()
                .orElseThrow(() -> new AssertionError("No se guardó la exitosa con UUID " + successUuid));
        InteractionEntity failed = savedInteractions.stream()
                .filter(i -> failUuid.equals(i.getId())).findFirst()
                .orElseThrow(() -> new AssertionError("No se guardó la fallida con UUID " + failUuid));

        assertEquals(InteractionStatus.PROCESSED, success.getStatus());
        assertEquals(InteractionStatus.ERROR, failed.getStatus());
    }

    // ==================================================
    // Valida status "parcial" + interacciones_fallidas en la respuesta
    // ==================================================
    @Test
    void process_shouldReturnParcialStatus_whenAiReturnsFailedInteractions() throws Exception {
        UUID successUuid = UUID.fromString("33333333-3333-3333-3333-333333333333");
        UUID failUuid    = UUID.fromString("44444444-4444-4444-4444-444444444444");

        doAnswer(inv -> {
            List<InteractionEntity> input = inv.getArgument(0);
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
                        .mainTopics(List.of())
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

        CommunityProcessResponseDto response = service.process(request);

        // validar status "parcial" + interacciones_fallidas
        assertEquals("parcial", response.getStatus());
        assertNotNull(response.getFailedInteractions());
        assertEquals(1, response.getFailedInteractions().size());
        assertEquals(failUuid.toString(), response.getFailedInteractions().get(0).getId());
    }

    // ==================================================
    // Test 2 — Normalización de activos (FIX: usando UUID real + analyzedInteractions)
    // ==================================================
    @Test
    void process_shouldNormalizeAssets() throws Exception {
        UUID validUuid = UUID.fromString("55555555-5555-5555-5555-555555555555");

        doAnswer(inv -> {
            List<InteractionEntity> input = inv.getArgument(0);
            if (input.size() == 1 && input.get(0).getId() == null) {
                input.get(0).setId(validUuid);
            }
            List<InteractionEntity> copy = new ArrayList<>(input);
            for (InteractionEntity e : copy) {
                if (!savedInteractions.contains(e)) savedInteractions.add(e);
            }
            return copy;
        }).when(interactionRepository).saveAll(anyList());

        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "logro conseguido")
        });

        // analyzedInteractions incluye el ID real de la entidad, no vacío
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
                .analyzedInteractions(List.of(
                        InteractionAnalysisDto.builder().id(validUuid.toString()).build()
                ))
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
    // Test 3 — total_descartadas (FIX: usa UUID real + analyzedInteractions)
    // ==================================================
    @Test
    void process_shouldCountDiscardedInteractions() throws Exception {
        UUID validUuid = UUID.fromString("66666666-6666-6666-6666-666666666666");

        doAnswer(inv -> {
            List<InteractionEntity> input = inv.getArgument(0);
            // El primero es el válido, los otros 2 son descartados
            if (input.size() == 3 && input.get(0).getId() == null) {
                input.get(0).setId(validUuid);
                input.get(1).setId(UUID.randomUUID());
                input.get(2).setId(UUID.randomUUID());
            }
            List<InteractionEntity> copy = new ArrayList<>(input);
            for (InteractionEntity e : copy) {
                if (!savedInteractions.contains(e)) savedInteractions.add(e);
            }
            return copy;
        }).when(interactionRepository).saveAll(anyList());

        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "válido"),
                interaction("b@test.com", ""),
                interaction("c@test.com", "   ")
        });

        // FIX (Bryan): analyzedInteractions incluye el ID real de la válida
        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("positivo")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(DistributionAssetsDto.builder().build())
                .analyzedInteractions(List.of(
                        InteractionAnalysisDto.builder().id(validUuid.toString()).build()
                ))
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