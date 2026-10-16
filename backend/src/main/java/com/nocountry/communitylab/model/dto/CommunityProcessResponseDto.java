package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.UUID;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CommunityProcessResponseDto {
    
    @JsonProperty("lote_id")
    private UUID batchId;

    @JsonProperty("status")
    private String status;

    @JsonProperty("resumen_comunidad")
    private CommunitySummaryDto summary;

    @JsonProperty("activos_distribucion_generados")
    private DistributionAssetsDto distributionAssets;
}
