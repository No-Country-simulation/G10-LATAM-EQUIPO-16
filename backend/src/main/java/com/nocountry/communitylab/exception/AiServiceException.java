package com.nocountry.communitylab.exception;

/**
 * Fallo definitivo del servicio de IA: respuesta invalida, error 4xx o 500 del motor de IA.
 * No se reintenta y la API responde 502. Los fallos temporales (timeout, conexion, 5xx distinto
 * de 500) usan {@link AiServiceUnavailableException}. El service debe capturarla y marcar
 * las interacciones como ERROR.
 */
public class AiServiceException extends RuntimeException {

    public AiServiceException(String message) {
        super(message);
    }

    public AiServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
