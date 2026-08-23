"use client";

import { useState, useMemo } from "react";
import NewsCard, { NewsItemData } from "./NewsCard";

interface NewsViewProps {
  news: NewsItemData[];
  lastUpdated?: string | null;
  onRefreshNews?: () => void;
  isRefreshing?: boolean;
}

const NEWS_TOPIC_CHIPS = [
  "All News",
  "Semiconductors",
  "NVIDIA",
  "AMD",
  "Intel",
  "Qualcomm",
  "AI Hardware",
  "Foundry & TSMC",
];

function formatLastUpdated(timestampStr?: string | null): string {
  if (!timestampStr) return "";
  try {
    const date = new Date(timestampStr);
    if (isNaN(date.getTime())) return timestampStr;
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return timestampStr;
  }
}

export default function NewsView({
  news = [],
  lastUpdated,
  onRefreshNews,
  isRefreshing = false,
}: NewsViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeChip, setActiveChip] = useState("All News");

  const formattedUpdated = formatLastUpdated(lastUpdated);

  // Filter news based on search query and active topic chip
  const filteredNews = useMemo(() => {
    return news.filter((item) => {
      // Search text match
      const query = searchQuery.trim().toLowerCase();
      const matchesQuery =
        !query ||
        item.title.toLowerCase().includes(query) ||
        (item.description && item.description.toLowerCase().includes(query)) ||
        (item.source && item.source.toLowerCase().includes(query)) ||
        (item.company && item.company.toLowerCase().includes(query));

      if (!matchesQuery) return false;

      // Chip match
      if (activeChip === "All News") return true;
      const chipLower = activeChip.toLowerCase();
      const combined = `${item.title} ${item.description || ""} ${item.company || ""} ${item.category || ""}`.toLowerCase();
      return combined.includes(chipLower);
    });
  }, [news, searchQuery, activeChip]);

  return (
    <div className="news-page-container">
      {/* Top Header Row */}
      <div
        className="companies-header-row"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "1rem",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h1 className="dashboard-title">News</h1>
          <p className="dashboard-subtitle">
            Real-time industry developments, competitor announcements, and market signals.
          </p>
        </div>

        {/* Sync Status & Action */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
          {onRefreshNews && (
            <button
              type="button"
              className="btn-primary"
              onClick={onRefreshNews}
              disabled={isRefreshing}
              style={{
                fontSize: "0.85rem",
                padding: "0.5rem 1rem",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
              }}
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                style={{
                  animation: isRefreshing ? "spin 1s linear infinite" : "none",
                }}
              >
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
              </svg>
              {isRefreshing ? "Syncing GNews..." : "⚡ Sync News"}
            </button>
          )}
        </div>
      </div>

      {/* Search & Topic Filters */}
      <div className="dashboard-card" style={{ padding: "1.25rem" }}>
        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={{ position: "relative", flex: 1, minWidth: "260px" }}>
            <span
              style={{
                position: "absolute",
                left: "0.85rem",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
              }}
            >
              🔍
            </span>
            <input
              type="text"
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search news by headline, company, topic, or source..."
              style={{
                width: "100%",
                paddingLeft: "2.4rem",
                paddingRight: searchQuery ? "2.5rem" : "1rem",
                background: "#ffffff",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-main)",
                fontSize: "0.925rem",
                height: "44px",
              }}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                style={{
                  position: "absolute",
                  right: "0.85rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  fontSize: "1rem",
                  padding: "0.2rem",
                }}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* Topic Filter Chips */}
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            marginTop: "1rem",
            alignItems: "center",
          }}
        >
          <span
            style={{
              fontSize: "0.8rem",
              color: "var(--text-secondary)",
              fontWeight: 600,
              marginRight: "0.25rem",
            }}
          >
            Topics:
          </span>
          {NEWS_TOPIC_CHIPS.map((chip) => {
            const isActive = activeChip === chip;
            return (
              <button
                key={chip}
                type="button"
                onClick={() => setActiveChip(chip)}
                style={{
                  fontSize: "0.775rem",
                  fontWeight: isActive ? 700 : 500,
                  padding: "0.3rem 0.75rem",
                  borderRadius: "16px",
                  background: isActive ? "var(--primary)" : "#f1f5f9",
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  border: isActive
                    ? "1px solid var(--primary)"
                    : "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {chip}
              </button>
            );
          })}
        </div>
      </div>

      {/* Meta Count & Sync Info Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.875rem",
          color: "var(--text-secondary)",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <span>
          Showing <strong>{filteredNews.length}</strong> {filteredNews.length === 1 ? "article" : "articles"}
          {searchQuery ? ` matching "${searchQuery}"` : ""}
        </span>

        {formattedUpdated && (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Last database sync: <strong>{formattedUpdated}</strong>
          </span>
        )}
      </div>

      {/* 3-Column Desktop / 2-Column Tablet / 1-Column Mobile News Grid */}
      {filteredNews.length > 0 ? (
        <div className="news-grid">
          {filteredNews.map((item, idx) => (
            <NewsCard key={item.id || item.url || `news-${idx}`} item={item} />
          ))}
        </div>
      ) : (
        <div
          className="dashboard-card"
          style={{
            padding: "3.5rem 1.5rem",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1rem",
          }}
        >
          <span style={{ fontSize: "3rem" }}>📰</span>
          <h2
            style={{
              fontSize: "1.3rem",
              fontWeight: 700,
              color: "var(--text-main)",
            }}
          >
            No Articles Found
          </h2>
          <p
            style={{
              color: "var(--text-secondary)",
              maxWidth: "480px",
              fontSize: "0.9rem",
              lineHeight: 1.5,
            }}
          >
            No news articles match your filter criteria. Try changing your search query or triggering a manual sync from GNews.
          </p>
          {onRefreshNews && (
            <button
              type="button"
              className="btn-primary"
              onClick={onRefreshNews}
              disabled={isRefreshing}
            >
              {isRefreshing ? "Syncing..." : "⚡ Sync News Now"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
