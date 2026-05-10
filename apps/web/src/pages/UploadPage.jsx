import { useState } from "react";

import FileUploadComponent from "../components/FileUploadComponent";
import TrendChart from "../components/TrendChart";
import { runPostExecutionWorkflow } from "../api";

export default function UploadPage({ navigate, workflow, setWorkflow }) {
  const [testName, setTestName] = useState("");
  const [files, setFiles] = useState({
    logXml: null,
    startLog: null,
    screenshots: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
      const screenshotPreview = (files.screenshots || []).map((file) => ({
        name: file.name,
        url: URL.createObjectURL(file)
      }));
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
        screenshotPreview,
        uploadedAt: new Date().toISOString()
      });
      navigate("results");
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-grid">
      <FileUploadComponent
        files={files}
        setFiles={setFiles}
        testName={testName}
        setTestName={setTestName}
        onSubmit={handleSubmit}
        loading={loading}
      />

      <article className="surface card-stack">
        <p className="eyebrow">How it works</p>
        <h3>Post-execution workflow</h3>
        <ol className="list ordered-list">
          <li>Select the folder that contains the completed START run artifacts.</li>
          <li>AQIS runs one canonical analysis flow across prediction, RCA, AutoFix, and test generation.</li>
          <li>You review the results on the analysis page.</li>
        </ol>
        {workflow?.warnings?.length ? (
          <ul className="list">
            {workflow.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        ) : null}
        {error ? <p className="error">{error}</p> : null}
      </article>

      <TrendChart prediction={workflow?.prediction || null} />
    </div>
  );
}
