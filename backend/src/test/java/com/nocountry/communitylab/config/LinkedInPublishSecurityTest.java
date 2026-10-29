package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties",
    "spring.datasource.url=jdbc:h2:mem:linkedin_publish_security;DB_CLOSE_DELAY=-1",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "oci.os.mode=mock"
})
@org.springframework.test.context.ActiveProfiles("linkedin-dev")
@AutoConfigureMockMvc
class LinkedInPublishSecurityTest {

    @Autowired
    MockMvc mvc;

    @Test
    void publicarSinAutorizacionEsRechazado() throws Exception {
        mvc.perform(post("/api/v1/linkedin/publish")
                .contentType("application/json")
                .content("{\"text\":\"Publicación de prueba\"}"))
            .andExpect(status().isForbidden());
    }
}
