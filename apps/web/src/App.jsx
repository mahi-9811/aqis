import { useState } from "react";

import AnalysisResultsPage from "./pages/AnalysisResultsPage";
import AnalyzeRunPage from "./pages/AnalyzeRunPage";
import HomePage from "./pages/HomePage";
import PredictionPage from "./pages/PredictionPage";
import TrendHistoryPage from "./pages/TrendHistoryPage";
import UploadPage from "./pages/UploadPage";

const NAV = [
  { id: "home",        label: "Home" },
  { id: "upload",      label: "Upload & Analyze" },
  { id: "analyze",     label: "Run Analysis" },
  { id: "results",     label: "Results" },
  { id: "predictions", label: "Predictions" },
  { id: "trends",      label: "Trend History" },
];

export default function App() {
  const [page, setPage] = useState("home");
  const [workflow, setWorkflow] = useState(null);
  const [predictionState, setPredictionState] = useState(null);

  function navigate(target) {
    setPage(target);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderPage() {
    switch (page) {
      case "home":
        return <HomePage navigate={navigate} />;
      case "upload":
        return <UploadPage navigate={navigate} workflow={workflow} setWorkflow={setWorkflow} />;
      case "analyze":
        return <AnalyzeRunPage workflow={workflow} setWorkflow={setWorkflow} navigate={navigate} />;
      case "results":
        return <AnalysisResultsPage workflow={workflow} navigate={navigate} />;
      case "predictions":
        return <PredictionPage predictionState={predictionState} setPredictionState={setPredictionState} />;
      case "trends":
        return <TrendHistoryPage predictionState={predictionState} workflow={workflow} navigate={navigate} />;
      default:
        return <HomePage navigate={navigate} />;
    }
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <button className="brand-button" type="button" onClick={() => navigate("home")}>
          AQIS
        </button>
        <nav className="nav-links">
          {NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={page === item.id ? "nav-active" : ""}
              onClick={() => navigate(item.id)}
            >
              {item.label}
            </button>
          ))}
          {workflow ? (
            <button
              className="secondary-button"
              type="button"
              onClick={() => { setWorkflow(null); navigate("home"); }}
            >
              Clear Analysis
            </button>
          ) : null}
        </nav>
      </header>

      {renderPage()}
    </main>
  );
}
