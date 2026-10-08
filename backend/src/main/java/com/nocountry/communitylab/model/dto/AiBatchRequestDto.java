package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AiBatchRequestDto {

    @JsonProperty("origen_comunidad")
    private String communitySource;

    @JsonProperty("periodo_referencia")
    private String referencePeriod;

    @JsonProperty("interacciones")
    private List<AiInteractionDto> interactions;
}
