"use client";

import { useState, useEffect, useCallback } from "react";
import ResearchPaperCard, { ResearchPaperData } from "./ResearchPaperCard";

interface ResearchPapersViewProps {
  onInvestigatePaper?: (paperTitle: string) => void;
  backendUrl?: string;
}

const TOPIC_CHIPS = [
  "All Papers",
  "NVIDIA Blackwell",
  "AMD CDNA 3",
  "LLM Reasoning Scaling",
  "HBM3e Packaging",
  "Mixture-of-Experts",
  "Transformer Optimization",
  "Quantum Computing",
];

export default function ResearchPapersView({
  onInvestigatePaper,
  backendUrl: propBackendUrl,
}: ResearchPapersViewProps) {
  const [query, setQuery] = useState("");
  const [activeChip, setActiveChip] = useState("All Papers");
  const [papers, setPapers] = useState<ResearchPaperData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sourceInfo, setSourceInfo] = useState<string>("Semantic Scholar & Database");
  const [totalCount, setTotalCount] = useState<number>(0);

  const backendUrl = (
    propBackendUrl ||
    process.env.NEXT_PUBLIC_BACKEND_URL ||
    "http://localhost:8000"
  ).replace(/\/+$/, "");

  // Fetch papers from backend
  const fetchPapers = useCallback(
    async (searchQuery: string = "") => {
      setIsLoading(true);
      setErrorMsg(null);
      try {
        const trimmed = searchQuery.trim();
        const endpoint = trimmed
          ? `${backendUrl}/api/research-papers/search?q=${encodeURIComponent(trimmed)}&limit=20`
          : `${backendUrl}/api/research-papers?limit=25`;

        const res = await fetch(endpoint, {
          method: "GET",
          headers: { "Content-Type": "application/json" },
        });

        if (!res.ok) {
          throw new Error(`Server returned HTTP ${res.status}`);
        }

        const data = await res.json();
        const fetchedList: ResearchPaperData[] = data.data || [];
        setPapers(fetchedList);
        setTotalCount(data.total || fetchedList.length);

        const src = data.source || "";
        if (src === "semantic_scholar_api") {
          setSourceInfo("Live Semantic Scholar API");
        } else if (src.includes("Live Search") || src.includes("arXiv")) {
          setSourceInfo("Live Academic Discovery (arXiv / OpenReview)");
        } else {
          setSourceInfo("Supabase & Curated Cache");
        }
      } catch (err: unknown) {
        console.error("Error loading research papers:", err);
        const detail = err instanceof Error ? ` (${err.message})` : "";
        setErrorMsg(`Could not connect to the research paper service at ${backendUrl}${detail}. Please ensure the backend is running.`);
      } finally {
        setIsLoading(false);
      }
    },
    [backendUrl]
  );

  // Initial load
  useEffect(() => {
    let isSubscribed = true;
    const load = async () => {
      if (isSubscribed) {
        await fetchPapers();
      }
    };
    load();
    return () => {
      isSubscribed = false;
    };
  }, [fetchPapers]);

  // Handle search submission
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setActiveChip(query ? "Custom" : "All Papers");
    fetchPapers(query);
  };

  // Handle topic chip selection
  const handleSelectChip = (chip: string) => {
    setActiveChip(chip);
    if (chip === "All Papers") {
      setQuery("");
      fetchPapers("");
    } else {
      setQuery(chip);
      fetchPapers(chip);
    }
  };

  return (
    <div className="research-papers-container">
      {/* Header Row */}
      <div className="companies-header-row" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem", flexWrap: "wrap" }}>
        <div>
          <h1 className="dashboard-title">Research Papers</h1>
          <p className="dashboard-subtitle">
            Explore frontier academic research, technical surveys, and architecture benchmarks via Semantic Scholar.
          </p>
        </div>

        {/* Source Badge */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            style={{
              fontSize: "0.8rem",
              fontWeight: 600,
              padding: "0.35rem 0.75rem",
              borderRadius: "20px",
              background: "rgba(16, 185, 129, 0.12)",
              color: "#059669",
              border: "1px solid rgba(16, 185, 129, 0.3)",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.35rem",
            }}
          >
            ● {sourceInfo}
          </span>
        </div>
      </div>

      {/* Search Bar & Actions */}
      <div className="dashboard-card" style={{ padding: "1.25rem" }}>
        <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          <div style={{ position: "relative", flex: 1, minWidth: "260px" }}>
            <span style={{ position: "absolute", left: "0.85rem", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }}>
              🔍
            </span>
            <input
              type="text"
              className="search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search research papers by title, topic, author, or architecture..."
              style={{
                width: "100%",
                paddingLeft: "2.4rem",
                paddingRight: query ? "2.5rem" : "1rem",
                background: "#ffffff",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                color: "var(--text-main)",
                fontSize: "0.925rem",
                height: "44px",
              }}
            />
            {query && (
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  setActiveChip("All Papers");
                  fetchPapers("");
                }}
                style={{
                  position: "absolute",
                  right: "0.85rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  color: "var(--text-muted)",
                  cursor: "pointer",
                  fontSize: "1rem",
                  padding: "0.2rem",
                }}
                title="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
            style={{ height: "44px", padding: "0 1.5rem", display: "inline-flex", alignItems: "center", gap: "0.4rem", fontSize: "0.925rem" }}
          >
            {isLoading ? "Searching..." : "Search Papers"}
          </button>
        </form>

        {/* Topic Filter Chips */}
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "1rem", alignItems: "center" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", fontWeight: 600, marginRight: "0.25rem" }}>
            Trending Topics:
          </span>
          {TOPIC_CHIPS.map((chip) => {
            const isActive = activeChip === chip;
            return (
              <button
                key={chip}
                type="button"
                onClick={() => handleSelectChip(chip)}
                style={{
                  fontSize: "0.775rem",
                  fontWeight: isActive ? 700 : 500,
                  padding: "0.3rem 0.75rem",
                  borderRadius: "16px",
                  background: isActive ? "var(--primary)" : "#f1f5f9",
                  color: isActive ? "#ffffff" : "var(--text-secondary)",
                  border: isActive ? "1px solid var(--primary)" : "1px solid var(--border-subtle)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {chip}
              </button>
            );
          })}
        </div>
      </div>

      {/* Meta Count Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.875rem", color: "var(--text-secondary)" }}>
        <span>
          Showing <strong>{papers.length}</strong> {papers.length === 1 ? "paper" : "papers"}
          {query ? ` for "${query}"` : ""}
        </span>
        {totalCount > 0 && (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Total Indexed: <strong>{totalCount}</strong>
          </span>
        )}
      </div>

      {/* Error State */}
      {errorMsg && (
        <div
          className="dashboard-card"
          style={{
            padding: "1.25rem",
            background: "var(--danger-light, #fef2f2)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "var(--danger, #ef4444)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>⚠️ {errorMsg}</span>
          <button
            type="button"
            className="btn-paper-cite"
            onClick={() => fetchPapers(query)}
            style={{ fontSize: "0.8rem", padding: "0.35rem 0.75rem" }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton Grid */}
      {isLoading && (
        <div className="research-papers-grid">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div
              key={n}
              className="research-paper-card"
              style={{
                minHeight: "320px",
                opacity: 0.7,
                animation: "pulse 1.5s infinite ease-in-out",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ height: "22px", background: "#e2e8f0", borderRadius: "4px", width: "35%" }} />
                <div style={{ height: "22px", background: "#e2e8f0", borderRadius: "12px", width: "25%" }} />
              </div>
              <div style={{ height: "24px", background: "#e2e8f0", borderRadius: "4px", width: "85%", marginTop: "0.5rem" }} />
              <div style={{ height: "16px", background: "#f1f5f9", borderRadius: "4px", width: "60%" }} />
              <div style={{ height: "80px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: "8px" }} />
              <div style={{ display: "flex", gap: "0.35rem" }}>
                <div style={{ height: "20px", background: "#f1f5f9", borderRadius: "4px", width: "50px" }} />
                <div style={{ height: "20px", background: "#f1f5f9", borderRadius: "4px", width: "65px" }} />
              </div>
              <div style={{ height: "36px", background: "#f1f5f9", borderRadius: "6px", marginTop: "auto" }} />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && papers.length === 0 && (
        <div
          className="dashboard-card"
          style={{ padding: "3.5rem 1.5rem", textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", gap: "1rem" }}
        >
          <span style={{ fontSize: "3rem" }}>📄</span>
          <h2 style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text-main)" }}>
            No Research Papers Found
          </h2>
          <p style={{ color: "var(--text-secondary)", maxWidth: "480px", fontSize: "0.9rem", lineHeight: 1.5 }}>
            No academic papers matched your query <strong>&quot;{query}&quot;</strong>. Try adjusting search terms or click one of the trending research topics.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={() => handleSelectChip("NVIDIA Blackwell")}
            style={{ marginTop: "0.5rem" }}
          >
            Explore NVIDIA Blackwell Research
          </button>
        </div>
      )}

      {/* Papers Grid */}
      {!isLoading && papers.length > 0 && (
        <div className="research-papers-grid">
          {papers.map((paper, idx) => (
            <ResearchPaperCard
              key={paper.external_id || paper.id || idx}
              paper={paper}
              onInvestigate={
                onInvestigatePaper
                  ? () => onInvestigatePaper(`Analyze research paper: "${paper.title}"`)
                  : undefined
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
