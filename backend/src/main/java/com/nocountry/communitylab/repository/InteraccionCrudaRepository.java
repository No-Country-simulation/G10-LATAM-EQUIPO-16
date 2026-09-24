package com.nocountry.communitylab.repository;

import com.nocountry.communitylab.model.entity.InteraccionCruda;
import com.nocountry.communitylab.model.enums.EstadoInteraccion;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface InteraccionCrudaRepository extends JpaRepository<InteraccionCruda, UUID> {
    List<InteraccionCruda> findByStatus(EstadoInteraccion status);
}
