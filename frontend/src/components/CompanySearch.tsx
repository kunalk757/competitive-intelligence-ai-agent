"use client";

interface CompanySearchProps {
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
}

export default function CompanySearch({
  value,
  onChange,
  placeholder = "Search companies...",
}: CompanySearchProps) {
  return (
    <div className="company-search-wrapper">
      <div className="company-search-icon">
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      </div>
      <input
        type="text"
        className="company-search-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        aria-label="Search companies"
      />
      {value && (
        <button
          type="button"
          className="company-search-clear"
          onClick={() => onChange("")}
          aria-label="Clear search"
        >
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
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      )}
    </div>
  );
}
