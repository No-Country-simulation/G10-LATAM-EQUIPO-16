package com.nocountry.communitylab.service;

import com.nocountry.communitylab.exception.AssetNotFoundException;
import com.nocountry.communitylab.exception.InvalidAssetCurationException;
import com.nocountry.communitylab.model.dto.AssetCurationRequestDto;
import com.nocountry.communitylab.model.dto.GeneratedAssetResponseDto;
import com.nocountry.communitylab.model.entity.AssetCuration;
import com.nocountry.communitylab.model.entity.GeneratedAsset;
import com.nocountry.communitylab.model.enums.AssetStatus;
import com.nocountry.communitylab.repository.AssetCurationRepository;
import com.nocountry.communitylab.repository.GeneratedAssetRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

/** Curaduría de activos generados por la IA: listado de pendientes y revisión con auditoría. */
@Slf4j
@Service
@RequiredArgsConstructor
public class AssetCurationService {

    private final GeneratedAssetRepository assetRepository;
    private final AssetCurationRepository curationRepository;

    /** Activos en PENDING, del más antiguo al más reciente. */
    @Transactional(readOnly = true)
    public List<GeneratedAssetResponseDto> getPendingAssets() {
        List<GeneratedAssetResponseDto> pending = assetRepository
                .findByStatusOrderByCreatedAtAsc(AssetStatus.PENDING)
                .stream()
                .map(this::toResponse)
                .toList();
        log.info("Activos pendientes de curaduría: {}", pending.size());
        return pending;
    }

    /**
     * Cura un activo: actualiza su estado (y contenido si se envía) y registra la auditoría.
     * Todo ocurre en una sola transacción: o se guardan ambos cambios o ninguno.
     *
     * @throws AssetNotFoundException         si el id no existe
     * @throws InvalidAssetCurationException  si la solicitud viola una regla de negocio
     */
    @Transactional
    public GeneratedAssetResponseDto curateAsset(UUID id, AssetCurationRequestDto request) {
        GeneratedAsset asset = assetRepository.findById(id)
                .orElseThrow(() -> new AssetNotFoundException(id));
        validateCuration(request);

        AssetStatus previousStatus = asset.getStatus();
        asset.setStatus(request.getNewStatus());
        if (request.getContent() != null) {
            asset.setContent(request.getContent());
        }
        // saveAndFlush fuerza el flush para que updatedAt (auditoría) quede actualizado en la respuesta
        GeneratedAsset saved = assetRepository.saveAndFlush(asset);

        curationRepository.save(AssetCuration.builder()
                .asset(saved)
                .reviewerNotes(request.getReviewerNotes())
                .previousStatus(previousStatus)
                .newStatus(request.getNewStatus())
                .build());

        log.info("Activo {} curado: {} -> {}", id, previousStatus, request.getNewStatus());
        return toResponse(saved);
    }

    private void validateCuration(AssetCurationRequestDto request) {
        if (request.getNewStatus() == AssetStatus.PENDING) {
            throw new InvalidAssetCurationException(
                    "El nuevo estado no puede ser PENDING: la curaduría debe aprobar, rechazar o editar el activo");
        }
        boolean hasContent = request.getContent() != null;
        if (hasContent && request.getContent().isBlank()) {
            throw new InvalidAssetCurationException("El contenido, si se envía, no puede estar vacío");
        }
        if (request.getNewStatus() == AssetStatus.EDITED && !hasContent) {
            throw new InvalidAssetCurationException("El estado EDITED requiere enviar el nuevo contenido");
        }
    }

    private GeneratedAssetResponseDto toResponse(GeneratedAsset asset) {
        return GeneratedAssetResponseDto.builder()
                .id(asset.getId())
                .batchId(asset.getBatch().getId())
                .assetType(asset.getAssetType())
                .content(asset.getContent())
                .status(asset.getStatus())
                .createdAt(asset.getCreatedAt())
                .updatedAt(asset.getUpdatedAt())
                .build();
    }
}
