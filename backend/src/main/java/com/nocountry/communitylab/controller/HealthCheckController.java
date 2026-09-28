package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.model.dto.MensajeRespuestaDTO;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/health")
public class HealthCheckController {

    @GetMapping
    public ResponseEntity<MensajeRespuestaDTO> verificarEstado() {
        MensajeRespuestaDTO respuesta = new MensajeRespuestaDTO("OK", "El backend en Java está operativo.");
        return ResponseEntity.ok(respuesta);
    }
}
