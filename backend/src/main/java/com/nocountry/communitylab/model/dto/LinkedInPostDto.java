package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class LinkedInPostDto {

    @JsonProperty("titulo")
    private String title;

    @JsonProperty("copy")
    private String copy;

    @JsonProperty("canal_recomendado")
    private String recommendedChannel;

    @JsonProperty("potencial_engagement")
    private String engagementPotential;
}
