export function describeFailureCategory(category) {
  switch (category) {
    case "PAGE_LOAD_TIMING":
      return "Page was not fully loaded before interaction.";
    case "LOCATOR_NOT_FOUND":
      return "AQIS could not find the expected UI element.";
    case "FLAKY_TEST":
      return "The scenario behaved inconsistently across retries.";
    case "ENVIRONMENT_INSTABILITY":
      return "Environment or SAP UI5 instability affected the run.";
    default:
      return "AQIS did not identify a stronger deterministic category.";
  }
}
