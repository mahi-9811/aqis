function normalizeTrendMetrics(prediction) {
  if (!prediction) {
    return [];
  }

  const trends = prediction.trends || {};
  const retryTrendScore = trends.retryTrend === "rising" ? 0.9 : trends.retryTrend === "falling" ? 0.3 : 0.5;
  const driftTrendScore =
    trends.driftTrend === "increasing"
      ? 0.9
      : trends.driftTrend === "intermittent"
        ? 0.65
        : trends.driftTrend === "decreasing"
          ? 0.25
          : 0.45;

  return [
    { label: "Risk Score", value: Number(prediction.riskScore || 0) },
    { label: "Retry Trend", value: retryTrendScore },
    { label: "Timing Drift", value: Math.min(1, Math.abs(Number(trends.timingSlope || 0)) / 100) },
    { label: "Locator Drift", value: driftTrendScore },
    { label: "UI Error Spike", value: trends.uiErrorSpike ? 0.85 : 0.2 }
  ];
}

export default function TrendChart({ prediction }) {
  const metrics = normalizeTrendMetrics(prediction);

  if (!prediction) {
    return (
      <article className="surface card-stack">
        <p className="support-text">Load a prediction to view trend history signals.</p>
      </article>
    );
  }

  if ((prediction.historyCount || 0) < 2) {
    return (
      <article className="surface card-stack">
        <p className="eyebrow">History Signals</p>
        <h3>{prediction.testName}</h3>
        <p className="support-text">
          {prediction.message || "Waiting for additional runs to enable prediction."}
        </p>
      </article>
    );
  }

  return (
    <article className="surface card-stack">
      <div className="card-header">
        <div>
          <p className="eyebrow">History Signals</p>
          <h3>{prediction.testName}</h3>
        </div>
      </div>
      <div className="trend-chart">
        {metrics.map((metric) => (
          <div className="trend-bar" key={metric.label}>
            <div className="trend-label-row">
              <span>{metric.label}</span>
              <strong>{metric.value.toFixed(2)}</strong>
            </div>
            <div className="trend-track">
              <div className="trend-fill" style={{ width: `${metric.value * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="metric-grid">
        <div className="metric-card">
          <span className="metric-label">History Count</span>
          <strong>{prediction.historyCount}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Retry Trend</span>
          <strong>{prediction.trends?.retryTrend || "stable"}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Drift Trend</span>
          <strong>{prediction.trends?.driftTrend || "stable"}</strong>
        </div>
      </div>
    </article>
  );
}
