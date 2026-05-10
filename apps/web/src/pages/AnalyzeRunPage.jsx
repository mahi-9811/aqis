import { useMemo, useState } from "react";

import { runPostExecutionWorkflow } from "../api";
import AutoFixPanel from "../components/AutoFixPanel";
import CollapsibleSection from "../components/CollapsibleSection";
import FileUploadComponent from "../components/FileUploadComponent";
import PredictionCard from "../components/PredictionCard";
import RCASummaryCard from "../components/RCASummaryCard";
import RiskBadge from "../components/RiskBadge";
import TestCasesList from "../components/TestCasesList";
import TrendChart from "../components/TrendChart";

function buildScreenshotPreview(files) {
  return (files || []).map((file) => ({
    name: file.name,
    url: URL.createObjectURL(file)
  }));
}

function summaryMetrics(workflow) {
  return [
    {
      label: "History Used",
      value: workflow?.prediction?.historyCount ?? 0
    },
    {
      label: "Screenshots",
      value: workflow?.testSummary?.uploadedArtifacts?.screenshotCount ?? 0
    },
    {
      label: "AutoFix Confidence",
      value: workflow?.autofix?.confidence ?? 0
    },
    {
      label: "Generated Tests",
      value: workflow?.testcases?.generatedTests?.length ?? 0
    }
  ];
}

export default function AnalyzeRunPage({ workflow, setWorkflow }) {
  const [testName, setTestName] = useState("");
  const [files, setFiles] = useState({
    logXml: null,
    startLog: null,
    screenshots: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const metrics = useMemo(() => summaryMetrics(workflow), [workflow]);
  const bundle = workflow?.bundle || workflow?.prediction?.bundle || null;
  const report = workflow?.analysis?.summary;
  const history = workflow?.prediction?.history || [];

  async function handleSubmit(event) {
    event.preventDefault();
    if (!files.logXml || !files.startLog) {
      setError("Select a folder that contains log.xml and STARTLog.txt.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const unified = await runPostExecutionWorkflow({
        testName,
        logXml: files.logXml,
        startLog: files.startLog,
        screenshots: files.screenshots
      });
      setWorkflow({
        ...unified,
        prediction: unified.prediction || null,
        analysis: unified.rootCauseAnalysis || null,
        autofix: unified.autoFix || null,
        testcases: unified.generatedTestCases || null,
        trendSummary: unified.trendSummary || null,
        nextRunRecommendation: unified.nextRunRecommendation || "",
        bundle: unified.bundle || null,
        testSummary: unified.testSummary || null,
        warnings: unified.warnings || [],
        screenshotPreview: buildScreenshotPreview(files.screenshots),
        uploadedAt: new Date().toISOString()
      });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="analysis-page">
      <section className="analysis-hero">
        <div className="hero-copy">
          <p className="eyebrow">Failed Run Analysis</p>
          <h1>Analyze one failed START run and leave with the next action.</h1>
          <p className="lede">
            Upload the run folder once. AQIS will extract evidence, explain the failure, score the next-run risk,
            recommend a safe fix, and generate preventive coverage from the same analysis pass.
          </p>
        </div>

        <aside className="surface card-stack status-panel">
          <p className="eyebrow">Workspace Status</p>
          <h3>{workflow?.prediction?.testName || "No run loaded"}</h3>
          <p className="support-text">
            {workflow
              ? "The current workspace is centered on one analyzed failure. Review evidence first, then decide whether to apply the proposed fix."
              : "Start by selecting the folder for one failed START execution. AQIS expects log.xml and STARTLog.txt, plus screenshots when available."}
          </p>
          <div className="metric-grid">
            {metrics.map((metric) => (
              <div className="metric-card" key={metric.label}>
                <span className="metric-label">{metric.label}</span>
                <strong>{metric.value}</strong>
              </div>
            ))}
          </div>
          {workflow?.warnings?.length ? (
            <div className="warning-stack">
              {workflow.warnings.map((warning) => (
                <p className="warning-chip" key={warning}>{warning}</p>
              ))}
            </div>
          ) : null}
          {error ? <p className="error">{error}</p> : null}
        </aside>
      </section>

      <section className="analysis-workspace">
        <FileUploadComponent
          files={files}
          setFiles={setFiles}
          testName={testName}
          setTestName={setTestName}
          onSubmit={handleSubmit}
          loading={loading}
        />

        {!workflow?.prediction ? (
          <article className="surface card-stack empty-state-panel">
            <p className="eyebrow">What You Get</p>
            <h2>One run, one decision surface</h2>
            <ul className="list">
              <li>Evidence-first analysis with uploaded screenshots, OCR text, and failed-step context.</li>
              <li>Deterministic root-cause summary and next-run risk from the same run bundle.</li>
              <li>Action output split into recommended fix and preventive tests.</li>
            </ul>
            <div className="analysis-sequence">
              <div className="sequence-step">
                <span className="sequence-index">1</span>
                <div>
                  <strong>Upload the failed run folder</strong>
                  <p className="support-text">AQIS ingests `log.xml`, `STARTLog.txt`, and screenshots if present.</p>
                </div>
              </div>
              <div className="sequence-step">
                <span className="sequence-index">2</span>
                <div>
                  <strong>Review evidence and root cause</strong>
                  <p className="support-text">Start with the failure summary, screenshots, OCR text, and historical context.</p>
                </div>
              </div>
              <div className="sequence-step">
                <span className="sequence-index">3</span>
                <div>
                  <strong>Take the next action</strong>
                  <p className="support-text">Use the AutoFix patch and generated tests to stabilize the next run.</p>
                </div>
              </div>
            </div>
          </article>
        ) : (
          <article className="surface card-stack analysis-summary">
            <div className="card-header">
              <div>
                <p className="eyebrow">Run Summary</p>
                <h2>{workflow.prediction.testName}</h2>
                <p className="support-text">
                  Uploaded {workflow.uploadedAt ? new Date(workflow.uploadedAt).toLocaleString() : "recently"}.
                </p>
              </div>
              <RiskBadge level={workflow.prediction.riskLevel || "UNKNOWN"} />
            </div>

            <div className="metric-grid">
              <div className="metric-card">
                <span className="metric-label">Failure Category</span>
                <strong>{workflow.testSummary?.failureCategory || "Unknown"}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Prediction</span>
                <strong>{workflow.prediction.prediction || "N/A"}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Risk Score</span>
                <strong>{workflow.prediction.riskScore ?? "N/A"}</strong>
              </div>
              <div className="metric-card">
                <span className="metric-label">Recommended Fix</span>
                <strong>{report?.recommendedFix || "Review RCA"}</strong>
              </div>
            </div>

            <div className={`banner banner-${(workflow.prediction.riskLevel || "low").toLowerCase()}`}>
              {workflow.nextRunRecommendation || "Review the evidence and choose the next stabilization action."}
            </div>
          </article>
        )}
      </section>

      {workflow?.prediction ? (
        <div className="analysis-results">
          <section className="evidence-grid">
            <PredictionCard prediction={workflow.prediction} />
            <RCASummaryCard analysis={workflow.analysis} />
          </section>

          <section className="surface split-card">
            <div className="card-stack">
              <div>
                <p className="eyebrow">Evidence</p>
                <h3>Screenshot preview</h3>
              </div>
              {workflow.screenshotPreview?.length ? (
                <div className="screenshot-gallery">
                  {workflow.screenshotPreview.map((preview) => (
                    <figure className="screenshot-card" key={preview.url}>
                      <img className="screenshot-preview" src={preview.url} alt={preview.name || "Uploaded START screenshot"} />
                      <figcaption className="support-text">{preview.name}</figcaption>
                    </figure>
                  ))}
                </div>
              ) : (
                <p className="support-text">No screenshots were uploaded for this run.</p>
              )}
            </div>

            <div className="card-stack">
              <div>
                <p className="eyebrow">OCR Evidence</p>
                <h3>Recovered screen text</h3>
              </div>
              <pre className="code-block code-light">{bundle?.ocrText || "OCR text not available."}</pre>
            </div>
          </section>

          <section className="evidence-grid">
            <AutoFixPanel autofix={workflow.autofix} />
            <TestCasesList testcases={workflow.testcases} />
          </section>

          <section className="evidence-grid">
            <TrendChart prediction={workflow.prediction} />
            <article className="surface card-stack">
              <div>
                <p className="eyebrow">Run History</p>
                <h3>Saved runs behind this prediction</h3>
                <p className="support-text">
                  Review the stored run history AQIS used to judge the next-run risk after this failure.
                </p>
              </div>
              {!history.length ? (
                <p className="support-text">No saved history is available for this testcase yet.</p>
              ) : (
                <div className="history-list">
                  {history.map((run) => (
                    <article className="metric-card history-card" key={`${run.runNumber}-${run.stepName}`}>
                      <div className="card-header">
                        <div>
                          <strong>{`Run ${run.runNumber}`}</strong>
                          <p className="support-text compact-text">{run.stepName}</p>
                        </div>
                        <span className={`mini-badge mini-badge-${(run.status || "LOW").toLowerCase()}`}>
                          {run.status}
                        </span>
                      </div>
                      <div className="history-meta">
                        <span>{`Retries: ${run.retries}`}</span>
                        <span>{`Exceptions: ${run.exceptionCount}`}</span>
                        <span>{`AutoHeal: ${run.autoHealCount}`}</span>
                      </div>
                      {run.errorMessage ? <p className="support-text">{run.errorMessage}</p> : null}
                    </article>
                  ))}
                </div>
              )}
            </article>
          </section>

          <CollapsibleSection title="Analysis Diagnostics" defaultOpen={false}>
            <div className="card-stack">
              <div className="metric-grid">
                {Object.entries(workflow.diagnostics?.phaseTimings || {}).map(([name, value]) => (
                  <div className="metric-card" key={name}>
                    <span className="metric-label">{name}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>
              <pre className="code-block code-light">{JSON.stringify(workflow.testSummary?.uploadedArtifacts || {}, null, 2)}</pre>
            </div>
          </CollapsibleSection>
        </div>
      ) : null}
    </div>
  );
}
