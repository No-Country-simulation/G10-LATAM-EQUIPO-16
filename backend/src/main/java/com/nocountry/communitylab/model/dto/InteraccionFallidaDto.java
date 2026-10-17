package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

/**
 * Representa una interacción que el motor de IA no pudo procesar.
 * Devuelta por el servicio Python en el campo {@code interacciones_fallidas}.
 */
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
@JsonIgnoreProperties(ignoreUnknown = true)
public class InteraccionFallidaDto {

    @JsonProperty("id")
    private String id;

    @JsonProperty("motivo")
    private String reason;
}
