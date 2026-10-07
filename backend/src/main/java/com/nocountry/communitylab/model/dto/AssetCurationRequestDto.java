package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.nocountry.communitylab.model.enums.AssetStatus;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.*;

/** Cuerpo del PATCH de curaduría enviado por el frontend. */
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AssetCurationRequestDto {

    @NotNull(message = "El nuevo estado es obligatorio")
    @JsonProperty("nuevo_estado")
    private AssetStatus newStatus;

    /** Opcional. Obligatorio si nuevo_estado es EDITED (regla validada en el servicio). */
    @Size(max = 20000, message = "El contenido no puede superar los 20000 caracteres")
    @JsonProperty("contenido")
    private String content;

    @NotBlank(message = "Las notas del revisor son obligatorias")
    @Size(max = 1000, message = "Las notas del revisor no pueden superar los 1000 caracteres")
    @JsonProperty("notas_revisor")
    private String reviewerNotes;
}
