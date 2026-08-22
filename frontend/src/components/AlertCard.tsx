"use client";

export type AlertType = "patent" | "trend" | "update" | "competitor";
export type AlertPriority = "high" | "medium" | "low";

export interface AlertItemData {
  id: string;
  type: AlertType;
  title: string;
  description: string;
  time: string;
  priority: AlertPriority;
}

interface AlertCardProps {
  alert: AlertItemData;
}

export default function AlertCard({ alert }: AlertCardProps) {
  const getIcon = () => {
    switch (alert.type) {
      case "patent":
        return (
          <div className="alert-icon-box alert-icon-patent">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </div>
        );
      case "trend":
        return (
          <div className="alert-icon-box alert-icon-trend">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
          </div>
        );
      case "update":
        return (
          <div className="alert-icon-box alert-icon-update">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
        );
      case "competitor":
      default:
        return (
          <div className="alert-icon-box alert-icon-competitor">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
        );
    }
  };

  const getPriorityClass = () => {
    switch (alert.priority) {
      case "high":
        return "priority-pill priority-high";
      case "medium":
        return "priority-pill priority-medium";
      case "low":
      default:
        return "priority-pill priority-low";
    }
  };

  return (
    <div className="alert-item">
      {getIcon()}
      <div className="alert-body">
        <div className="alert-header">
          <h4 className="alert-title">{alert.title}</h4>
          <span className={getPriorityClass()}>{alert.priority}</span>
        </div>
        <p className="alert-desc">{alert.description}</p>
        <span className="alert-time">{alert.time}</span>
      </div>
    </div>
  );
}
