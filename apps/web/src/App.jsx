import { useState } from "react";

import AnalyzeRunPage from "./pages/AnalyzeRunPage";

export default function App() {
  const [workflow, setWorkflow] = useState(null);

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <button className="brand-button" type="button">
          AQIS
        </button>
        <nav className="nav-links">
          <button type="button">Analyze Failed Run</button>
          {workflow ? (
            <button className="secondary-button" type="button" onClick={() => setWorkflow(null)}>
              Clear Current Analysis
            </button>
          ) : null}
        </nav>
      </header>

      <AnalyzeRunPage workflow={workflow} setWorkflow={setWorkflow} />
    </main>
  );
}
