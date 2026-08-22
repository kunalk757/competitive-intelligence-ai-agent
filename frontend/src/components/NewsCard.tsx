"use client";

import { useState } from "react";

export interface NewsItemData {
  id?: string;
  title: string;
  source: string;
  published_at?: string;
  time?: string;
  description?: string;
  category?: string;
  company_tag?: string;
  companyTag?: string;
  url?: string;
  image_url?: string;
  thumbnailBadge?: string;
}

interface NewsCardProps {
  item: NewsItemData;
}

export default function NewsCard({ item }: NewsCardProps) {
  const [isSaved, setIsSaved] = useState(false);
  const [imgError, setImgError] = useState(false);

  const displayTime = item.published_at || item.time || "Recent";
  const displayCompany = item.company_tag || item.companyTag;
  const displayCategory = item.category || "News";

  const handleCardClick = () => {
    if (item.url) {
      window.open(item.url, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <article
      className="news-item"
      onClick={handleCardClick}
      style={{
        cursor: item.url ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      {/* Thumbnail or Badge Fallback */}
      <div className="news-thumbnail" style={{ overflow: "hidden" }}>
        {item.image_url && !imgError ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={item.image_url}
            alt={item.title}
            onError={() => setImgError(true)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        ) : (
          <span>
            {item.thumbnailBadge ||
              (item.source ? item.source.slice(0, 3).toUpperCase() : "NW")}
          </span>
        )}
      </div>

      <div className="news-content">
        <div>
          <div className="news-meta-top">
            <div className="news-source-time">
              <strong>{item.source}</strong>
              <span>•</span>
              <span>{displayTime}</span>
            </div>
            <div
              className="news-actions"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                type="button"
                className="action-icon-btn"
                onClick={() => setIsSaved(!isSaved)}
                title={isSaved ? "Saved" : "Save article"}
                style={{ color: isSaved ? "var(--primary)" : undefined }}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill={isSaved ? "currentColor" : "none"}
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
                </svg>
              </button>
              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="action-icon-btn"
                  title="Open source article"
                  onClick={(e) => e.stopPropagation()}
                >
                  <svg
                    width="15"
                    height="15"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              )}
            </div>
          </div>

          <h3 className="news-title">
            {item.url ? (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "inherit", textDecoration: "none" }}
                onClick={(e) => e.stopPropagation()}
              >
                {item.title}
              </a>
            ) : (
              item.title
            )}
          </h3>

          {item.description && (
            <p className="news-desc">{item.description}</p>
          )}
        </div>

        <div className="news-tags-actions">
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            {displayCompany && (
              <span className="tag-pill tag-company">{displayCompany}</span>
            )}
            {displayCategory && (
              <span className="tag-pill">{displayCategory}</span>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}
