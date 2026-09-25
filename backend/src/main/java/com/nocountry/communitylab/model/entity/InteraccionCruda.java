package com.nocountry.communitylab.model.entity;

import com.nocountry.communitylab.model.enums.EstadoInteraccion;
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
public class InteraccionCruda {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "fuente_comunidad")
    private String communitySource;

    @Column(name = "periodo_referencia")
    private String referencePeriod;

    private String autor;
    private String canal;
    private String tipo;

    @Column(columnDefinition = "TEXT")
    private String text;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private EstadoInteraccion status;

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

    public boolean esTrivialmenteVacia() {
        if (this.text == null || this.text.isBlank()) {
            return true;
        }
        // Descartamos si no contiene letras ni números (solo emojis, espacios o caracteres especiales)
        return !this.text.matches(".*[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ].*");
    }

    public void marcarComoDescartada() {
        this.status = EstadoInteraccion.DESCARTADO;
    }

    public void marcarComoProcesando() {
        this.status = EstadoInteraccion.PROCESANDO;
    }

    public void marcarComoProcesada(String rutaOci) {
        this.status = EstadoInteraccion.PROCESADO;
        this.ociObjectRoute = rutaOci;
    }

    public void marcarComoError() {
        this.status = EstadoInteraccion.ERROR;
    }
}
