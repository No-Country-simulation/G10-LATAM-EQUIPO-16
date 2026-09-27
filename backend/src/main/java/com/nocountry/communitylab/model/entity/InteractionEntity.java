package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.InteractionStatus;
import jakarta.persistence.*;
import lombok.*;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "interaccion_cruda")
@EntityListeners(AuditingEntityListener.class)
@Getter
@Setter
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class InteractionEntity {
    @Id
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
    private InteractionStatus status;

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
        // Descartamos si no contiene letras ni números (solo emojis, espacios o caracteres especiales)
        return !this.text.matches(".*[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ].*");
    }

    public void markAsDiscarded() {
        this.status = InteractionStatus.DISCARDED;
    }

    public void markAsProcessing() {
        this.status = InteractionStatus.PROCESSING;
    }

    public void markAsProcessed(String rutaOci) {
        this.status = InteractionStatus.PROCESSED;
        this.ociObjectRoute = rutaOci;
    }

    public void markAsError() {
        this.status = InteractionStatus.ERROR;
    }
}
