package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

import java.util.List;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class CommunitySummaryDto {

    @JsonProperty("total_interacciones_procesadas")
    private Integer totalProcessedInteractions;

    @JsonProperty("sentimiento_predominante")
    private String dominantSentiment;

    @JsonProperty("temas_principales")
    private List<String> mainTopics;
}
