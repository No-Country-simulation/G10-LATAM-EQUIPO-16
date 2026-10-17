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
public class NewsletterHighlightDto {

    @JsonProperty("interaccion_id")
    private String interactionId;

    @JsonProperty("seccion")
    private String section;

    @JsonProperty("titular")
    private String headline;

    @JsonProperty("resumen")
    private String summary;
}
