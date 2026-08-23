"use client";

import NewsCard, { NewsItemData } from "./NewsCard";

interface NewsListProps {
  news?: NewsItemData[];
  lastUpdated?: string | null;
  onViewAll?: () => void;
  onRefreshNews?: () => void;
  isRefreshing?: boolean;
}

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

export default function NewsList({
  news = [],
  lastUpdated,
  onViewAll,
  onRefreshNews,
  isRefreshing = false,
}: NewsListProps) {
  const hasNews = news && news.length > 0;
  const formattedUpdated = formatLastUpdated(lastUpdated);

  return (
    <div className="dashboard-card">
      <div
        className="card-header-row"
        style={{ alignItems: "flex-start", marginBottom: "1rem" }}
      >
        <div>
          <h2 className="card-title">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ color: "var(--primary)" }}
            >
              <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
              <path d="M18 14h-8" />
              <path d="M15 18h-5" />
            </svg>
            Latest News
          </h2>
          {/* Subtle Update Schedule & Last Updated Indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "0.4rem",
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              marginTop: "0.25rem",
            }}
          >
            <span style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
              <svg
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                style={{ color: "var(--primary)", opacity: 0.85 }}
              >
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
              <span>Updates daily at 10:00 AM &amp; 10:00 PM IST</span>
            </span>

            {formattedUpdated && (
              <>
                <span>•</span>
                <span style={{ color: "var(--text-secondary)" }}>
                  Last updated: {formattedUpdated}
                </span>
              </>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {onRefreshNews && (
            <button
              type="button"
              onClick={onRefreshNews}
              disabled={isRefreshing}
              title="Manually trigger news sync"
              style={{
                background: "transparent",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "0.3rem 0.55rem",
                fontSize: "0.75rem",
                fontWeight: 600,
                color: "var(--text-secondary)",
                cursor: isRefreshing ? "not-allowed" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.3rem",
                transition: "all 0.15s ease",
              }}
              onMouseEnter={(e) => {
                if (!isRefreshing) e.currentTarget.style.color = "var(--primary)";
              }}
              onMouseLeave={(e) => {
                if (!isRefreshing) e.currentTarget.style.color = "var(--text-secondary)";
              }}
            >
              <svg
                width="12"
                height="12"
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
              {isRefreshing ? "Syncing..." : "Refresh"}
            </button>
          )}

          <span
            className="link-btn"
            style={{
              color: hasNews ? "var(--primary)" : "var(--text-muted)",
              cursor: hasNews ? "pointer" : "default",
              pointerEvents: hasNews ? "auto" : "none",
            }}
            onClick={hasNews ? onViewAll : undefined}
          >
            View all
          </span>
        </div>
      </div>

      {hasNews ? (
        <div className="news-grid" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
          {news.map((item, idx) => (
            <NewsCard key={item.id || item.url || `news-${idx}`} item={item} />
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
              backgroundColor: "var(--primary-light)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--primary)",
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
              <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
              <path d="M18 14h-8" />
              <path d="M15 18h-5" />
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
            No saved news articles in database yet.
          </p>
          <p
            style={{
              color: "var(--text-secondary)",
              fontSize: "0.825rem",
              marginBottom: "1rem",
            }}
          >
            Scheduled updates run twice daily (10:00 AM &amp; 10:00 PM IST), or trigger an immediate sync below.
          </p>
          {onRefreshNews && (
            <button
              type="button"
              className="btn-primary"
              onClick={onRefreshNews}
              disabled={isRefreshing}
              style={{
                fontSize: "0.825rem",
                padding: "0.45rem 1rem",
                margin: "0 auto",
              }}
            >
              {isRefreshing ? "Fetching Latest News..." : "⚡ Sync News Now"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
