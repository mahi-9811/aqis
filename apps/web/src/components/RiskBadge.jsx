export default function RiskBadge({ level = "UNKNOWN" }) {
  const normalized = String(level || "unknown").toLowerCase();
  return <span className={`risk-badge risk-badge-${normalized}`}>{level}</span>;
}
