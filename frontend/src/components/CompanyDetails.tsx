"use client";

import { useEffect, useState, useCallback } from "react";
import { Company, CompanyDetailsResponse } from "@/types/company";

interface CompanyDetailsProps {
  company: Company;
  onBack: () => void;
}

export default function CompanyDetails({
  company,
  onBack,
}: CompanyDetailsProps) {
  const { name, ticker, industry, description, logoText, logoUrl, accentColor } = company;

  const [detailsData, setDetailsData] = useState<CompanyDetailsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [imgError, setImgError] = useState(false);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const loadCompanyData = useCallback(
    async (forceRefresh = false) => {
      setFetchError(null);

      try {
        const url = `${backendUrl}/api/companies/${encodeURIComponent(name)}${
          forceRefresh ? "?refresh=true" : ""
        }`;
        const res = await fetch(url);
        if (!res.ok) {
          throw new Error(`Server returned HTTP ${res.status}`);
        }
        const data: CompanyDetailsResponse = await res.json();
        setDetailsData(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load company intelligence";
        setFetchError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [backendUrl, name]
  );

  useEffect(() => {
    let isMounted = true;
    fetch(`${backendUrl}/api/companies/${encodeURIComponent(name)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data: CompanyDetailsResponse) => {
        if (isMounted) {
          setDetailsData(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setFetchError(err.message || "Failed to load company intelligence");
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [backendUrl, name]);

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoString;
    }
  };

  const getDomainFromUrl = (urlStr: string) => {
    try {
      const parsed = new URL(urlStr);
      return parsed.hostname.replace(/^www\./, "");
    } catch {
      return "Source Link";
    }
  };

  return (
    <div className="company-details-view">
      {/* Navigation Breadcrumb / Back Button */}
      <div className="company-details-nav-row">
        <button
          type="button"
          className="btn-back"
          onClick={onBack}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span>Back to Companies</span>
        </button>

        {detailsData && (
          <div className="company-sync-status">
            {detailsData.last_updated && (
              <span className="last-synced-text">
                Last updated: {formatDate(detailsData.last_updated)}
              </span>
            )}
            {detailsData.cached && (
              <span className="badge-cached">Cached</span>
            )}
          </div>
        )}
      </div>

      {/* Company Header Profile Card */}
      <div className="company-details-header-card">
        <div className="company-details-main">
          <div
            className="company-logo-badge large"
            style={{
              borderColor: accentColor ? `${accentColor}44` : "var(--border-subtle)",
            }}
          >
            {logoUrl && !imgError ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={logoUrl}
                alt={`${name} logo`}
                className="company-logo-img large"
                onError={() => setImgError(true)}
              />
            ) : (
              <span
                className="company-logo-text large"
                style={{ color: accentColor || "var(--primary)" }}
              >
                {logoText || name.slice(0, 2).toUpperCase()}
              </span>
            )}
          </div>

          <div className="company-details-title-wrap">
            <div className="title-row">
              <h1 className="company-details-title">{name}</h1>
              {ticker && <span className="company-ticker-badge large">{ticker}</span>}
            </div>
            {industry && (
              <span className="company-industry-tag">{industry}</span>
            )}
            {description && (
              <p className="company-details-desc">{description}</p>
            )}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading ? (
        <div className="company-intelligence-placeholder-card">
          <div className="placeholder-spinner" />
          <h3 className="placeholder-heading" style={{ marginTop: "1rem" }}>
            Retrieving Live Intelligence for {name}...
          </h3>
          <p className="placeholder-subtext">
            Querying Tavily Web Intelligence and GNews real-time news feeds.
          </p>
        </div>
      ) : fetchError ? (
        <div className="company-intelligence-placeholder-card">
          <div className="placeholder-icon-wrap" style={{ color: "var(--warning)" }}>
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <h3 className="placeholder-heading">Unable to Load Live Data</h3>
          <p className="placeholder-subtext">
            {fetchError}. Please verify backend server and API configurations.
          </p>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => loadCompanyData(true)}
            style={{ marginTop: "1rem" }}
          >
            Retry Sync
          </button>
        </div>
      ) : (
        <div className="company-content-layout">
          {/* Section 1: Tavily Company Overview */}
          <div className="dashboard-card company-overview-card">
            <div className="card-header-row">
              <h2 className="card-title">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ color: "var(--primary)" }}
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
                Company Overview
              </h2>
              {detailsData?.company.website && (
                <a
                  href={detailsData.company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="company-website-link"
                >
                  <span>Official Website</span>
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              )}
            </div>

            {detailsData?.company.overview ? (
              <div className="company-overview-content">
                <p className="overview-text">{detailsData.company.overview}</p>

                {/* Verified Source Citations */}
                {detailsData.company.sources && detailsData.company.sources.length > 0 && (
                  <div className="company-sources-section">
                    <h4 className="sources-heading">Verified Source Citations</h4>
                    <div className="sources-list">
                      {detailsData.company.sources.map((src, idx) => (
                        <a
                          key={idx}
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="source-chip"
                          title={src.snippet || src.title}
                        >
                          <span className="source-chip-domain">
                            {getDomainFromUrl(src.url)}
                          </span>
                          <span className="source-chip-title">{src.title}</span>
                          <svg
                            width="11"
                            height="11"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                          >
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                            <polyline points="15 3 21 3 21 9" />
                            <line x1="10" y1="14" x2="21" y2="3" />
                          </svg>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="overview-empty-box">
                <p className="overview-empty-text">
                  No detailed company overview found currently. Click Refresh to query live web intelligence.
                </p>
              </div>
            )}
          </div>

          {/* Section 2: GNews Latest Company News */}
          <div className="dashboard-card company-news-section-card">
            <div className="card-header-row">
              <h2 className="card-title">
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ color: "var(--primary)" }}
                >
                  <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
                  <path d="M18 14h-8" />
                  <path d="M15 18h-5" />
                  <path d="M10 6h8v4h-8V6Z" />
                </svg>
                Latest {name} News ({detailsData?.news.length || 0})
              </h2>
            </div>

            {detailsData && detailsData.news.length > 0 ? (
              <div className="company-news-grid">
                {detailsData.news.map((item, idx) => (
                  <div key={idx} className="company-news-card">
                    {item.image_url && (
                      <div className="company-news-thumb-wrap">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={item.image_url}
                          alt={item.title}
                          className="company-news-thumb"
                          onError={(e) => {
                            (e.currentTarget as HTMLElement).style.display = "none";
                          }}
                        />
                      </div>
                    )}
                    <div className="company-news-content">
                      <div className="company-news-meta">
                        <span className="news-source-pill">{item.source}</span>
                        {item.published_at && (
                          <span className="news-date-text">
                            {formatDate(item.published_at)}
                          </span>
                        )}
                      </div>

                      <h3 className="company-news-title">{item.title}</h3>

                      {item.description && (
                        <p className="company-news-desc">{item.description}</p>
                      )}

                      <div className="company-news-card-footer">
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-open-article"
                        >
                          <span>Open Article</span>
                          <svg
                            width="12"
                            height="12"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                            <polyline points="15 3 21 3 21 9" />
                            <line x1="10" y1="14" x2="21" y2="3" />
                          </svg>
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="overview-empty-box">
                <p className="overview-empty-text">
                  No company-specific news articles found currently. Trigger Refresh to query live GNews feeds.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
