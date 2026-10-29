package com.nocountry.communitylab.config;

import com.nocountry.communitylab.service.linkedin.LinkedInApprovalService;
import com.nocountry.communitylab.service.linkedin.LinkedInDraftTransferService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

@Configuration
public class LinkedInApprovalConfig {

    @Bean
    public LinkedInApprovalService linkedInApprovalService() {
        return new LinkedInApprovalService(Clock.systemUTC());
    }

    @Bean
    public LinkedInDraftTransferService linkedInDraftTransferService() {
        return new LinkedInDraftTransferService(Clock.systemUTC());
    }
}
