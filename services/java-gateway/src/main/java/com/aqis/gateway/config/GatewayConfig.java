package com.aqis.gateway.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.client.RestClient;

@Configuration
@EnableConfigurationProperties({PythonApiProperties.class, GatewayAuthProperties.class})
public class GatewayConfig {

    @Bean
    RestClient restClient(PythonApiProperties properties) {
        return RestClient.builder()
                .baseUrl(properties.baseUrl())
                .build();
    }

    @Bean
    WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/api/**")
                        .allowedOrigins("*")
                        .allowedMethods("GET", "POST", "OPTIONS");
            }
        };
    }

    @Bean
    ApiKeyInterceptor apiKeyInterceptor(GatewayAuthProperties properties) {
        return new ApiKeyInterceptor(properties);
    }

    @Bean
    WebMvcConfigurer authConfigurer(ApiKeyInterceptor apiKeyInterceptor) {
        return new WebMvcConfigurer() {
            @Override
            public void addInterceptors(org.springframework.web.servlet.config.annotation.InterceptorRegistry registry) {
                registry.addInterceptor(apiKeyInterceptor)
                        .addPathPatterns("/api/**");
            }
        };
    }
}
