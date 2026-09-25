package com.nocountry.communitylab.model.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.*;

@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class DistributionAssetsDto {

    @JsonProperty("post_linkedin")
    private LinkedInPostDto linkedInPost;

    @JsonProperty("destaque_newsletter_semanal")
    private NewsletterHighlightDto newsletterHighlight;

    @JsonProperty("sugerencia_contenido_faq")
    private FaqSuggestionDto faqSuggestion;

    @JsonProperty("almacenamiento_oci")
    private OciStorageInfoDto ociStorage;
}
