package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class FastAiAnalysisResult {

    @JsonProperty("status")
    private String status;

    @JsonProperty("resumen_comunidad")
    private CommunitySummaryDto summary;

    @JsonProperty("activos_distribucion_generados")
    private DistributionAssetsDto distributionAssets;

    @JsonProperty("interacciones_analizadas")
    private List<InteractionAnalysisDto> analyzedInteractions;

    /**
     * mock de respaldo mientras el servicio python no esta disponible.
     */
    public static FastAiAnalysisResult mock() {
        return FastAiAnalysisResult.builder()
                .status("mock_processed")
                .summary(null)
                .distributionAssets(null)
                .analyzedInteractions(null)
                .build();
    }
}
