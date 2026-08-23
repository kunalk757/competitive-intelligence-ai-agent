"use client";

import { useState } from "react";

export interface ResearchPaperData {
  id?: string;
  external_id?: string;
  title: string;
  authors?: string[];
  abstract?: string;
  year?: number | null;
  venue?: string | null;
  url?: string | null;
  citation_count?: number | null;
  fields_of_study?: string[];
  source?: string;
  fetched_at?: string;
}

interface ResearchPaperCardProps {
  paper: ResearchPaperData;
  onInvestigate?: (paperTitle: string) => void;
}

export default function ResearchPaperCard({
  paper,
  onInvestigate,
}: ResearchPaperCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const authorsText =
    paper.authors && paper.authors.length > 0
      ? paper.authors.join(", ")
      : "Unknown Authors";

  const handleCopyCitation = (e: React.MouseEvent) => {
    e.stopPropagation();
    const citation = `${authorsText} (${paper.year || "n.d."}). "${paper.title}". ${paper.venue || paper.source || "Academic Pre-print"}. ${paper.url || ""}`;
    navigator.clipboard.writeText(citation);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const handleOpenPaper = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (paper.url) {
      window.open(paper.url, "_blank", "noopener,noreferrer");
    }
  };

  const isHighCitation =
    paper.citation_count !== undefined &&
    paper.citation_count !== null &&
    paper.citation_count >= 100;

  const displayTags =
    paper.fields_of_study && paper.fields_of_study.length > 0
      ? paper.fields_of_study.slice(0, 4)
      : ["AI Research"];

  return (
    <article className="research-paper-card">
      {/* Top Meta: Source, Year, Venue & Citation Count Badge */}
      <div className="research-paper-header">
        <div className="research-paper-meta-left">
          <span className="research-paper-source-badge">
            📚 {paper.source || "Semantic Scholar"}
          </span>

          {paper.year && (
            <span className="research-paper-year-badge">
              🗓️ {paper.year}
            </span>
          )}

          {paper.venue && (
            <span className="research-paper-venue" title={paper.venue}>
              🏛️ {paper.venue}
            </span>
          )}
        </div>

        {/* Citation Count Badge */}
        {paper.citation_count !== undefined && paper.citation_count !== null && (
          <span
            className={`research-paper-citation-badge ${isHighCitation ? "high" : ""}`}
            title={`${paper.citation_count} academic citations`}
          >
            {isHighCitation ? "🔥" : "📈"} {paper.citation_count} citations
          </span>
        )}
      </div>

      {/* Main Content: Title, Authors & Abstract */}
      <div className="research-paper-content">
        <h3 className="research-paper-title" title={paper.title}>
          {paper.title}
        </h3>

        <p className="research-paper-authors" title={authorsText}>
          <strong>Authors:</strong> {authorsText}
        </p>

        {/* Abstract Preview */}
        <div className="research-paper-abstract-wrap">
          {paper.abstract ? (
            <>
              <p
                className={`research-paper-abstract-text ${isExpanded ? "expanded" : ""}`}
              >
                {paper.abstract}
              </p>
              {paper.abstract.length > 180 && (
                <button
                  type="button"
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="research-paper-abstract-toggle"
                >
                  {isExpanded ? "Show Less ↑" : "Read Full Abstract ↓"}
                </button>
              )}
            </>
          ) : (
            <p className="research-paper-abstract-placeholder">
              No abstract preview provided by publisher. Access the publication using the link below.
            </p>
          )}
        </div>

        {/* Fields of Study Tags */}
        <div className="research-paper-tags">
          {displayTags.map((tag, idx) => (
            <span key={idx} className="research-paper-tag">
              #{tag.replace(/^#/, "")}
            </span>
          ))}
        </div>
      </div>

      {/* Bottom Actions Row */}
      <div className="research-paper-footer">
        <div className="research-paper-footer-left">
          {paper.url ? (
            <button
              type="button"
              className="btn-paper-open"
              onClick={handleOpenPaper}
              title="Open full paper in external tab"
            >
              📄 Open Paper ↗
            </button>
          ) : (
            <span
              className="btn-paper-open"
              style={{ opacity: 0.5, cursor: "not-allowed" }}
              title="No direct URL available"
            >
              📄 No Direct Link
            </span>
          )}

          <button
            type="button"
            className={`btn-paper-cite ${isCopied ? "copied" : ""}`}
            onClick={handleCopyCitation}
            title={isCopied ? "Citation copied to clipboard!" : "Copy citation"}
          >
            {isCopied ? "✓ Copied" : "📋 Cite"}
          </button>
        </div>

        {onInvestigate && (
          <button
            type="button"
            className="btn-paper-investigate"
            onClick={() => onInvestigate(paper.title)}
            title="Open AI Intelligence Agent to investigate this paper"
          >
            🤖 Investigate with AI
          </button>
        )}
      </div>
    </article>
  );
}
