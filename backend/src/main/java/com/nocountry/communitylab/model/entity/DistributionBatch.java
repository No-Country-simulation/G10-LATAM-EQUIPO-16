package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.BatchStatus;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * lote de distribucion - paquete generado a partir de
 * un conjunto de interacciones y almacenado en OCI Object Storage.
 *
 *  - Agrupa N interacciones (relación 1:N con InteractionEntity, queda pendiente)
 *  - Registra la ubicación del paquete JSON en OCI
 *  - Guarda metadatos del lote (origen_comunidad, periodo_referencia)
 */

@Entity
@Table(name = "lote_distribucion")
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class DistributionBatch {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "fuente_comunidad", nullable = false)
    private String communitySource;

    @Column(name = "periodo_referencia", nullable = false)
    private String referencePeriod;

    @Column(name = "oci_bucket")
    private String ociBucket;

    @Column(name = "ruta_oci")
    private String ociObjectRoute;

    @Column(name = "oci_status")
    private String ociStorageStatus;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private BatchStatus status;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
