package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.InteractionStatus;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;
import java.util.regex.Pattern;

@Entity
@Table(name = "interaccion_cruda")
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class InteractionEntity {

    /** Regex para detectar al menos una letra o número unicode en el texto. */
    private static final Pattern MEANINGFUL_CHAR = Pattern.compile("[\\p{L}\\p{N}]");

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "fuente_comunidad")
    private String communitySource;

    @Column(name = "periodo_referencia")
    private String referencePeriod;

    private String author;
    private String channel;
    private String type;

    @Column(columnDefinition = "TEXT")
    private String text;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private InteractionStatus status = InteractionStatus.PENDING;

    @Column(name = "ruta_oci")
    private String ociObjectRoute;

    @Column(name = "recibido_en")
    private LocalDateTime receivedAt;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    //filtro conservador

    public boolean isTriviallyEmpty() {
        if (this.text == null || this.text.isBlank()) {
            return true;
        }
        return !MEANINGFUL_CHAR.matcher(this.text).find();
    }

    public void markAsDiscarded() {
        this.status = InteractionStatus.DISCARDED;
    }

    public void markAsProcessing() {
        this.status = InteractionStatus.PROCESSING;
    }

    public void markAsProcessed(String ociObjectRoute) {
        this.status = InteractionStatus.PROCESSED;
        this.ociObjectRoute = ociObjectRoute;
    }

    public void markAsError() {
        this.status = InteractionStatus.ERROR;
    }
}
