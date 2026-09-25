package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.model.dto.CommunityProcessRequestDto;
import com.nocountry.communitylab.model.dto.CommunityProcessResponseDto;
import com.nocountry.communitylab.service.CommunityProcessService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/community")
public class CommunityController {
    private final CommunityProcessService communityProcessService;

    public CommunityController(CommunityProcessService communityProcessService) {
        this.communityProcessService = communityProcessService;
    }

    //Procesa un lote de interacciones y devuelve el resumen y los activos generados.
    @PostMapping("/process")
    public ResponseEntity<CommunityProcessResponseDto> processCommunityBatch(
            @RequestBody CommunityProcessRequestDto request) {
        CommunityProcessResponseDto response = communityProcessService.process(request);
        return ResponseEntity.ok(response);
    }
}
