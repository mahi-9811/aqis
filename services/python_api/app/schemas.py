from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class BundleStep(FlexibleModel):
    stepName: str | None = None
    executedProperty: str | None = None
    timing: str | int | float | None = None
    labels: list[str] = Field(default_factory=list)
    errorMessage: str | None = None


class BundlePayload(FlexibleModel):
    testName: str | None = None
    steps: list[BundleStep] = Field(default_factory=list)
    exception: list[Any] = Field(default_factory=list)
    retries: int | None = None
    autoHeal: list[Any] = Field(default_factory=list)
    driftSignals: list[Any] = Field(default_factory=list)
    ocrText: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class HistoryRunSummary(FlexibleModel):
    runNumber: int
    stepName: str
    status: str
    retries: int
    exceptionCount: int
    autoHealCount: int
    errorMessage: str = ""


class UploadedArtifacts(FlexibleModel):
    logXml: str | None = None
    startLog: str | None = None
    screenshots: list[str] = Field(default_factory=list)
    screenshotCount: int = 0
    screenshotProvided: bool = False
    ocrWarning: str | None = None


class PredictionResponse(FlexibleModel):
    testName: str
    riskScore: float
    riskLevel: str
    prediction: str
    reasons: list[str] = Field(default_factory=list)
    historyCount: int = 0
    history: list[HistoryRunSummary] = Field(default_factory=list)
    featuresCurrent: dict[str, Any] = Field(default_factory=dict)
    trends: dict[str, Any] = Field(default_factory=dict)
    available: bool | None = None
    message: str | None = None


class PredictionWithBundleResponse(PredictionResponse):
    ingestedArtifacts: UploadedArtifacts | None = None
    bundle: BundlePayload | None = None


class SimilarCaseMatch(FlexibleModel):
    testName: str | None = None
    failureCategory: str | None = None
    fixApplied: str | None = None
    confidence: float = 0.0
    timestamp: str | None = None


class LearningSimilarResponse(FlexibleModel):
    similarCasesFound: bool
    matches: list[SimilarCaseMatch] = Field(default_factory=list)


class LearningStatsResponse(FlexibleModel):
    storedRuns: int = 0
    knownTests: int = 0
    fixSuccessCount: int = 0
    fixFailureCount: int = 0
    vectorCount: int = 0
    backend: str | None = None


class FeedbackResponse(FlexibleModel):
    stored: bool
    entry: dict[str, Any] = Field(default_factory=dict)


class AutofixCandidate(FlexibleModel):
    fixType: str | None = None
    confidence: float = 0.0
    rollbackSafe: bool = False
    description: str | None = None
    locators: list[Any] = Field(default_factory=list)
    waits: list[Any] = Field(default_factory=list)
    preconditions: list[Any] = Field(default_factory=list)


class AutofixResponse(FlexibleModel):
    fixes: list[AutofixCandidate] = Field(default_factory=list)
    patch: str = ""
    confidence: float = 0.0
    recommended: bool = False
    message: str | None = None


class GeneratedTestCase(FlexibleModel):
    name: str
    description: str
    type: str
    priority: str


class GeneratedTestCasesResponse(FlexibleModel):
    coverageAnalysis: dict[str, Any] = Field(default_factory=dict)
    generatedTests: list[GeneratedTestCase] = Field(default_factory=list)
    priorityOrder: list[str] = Field(default_factory=list)
    recommendation: str
    automationTemplates: dict[str, Any] = Field(default_factory=dict)


class DiagnosticsResponse(FlexibleModel):
    phaseTimings: dict[str, float] = Field(default_factory=dict)
    knowledgeRecordId: str | None = None


class TestSummaryResponse(FlexibleModel):
    testName: str
    uiContext: Any = None
    stepSummary: Any = None
    historyCount: int = 0
    currentRunStored: bool = False
    uploadedArtifacts: UploadedArtifacts = Field(default_factory=UploadedArtifacts)
    screenshotAvailable: bool = False
    ocrText: str = ""
    failureCategory: str | None = None


class RootCauseAnalysisResponse(FlexibleModel):
    summary: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
    priorKnowledge: LearningSimilarResponse = Field(default_factory=lambda: LearningSimilarResponse(similarCasesFound=False))


class TrendSummaryResponse(FlexibleModel):
    timingSlope: float = 0.0
    retryTrend: str = "stable"
    driftTrend: str = "stable"
    uiErrorSpike: bool = False
    riskScoreOverTime: list[float] = Field(default_factory=list)
    featureSnapshot: dict[str, Any] = Field(default_factory=dict)


class UnifiedAnalysisResponse(FlexibleModel):
    testSummary: TestSummaryResponse
    prediction: PredictionResponse
    rootCauseAnalysis: RootCauseAnalysisResponse
    autoFix: AutofixResponse
    generatedTestCases: GeneratedTestCasesResponse
    trendSummary: TrendSummaryResponse
    nextRunRecommendation: str
    warnings: list[str] = Field(default_factory=list)
    diagnostics: DiagnosticsResponse
    bundle: BundlePayload


class AgentAnalysisResponse(FlexibleModel):
    testName: str
    agents: dict[str, Any] = Field(default_factory=dict)
    finalReport: dict[str, Any] = Field(default_factory=dict)
