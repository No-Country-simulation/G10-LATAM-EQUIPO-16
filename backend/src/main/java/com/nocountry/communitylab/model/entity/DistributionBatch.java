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
 * Representa un lote de distribución: el paquete de activos generado a partir de
 * un conjunto de interacciones y almacenado en OCI Object Storage.
 *
 * <p>Reglas de negocio:
 * <ul>
 *   <li>Todos los lotes nacen en {@link BatchStatus#PENDING}.</li>
 *   <li>{@link #ociObjectRoute} almacena únicamente el <b>nombre/ruta interna</b> del objeto
 *       (ej. {@code activos/2026-semana-04/paquete.json}), no una URL completa con {@code oci://}.
 *       Permanece nulo hasta que la subida a OCI se confirme.</li>
 *   <li>Regla del pipeline: {@code PROCESSED ⇒ ociObjectRoute != null}.</li>
 * </ul>
 *
 * <p>Relación con otras entidades:
 * <ul>
 *   <li>1:N con {@code InteractionEntity} (pendiente de integrar en el service).</li>
 * </ul>
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

    /**
     * Nombre del bucket OCI donde se almacenan los activos.
     * Se mantiene por trazabilidad histórica y potencial soporte multibucket.
     */
    @Column(name = "oci_bucket")
    private String ociBucket;

    /**
     * Namespace del bucket OCI (requerido por el SDK de OCI).
     */
    @Column(name = "oci_namespace")
    private String ociNamespace;

    /**
     * Nombre/ruta interna del objeto en OCI (ej. {@code activos/2026-semana-04/paquete.json}).
     * NO incluye el protocolo {@code oci://}. Nulo hasta que la subida se confirme.
     */
    @Column(name = "ruta_oci")
    private String ociObjectRoute;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private BatchStatus status = BatchStatus.PENDING;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
