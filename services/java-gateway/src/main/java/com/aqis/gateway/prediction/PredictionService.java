package com.aqis.gateway.prediction;

import java.io.IOException;
import java.util.List;
import java.util.Map;

import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

@Service
public class PredictionService {

    private final RestClient restClient;

    public PredictionService(RestClient restClient) {
        this.restClient = restClient;
    }

    public Map<String, Object> predict(String testName) {
        if (testName == null || testName.isBlank()) {
            throw new IllegalArgumentException("testName is required.");
        }

        return restClient.get()
                .uri("/predict/{testName}", testName)
                .retrieve()
                .body(Map.class);
    }

    public Map<String, Object> uploadAndPredict(
            MultipartFile logXml,
            MultipartFile startLog,
            List<MultipartFile> screenshots,
            String testName
    ) throws IOException {
        validateRequiredFile(logXml, "logXml");
        validateRequiredFile(startLog, "startLog");

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("logXml", multipartPart("logXml", logXml));
        body.add("startLog", multipartPart("startLog", startLog));
        if (screenshots != null) {
            for (MultipartFile screenshot : screenshots) {
                if (screenshot != null && !screenshot.isEmpty()) {
                    body.add("screenshot", multipartPart("screenshot", screenshot));
                }
            }
        }
        if (testName != null && !testName.isBlank()) {
            body.add("testName", testName);
        }

        return restClient.post()
                .uri("/analyze")
                .contentType(MediaType.MULTIPART_FORM_DATA)
                .body(body)
                .retrieve()
                .body(Map.class);
    }

    private void validateRequiredFile(MultipartFile file, String fieldName) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Missing or empty required upload part: " + fieldName);
        }
    }

    private HttpEntity<ByteArrayResource> multipartPart(String name, MultipartFile file) throws IOException {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(resolveContentType(file));
        headers.setContentDisposition(ContentDisposition.formData()
                .name(name)
                .filename(file.getOriginalFilename())
                .build());

        ByteArrayResource resource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() {
                return file.getOriginalFilename();
            }
        };
        return new HttpEntity<>(resource, headers);
    }

    private MediaType resolveContentType(MultipartFile file) {
        if (file.getContentType() == null || file.getContentType().isBlank()) {
            return MediaType.APPLICATION_OCTET_STREAM;
        }
        return MediaType.parseMediaType(file.getContentType());
    }
}
