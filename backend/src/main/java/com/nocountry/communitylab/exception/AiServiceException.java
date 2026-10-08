package com.nocountry.communitylab.exception;

/** Excepción base genérica para cualquier problema (no reintentable) al invocar el servicio de IA:
 * por ejemplo HTTP 4xx o contrato inválido. */
public class AiServiceException extends Exception {
    public AiServiceException(String message) {
        super(message);
    }

    public AiServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}