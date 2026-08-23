"use client";

import NewsList from "./NewsList";
import { NewsItemData } from "./NewsCard";

interface DashboardViewProps {
  news?: NewsItemData[];
  lastUpdated?: string | null;
  onRefreshNews?: () => void;
  isRefreshing?: boolean;
  onNewResearchClick: (initialGoal?: string) => void;
  onViewAllNews?: () => void;
}

export default function DashboardView({
  news = [],
  lastUpdated,
  onRefreshNews,
  isRefreshing = false,
  onNewResearchClick,
  onViewAllNews,
}: DashboardViewProps) {
  return (
    <div>
      {/* Dashboard Top Heading */}
      <div className="dashboard-heading-row">
        <div>
          <h1 className="dashboard-title">Competitive Intelligence Dashboard</h1>
          <p className="dashboard-subtitle">
            Real-time market intelligence, competitor tracking, and synthesized research.
          </p>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={() => onNewResearchClick()}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          + New Research
        </button>
      </div>

      {/* Rebalanced Content Layout */}
      <div className="dashboard-grid">
        <NewsList
          news={news}
          lastUpdated={lastUpdated}
          onRefreshNews={onRefreshNews}
          isRefreshing={isRefreshing}
          onViewAll={
            onViewAllNews ||
            (() =>
              onNewResearchClick(
                "Analyze recent semiconductor and AI chip competitor news."
              ))
          }
        />
      </div>
    </div>
  );
}
