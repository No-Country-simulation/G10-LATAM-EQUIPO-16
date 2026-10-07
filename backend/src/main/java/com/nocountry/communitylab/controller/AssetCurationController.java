package com.nocountry.communitylab.controller;

import com.nocountry.communitylab.model.dto.AssetCurationRequestDto;
import com.nocountry.communitylab.model.dto.GeneratedAssetResponseDto;
import com.nocountry.communitylab.service.AssetCurationService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/assets")
@RequiredArgsConstructor
public class AssetCurationController {

    private final AssetCurationService assetCurationService;

    // Lista los activos generados que esperan curaduría (estado PENDING).
    @GetMapping("/pending")
    public ResponseEntity<List<GeneratedAssetResponseDto>> getPendingAssets() {
        return ResponseEntity.ok(assetCurationService.getPendingAssets());
    }

    // Actualiza el estado (y opcionalmente el contenido) de un activo y registra la auditoría.
    @PatchMapping("/{id}/curate")
    public ResponseEntity<GeneratedAssetResponseDto> curateAsset(
            @PathVariable UUID id,
            @Valid @RequestBody AssetCurationRequestDto request) {
        return ResponseEntity.ok(assetCurationService.curateAsset(id, request));
    }
}
