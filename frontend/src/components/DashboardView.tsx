"use client";

import NewsList from "./NewsList";
import AlertList from "./AlertList";
import { NewsItemData } from "./NewsCard";

interface DashboardViewProps {
  news?: NewsItemData[];
  onNewResearchClick: (initialGoal?: string) => void;
}

/**
 * ============================================================================
 * TEMPORARY DEMO DATA — REAL WEB-SOURCED NEWS
 * ============================================================================
 * These 4 items are sourced strictly from verified public web articles
 * (Reuters & Tom's Hardware) for UI demonstration.
 * NOTE: This will be replaced by the live GNews API in subsequent steps.
 * ============================================================================
 */
export const demoWebNews: NewsItemData[] = [
  {
    id: "news-reuters-nvidia-china",
    title: "Nvidia denies report it is rolling out China AI chip by year-end",
    source: "Reuters",
    published_at: "August 20, 2026",
    time: "August 20, 2026",
    description:
      "Nvidia denied a media report that it was preparing to ship a new artificial intelligence chip designed for the Chinese market by the end of this year.",
    category: "Semiconductors",
    company_tag: "NVIDIA",
    thumbnailBadge: "NV",
    url: "https://www.reuters.com/world/china/nvidia-ship-ai-chip-china-by-year-end-information-reports-2026-08-20/",
  },
  {
    id: "news-reuters-marvell-google",
    title: "Marvell gives Google option to buy $12.2 billion stake in custom AI chip deal",
    source: "Reuters",
    published_at: "August 19, 2026",
    time: "August 19, 2026",
    description:
      "Marvell Technology granted Google the right to acquire up to 12.2% of the semiconductor design company as part of an expanded partnership to develop custom AI processors.",
    category: "Cloud & Custom Silicon",
    company_tag: "Marvell / Google",
    thumbnailBadge: "MR",
    url: "https://www.reuters.com/technology/marvell-grants-google-122-billion-stock-warrant-custom-chip-deal-2026-08-19/",
  },
  {
    id: "news-reuters-broadcom-debt",
    title: "Broadcom seeks more than $60 billion in latest AI debt deal",
    source: "Reuters",
    published_at: "August 20, 2026",
    time: "August 20, 2026",
    description:
      "Broadcom is seeking more than $60 billion in credit facilities and debt financing to support escalating demand for custom AI accelerators and next-generation networking silicon.",
    category: "Finance & Infrastructure",
    company_tag: "Broadcom",
    thumbnailBadge: "BC",
    url: "https://www.reuters.com/technology/broadcom-seeks-more-than-60-billion-latest-ai-debt-deal-2026-08-20/",
  },
  {
    id: "news-tomshardware-amd-rack",
    title:
      "AMD claims its 2026 rack-scale AI solution is 4X more energy efficient than its 2024 platform",
    source: "Tom's Hardware",
    published_at: "August 19, 2026",
    time: "August 19, 2026",
    description:
      "AMD highlighted that its latest rack-scale AI architecture delivers 4X higher energy efficiency per token compared to its 2024 systems, pacing ahead of its target for 20X efficiency by 2030.",
    category: "AI Hardware",
    company_tag: "AMD",
    thumbnailBadge: "AMD",
    url: "https://www.tomshardware.com/tech-industry/artificial-intelligence/amd-claims-its-2026-rack-scale-ai-solution-is-4x-more-energy-efficient-than-its-2024-ai-platform-company-says-its-pacing-ahead-of-20x-efficiency-by-2030",
  },
];

export default function DashboardView({
  news,
  onNewResearchClick,
}: DashboardViewProps) {
  // Use passed news if available; otherwise use the verified demoWebNews dataset
  const activeNews = news && news.length > 0 ? news : demoWebNews;

  return (
    <div>
      {/* Dashboard Top Heading */}
      <div className="dashboard-heading-row">
        <div>
          <h1 className="dashboard-title">Good morning, Alex</h1>
          <p className="dashboard-subtitle">
            Here&apos;s what&apos;s happening in your intelligence dashboard today.
          </p>
        </div>

        <button
          type="button"
          className="btn-primary"
          onClick={() => onNewResearchClick()}
        >
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          + New Research
        </button>
      </div>

      {/* 2-Column Content Grid */}
      <div className="dashboard-grid">
        <NewsList
          news={activeNews}
          onViewAll={() =>
            onNewResearchClick(
              "Analyze recent semiconductor and AI chip competitor news."
            )
          }
        />

        {/* Intelligence Alerts remain empty until backed by real backend alert triggers */}
        <AlertList
          alerts={[]}
          onViewAll={() =>
            onNewResearchClick(
              "Investigate all high-priority patent and competitor alerts."
            )
          }
        />
      </div>
    </div>
  );
}
