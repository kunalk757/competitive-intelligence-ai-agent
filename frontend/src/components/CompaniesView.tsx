"use client";

import { useState, useMemo } from "react";
import { Company } from "@/types/company";
import { INITIAL_COMPANIES } from "@/data/companies";
import CompanySearch from "./CompanySearch";
import CompanyGrid from "./CompanyGrid";
import CompanyDetails from "./CompanyDetails";

export default function CompaniesView() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);

  // Filter companies by name (case-insensitive)
  const filteredCompanies = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return INITIAL_COMPANIES;
    return INITIAL_COMPANIES.filter((company) =>
      company.name.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  // If a company is selected, render the Company Details view
  if (selectedCompany) {
    return (
      <CompanyDetails
        company={selectedCompany}
        onBack={() => setSelectedCompany(null)}
      />
    );
  }

  return (
    <div className="companies-page-container">
      {/* Top Heading & Action Row */}
      <div className="companies-header-row">
        <div>
          <h1 className="dashboard-title">Companies</h1>
          <p className="dashboard-subtitle">
            Monitor companies and view their latest intelligence.
          </p>
        </div>

        <div className="companies-controls-row">
          <CompanySearch
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search companies..."
          />
        </div>
      </div>

      {/* Companies Metrics / Filter Bar */}
      <div className="companies-meta-bar">
        <span className="companies-count-badge">
          Showing {filteredCompanies.length} of {INITIAL_COMPANIES.length} companies
        </span>
      </div>

      {/* Companies Grid */}
      <CompanyGrid
        companies={filteredCompanies}
        onViewDetails={(company) => setSelectedCompany(company)}
        searchQuery={searchQuery}
        onClearSearch={() => setSearchQuery("")}
      />
    </div>
  );
}
