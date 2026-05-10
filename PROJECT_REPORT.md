# AQIS Project Report

Date: 2026-05-04

## 1. Executive Summary

AQIS is a multi-service quality intelligence platform designed to analyze automated test artifacts, estimate execution risk, explain failures, and support follow-up actions such as autofix suggestions and test-case generation.

The repository is organized as a monorepo with three primary runtime surfaces:

- a Python decision engine and API
- a Java gateway intended for enterprise orchestration
- a React web application for upload and result visualization

Based on the checked-in code, the Python layer remains the most mature part of the system. It contains the domain logic, API routes, and the largest body of tests. The React frontend is implemented and now defaults to the documented gateway path. The Java gateway is also materially implemented: it contains Spring Boot application, configuration, prediction controller/service, gateway error handling, optional API-key interception, and focused tests for controller, service, and auth behavior.

## 2. Project Objective

The project appears to solve a post-test execution analysis workflow:

- ingest test artifacts such as `log.xml`, `STARTLog.txt`, and screenshots
- parse and normalize those artifacts
- extract features relevant to test health and failure patterns
- calculate risk or likely next-run behavior
- provide operator-facing analysis, trend views, and remediation support

This makes AQIS suitable for CI/CD quality monitoring, failure triage, and regression risk assessment.

## 3. Repository Structure

Top-level areas identified in the repository:

- `aqis/`: Python domain package
- `services/python_api/`: FastAPI wrapper around the AQIS package
- `services/java-gateway/`: Spring Boot gateway for prediction lookup, artifact upload forwarding, and platform concerns
- `apps/web/`: React frontend built with Vite
- `docs/`: architecture documentation
- `deployment/`: deployment-related assets
- `config/`: environment and logging configuration
- `data/`: historical and learning-related storage directories

## 4. Architecture Overview

The intended request flow documented in the repository is:

1. A user uploads execution artifacts from the web UI.
2. The Java gateway receives the request and handles platform concerns.
3. The Java gateway forwards the request to the Python API.
4. The Python API parses, analyzes, and returns prediction data.

This split is consistent across:

- `README.md`
- `docs/architecture.md`
- `docker-compose.yml`

### Current practical architecture

From the checked-in implementation, the practical system status is:

- Python: implemented and central to all domain behavior
- Web: implemented and able to call backend endpoints
- Java: implemented as a Spring Boot gateway that forwards prediction lookup and artifact upload requests to the Python API

## 5. Python Domain Package Assessment

The Python package under `aqis/` is the core of the system and contains multiple subsystems.

### Parsing and normalization

Modules found:

- `aqis/parser/xml_parser.py`
- `aqis/parser/startlog_parser.py`
- `aqis/parser/screenshot_ocr.py`
- `aqis/parser/bundle_normalizer.py`

These indicate support for:

- XML parsing
- start log parsing
- OCR on screenshots
- normalization into a common bundle structure

### Risk and prediction engine

Modules found:

- `aqis/risk_engine/feature_extractor.py`
- `aqis/risk_engine/history_manager.py`
- `aqis/risk_engine/prediction_engine.py`
- `aqis/risk_engine/risk_scorer.py`
- `aqis/risk_engine/trend_analyzer.py`

This suggests an end-to-end analytical pipeline covering:

- feature extraction
- use of historical run data
- rule-based or heuristic scoring
- trend analysis
- next-run prediction

### Agentic analysis

Modules found:

- `aqis/agents/base_agent.py`
- `aqis/agents/failure_agent.py`
- `aqis/agents/fix_agent.py`
- `aqis/agents/orchestrator.py`
- `aqis/agents/reporter_agent.py`
- `aqis/agents/retriever_agent.py`
- `aqis/agents/test_reader_agent.py`
- `aqis/agents/validator_agent.py`

This indicates a modular agent workflow for interpreting analyzed bundles and generating richer outputs such as failure reasoning and report content.

### Autofix support

Modules found:

- `aqis/autofix/base_fix.py`
- `aqis/autofix/locator_generator.py`
- `aqis/autofix/orchestrator.py`
- `aqis/autofix/patch_builder.py`
- `aqis/autofix/precondition_generator.py`
- `aqis/autofix/wait_strategy.py`

This is a meaningful extension beyond simple prediction. It suggests AQIS is not only diagnostic but also prescriptive, producing remediation guidance for UI or automation failures.

### Learning and retrieval

Modules found:

- `aqis/learning/embedding_generator.py`
- `aqis/learning/knowledge_store.py`
- `aqis/learning/orchestrator.py`
- `aqis/learning/similarity_retriever.py`
- `aqis/learning/vector_store.py`

Repository dependencies also include:

- `sentence-transformers`
- `faiss-cpu`

This implies a retrieval or similarity-learning capability, likely used for analogous failure lookup or feedback-informed recommendations.

### Test generation

Modules found:

- `aqis/testgen/coverage_analyzer.py`
- `aqis/testgen/negative_generator.py`
- `aqis/testgen/orchestrator.py`
- `aqis/testgen/scenario_generator.py`
- `aqis/testgen/template_generator.py`

This broadens AQIS from analysis into QA acceleration by generating follow-up test cases based on observed execution outcomes.

## 6. Python API Assessment

The FastAPI implementation under `services/python_api/` is substantial and is the clearest operational backend in the repository.

### Confirmed API capabilities

Observed routes:

- `GET /health`
- `GET /health/live`
- `GET /health/ready`
- `GET /metrics`
- `GET /predict/{test_name}`
- `POST /analyze/bundle`
- `POST /analyze/agents`
- `POST /analyze`
- `POST /artifacts/predict`
- `POST /autofix`
- `GET /learning/similar/{test_name}`
- `GET /learning/stats`
- `POST /learning/feedback`
- `POST /testcases/generate`

### API characteristics

The API includes:

- CORS middleware
- request ID propagation
- request timing and counters
- centralized error handling
- simple rate-limiting placeholder
- upload validation and filename sanitization
- health and metrics endpoints

This is a solid backend shape for an internal platform service.

### Python dependencies

The API service requirements include:

- `fastapi`
- `uvicorn`
- `pydantic`
- `opencv-python`
- `pytesseract`
- `numpy`
- `python-multipart`
- `sentence-transformers`
- `faiss-cpu`

This dependency profile aligns with OCR, ML embeddings, and file upload ingestion.

## 7. Web Application Assessment

The frontend under `apps/web/` is a Vite + React application.

### Confirmed frontend structure

Main application pages:

- `HomePage`
- `UploadPage`
- `PredictionPage`
- `AnalysisResultsPage`
- `TrendHistoryPage`

Main components:

- `FileUploadComponent`
- `PredictionCard`
- `RCASummaryCard`
- `RiskBadge`
- `TrendChart`
- `AutoFixPanel`
- `TestCasesList`

### Frontend behavior inferred from code

The frontend supports:

- navigation across workflow screens
- history lookup by test name
- artifact upload for XML, start log, and screenshots
- display of predictions and analysis results
- trend visualization
- autofix and test case presentation

### Backend integration

The frontend currently defaults to:

- `/api/predictions` via `VITE_API_BASE_URL`

This matches the documented target architecture: browser requests go through the Java gateway path, with Vite and Nginx handling local/container routing.

## 8. Java Gateway Assessment

The Java gateway contains:

- `pom.xml`
- `src/main/java/com/aqis/gateway/AqisGatewayApplication.java`
- `src/main/java/com/aqis/gateway/config/GatewayConfig.java`
- `src/main/java/com/aqis/gateway/config/PythonApiProperties.java`
- `src/main/java/com/aqis/gateway/config/GatewayAuthProperties.java`
- `src/main/java/com/aqis/gateway/config/ApiKeyInterceptor.java`
- `src/main/java/com/aqis/gateway/prediction/PredictionController.java`
- `src/main/java/com/aqis/gateway/prediction/PredictionService.java`
- `src/main/java/com/aqis/gateway/prediction/GatewayExceptionHandler.java`
- `src/main/resources/application.yml`
- `README.md`

The Maven project is configured with:

- Spring Boot Web
- Validation
- Actuator
- Spring Boot Test

The checked-in implementation exposes:

- `GET /api/predictions/{testName}`
- `POST /api/predictions/upload`

The gateway forwards lookup requests to Python `GET /predict/{testName}` and multipart artifact uploads to Python `POST /analyze`. It also includes request validation, upstream error mapping, CORS configuration, and optional API-key authentication.

Java test files are present for:

- API-key interceptor behavior
- prediction controller request/response behavior
- prediction service forwarding behavior

### Conclusion on Java status

The gateway is currently:

- implemented for the core supported request flow
- build-configured and containerized
- referenced in Docker Compose
- covered by focused unit/web tests

The remaining Java work is hardening rather than first implementation: broader integration tests, enterprise auth/persistence, richer audit logging, and verified Maven execution in environments where Maven is installed.

## 9. Deployment and Runtime Model

The repository includes `docker-compose.yml` with three services:

- `python-api` on port `8000`
- `java-gateway` on port `8080`
- `web` on port `5173`

The compose file includes:

- health checks for the Python API
- Java dependency on Python readiness
- web containerization

This shows the project is intended to run as a composed local platform with the Java layer in front of the Python API.

## 10. Test Coverage Signal

The repository contains Python tests under `aqis/tests/`, including tests for:

- agents
- autofix
- feature extraction
- history management
- learning
- multi-screenshot upload
- risk scoring
- test generation
- trend analysis
- XML parsing
- integration paths

This is a positive signal for backend maturity.

### Test execution note

The Python suite was run from the repository root and passed with `25 passed`. The web test suite passed with `1 passed`. Java tests are present, but local execution could not be verified in this workspace because Maven is not installed.

## 11. Strengths

Key strengths visible in the checked-in code:

- Strong separation of concerns across parsing, scoring, learning, autofix, and test generation
- Clear service-oriented architecture
- Practical API concerns already addressed in the Python layer
- Real frontend implementation rather than placeholder scaffolding
- Docker Compose support for multi-service local execution
- Meaningful backend test coverage
- Support for richer workflows beyond prediction alone

## 12. Risks and Gaps

The main risks or gaps visible from repository inspection are:

- Java test execution depends on Maven availability; Maven was not available in the local workspace used for this report.
- The root `requirements.txt` is minimal and does not represent the full Python service dependency set.
- `aqis/pyproject.toml` only contains build-system metadata and does not describe package dependencies or tooling in a complete way.
- Runtime validation of the full Docker/Kubernetes stack was not completed as part of this report.
- The repository root is not a Git repository in this workspace snapshot, so branch state and change history could not be assessed from the top level.

## 13. Maturity Assessment

Current maturity by layer:

- Python domain package: high relative maturity
- Python API: medium to high maturity
- React frontend: medium maturity
- Java gateway: medium maturity in checked-in implementation
- End-to-end platform alignment: medium to high, because the documented gateway path is now represented in code and frontend defaults

## 14. Recommendations

Recommended next steps for the project:

1. Install Maven or add a Maven wrapper so Java gateway tests can be run consistently in local and CI environments.
2. Add Java integration tests against a stubbed Python API to verify gateway forwarding and error mapping end to end.
3. Consolidate Python packaging metadata so dependencies and tooling are declared in a single authoritative place.
4. Continue recording full Python, frontend, and Java test results as the baseline quality signal.
5. Expand the Java service only where platform responsibilities require it, such as auth integration, persistence, workflow orchestration, and audit logging.
6. Consider a single architectural status document that distinguishes implemented behavior from planned behavior.

## 15. Final Conclusion

AQIS is a promising and technically ambitious quality intelligence platform. The Python side is still the product center today: it contains parsing, OCR, risk analysis, learning, agentic reasoning, autofix support, and test generation. The frontend exposes these capabilities through the documented gateway path. The Java gateway is now materially represented in code for the core prediction and upload workflow, with additional enterprise concerns left as future hardening.

If this report is intended for stakeholders, the safest framing is:

- AQIS already has a functional Python-based analysis platform with UI support.
- The enterprise gateway layer now exists for the supported request path, while broader enterprise orchestration remains a next-stage expansion.
