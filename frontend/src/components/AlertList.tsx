"use client";

import AlertCard, { AlertItemData } from "./AlertCard";

interface AlertListProps {
  alerts?: AlertItemData[];
  onViewAll?: () => void;
}

export default function AlertList({ alerts = [], onViewAll }: AlertListProps) {
  const hasAlerts = alerts && alerts.length > 0;

  return (
    <div className="dashboard-card">
      <div className="card-header-row">
        <h2 className="card-title">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ color: "#d97706" }}
          >
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          Intelligence Alerts
        </h2>
        <span
          className="link-btn"
          style={{
            color: hasAlerts ? "var(--primary)" : "var(--text-muted)",
            cursor: hasAlerts ? "pointer" : "default",
            pointerEvents: hasAlerts ? "auto" : "none",
          }}
          onClick={hasAlerts ? onViewAll : undefined}
        >
          View all
        </span>
      </div>

      {hasAlerts ? (
        <div className="alerts-list">
          {alerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      ) : (
        <div
          style={{
            padding: "2.75rem 1.5rem",
            textAlign: "center",
            border: "1px dashed var(--border-subtle)",
            borderRadius: "var(--radius-md)",
            backgroundColor: "#fafbfc",
          }}
        >
          <div
            style={{
              width: "44px",
              height: "44px",
              margin: "0 auto 0.75rem",
              borderRadius: "50%",
              backgroundColor: "#fef3c7",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#d97706",
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </div>
          <p
            style={{
              fontWeight: 600,
              color: "var(--text-main)",
              fontSize: "0.925rem",
              marginBottom: "0.25rem",
            }}
          >
            No new intelligence alerts
          </p>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.825rem" }}>
            Alerts will appear when the agent detects important developments.
          </p>
        </div>
      )}
    </div>
  );
}
