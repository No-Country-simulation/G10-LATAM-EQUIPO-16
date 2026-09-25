package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class NewsletterHighlightDto {

    @JsonProperty("seccion")
    private String section;

    @JsonProperty("titular")
    private String headline;

    @JsonProperty("resumen")
    private String summary;
}
