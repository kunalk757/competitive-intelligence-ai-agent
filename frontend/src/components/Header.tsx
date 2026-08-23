"use client";

import SearchBar from "./SearchBar";

interface HeaderProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onToggleMobileSidebar: () => void;
  onNewResearchClick: () => void;
}

export default function Header({
  searchQuery,
  onSearchChange,
  onToggleMobileSidebar,
}: HeaderProps) {
  return (
    <header className="top-header">
      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
        <button
          className="mobile-toggle-btn"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle Navigation"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
        <SearchBar value={searchQuery} onChange={onSearchChange} />
      </div>

      <div className="header-actions">
        {/* Notification Bell */}
        <button className="icon-btn" aria-label="Notifications" title="Notifications">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="notification-dot" />
        </button>
      </div>
    </header>
  );
}
