export default function HomePage({ navigate }) {
  return (
    <section className="hero-panel">
      <div className="hero-copy">
        <p className="eyebrow">AQIS Dashboard</p>
        <h1>Predict failures, explain root causes, and prevent the next one.</h1>
        <p className="lede">
          AQIS gives QA engineers and managers one place to upload START artifacts, review next-run risk,
          inspect deterministic RCA, validate AutoFix recommendations, and prioritize preventive tests.
        </p>
        <div className="cta-row">
          <button type="button" onClick={() => navigate("upload")}>
            Upload START Artifacts
          </button>
          <button className="secondary-button" type="button" onClick={() => navigate("predictions")}>
            View Predictions
          </button>
        </div>
      </div>
      <div className="hero-stats surface">
        <h3>What this MVP shows</h3>
        <ul className="list">
          <li>Pre-execution prediction with risk and reasons</li>
          <li>Post-execution RCA, AutoFix, and preventive test generation</li>
          <li>Trend signals across retries, timing, and drift</li>
        </ul>
      </div>
    </section>
  );
}
