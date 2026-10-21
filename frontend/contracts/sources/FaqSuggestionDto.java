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
public class FaqSuggestionDto {

    @JsonProperty("interaccion_id")
    private String interactionId;

    @JsonProperty("tema")
    private String topic;

    @JsonProperty("origen")
    private String origin;

    @JsonProperty("pregunta")
    private String question;

    @JsonProperty("respuesta")
    private String answer;

    @JsonProperty("status")
    private String status;
}
