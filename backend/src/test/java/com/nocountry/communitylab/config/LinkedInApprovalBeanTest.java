package com.nocountry.communitylab.config;

import com.nocountry.communitylab.service.linkedin.LinkedInApprovalService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.ApplicationContext;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("linkedin-dev")
@TestPropertySource(properties = {
    "spring.config.import=optional:classpath:/linkedin-dev-unused.properties"
})
class LinkedInApprovalBeanTest {

    @Autowired
    private LinkedInApprovalService approvalService;

    @Autowired
    private ApplicationContext applicationContext;

    @Test
    void servicioEsUnBeanSingleton() {
        assertNotNull(approvalService);

        LinkedInApprovalService secondReference =
            applicationContext.getBean(LinkedInApprovalService.class);

        assertSame(approvalService, secondReference);
    }

    @Test
    void aprobacionEstaVinculadaASesionEIdentidad() {
        var approval = approvalService.create(
            "sesion-prueba-bean",
            "linkedin-user-A",
            "Contenido de prueba de Aigoraweave"
        );

        assertNotNull(approval);

        assertNotNull(approvalService.findForSession(
            approval.approvalId(),
            "sesion-prueba-bean",
            "linkedin-user-A"
        ));

        assertNull(approvalService.findForSession(
            approval.approvalId(),
            "sesion-prueba-bean",
            "linkedin-user-B"
        ));

        assertNull(approvalService.findForSession(
            approval.approvalId(),
            "otra-sesion",
            "linkedin-user-A"
        ));
    }
}
