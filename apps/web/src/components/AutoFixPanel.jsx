export default function AutoFixPanel({ autofix }) {
  return (
    <article className="surface card-stack">
      <div className="card-header">
        <div>
          <p className="eyebrow">Recommended Fix</p>
          <h3>Safe self-healing recommendation</h3>
        </div>
      </div>

      {autofix ? (
        <>
          <p className="support-text">{autofix.message}</p>
          <div className="metric-grid">
            <div className="metric-card">
              <span className="metric-label">Confidence</span>
              <strong>{autofix.confidence}</strong>
            </div>
            <div className="metric-card">
              <span className="metric-label">Recommended</span>
              <strong>{autofix.recommended ? "Yes" : "No"}</strong>
            </div>
          </div>

          {autofix.fixes?.length ? (
            <ul className="list">
              {autofix.fixes.map((fix) => (
                <li key={`${fix.fixType}-${fix.affectedStep}`}>
                  <strong>{fix.fixType}:</strong> {fix.description}
                </li>
              ))}
            </ul>
          ) : (
            <p className="support-text">AutoFix not recommended for this failure type.</p>
          )}

          <pre className="code-block">{autofix.patch}</pre>
        </>
      ) : (
        <p className="support-text">AutoFix recommendations are not available.</p>
      )}
    </article>
  );
}
