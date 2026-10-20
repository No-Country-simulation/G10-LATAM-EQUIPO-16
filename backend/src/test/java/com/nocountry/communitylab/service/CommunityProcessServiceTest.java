package com.nocountry.communitylab.service;

import com.nocountry.communitylab.client.ResilientAiClient;
import com.nocountry.communitylab.model.dto.*;
import com.nocountry.communitylab.model.entity.DistributionBatch;
import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.enums.BatchStatus;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import com.nocountry.communitylab.repository.DistributionBatchRepository;
import com.nocountry.communitylab.repository.InteractionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
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
    // valida el JSON enviado a uploadJson - deuda tecnica Oscar
    // FIX Se usa ObjectMapper real en lugar de StringBuilder
    // ==================================================
    @Test
    void process_shouldSendPackageWithRequiredFieldsToOci() throws Exception {
        UUID batchUuid = UUID.fromString("77777777-7777-7777-7777-777777777777");

        when(distributionBatchRepository.save(any(DistributionBatch.class)))
                .thenAnswer(inv -> {
                    DistributionBatch b = inv.getArgument(0);
                    b.setId(batchUuid);
                    return b;
                });

        // Forzamos que la ruta use el ID real que se le pasa
        when(objectStorageService.buildBatchRoute(anyString(), any(UUID.class)))
                .thenAnswer(invocation -> {
                    UUID id = invocation.getArgument(1);
                    return "activos/2026-semana-42/paquete-distribucion-" + id + ".json";
                });

        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "mensaje válido"),
                interaction("b@test.com", "")
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

        // Instanciamos un ObjectMapper real para el test
        ObjectMapper realMapper = new ObjectMapper();
        when(objectMapper.writeValueAsString(any())).thenAnswer(inv -> {
            return realMapper.writeValueAsString(inv.getArgument(0));
        });

        // Capturamos el JSON que se envía a uploadJson
        ArgumentCaptor<String> jsonCaptor = ArgumentCaptor.forClass(String.class);
        ArgumentCaptor<String> routeCaptor = ArgumentCaptor.forClass(String.class);

        service.process(request);

        verify(objectStorageService).uploadJson(jsonCaptor.capture(), routeCaptor.capture());

        String json = jsonCaptor.getValue();
        String route = routeCaptor.getValue();

        // Validar campos obligatorios del paquete
        assertTrue(json.contains("\"lote_id\":\"" + batchUuid + "\""),
                "El paquete debe incluir lote_id");
        assertTrue(json.contains("\"total_descartadas\":1"),
                "El paquete debe incluir total_descartadas = 1");
        assertTrue(json.contains("\"generado_en\":\""),
                "El paquete debe incluir generado_en (UTC)");
        assertTrue(json.contains("\"origen_comunidad\":\"Discord\""),
                "El paquete debe incluir origen_comunidad");

        // Validar la ruta: debe contener el lote_id
        assertTrue(route.contains(batchUuid.toString()),
                "La ruta OCI debe incluir el lote_id");
    }

    // ==================================================
    // Verifica el límite de 10 interacciones
    // ==================================================
    @Test
    void process_shouldRejectMoreThanTenInteractions() {
        // Creamos 11 interacciones (excede el límite)
        InteractionRequestDto[] elevenInteractions = new InteractionRequestDto[11];
        for (int i = 0; i < 11; i++) {
            elevenInteractions[i] = interaction("user" + i + "@test.com", "texto " + i);
        }

        CommunityProcessRequestDto request = CommunityProcessRequestDto.builder()
                .communitySource("Discord")
                .referencePeriod("2026-semana-42")
                .interactions(List.of(elevenInteractions))
                .build();

        // Usamos el Validator de Jakarta para probar las anotaciones del DTO directamente
        try (var factory = jakarta.validation.Validation.buildDefaultValidatorFactory()) {
            var validator = factory.getValidator();
            var violations = validator.validate(request);

            assertFalse(violations.isEmpty(), "Debería haber violaciones de validación para más de 10 interacciones");

            boolean hasSizeViolation = violations.stream()
                    .anyMatch(v -> v.getPropertyPath().toString().equals("interactions"));

            assertTrue(hasSizeViolation, "El error debe ser por el tamaño de la lista de interacciones");
        }
    }

    // ==================================================
    // Test de error de subida a OCI (DEC-14)
    // ==================================================
    @Test
    void process_shouldReturn200WithErrorSubida_whenOciUploadFails() throws Exception {
        UUID batchUuid = UUID.fromString("88888888-8888-8888-8888-888888888888");

        // 1. Simulamos que el lote se guarda con este ID
        when(distributionBatchRepository.save(any(DistributionBatch.class)))
                .thenAnswer(inv -> {
                    DistributionBatch b = inv.getArgument(0);
                    b.setId(batchUuid);
                    return b;
                });

        // 2. Simulamos la ruta de OCI (Buena práctica para evitar nulos)
        when(objectStorageService.buildBatchRoute(anyString(), any(UUID.class)))
                .thenReturn("activos/2026-semana-42/paquete-distribucion-" + batchUuid + ".json");

        CommunityProcessRequestDto request = buildRequest(new InteractionRequestDto[]{
                interaction("a@test.com", "mensaje válido")
        });

        // 3. Simulamos que la IA responde bien
        FastAiAnalysisResult aiResult = FastAiAnalysisResult.builder()
                .status("exito")
                .summary(CommunitySummaryDto.builder()
                        .totalProcessedInteractions(1)
                        .dominantSentiment("positivo")
                        .mainTopics(List.of())
                        .build())
                .distributionAssets(DistributionAssetsDto.builder().build())
                .analyzedInteractions(List.of(
                        InteractionAnalysisDto.builder().id("11111111-1111-1111-1111-111111111111").build()
                ))
                .failedInteractions(null)
                .build();

        when(resilientAiClient.analyzeWithRetry(anyList(), anyString(), anyString()))
                .thenReturn(aiResult);

        // 4. FORZAMOS EL FALLO DE OCI:
        // Hacemos que la serialización del JSON lance una excepción.
        // Esto hará que uploadToOci atrape el error y devuelva null (simulando fallo de OCI)
        when(objectMapper.writeValueAsString(any()))
                .thenThrow(new RuntimeException("Fallo simulado de OCI"));

        // 5. Ejecutamos el servicio
        CommunityProcessResponseDto response = service.process(request);

        // 6. Validaciones del contrato (DEC-14)
        // Verifica que devuelve 200 (implícito al no lanzar excepción) y status error_subida
        assertEquals("error_subida", response.getOciStorage().getStatus());

        // Verifica que los activos generados por la IA no se pierden
        assertNotNull(response.getDistributionAssets());

        // 7. Validar que el lote se guardó en estado ERROR
        verify(distributionBatchRepository, atLeastOnce()).save(argThat(b ->
                b.getStatus() == BatchStatus.ERROR
        ));

        // 8. Validar que las interacciones también se marcaron como ERROR
        verify(interactionRepository, atLeastOnce()).saveAll(argThat(list ->
                ((List<InteractionEntity>) list).stream()
                        .anyMatch(i -> i.getStatus() == InteractionStatus.ERROR)
        ));
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