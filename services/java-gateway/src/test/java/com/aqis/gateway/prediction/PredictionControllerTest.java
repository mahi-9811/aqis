package com.aqis.gateway.prediction;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.ResourceAccessException;

@WebMvcTest(PredictionController.class)
class PredictionControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private PredictionService predictionService;

    @Test
    void predictForwardsToService() throws Exception {
        when(predictionService.predict("CheckoutTest")).thenReturn(Map.of("testName", "CheckoutTest"));

        mockMvc.perform(get("/api/predictions/CheckoutTest"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.testName").value("CheckoutTest"));

        verify(predictionService).predict("CheckoutTest");
    }

    @Test
    void uploadRejectsEmptyRequiredLogXml() throws Exception {
        MockMultipartFile emptyLogXml = new MockMultipartFile(
                "logXml", "log.xml", MediaType.TEXT_XML_VALUE, new byte[0]);
        MockMultipartFile startLog = new MockMultipartFile(
                "startLog", "STARTLog.txt", MediaType.TEXT_PLAIN_VALUE, "started".getBytes());

        mockMvc.perform(multipart("/api/predictions/upload")
                        .file(emptyLogXml)
                        .file(startLog))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("Missing or empty required upload part: logXml"));

        verifyNoInteractions(predictionService);
    }

    @Test
    void uploadForwardsValidArtifacts() throws Exception {
        MockMultipartFile logXml = new MockMultipartFile(
                "logXml", "log.xml", MediaType.TEXT_XML_VALUE, "<testsuite />".getBytes());
        MockMultipartFile startLog = new MockMultipartFile(
                "startLog", "STARTLog.txt", MediaType.TEXT_PLAIN_VALUE, "started".getBytes());

        when(predictionService.uploadAndPredict(any(), any(), any(), eq("CheckoutTest")))
                .thenReturn(Map.of("testName", "CheckoutTest"));

        mockMvc.perform(multipart("/api/predictions/upload")
                        .file(logXml)
                        .file(startLog)
                        .param("testName", "CheckoutTest"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.testName").value("CheckoutTest"));

        verify(predictionService).uploadAndPredict(any(), any(), isNull(), eq("CheckoutTest"));
    }

    @Test
    void upstreamConnectionFailureReturnsBadGateway() throws Exception {
        when(predictionService.predict("CheckoutTest"))
                .thenThrow(new ResourceAccessException("connection refused"));

        mockMvc.perform(get("/api/predictions/CheckoutTest"))
                .andExpect(status().isBadGateway())
                .andExpect(jsonPath("$.detail").value("Python API is unavailable."));
    }
}
