package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class InteractionRequestDto {

    @JsonProperty("autor")
    @NotBlank(message = "autor es obligatorio")
    private String author;

    @JsonProperty("canal")
    @NotBlank(message = "canal es obligatorio")
    private String channel;

    @JsonProperty("tipo")
    @NotBlank(message = "tipo es obligatorio")
    private String type;

    @JsonProperty("texto")
    @NotBlank(message = "texto es obligatorio")
    private String text;
}
