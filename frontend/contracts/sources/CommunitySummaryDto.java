package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class CommunitySummaryDto {

    @JsonProperty("total_interacciones_procesadas")
    private Integer totalProcessedInteractions;

    @JsonProperty("total_descartadas")
    private Integer totalDiscarded;

    @JsonProperty("sentimiento_predominante")
    private String dominantSentiment;

    @JsonProperty("temas_principales")
    private List<String> mainTopics;
}
