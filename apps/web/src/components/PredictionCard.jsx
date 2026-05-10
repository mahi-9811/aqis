import RiskBadge from "./RiskBadge";

export default function PredictionCard({ prediction }) {
  if (!prediction) {
    return null;
  }

  return (
    <article className="surface card-stack">
      <div className="card-header">
        <div>
          <p className="eyebrow">Next-Run Risk</p>
          <h3>{prediction.testName}</h3>
        </div>
        <RiskBadge level={prediction.riskLevel || "UNKNOWN"} />
      </div>

      <div className="metric-grid">
        <div className="metric-card">
          <span className="metric-label">Risk Score</span>
          <strong>{prediction.riskScore ?? "N/A"}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Prediction</span>
          <strong>{prediction.prediction || "N/A"}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">History Count</span>
          <strong>{prediction.historyCount ?? 0}</strong>
        </div>
      </div>

      <div className={`banner banner-${(prediction.riskLevel || "low").toLowerCase()}`}>
        {prediction.message
          ? prediction.message
          : prediction.riskLevel === "HIGH"
            ? "Run stabilization and preventive checks before the next execution."
            : prediction.riskLevel === "MEDIUM"
              ? "Review RCA and trend signals before the next scheduled run."
              : "Current signals look stable, but keep monitoring drift and timing trends."}
      </div>

      {prediction.reasons?.length ? (
        <div>
          <h4>Reasons</h4>
          <ul className="list">
            {prediction.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}
