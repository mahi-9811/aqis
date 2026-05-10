const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/predictions";

async function parseJsonResponse(response, fallbackMessage) {
  if (!response.ok) {
    let detail = fallbackMessage;
    try {
      const payload = await response.json();
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep fallback error when the payload is not JSON.
    }
    throw new Error(detail);
  }

  return response.json();
}

export async function fetchPrediction(testName) {
  const response = await fetch(`${API_BASE_URL}/${encodeURIComponent(testName)}`);
  return parseJsonResponse(response, "Unable to load prediction.");
}

export async function analyzeArtifacts({ testName, logXml, startLog, screenshots }) {
  const formData = new FormData();
  formData.append("logXml", logXml);
  formData.append("startLog", startLog);
  for (const screenshot of screenshots || []) {
    formData.append("screenshot", screenshot);
  }
  if (testName?.trim()) {
    formData.append("testName", testName.trim());
  }

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData
  });

  return parseJsonResponse(response, "Artifact upload failed.");
}

export async function runPostExecutionWorkflow({ testName, logXml, startLog, screenshots }) {
  return analyzeArtifacts({ testName, logXml, startLog, screenshots });
}
