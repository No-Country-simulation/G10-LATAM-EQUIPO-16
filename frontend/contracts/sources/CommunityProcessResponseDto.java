package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;
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

    @JsonProperty("interacciones_fallidas")
    private List<InteraccionFallidaDto> failedInteractions;

    /**
     * Info del almacenamiento en OCI. Se expone TAMBIÉN en la raíz (DEC-11)
     * además de anidada en {@link DistributionAssetsDto}, para que el Frontend
     * pueda leerla de la raíz cuando esté lista para migrar.
     */
    @JsonProperty("almacenamiento_oci")
    private OciStorageInfoDto ociStorage;
}
