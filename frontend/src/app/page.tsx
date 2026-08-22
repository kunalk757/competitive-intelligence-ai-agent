"use client";

import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import DashboardView from "@/components/DashboardView";
import ResearchModal from "@/components/ResearchModal";
import { NewsItemData } from "@/components/NewsCard";

interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isResearchModalOpen, setIsResearchModalOpen] = useState(false);
  const [modalInitialGoal, setModalInitialGoal] = useState(
    "Analyze the competitive landscape for AI chips."
  );

  // Dynamic news results list (starts clean & empty until populated by real search tools)
  const [latestNews, setLatestNews] = useState<NewsItemData[]>([]);

  // Backend health status
  const [healthStatus, setHealthStatus] = useState<
    "checking" | "healthy" | "error"
  >("checking");
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const checkBackendHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await fetch(`${backendUrl}/health`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error("Health check failed");
      const data: HealthResponse = await res.json();
      if (data.status === "healthy") {
        setHealthStatus("healthy");
      } else {
        setHealthStatus("error");
      }
    } catch {
      setHealthStatus("error");
    } finally {
      setIsCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const openNewResearch = (initialGoal?: string) => {
    if (initialGoal) setModalInitialGoal(initialGoal);
    setIsResearchModalOpen(true);
  };

  const handleNewsReceived = (newArticles: NewsItemData[]) => {
    if (newArticles && newArticles.length > 0) {
      setLatestNews((prev) => {
        // Deduplicate incoming articles by URL or title
        const existingUrls = new Set(prev.map((a) => a.url || a.title));
        const filteredNew = newArticles.filter(
          (a) => !existingUrls.has(a.url || a.title)
        );
        return [...filteredNew, ...prev];
      });
    }
  };

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          if (tab === "research") {
            openNewResearch();
          }
        }}
        isOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        healthStatus={healthStatus}
        onRefreshHealth={checkBackendHealth}
        isCheckingHealth={isCheckingHealth}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        {/* Top Header */}
        <Header
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onToggleMobileSidebar={() =>
            setIsMobileSidebarOpen(!isMobileSidebarOpen)
          }
          onNewResearchClick={() => openNewResearch()}
        />

        {/* Dashboard Content */}
        <main className="content-area">
          {activeTab === "dashboard" && (
            <DashboardView
              news={latestNews}
              onNewResearchClick={openNewResearch}
            />
          )}

          {activeTab !== "dashboard" && (
            <div
              className="dashboard-card"
              style={{ padding: "2.5rem", textAlign: "center" }}
            >
              <h2
                style={{
                  fontSize: "1.35rem",
                  fontWeight: 700,
                  marginBottom: "0.5rem",
                  textTransform: "capitalize",
                }}
              >
                {activeTab.replace("-", " ")} Intelligence
              </h2>
              <p
                style={{
                  color: "var(--text-secondary)",
                  fontSize: "0.9rem",
                  maxWidth: "600px",
                  margin: "0 auto 1.5rem",
                }}
              >
                View, filter, and track competitive insights categorized under{" "}
                {activeTab}. You can launch an autonomous ReAct investigation at
                any time.
              </p>
              <button
                type="button"
                className="btn-primary"
                onClick={() =>
                  openNewResearch(
                    `Investigate recent developments in ${activeTab}`
                  )
                }
                style={{ margin: "0 auto" }}
              >
                🚀 Run {activeTab} Investigation
              </button>
            </div>
          )}
        </main>
      </div>

      {/* ReAct Agent Investigation Modal */}
      <ResearchModal
        isOpen={isResearchModalOpen}
        onClose={() => setIsResearchModalOpen(false)}
        initialGoal={modalInitialGoal}
        backendUrl={backendUrl}
        onNewsReceived={handleNewsReceived}
      />
    </div>
  );
}
