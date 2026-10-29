package com.nocountry.communitylab.config;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:linkedin_security_test;DB_CLOSE_DELAY=-1",
    "spring.datasource.driver-class-name=org.h2.Driver",
    "spring.datasource.username=sa",
    "spring.datasource.password=",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
    "oci.os.mode=mock"
})
@AutoConfigureMockMvc
class SecurityHttpIntegrationTest {

    @Autowired
    MockMvc mvc;

    @Test
    void saludEsPublica() throws Exception {
        mvc.perform(get("/api/v1/health"))
            .andExpect(status().isOk());
    }

    @Test
    void linkedinEstaProtegido() throws Exception {
        mvc.perform(get("/api/v1/linkedin/status"))
            .andExpect(status().isForbidden());
    }

    @Test
    void procesoNoEsBloqueadoPorCsrf() throws Exception {
        mvc.perform(post("/api/v1/community/process")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest());
    }
}
