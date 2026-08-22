"use client";

import { useState } from "react";
import { Company } from "@/types/company";

interface CompanyCardProps {
  company: Company;
  onViewDetails: (company: Company) => void;
}

export default function CompanyCard({
  company,
  onViewDetails,
}: CompanyCardProps) {
  const { name, ticker, industry, description, logoText, logoUrl, accentColor } = company;
  const [imgError, setImgError] = useState(false);

  return (
    <div className="company-card">
      <div className="company-card-header">
        <div
          className="company-logo-badge"
          style={{
            borderColor: accentColor ? `${accentColor}33` : "var(--border-subtle)",
          }}
        >
          {logoUrl && !imgError ? (
            /* eslint-disable-next-line @next/next/no-img-element */
            <img
              src={logoUrl}
              alt={`${name} logo`}
              className="company-logo-img"
              onError={() => setImgError(true)}
            />
          ) : (
            <span
              className="company-logo-text"
              style={{ color: accentColor || "var(--primary)" }}
            >
              {logoText || name.slice(0, 2).toUpperCase()}
            </span>
          )}
        </div>

        <div className="company-title-wrap">
          <h3 className="company-card-name">{name}</h3>
          {ticker && <span className="company-ticker-badge">{ticker}</span>}
        </div>
      </div>

      {industry && (
        <div className="company-industry-tag">
          <span>{industry}</span>
        </div>
      )}

      {description && (
        <p className="company-card-description">{description}</p>
      )}

      <div className="company-card-footer">
        <button
          type="button"
          className="btn-view-details"
          onClick={() => onViewDetails(company)}
        >
          <span>View Details</span>
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </button>
      </div>
    </div>
  );
}
