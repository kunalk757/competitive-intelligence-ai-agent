"use client";

import PlanUsageCard from "./PlanUsageCard";

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  isOpen: boolean;
  onCloseMobile: () => void;
  healthStatus: "checking" | "healthy" | "error";
  onRefreshHealth: () => void;
  isCheckingHealth: boolean;
}

interface NavItem {
  id: string;
  label: string;
  comingSoon?: boolean;
  icon: (props: { className?: string }) => React.ReactNode;
}

const navItems: NavItem[] = [
  {
    id: "intelligence",
    label: "AI Intelligence",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-4 4 4 4 0 0 1-4-4V6a4 4 0 0 1 4-4Z" />
        <path d="M18 14v1a6 6 0 0 1-12 0v-1" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    ),
  },
  {
    id: "dashboard",
    label: "Dashboard",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
      </svg>
    ),
  },
  {
    id: "research",
    label: "Research",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="11" cy="11" r="8" />
        <line x1="21" y1="21" x2="16.65" y2="16.65" />
      </svg>
    ),
  },
  {
    id: "companies",
    label: "Companies",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="2" y="7" width="20" height="14" rx="2" />
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
      </svg>
    ),
  },
  {
    id: "news",
    label: "News",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
        <path d="M18 14h-8" />
        <path d="M15 18h-5" />
        <path d="M10 6h8v4h-8V6Z" />
      </svg>
    ),
  },
  {
    id: "papers",
    label: "Research Papers",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    ),
  },
  {
    id: "settings",
    label: "Settings",
    icon: () => (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    ),
  },
];

export default function Sidebar({
  activeTab,
  onTabChange,
  isOpen,
  onCloseMobile,
  healthStatus,
  onRefreshHealth,
  isCheckingHealth,
}: SidebarProps) {
  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <div>
        <div className="sidebar-header">
          <div className="logo-icon">CI</div>
          <div className="logo-text">
            <h2>CI Agent</h2>
            <p>Competitive Intelligence</p>
          </div>
        </div>

        <ul className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={`nav-item ${isActive ? "active" : ""}`}
                  style={{ width: "100%", textAlign: "left" }}
                  onClick={() => {
                    onTabChange(item.id);
                    onCloseMobile();
                  }}
                >
                  <div className="nav-item-content">
                    <Icon />
                    <span>{item.label}</span>
                  </div>
                  {item.comingSoon && (
                    <span className="badge-coming-soon">Coming Soon</span>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </div>

      <div className="sidebar-footer">
        <PlanUsageCard
          healthStatus={healthStatus}
          onRefreshHealth={onRefreshHealth}
          isChecking={isCheckingHealth}
        />
      </div>
    </aside>
  );
}
