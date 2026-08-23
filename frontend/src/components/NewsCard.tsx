"use client";

import { useState } from "react";

export interface NewsItemData {
  id?: string;
  title: string;
  source?: string;
  source_name?: string;
  published_at?: string;
  fetched_at?: string;
  time?: string;
  description?: string;
  category?: string;
  company?: string;
  company_tag?: string;
  companyTag?: string;
  url?: string;
  source_url?: string;
  image_url?: string | null;
  image?: string | null;
  thumbnailBadge?: string;
}

interface NewsCardProps {
  item: NewsItemData;
}

function formatNewsDate(dateStr?: string): string {
  if (!dateStr) return "Recent";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return dateStr;
  }
}

export default function NewsCard({ item }: NewsCardProps) {
  const [isSaved, setIsSaved] = useState(false);
  const [failedImages, setFailedImages] = useState<{ [url: string]: boolean }>({});

  const displayTime = formatNewsDate(item.published_at || item.time);
  const displaySource = item.source || item.source_name || "Intelligence News";
  const displayCompany = item.company_tag || item.companyTag || item.company;
  const displayCategory = item.category || "Technology";
  const articleUrl = item.url || item.source_url;
  const rawImageUrl = item.image_url || item.image;
  const isImageFailed = Boolean(rawImageUrl && failedImages[rawImageUrl]);
  const hasValidImage = Boolean(rawImageUrl && rawImageUrl.trim() !== "" && !isImageFailed);

  const handleCardClick = () => {
    if (articleUrl) {
      window.open(articleUrl, "_blank", "noopener,noreferrer");
    }
  };

  const handleOpenSource = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (articleUrl) {
      window.open(articleUrl, "_blank", "noopener,noreferrer");
    }
  };

  const handleToggleSave = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsSaved(!isSaved);
  };

  return (
    <article
      className="news-card"
      onClick={handleCardClick}
      style={{
        cursor: articleUrl ? "pointer" : "default",
        userSelect: "none",
      }}
    >
      {/* Top News Article Image / Clean Fallback Container */}
      <div className="news-card-image-wrap">
        {hasValidImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={rawImageUrl!}
            alt={item.title}
            onError={() => {
              if (rawImageUrl) {
                setFailedImages((prev) => ({ ...prev, [rawImageUrl]: true }));
              }
            }}
            className="news-card-image"
            loading="lazy"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="news-card-image-fallback">
            <span className="news-card-fallback-badge">
              📰 {item.thumbnailBadge || displaySource.slice(0, 3).toUpperCase()}
            </span>
            <span className="news-card-fallback-caption">
              {displaySource}
            </span>
          </div>
        )}
      </div>

      {/* Card Body */}
      <div className="news-card-body">
        <div className="news-card-content">
          {/* Source & Publication Date & Bookmark Action */}
          <div className="news-card-meta">
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span className="news-card-source">
                🏢 {displaySource}
              </span>
              <span>•</span>
              <span className="news-card-date">
                🗓️ {displayTime}
              </span>
            </div>

            <button
              type="button"
              className="action-icon-btn"
              onClick={handleToggleSave}
              title={isSaved ? "Article Saved" : "Save article"}
              style={{ color: isSaved ? "var(--primary)" : undefined }}
            >
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill={isSaved ? "currentColor" : "none"}
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z" />
              </svg>
            </button>
          </div>

          {/* Headline */}
          <h3 className="news-card-title" title={item.title}>
            {articleUrl ? (
              <a
                href={articleUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
              >
                {item.title}
              </a>
            ) : (
              item.title
            )}
          </h3>

          {/* Short Description */}
          {item.description && (
            <p className="news-card-desc" title={item.description}>
              {item.description}
            </p>
          )}
        </div>

        {/* Tags & Open Article Footer */}
        <div className="news-card-footer">
          <div className="news-card-tags">
            {displayCompany && (
              <span className="tag-pill tag-company">{displayCompany}</span>
            )}
            {displayCategory && (
              <span className="tag-pill">{displayCategory}</span>
            )}
          </div>

          {articleUrl && (
            <button
              type="button"
              className="btn-news-open"
              onClick={handleOpenSource}
              title="Open full news article in external tab"
            >
              <span>Open Article</span>
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
