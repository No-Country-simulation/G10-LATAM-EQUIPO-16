package com.nocountry.communitylab.repository;

import com.nocountry.communitylab.model.entity.GeneratedAsset;
import com.nocountry.communitylab.model.enums.AssetStatus;
import org.springframework.data.jpa.repository.EntityGraph;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface GeneratedAssetRepository extends JpaRepository<GeneratedAsset, UUID> {

    // El EntityGraph carga el lote en la misma consulta y evita un SELECT por cada activo (N+1).
    @EntityGraph(attributePaths = "batch")
    List<GeneratedAsset> findByStatusOrderByCreatedAtAsc(AssetStatus status);
}
