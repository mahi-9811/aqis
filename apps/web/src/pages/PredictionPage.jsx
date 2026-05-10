import { useRef, useState } from "react";

import PredictionCard from "../components/PredictionCard";
import TrendChart from "../components/TrendChart";
import { fetchPrediction } from "../api";

export default function PredictionPage({ predictionState, setPredictionState }) {
  const [testName, setTestName] = useState(predictionState?.prediction?.testName || "LoginTest");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const historyRef = useRef(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const prediction = await fetchPrediction(testName);
      setPredictionState({ prediction, loadedAt: new Date().toISOString() });
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  function scrollToHistory() {
    historyRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const prediction = predictionState?.prediction || null;
  const savedHistory = prediction?.history || [];

  return (
    <div className="page-grid">
      <section className="surface card-stack">
        <div>
          <p className="eyebrow">Pre-Execution</p>
          <h2>Predict the next START run</h2>
          <p className="support-text">
            Enter a known test case to fetch its current risk score, prediction, and trends from history.
          </p>
        </div>

        <form className="inline-form" onSubmit={handleSubmit}>
          <input value={testName} onChange={(event) => setTestName(event.target.value)} placeholder="Enter test case name" />
          <button type="submit" disabled={loading || !testName.trim()}>
            {loading ? "Loading..." : "View Prediction"}
          </button>
        </form>
        {prediction ? (
          <button className="secondary-button" type="button" onClick={scrollToHistory}>
            Scroll to saved history
          </button>
        ) : null}
        {error ? <p className="error">{error}</p> : null}
      </section>

      <PredictionCard prediction={prediction} />
      <TrendChart prediction={prediction} />

      <section className="surface card-stack" ref={historyRef}>
        <div>
          <p className="eyebrow">Saved History</p>
          <h3>{prediction?.testName || "Testcase history"}</h3>
          <p className="support-text">
            Review the saved runs AQIS is using to calculate the next-run prediction.
          </p>
        </div>
        {!prediction ? (
          <p className="support-text">Load a prediction to view saved testcase history.</p>
        ) : !savedHistory.length ? (
          <p className="support-text">No saved history is available for this testcase yet.</p>
        ) : (
          <div className="history-list">
            {savedHistory.map((run) => (
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
      </section>
    </div>
  );
}
