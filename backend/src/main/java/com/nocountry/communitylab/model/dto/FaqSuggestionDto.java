package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class FaqSuggestionDto {

    @JsonProperty("tema")
    private String topic;

    @JsonProperty("origen")
    private String origin;

    @JsonProperty("status")
    private String status;
}
