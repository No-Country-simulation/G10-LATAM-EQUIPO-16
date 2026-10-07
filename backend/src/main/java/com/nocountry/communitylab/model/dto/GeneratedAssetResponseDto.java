package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.nocountry.communitylab.model.enums.AssetStatus;
import com.nocountry.communitylab.model.enums.AssetType;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

/** Activo generado tal como se entrega al frontend (listado y resultado de la curaduría). */
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GeneratedAssetResponseDto {

    @JsonProperty("id")
    private UUID id;

    @JsonProperty("lote_id")
    private UUID batchId;

    @JsonProperty("tipo_activo")
    private AssetType assetType;

    @JsonProperty("contenido")
    private String content;

    @JsonProperty("estado")
    private AssetStatus status;

    @JsonProperty("creado_en")
    private LocalDateTime createdAt;

    @JsonProperty("actualizado_en")
    private LocalDateTime updatedAt;
}
