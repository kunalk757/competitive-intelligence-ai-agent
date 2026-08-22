"use client";

import NewsList from "./NewsList";
import AlertList from "./AlertList";
import { NewsItemData } from "./NewsCard";

interface DashboardViewProps {
  news?: NewsItemData[];
  lastUpdated?: string | null;
  onRefreshNews?: () => void;
  isRefreshing?: boolean;
  onNewResearchClick: (initialGoal?: string) => void;
}

export default function DashboardView({
  news = [],
  lastUpdated,
  onRefreshNews,
  isRefreshing = false,
  onNewResearchClick,
}: DashboardViewProps) {
  return (
    <div>
      {/* Dashboard Top Heading */}
      <div className="dashboard-heading-row">
        <div>
          <h1 className="dashboard-title">Good morning, Alex</h1>
          <p className="dashboard-subtitle">
            Here&apos;s what&apos;s happening in your intelligence dashboard today.
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

      {/* 2-Column Content Grid */}
      <div className="dashboard-grid">
        <NewsList
          news={news}
          lastUpdated={lastUpdated}
          onRefreshNews={onRefreshNews}
          isRefreshing={isRefreshing}
          onViewAll={() =>
            onNewResearchClick(
              "Analyze recent semiconductor and AI chip competitor news."
            )
          }
        />

        {/* Intelligence Alerts remain empty until backed by real backend alert triggers */}
        <AlertList
          alerts={[]}
          onViewAll={() =>
            onNewResearchClick(
              "Investigate all high-priority patent and competitor alerts."
            )
          }
        />
      </div>
    </div>
  );
}
