export default function FileUploadComponent({
  files,
  setFiles,
  testName,
  setTestName,
  onSubmit,
  loading
}) {
  function isScreenshot(file) {
    const name = (file?.name || "").toLowerCase();
    const type = (file?.type || "").toLowerCase();
    return type.startsWith("image/") || [".png", ".jpg", ".jpeg"].some((ext) => name.endsWith(ext));
  }

  function deriveTestNameFromFilename(file) {
    const name = file?.name || "";
    if (!name.includes(".")) {
      return name;
    }
    return name.replace(/\.[^.]+$/, "");
  }

  function deriveTestNameFromFolder(filesFromFolder) {
    const firstPath = filesFromFolder.find((file) => file.webkitRelativePath)?.webkitRelativePath || "";
    const [folderName] = firstPath.split("/");
    return folderName || "";
  }

  function handleFolderSelection(event) {
    const selectedFiles = Array.from(event.target.files || []);
    if (!selectedFiles.length) {
      return;
    }

    const logXml = selectedFiles.find((file) => file.name.toLowerCase() === "log.xml") || null;
    const startLog = selectedFiles.find((file) => file.name.toLowerCase() === "startlog.txt") || null;
    const screenshots = selectedFiles.filter((file) => isScreenshot(file));

    setFiles({
      logXml,
      startLog,
      screenshots
    });

    if (!testName.trim()) {
      const fallbackName = deriveTestNameFromFolder(selectedFiles) || deriveTestNameFromFilename(logXml);
      if (fallbackName) {
        setTestName(fallbackName);
      }
    }
  }

  return (
    <form className="surface card-stack" onSubmit={onSubmit}>
      <div>
        <p className="eyebrow">Run Intake</p>
        <h2>Analyze a failed START run</h2>
        <p className="support-text">
          Select the folder for one failed START execution. AQIS will extract the evidence once,
          then run RCA, next-run risk scoring, AutoFix generation, and preventive test design from the same bundle.
        </p>
      </div>

      <label className="field">
        <span>START artifact folder</span>
        <input
          type="file"
          multiple
          webkitdirectory=""
          directory=""
          onChange={handleFolderSelection}
        />
        <small className="support-text compact-text">
          AQIS looks for `log.xml`, `STARTLog.txt`, and any screenshots inside the selected folder.
        </small>
      </label>

      <label className="field">
        <span>Test case name</span>
        <input
          value={testName}
          onChange={(event) => setTestName(event.target.value)}
          placeholder="Optional if embedded in log.xml"
        />
      </label>

      <div className="upload-summary">
        <span>{files.logXml ? files.logXml.name : "No XML selected"}</span>
        <span>{files.startLog ? files.startLog.name : "No STARTLog selected"}</span>
        <span>
          {files.screenshots?.length
            ? `${files.screenshots.length} screenshot(s) selected`
            : "No screenshots selected"}
        </span>
      </div>

      <button type="submit" disabled={loading || !files.logXml || !files.startLog}>
        {loading ? "Analyzing..." : "Analyze Failed Run"}
      </button>
    </form>
  );
}
