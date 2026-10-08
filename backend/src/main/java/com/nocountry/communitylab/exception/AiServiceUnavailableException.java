package com.nocountry.communitylab.exception;

//El servicio de IA no está disponible: HTTP 5xx, timeout o conexión rechazada.

public class AiServiceUnavailableException extends AiServiceException {
    private final Integer httpStatus;

    public AiServiceUnavailableException(String message, Integer httpStatus) {
        super(message);
        this.httpStatus = httpStatus;
    }

    public AiServiceUnavailableException(String message, Throwable cause) {
        super(message, cause);
        this.httpStatus = null;
    }

    public Integer getHttpStatus() { return httpStatus; }
}