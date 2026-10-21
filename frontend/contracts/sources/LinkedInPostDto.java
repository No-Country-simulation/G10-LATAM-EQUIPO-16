package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class LinkedInPostDto {

    @JsonProperty("interaccion_id")
    private String interactionId;

    @JsonProperty("titulo")
    private String title;

    @JsonProperty("copy")
    private String copy;

    @JsonProperty("canal_recomendado")
    private String recommendedChannel;

    @JsonProperty("potencial_engagement")
    private String engagementPotential;
}
