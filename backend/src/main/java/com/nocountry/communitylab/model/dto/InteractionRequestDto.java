package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class InteractionRequestDto {

    @JsonProperty("autor")
    private String author;

    @JsonProperty("canal")
    private String channel;

    @JsonProperty("tipo")
    private String type;

    @JsonProperty("texto")
    private String text;
}
