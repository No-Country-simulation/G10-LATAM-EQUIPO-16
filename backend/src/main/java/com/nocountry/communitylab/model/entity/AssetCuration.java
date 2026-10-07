package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.AssetStatus;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Registro de auditoría de la curaduría: una fila por cada revisión de un {@link GeneratedAsset}.
 * Es de solo inserción; nunca se actualiza.
 */
@Entity
@Table(name = "curaduria_activo",
        indexes = @Index(name = "idx_curaduria_activo_activo", columnList = "activo_id"))
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AssetCuration {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "activo_id", nullable = false)
    private GeneratedAsset asset;

    @Column(name = "notas_revisor", length = 1000)
    private String reviewerNotes;

    @Enumerated(EnumType.STRING)
    @Column(name = "estado_anterior", nullable = false, length = 20)
    private AssetStatus previousStatus;

    @Enumerated(EnumType.STRING)
    @Column(name = "estado_nuevo", nullable = false, length = 20)
    private AssetStatus newStatus;

    @CreatedDate
    @Column(name = "curado_en", nullable = false, updatable = false)
    private LocalDateTime curatedAt;
}
