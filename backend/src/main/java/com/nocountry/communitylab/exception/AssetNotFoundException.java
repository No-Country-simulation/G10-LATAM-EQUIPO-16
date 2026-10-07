package com.nocountry.communitylab.exception;

import java.util.UUID;

/** No existe un activo generado con el id indicado. Se traduce a HTTP 404. */
public class AssetNotFoundException extends RuntimeException {
    public AssetNotFoundException(UUID id) {
        super("No se encontró el activo con id: " + id);
    }
}
