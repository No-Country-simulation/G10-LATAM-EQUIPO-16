package com.nocountry.communitylab.model.enums;

/** Estado de un activo generado dentro del flujo de curaduría. */
public enum AssetStatus {
    /** Recién generado, esperando revisión humana. */
    PENDING,
    /** Aprobado por el revisor. */
    APPROVED,
    /** Rechazado por el revisor. */
    REJECTED,
    /** Editado por el revisor (requiere nuevo contenido). */
    EDITED
}
