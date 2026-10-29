package com.nocountry.communitylab.config;

import com.nocountry.communitylab.CommunitylabApplication;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(
    classes = CommunitylabApplication.class,
    properties = {
        "spring.config.import=optional:classpath:/linkedin-dev-unused.properties"
    }
)
@AutoConfigureMockMvc
@ActiveProfiles("linkedin-dev")
class LinkedInReviewEndpointTest {

    @Autowired
    private MockMvc mvc;

    @Test
    void reviewIsBlockedWhenLinkedInOAuthIsDisabled() throws Exception {
        mvc.perform(get(
            "/api/v1/linkedin/approvals/example-id/review"
        )).andExpect(status().isForbidden());
    }
}
