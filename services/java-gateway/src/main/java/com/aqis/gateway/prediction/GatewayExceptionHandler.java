package com.aqis.gateway.prediction;

import java.io.IOException;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@RestControllerAdvice
public class GatewayExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<Map<String, Object>> handleBadRequest(IllegalArgumentException ex) {
        return error(HttpStatus.BAD_REQUEST, ex.getMessage());
    }

    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<Map<String, Object>> handleMissingParameter(MissingServletRequestParameterException ex) {
        return error(HttpStatus.BAD_REQUEST, "Missing required request part: " + ex.getParameterName());
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleUploadTooLarge() {
        return error(HttpStatus.PAYLOAD_TOO_LARGE, "Uploaded artifact is too large.");
    }

    @ExceptionHandler(IOException.class)
    public ResponseEntity<Map<String, Object>> handleIoError() {
        return error(HttpStatus.BAD_REQUEST, "Unable to read uploaded artifact.");
    }

    @ExceptionHandler(RestClientResponseException.class)
    public ResponseEntity<Map<String, Object>> handlePythonApiResponse(RestClientResponseException ex) {
        HttpStatus status = HttpStatus.resolve(ex.getStatusCode().value());
        if (status == null || status.is5xxServerError()) {
            status = HttpStatus.BAD_GATEWAY;
        }
        return error(status, "Python API request failed.", ex.getStatusCode().value());
    }

    @ExceptionHandler(RestClientException.class)
    public ResponseEntity<Map<String, Object>> handlePythonApiUnavailable() {
        return error(HttpStatus.BAD_GATEWAY, "Python API is unavailable.");
    }

    private ResponseEntity<Map<String, Object>> error(HttpStatus status, String detail) {
        return ResponseEntity.status(status)
                .body(Map.of("detail", detail, "status", status.value()));
    }

    private ResponseEntity<Map<String, Object>> error(HttpStatus status, String detail, int upstreamStatus) {
        return ResponseEntity.status(status)
                .body(Map.of("detail", detail, "status", status.value(), "upstreamStatus", upstreamStatus));
    }
}
