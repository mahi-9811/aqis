package com.aqis.gateway.config;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

class ApiKeyInterceptorTest {

    @Test
    void disabledAuthAllowsRequest() throws Exception {
        ApiKeyInterceptor interceptor = new ApiKeyInterceptor(
                new GatewayAuthProperties(false, "X-AQIS-API-Key", ""));

        boolean allowed = interceptor.preHandle(
                new MockHttpServletRequest(),
                new MockHttpServletResponse(),
                new Object());

        assertThat(allowed).isTrue();
    }

    @Test
    void enabledAuthRejectsMissingKey() throws Exception {
        ApiKeyInterceptor interceptor = new ApiKeyInterceptor(
                new GatewayAuthProperties(true, "X-AQIS-API-Key", "secret"));
        MockHttpServletResponse response = new MockHttpServletResponse();

        boolean allowed = interceptor.preHandle(new MockHttpServletRequest(), response, new Object());

        assertThat(allowed).isFalse();
        assertThat(response.getStatus()).isEqualTo(401);
        assertThat(response.getContentAsString()).contains("Missing or invalid gateway API key.");
    }

    @Test
    void enabledAuthAllowsMatchingKey() throws Exception {
        ApiKeyInterceptor interceptor = new ApiKeyInterceptor(
                new GatewayAuthProperties(true, "X-AQIS-API-Key", "secret"));
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("X-AQIS-API-Key", "secret");

        boolean allowed = interceptor.preHandle(request, new MockHttpServletResponse(), new Object());

        assertThat(allowed).isTrue();
    }

    @Test
    void enabledAuthAllowsPreflightRequests() throws Exception {
        ApiKeyInterceptor interceptor = new ApiKeyInterceptor(
                new GatewayAuthProperties(true, "X-AQIS-API-Key", "secret"));
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("OPTIONS");

        boolean allowed = interceptor.preHandle(request, new MockHttpServletResponse(), new Object());

        assertThat(allowed).isTrue();
    }
}
