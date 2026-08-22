"use client";

import NewsCard, { NewsItemData } from "./NewsCard";

interface NewsListProps {
  news?: NewsItemData[];
  onViewAll?: () => void;
}

export default function NewsList({ news = [], onViewAll }: NewsListProps) {
  const hasNews = news && news.length > 0;

  return (
    <div className="dashboard-card">
      <div className="card-header-row" style={{ alignItems: "flex-start", marginBottom: "1rem" }}>
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
          {/* Subtle Update Schedule Indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              marginTop: "0.25rem",
            }}
          >
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
            <span>News updates twice daily • 10:00 AM &amp; 10:00 PM IST</span>
          </div>
        </div>

        <span
          className="link-btn"
          style={{
            color: hasNews ? "var(--primary)" : "var(--text-muted)",
            cursor: hasNews ? "pointer" : "default",
            pointerEvents: hasNews ? "auto" : "none",
            marginTop: "0.15rem",
          }}
          onClick={hasNews ? onViewAll : undefined}
        >
          View all
        </span>
      </div>

      {hasNews ? (
        <div className="news-list">
          {news.map((item) => (
            <NewsCard key={item.id} item={item} />
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
            No intelligence updates available yet.
          </p>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.825rem" }}>
            Connect a news source to start monitoring.
          </p>
        </div>
      )}
    </div>
  );
}
