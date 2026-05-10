import TrendChart from "../components/TrendChart";

export default function TrendHistoryPage({ predictionState, workflow, navigate }) {
  const prediction = predictionState?.prediction || workflow?.prediction || null;

  return (
    <div className="page-grid">
      <TrendChart prediction={prediction} />
      <section className="surface card-stack">
        <p className="eyebrow">History Guidance</p>
        <h2>What to watch between runs</h2>
        <ul className="list">
          <li>Rising retry trend usually means synchronization issues are growing.</li>
          <li>Timing drift suggests page readiness or backend responsiveness is changing.</li>
          <li>Locator drift and UI error spikes often predict the next failure before release.</li>
        </ul>
        {!prediction ? (
          <button type="button" onClick={() => navigate("predictions")}>
            Load A Prediction
          </button>
        ) : null}
      </section>
    </div>
  );
}
