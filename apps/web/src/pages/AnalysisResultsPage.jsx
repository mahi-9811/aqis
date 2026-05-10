import CollapsibleSection from "../components/CollapsibleSection";
import PredictionCard from "../components/PredictionCard";
import RCASummaryCard from "../components/RCASummaryCard";
import AutoFixPanel from "../components/AutoFixPanel";
import TestCasesList from "../components/TestCasesList";

export default function AnalysisResultsPage({ workflow, navigate }) {
  if (!workflow?.prediction) {
    return (
      <section className="surface card-stack">
        <p className="eyebrow">Analysis Results</p>
        <h2>No uploaded run available</h2>
        <p className="support-text">Upload START artifacts first to populate this page.</p>
        <button type="button" onClick={() => navigate("upload")}>
          Go To Upload
        </button>
      </section>
    );
  }

  const bundle = workflow.bundle || workflow.prediction.bundle;
  const report = workflow.analysis?.summary;

  return (
    <div className="results-layout">
      <section className="surface card-stack">
        <p className="eyebrow">Post-Execution Results</p>
        <h2>{workflow.prediction.testName}</h2>
        <p className="support-text">
          Uploaded {workflow.uploadedAt ? new Date(workflow.uploadedAt).toLocaleString() : "recently"}.
        </p>
        {workflow.warnings?.length ? (
          <ul className="list">
            {workflow.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <CollapsibleSection title="Test Summary">
        <PredictionCard prediction={workflow.prediction} />
      </CollapsibleSection>

      <CollapsibleSection title="Root Cause Analysis">
        <RCASummaryCard analysis={workflow.analysis} />
      </CollapsibleSection>

      <CollapsibleSection title="AutoFix Suggestions">
        <AutoFixPanel autofix={workflow.autofix} />
      </CollapsibleSection>

      <CollapsibleSection title="Screenshot Preview + OCR">
        <div className="surface split-card">
          <div>
            <h3>Screenshots</h3>
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
              <p className="support-text">No screenshots uploaded for this run.</p>
            )}
          </div>
          <div>
            <h3>OCR Text</h3>
            <pre className="code-block code-light">{bundle?.ocrText || "OCR text not available."}</pre>
          </div>
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="Generated Test Cases">
        <TestCasesList testcases={workflow.testcases} />
      </CollapsibleSection>

      <CollapsibleSection title="Risk Update For Next Run">
        <div className="surface card-stack">
          <h3>{report?.recommendedFix || "No fix recommendation available"}</h3>
          <p className="support-text">
            {workflow.nextRunRecommendation || "AQIS will use the current post-execution signals to update the next-run risk prediction."}
          </p>
          {workflow.prediction.reasons?.length ? (
            <ul className="list">
              {workflow.prediction.reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          ) : null}
        </div>
      </CollapsibleSection>
    </div>
  );
}
