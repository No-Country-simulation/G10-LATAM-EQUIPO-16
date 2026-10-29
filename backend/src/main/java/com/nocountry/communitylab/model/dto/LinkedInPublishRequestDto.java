package com.nocountry.communitylab.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record LinkedInPublishRequestDto(

    @NotBlank
    String approvalId,

    @NotBlank
    String confirmationToken,

    @NotBlank
    @Size(max = 128)
    String idempotencyKey

) {}
