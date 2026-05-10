export default function TestCasesList({ testcases }) {
  return (
    <article className="surface card-stack">
      <div className="card-header">
        <div>
          <p className="eyebrow">Preventive Coverage</p>
          <h3>Generated tests for the next run</h3>
        </div>
      </div>

      {testcases ? (
        <>
          <p className="support-text">{testcases.recommendation}</p>
          <div className="testcase-list">
            {(testcases.generatedTests || []).map((test) => (
              <div className="testcase-item" key={`${test.name}-${test.type}`}>
                <div className="testcase-meta">
                  <span className={`mini-badge mini-badge-${test.priority.toLowerCase()}`}>{test.priority}</span>
                  <span>{test.type}</span>
                </div>
                <strong>{test.name}</strong>
                <p>{test.description}</p>
              </div>
            ))}
          </div>
          <pre className="code-block">{testcases.automationTemplates?.automationTemplates}</pre>
        </>
      ) : (
        <p className="support-text">Generated preventive tests are not available.</p>
      )}
    </article>
  );
}
