package com.nocountry.communitylab.exception;

/** La curaduría solicitada viola una regla de negocio (por ejemplo EDITED sin contenido). Se traduce a HTTP 422. */
public class InvalidAssetCurationException extends RuntimeException {
    public InvalidAssetCurationException(String message) {
        super(message);
    }
}
