package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class OciStorageInfoDto {

    @JsonProperty("bucket")
    private String bucket;

    @JsonProperty("ruta_objeto")
    private String objectRoute;

    @JsonProperty("status")
    private String status;
}
