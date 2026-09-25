package com.nocountry.communitylab.repository;

import com.nocountry.communitylab.model.entity.InteractionEntity;
import com.nocountry.communitylab.model.enums.InteractionStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface InteractionRepository extends JpaRepository<InteractionEntity, UUID> {
    List<InteractionEntity> findByStatus(InteractionStatus status);
}
