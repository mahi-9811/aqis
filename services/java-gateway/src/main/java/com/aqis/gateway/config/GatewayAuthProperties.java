package com.aqis.gateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "aqis.gateway.auth")
public record GatewayAuthProperties(
        boolean enabled,
        String headerName,
        String apiKey
) {
    public String resolvedHeaderName() {
        return headerName == null || headerName.isBlank() ? "X-AQIS-API-Key" : headerName;
    }
}
