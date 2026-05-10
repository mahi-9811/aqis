import { describeFailureCategory } from "../labels";

export default function RCASummaryCard({ analysis }) {
  const report = analysis?.summary;
  const failure = analysis?.details?.failureAnalyzer;

  return (
    <article className="surface card-stack">
      <div className="card-header">
        <div>
          <p className="eyebrow">Root Cause Analysis</p>
          <h3>{report?.summary || "RCA pending"}</h3>
        </div>
      </div>

      {analysis ? (
        <>
          <div className="metric-grid">
            <div className="metric-card">
              <span className="metric-label">Primary Category</span>
              <strong>{failure?.failureCategory || "Unknown"}</strong>
              <p className="support-text compact-text">
                {describeFailureCategory(failure?.failureCategory)}
              </p>
            </div>
            <div className="metric-card">
              <span className="metric-label">Risk Level</span>
              <strong>{report?.riskLevel || "Unknown"}</strong>
            </div>
          </div>

          <div>
            <h4>Root Causes</h4>
            <ul className="list">
              {(failure?.rootCauses || []).map((cause) => (
                <li key={cause}>{cause}</li>
              ))}
            </ul>
          </div>

          <div>
            <h4>Historical Insights</h4>
            {analysis?.details?.contextRetriever?.historicalInsights?.length ? (
              <ul className="list">
                {analysis.details.contextRetriever.historicalInsights.map((insight) => (
                  <li key={insight}>{insight}</li>
                ))}
              </ul>
            ) : (
              <p className="support-text">No similar failures were found in the available history.</p>
            )}
          </div>
        </>
      ) : (
        <p className="support-text">Detailed RCA data is not available for this run.</p>
      )}
    </article>
  );
}
