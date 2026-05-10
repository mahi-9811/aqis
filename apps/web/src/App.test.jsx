import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";


describe("AQIS dashboard", () => {
  it("renders the failed-run analysis workspace by default", () => {
    render(<App />);
    expect(screen.getByText("Failed Run Analysis")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /analyze one failed start run/i })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Analyze Failed Run" }).length).toBeGreaterThan(0);
  });
});
