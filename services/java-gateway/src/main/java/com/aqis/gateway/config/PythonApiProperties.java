package com.aqis.gateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "aqis.python")
public record PythonApiProperties(String baseUrl) {
}
