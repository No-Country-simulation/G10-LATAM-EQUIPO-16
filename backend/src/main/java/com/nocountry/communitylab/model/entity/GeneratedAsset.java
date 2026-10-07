package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.AssetStatus;
import com.nocountry.communitylab.model.enums.AssetType;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Activo de marketing generado por la IA (post de LinkedIn, newsletter o FAQ)
 * que debe pasar por curaduría humana antes de distribuirse.
 *
 * <p>Reglas de negocio:
 * <ul>
 *   <li>Todos los activos nacen en {@link AssetStatus#PENDING}.</li>
 *   <li>Pertenece a un único {@link DistributionBatch}.</li>
 *   <li>Cada cambio de estado queda registrado en {@link AssetCuration}.</li>
 * </ul>
 */
@Entity
@Table(name = "activo_generado",
        indexes = @Index(name = "idx_activo_generado_estado", columnList = "estado"))
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GeneratedAsset {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "lote_id", nullable = false)
    private DistributionBatch batch;

    @Enumerated(EnumType.STRING)
    @Column(name = "tipo_activo", nullable = false, length = 30)
    private AssetType assetType;

    /**
     * Texto del activo (o JSON serializado). Se usa length en lugar de columnDefinition = "TEXT"
     * para que Hibernate elija el tipo correcto: varchar en PostgreSQL y CLOB en Oracle.
     */
    @Column(name = "contenido", nullable = false, length = 20000)
    private String content;

    @Enumerated(EnumType.STRING)
    @Column(name = "estado", nullable = false, length = 20)
    @Builder.Default
    private AssetStatus status = AssetStatus.PENDING;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
