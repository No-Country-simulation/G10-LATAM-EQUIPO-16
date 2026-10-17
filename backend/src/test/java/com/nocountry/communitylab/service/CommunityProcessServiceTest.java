package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.DistributionBatch;
import com.nocountry.communitylab.model.entity.InteractionEntity;
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

    @Mock
    private InteractionRepository interactionRepository;

    @Mock
    private DistributionBatchRepository distributionBatchRepository;

    @Mock
    private ResilientAiClient resilientAiClient;

    @Mock
    private OciObjectStorageService objectStorageService;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private CommunityProcessService service;

    @BeforeEach
    void setUp() throws Exception {
        // saveAll devuelve la lista con IDs generados
        when(interactionRepository.saveAll(anyList()))
                .thenAnswer(inv -> {
                    List<InteractionEntity> input = inv.getArgument(0);
                    List<InteractionEntity> result = new ArrayList<>();
                    for (InteractionEntity e : input) {
                        if (e.getId() == null) e.setId(UUID.randomUUID());
                        result.add(e);
                    }
                    return result;
                });

        // save del batch le asigna UUID
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
    // Test 1 — Caso "parcial" con interacciones fallidas
    // ==================================================
    @Test
    void process_shouldReturnParcial_whenAiReturnsFailedInteractions() throws Exception {
        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "primer mensaje"),
                interaction("b@test.com", "segundo mensaje")
        });

        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("positivo")
                        .mainTopics(List.of("empleabilidad"))
                        .build())
                .distributionAssets(DistributionAssetsDto.builder()
                        .linkedInPost(LinkedInPostDto.builder()
                                .title("Logro")
                                .copy("Copy del post")
                                .recommendedChannel("LinkedIn")
                                .engagementPotential("high")
                                .build())
                        .build())
                .analyzedInteractions(List.of(
                        InteractionAnalysisDto.builder().id("id-ok").build()
                ))
                .failedInteractions(List.of(
                        InteraccionFallidaDto.builder().id("id-fail").reason("No procesada").build()
                ))
                .build();

        when(resilientAiClient.analyzeWithRetry(anyList(), anyString(), anyString()))
                .thenReturn(aiResult);

        CommunityProcessResponseDto response = service.process(request);

        assertEquals("parcial", response.getStatus());
        assertEquals(1, response.getSummary().getTotalProcessedInteractions());
        assertEquals(0, response.getSummary().getTotalDiscarded());
        assertNotNull(response.getFailedInteractions());
        assertEquals(1, response.getFailedInteractions().size());
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
                                .title("t")
                                .copy("c")
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
    // Test 3 — total_descartadas contado correctamente
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
                .author(author)
                .channel("#general")
                .type("mensaje")
                .text(text)
                .build();
    }
}