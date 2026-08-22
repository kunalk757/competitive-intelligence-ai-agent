"use client";

interface PlanUsageCardProps {
  healthStatus: "checking" | "healthy" | "error";
  onRefreshHealth: () => void;
  isChecking: boolean;
}

export default function PlanUsageCard({
  healthStatus,
  onRefreshHealth,
  isChecking,
}: PlanUsageCardProps) {
  return (
    <div className="plan-card">
      <div className="plan-header">
        <span className="plan-title">Workspace Plan</span>
        <span className="badge-pill">Free Tier</span>
      </div>
      <div className="health-status-row">
        <span
          className={`status-indicator ${
            healthStatus === "healthy"
              ? "status-online"
              : healthStatus === "error"
              ? "status-offline"
              : "status-online"
          }`}
          style={{
            backgroundColor:
              healthStatus === "healthy"
                ? "var(--success)"
                : healthStatus === "error"
                ? "var(--danger)"
                : "var(--warning)",
          }}
        />
        <span>
          Backend:{" "}
          <strong>
            {healthStatus === "healthy"
              ? "Connected"
              : healthStatus === "error"
              ? "Offline"
              : "Checking..."}
          </strong>
        </span>
        <button
          onClick={onRefreshHealth}
          disabled={isChecking}
          style={{
            marginLeft: "auto",
            background: "none",
            border: "none",
            color: "var(--primary)",
            fontSize: "0.725rem",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          {isChecking ? "..." : "Ping"}
        </button>
      </div>
    </div>
  );
}
