package com.nocountry.communitylab.exception;

/**
 * Excepcion lanzada cuando el servicio de IA falla o devuelve una respuesta invalida.
 * El service correspondiente debe capturarla, marcar las interacciones como ERROR
 * y devolver una respuesta con status "error".
 */
public class AiServiceException extends  RuntimeException{

    public AiServiceException(String message) {
        super(message);
    }

    public AiServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
