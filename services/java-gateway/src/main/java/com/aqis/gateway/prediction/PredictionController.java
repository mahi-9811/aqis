package com.aqis.gateway.prediction;

import java.io.IOException;
import java.util.List;
import java.util.Map;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @GetMapping("/{testName}")
    public Map<String, Object> predict(@PathVariable String testName) {
        return predictionService.predict(testName);
    }

    @PostMapping(
            value = "/upload",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public Map<String, Object> uploadAndPredict(
            @RequestParam("logXml") MultipartFile logXml,
            @RequestParam("startLog") MultipartFile startLog,
            @RequestParam(value = "screenshot", required = false) List<MultipartFile> screenshots,
            @RequestParam(value = "testName", required = false) String testName
    ) throws IOException {
        validateRequiredFile(logXml, "logXml");
        validateRequiredFile(startLog, "startLog");
        return predictionService.uploadAndPredict(logXml, startLog, screenshots, testName);
    }

    private void validateRequiredFile(MultipartFile file, String fieldName) {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("Missing or empty required upload part: " + fieldName);
        }
    }
}
