package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CommunityProcessRequestDto {
    @JsonProperty("origen_comunidad")
    @NotBlank(message = "origen_comunidad es obligatorio")
    private String communitySource;

    @JsonProperty("periodo_referencia")
    @NotBlank(message = "periodo_referencia es obligatorio")
    private String referencePeriod;

    @JsonProperty("interacciones")
    @NotEmpty(message = "El lote debe tener al menos una interacción")
    @Size(min = 1, max = 10, message = "El lote debe tener entre 1 y 10 interacciones")
    private List<InteractionRequestDto> interactions;
}
