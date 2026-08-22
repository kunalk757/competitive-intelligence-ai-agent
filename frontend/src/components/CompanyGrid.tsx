"use client";

import { Company } from "@/types/company";
import CompanyCard from "./CompanyCard";

interface CompanyGridProps {
  companies: Company[];
  onViewDetails: (company: Company) => void;
  searchQuery?: string;
  onClearSearch?: () => void;
}

export default function CompanyGrid({
  companies,
  onViewDetails,
  searchQuery,
  onClearSearch,
}: CompanyGridProps) {
  if (companies.length === 0) {
    return (
      <div className="companies-empty-state">
        <div className="empty-icon-wrap">
          <svg
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
            <line x1="8" y1="11" x2="14" y2="11" />
          </svg>
        </div>
        <h4 className="empty-state-title">No companies found</h4>
        <p className="empty-state-desc">
          No companies matched &ldquo;{searchQuery}&rdquo;. Try searching for a different company name.
        </p>
        {onClearSearch && (
          <button
            type="button"
            className="btn-secondary"
            onClick={onClearSearch}
            style={{ marginTop: "1rem" }}
          >
            Clear Search
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="companies-grid">
      {companies.map((company) => (
        <CompanyCard
          key={company.id}
          company={company}
          onViewDetails={onViewDetails}
        />
      ))}
    </div>
  );
}
