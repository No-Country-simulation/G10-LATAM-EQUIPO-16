package com.nocountry.communitylab.repository;

import com.nocountry.communitylab.model.entity.AssetCuration;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface AssetCurationRepository extends JpaRepository<AssetCuration, UUID> {

    // Historial de curaduría de un activo, del más reciente al más antiguo.
    List<AssetCuration> findByAssetIdOrderByCuratedAtDesc(UUID assetId);
}
