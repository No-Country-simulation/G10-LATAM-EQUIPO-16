package com.nocountry.communitylab.repository;

import com.nocountry.communitylab.model.entity.DistributionBatch;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.nocountry.communitylab.model.enums.BatchStatus;

import java.util.List;
import java.util.UUID;

@Repository
public interface DistributionBatchRepository extends JpaRepository<DistributionBatch, UUID> {
    // Métodos para el futuro: Permiten buscar lotes por su estado o por origen/fecha.
    List<DistributionBatch> findByStatus(BatchStatus status);
    List<DistributionBatch> findByCommunitySourceAndReferencePeriod(String communitySource, String referencePeriod);
}
