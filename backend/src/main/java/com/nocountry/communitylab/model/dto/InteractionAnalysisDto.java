package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class InteractionAnalysisDto {

    @JsonProperty("id")
    private String id;

    @JsonProperty("sentimiento")
    private String sentiment;

    @JsonProperty("tema")
    private String topic;

    @JsonProperty("tipo")
    private String type;

    @JsonProperty("relevancia")
    private String relevance;

    @JsonProperty("insight")
    private String insight;
}
