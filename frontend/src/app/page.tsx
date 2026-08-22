"use client";

import { useState, useEffect, useCallback } from "react";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import DashboardView from "@/components/DashboardView";
import CompaniesView from "@/components/CompaniesView";
import ResearchModal from "@/components/ResearchModal";
import { NewsItemData } from "@/components/NewsCard";

interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
}

interface NewsApiResponse {
  articles: NewsItemData[];
  total_count: number;
  last_updated?: string | null;
  schedule_notice?: string;
  is_supabase_connected?: boolean;
}

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [isResearchModalOpen, setIsResearchModalOpen] = useState(false);
  const [modalInitialGoal, setModalInitialGoal] = useState(
    "Analyze the competitive landscape for AI chips."
  );

  // Persistent database-backed news articles & sync metadata
  const [latestNews, setLatestNews] = useState<NewsItemData[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isRefreshingNews, setIsRefreshingNews] = useState(false);

  // Backend health status
  const [healthStatus, setHealthStatus] = useState<
    "checking" | "healthy" | "error"
  >("checking");
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  const checkBackendHealth = useCallback(async () => {
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
  }, [backendUrl]);

  // Fetch persistent saved news from Backend -> Supabase
  const loadSavedNews = useCallback(async () => {
    try {
      const res = await fetch(`${backendUrl}/api/news?limit=25`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        const data: NewsApiResponse = await res.json();
        if (data.articles) {
          setLatestNews(data.articles);
        }
        if (data.last_updated) {
          setLastUpdated(data.last_updated);
        }
      }
    } catch (err) {
      console.warn("Could not load news from backend:", err);
    }
  }, [backendUrl]);

  // Trigger manual news refresh
  const handleRefreshNews = async () => {
    setIsRefreshingNews(true);
    try {
      const res = await fetch(`${backendUrl}/api/news/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (res.ok) {
        await loadSavedNews();
      }
    } catch (err) {
      console.error("Error refreshing news:", err);
    } finally {
      setIsRefreshingNews(false);
    }
  };

  useEffect(() => {
    let isMounted = true;

    fetch(`${backendUrl}/health`)
      .then((res) => {
        if (!res.ok) throw new Error("Health check failed");
        return res.json();
      })
      .then((data: HealthResponse) => {
        if (isMounted) {
          setHealthStatus(data.status === "healthy" ? "healthy" : "error");
        }
      })
      .catch(() => {
        if (isMounted) setHealthStatus("error");
      });

    fetch(`${backendUrl}/api/news?limit=25`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: NewsApiResponse | null) => {
        if (isMounted && data) {
          if (data.articles) setLatestNews(data.articles);
          if (data.last_updated) setLastUpdated(data.last_updated);
        }
      })
      .catch((err) => console.warn("Could not load news from backend:", err));

    return () => {
      isMounted = false;
    };
  }, [backendUrl]);

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
              lastUpdated={lastUpdated}
              onRefreshNews={handleRefreshNews}
              isRefreshing={isRefreshingNews}
              onNewResearchClick={openNewResearch}
            />
          )}

          {activeTab === "companies" && (
            <CompaniesView />
          )}

          {activeTab !== "dashboard" && activeTab !== "companies" && (
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
