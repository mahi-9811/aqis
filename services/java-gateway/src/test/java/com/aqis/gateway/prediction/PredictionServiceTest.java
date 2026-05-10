package com.aqis.gateway.prediction;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.content;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

class PredictionServiceTest {

    @Test
    void predictCallsPythonApi() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://python-api");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        PredictionService service = new PredictionService(builder.build());
        server.expect(requestTo("http://python-api/predict/CheckoutTest"))
                .andExpect(method(HttpMethod.GET))
                .andRespond(withSuccess("{\"testName\":\"CheckoutTest\"}", MediaType.APPLICATION_JSON));

        Map<String, Object> response = service.predict("CheckoutTest");

        assertThat(response).containsEntry("testName", "CheckoutTest");
        server.verify();
    }

    @Test
    void uploadCallsAnalyzeEndpointWithMultipartBody() throws Exception {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://python-api");
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        PredictionService service = new PredictionService(builder.build());
        MockMultipartFile logXml = new MockMultipartFile(
                "logXml", "log.xml", MediaType.TEXT_XML_VALUE, "<testsuite />".getBytes());
        MockMultipartFile startLog = new MockMultipartFile(
                "startLog", "STARTLog.txt", MediaType.TEXT_PLAIN_VALUE, "started".getBytes());

        server.expect(requestTo("http://python-api/analyze"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(content().contentTypeCompatibleWith(MediaType.MULTIPART_FORM_DATA))
                .andRespond(withSuccess("{\"status\":\"ok\"}", MediaType.APPLICATION_JSON));

        Map<String, Object> response = service.uploadAndPredict(logXml, startLog, null, "CheckoutTest");

        assertThat(response).containsEntry("status", "ok");
        server.verify();
    }

    @Test
    void uploadRejectsEmptyStartLogBeforeCallingPythonApi() {
        PredictionService service = new PredictionService(RestClient.create("http://python-api"));
        MockMultipartFile logXml = new MockMultipartFile(
                "logXml", "log.xml", MediaType.TEXT_XML_VALUE, "<testsuite />".getBytes());
        MockMultipartFile startLog = new MockMultipartFile(
                "startLog", "STARTLog.txt", MediaType.TEXT_PLAIN_VALUE, new byte[0]);

        assertThatThrownBy(() -> service.uploadAndPredict(logXml, startLog, null, null))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Missing or empty required upload part: startLog");
    }
}
