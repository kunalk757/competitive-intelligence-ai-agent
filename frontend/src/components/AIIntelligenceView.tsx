"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  ChatMessage,
  AgentRunResponse,
  CompanyCardData,
  NewsArticleData,
  ResearchPaperData,
  SourceItemData,
} from "@/types/agent";

interface AIIntelligenceViewProps {
  onNavigateToCompany?: (companyName: string) => void;
}

const STARTER_SUGGESTIONS = [
  {
    title: "Compare NVIDIA and AMD in AI chips",
    subtitle: "Architecture, accelerators, and market positioning",
    icon: "⚡",
  },
  {
    title: "Latest AI chip developments",
    subtitle: "Next-gen Blackwell, MI350, and custom silicon",
    icon: "🔥",
  },
  {
    title: "Research on LLMs",
    subtitle: "Reasoning models, post-training, and architectures",
    icon: "🔬",
  },
  {
    title: "Analyze Apple's latest technology news",
    subtitle: "Apple Intelligence, chips, and market moves",
    icon: "📰",
  },
];

function extractDomain(url?: string): string {
  if (!url) return "";
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

interface ActiveSourceDetail {
  category: "source" | "news" | "research" | "company";
  title: string;
  sourceName?: string;
  publishedDate?: string;
  snippet?: string;
  imageUrl?: string;
  authors?: string;
  url?: string;
  badgeLabel: string;
  badgeIcon: string;
}

export default function AIIntelligenceView({ onNavigateToCompany }: AIIntelligenceViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedActivities, setExpandedActivities] = useState<{ [msgId: string]: boolean }>({});
  const [activeSourceModal, setActiveSourceModal] = useState<ActiveSourceDetail | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => `session-${Math.random().toString(36).substring(2, 11)}`);
  
  // Developer / Adversarial Test Mode State (Hackathon Live Demonstration)
  const [devModeOpen, setDevModeOpen] = useState(false);
  const [devModeActive, setDevModeActive] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState<"tavily_fail" | "gnews_fail" | "repeated_fail" | "conflict_evidence">("tavily_fail");

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const rawBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const backendUrl = rawBackendUrl.replace(/\/+$/, "");
  const activeAbortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  // Adjust textarea height dynamically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [inputValue]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setActiveSourceModal(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      if (activeAbortControllerRef.current) {
        activeAbortControllerRef.current.abort();
      }
    };
  }, []);

  const toggleActivity = (id: string) => {
    setExpandedActivities((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleStop = () => {
    if (activeAbortControllerRef.current) {
      activeAbortControllerRef.current.abort();
    }
  };

  const handleStartNewResearch = () => {
    setMessages([]);
    setSessionId(`session-${Math.random().toString(36).substring(2, 11)}`);
  };

  const handleSend = useCallback(
    async (queryToSend?: string) => {
      const q = (queryToSend || inputValue).trim();
      if (!q || isSubmitting) return;

      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `assistant-${Date.now()}`;

      const newUserMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        queryText: q,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        session_id: sessionId,
      };

      const newAssistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        isLoading: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        session_id: sessionId,
      };

      // Construct recent chat history context for continuous multi-turn conversations
      const historyContext = messages
        .filter((m) => !m.isLoading && !m.error)
        .map((m) => ({
          role: m.role,
          content: m.role === "user" ? m.queryText || "" : m.response?.answer || "",
        }));

      // Construct adversarial configuration if developer test mode is enabled
      let adversarialConfig: Record<string, any> | undefined = undefined;
      if (devModeActive) {
        if (selectedScenario === "tavily_fail") {
          adversarialConfig = { force_tavily_fail: true };
        } else if (selectedScenario === "gnews_fail") {
          adversarialConfig = { force_gnews_fail: true };
        } else if (selectedScenario === "repeated_fail") {
          adversarialConfig = { force_repeated_tool_fail: "search_news" };
        } else if (selectedScenario === "conflict_evidence") {
          adversarialConfig = {
            inject_conflicting_evidence: {
              topic: "H100 vs MI300X Memory Bandwidth and Specs",
              claim_a: "Initial preliminary leak claimed MI300X memory bandwidth falls below 4 TB/s.",
              source_a: "Tech Blog Rumors",
              date_a: "2023-11-01",
              claim_b: "Official MLPerf and IEEE architectural benchmarks verified MI300X delivers 5.3 TB/s bandwidth and matches H100 in FP8 throughput.",
              source_b: "IEEE Micro & MLPerf Verified Benchmark",
              date_b: "2024-06-15",
            },
          };
        }
      }

      setMessages((prev) => [...prev, newUserMsg, newAssistantMsg]);
      setInputValue("");
      setIsSubmitting(true);

      const controller = new AbortController();
      activeAbortControllerRef.current = controller;

      try {
        console.debug(`[AIIntelligence] Invoking multi-agent flow: "${q}" (session: ${sessionId})`, {
          adversarialConfig,
        });
        const res = await fetch(`${backendUrl}/agent/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            goal: q,
            max_iterations: 5,
            chat_history: historyContext,
            session_id: sessionId,
            ...(adversarialConfig ? { adversarial_config: adversarialConfig } : {}),
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          console.error("Backend agent run failed:", res.status, errData);
          throw new Error(errData.detail || `Agent returned HTTP ${res.status}`);
        }

        const rawData = await res.json();
        console.debug("[AIIntelligence] Received agent response:", rawData);

        const normalizedData: AgentRunResponse = {
          success: rawData.success ?? true,
          answer: rawData.answer || "Investigation concluded with no report generated.",
          steps: Array.isArray(rawData.steps) ? rawData.steps : [],
          tools_used: Array.isArray(rawData.tools_used) ? rawData.tools_used : [],
          iterations: typeof rawData.iterations === "number" ? rawData.iterations : 1,
          session_id: rawData.session_id || sessionId,
          companies: Array.isArray(rawData.companies) ? rawData.companies : [],
          news: Array.isArray(rawData.news)
            ? rawData.news
            : Array.isArray(rawData.news_results)
            ? rawData.news_results
            : [],
          research: Array.isArray(rawData.research) ? rawData.research : [],
          patents: Array.isArray(rawData.patents) ? rawData.patents : [],
          sources: Array.isArray(rawData.sources) ? rawData.sources : [],
          error: rawData.error,
        };

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isLoading: false,
                  response: normalizedData,
                }
              : msg
          )
        );
      } catch (err: unknown) {
        const errorObj = err as Error | undefined;
        const isAbort = errorObj?.name === "AbortError" || errorObj?.message?.includes("aborted");

        console.error("AI Intelligence request failed:", {
          error: err,
          name: errorObj?.name,
          message: errorObj?.message,
          isAbort,
        });

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isLoading: false,
                  error: isAbort
                    ? "Agent investigation was cancelled."
                    : "Unable to complete the investigation right now. Please try again.",
                }
              : msg
          )
        );
      } finally {
        activeAbortControllerRef.current = null;
        setIsSubmitting(false);
      }
    },
    [inputValue, isSubmitting, messages, backendUrl, sessionId, devModeActive, selectedScenario]
  );

  return (
    <div className="chat-interface-wrapper">
      {/* Top Conversation Header */}
      <div className="chat-top-bar">
        <div className="chat-brand-meta">
          <div className="chat-avatar-icon">🤖</div>
          <div>
            <h1 className="chat-title">AI Intelligence</h1>
            <p className="chat-status-text">
              <span className="online-pulse-dot" /> Autonomous Multi-Agent Research Assistant (LangGraph Engine)
            </p>
          </div>
        </div>

        <div className="chat-top-actions">
          <button
            type="button"
            className={`btn-dev-test-mode ${devModeActive ? "active" : ""}`}
            onClick={() => setDevModeOpen(!devModeOpen)}
            title="Toggle Developer / Adversarial Test Mode panel"
          >
            <span>🛠️ Dev Test Mode</span>
            {devModeActive && <span className="dev-active-badge">ACTIVE</span>}
          </button>

          {messages.length > 0 && (
            <button
              type="button"
              className="btn-new-research-thread"
              onClick={handleStartNewResearch}
              title="Start new research thread"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="15" height="15">
                <path d="M12 5v14M5 12h14" />
              </svg>
              <span>New Research</span>
            </button>
          )}
        </div>
      </div>

      {/* Developer / Adversarial Test Mode Panel */}
      {devModeOpen && (
        <div className="dev-mode-panel">
          <div className="dev-mode-header">
            <div className="dev-mode-title-wrap">
              <span className="dev-mode-tag">DEVELOPER TEST MODE</span>
              <h4 className="dev-mode-heading">Adversarial Failure & Conflict Simulation</h4>
            </div>
            <div className="dev-mode-master-toggle">
              <label className="switch-label">
                <input
                  type="checkbox"
                  checked={devModeActive}
                  onChange={(e) => setDevModeActive(e.target.checked)}
                />
                <span className="switch-slider" />
                <span className="switch-text">{devModeActive ? "Simulation Enabled" : "Disabled (Production Mode)"}</span>
              </label>
            </div>
          </div>

          <p className="dev-mode-desc">
            Select a controlled fault condition to test LangGraph’s autonomous recovery loops, tool fallback routing, hypothesis verification, and circuit breaker logic without impacting real production APIs.
          </p>

          <div className={`dev-scenario-grid ${!devModeActive ? "disabled" : ""}`}>
            {/* Scenario 1: Tavily Failure */}
            <div
              className={`dev-scenario-card ${selectedScenario === "tavily_fail" ? "selected" : ""}`}
              onClick={() => devModeActive && setSelectedScenario("tavily_fail")}
            >
              <div className="scenario-card-header">
                <span className="scenario-icon">⚡</span>
                <span className="scenario-name">1. Tavily Search Failure</span>
              </div>
              <p className="scenario-detail">
                Simulates 503 outage on primary web search. Tests: Failure detection $\rightarrow$ Autonomous Replanning $\rightarrow$ GNews & Company Intelligence fallback.
              </p>
              <div className="scenario-config-tag">force_tavily_fail: true</div>
            </div>

            {/* Scenario 2: GNews Failure */}
            <div
              className={`dev-scenario-card ${selectedScenario === "gnews_fail" ? "selected" : ""}`}
              onClick={() => devModeActive && setSelectedScenario("gnews_fail")}
            >
              <div className="scenario-card-header">
                <span className="scenario-icon">📰</span>
                <span className="scenario-name">2. GNews API Failure</span>
              </div>
              <p className="scenario-detail">
                Simulates 429 rate limit on news feeds. Tests: Tool fallback to live web search without crashing the multi-agent investigation.
              </p>
              <div className="scenario-config-tag">force_gnews_fail: true</div>
            </div>

            {/* Scenario 3: Repeated Tool Failure */}
            <div
              className={`dev-scenario-card ${selectedScenario === "repeated_fail" ? "selected" : ""}`}
              onClick={() => devModeActive && setSelectedScenario("repeated_fail")}
            >
              <div className="scenario-card-header">
                <span className="scenario-icon">🔁</span>
                <span className="scenario-name">3. Repeated Failure & Deadlock</span>
              </div>
              <p className="scenario-detail">
                Simulates persistent tool failures. Tests: State action counters, Circuit Breaker trigger, and safe termination within resource limits.
              </p>
              <div className="scenario-config-tag">force_repeated_tool_fail: "search_news"</div>
            </div>

            {/* Scenario 4: Conflicting Evidence */}
            <div
              className={`dev-scenario-card ${selectedScenario === "conflict_evidence" ? "selected" : ""}`}
              onClick={() => devModeActive && setSelectedScenario("conflict_evidence")}
            >
              <div className="scenario-card-header">
                <span className="scenario-icon">⚖️</span>
                <span className="scenario-name">4. Conflicting Evidence Injection</span>
              </div>
              <p className="scenario-detail">
                Injects contradictory claims (Source A vs Source B). Tests: Source recency & reliability weighting, uncertainty rating, and transparent disclosure.
              </p>
              <div className="scenario-config-tag">inject_conflicting_evidence: &#123;...&#125;</div>
            </div>
          </div>

          {devModeActive && (
            <div className="dev-active-status-bar">
              <span className="status-indicator-dot" />
              <span>
                Active Simulation: <strong>{selectedScenario.toUpperCase()}</strong>. Next query will dispatch with LangGraph adversarial payload.
              </span>
            </div>
          )}
        </div>
      )}


      {/* Main Conversation Stream */}
      <div className="chat-stream-container">
        {messages.length === 0 ? (
          /* Empty / Welcome State */
          <div className="chat-welcome-hero">
            <div className="welcome-avatar-badge">
              <span>🤖</span>
            </div>
            <h2 className="welcome-heading">What would you like to investigate?</h2>
            <p className="welcome-description">
              Ask anything about companies, competitors, news, technologies, or research.
              Our Multi-Agent architecture will plan, gather live factual data, and synthesize structured intelligence.
            </p>

            <div className="welcome-suggestions-grid">
              {STARTER_SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="welcome-suggestion-card"
                  onClick={() => handleSend(item.title)}
                >
                  <div className="suggestion-card-header">
                    <span className="suggestion-icon">{item.icon}</span>
                    <span className="suggestion-title">{item.title}</span>
                  </div>
                  <p className="suggestion-subtitle">{item.subtitle}</p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Conversational Thread */
          <div className="chat-messages-flow">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`chat-turn-row ${msg.role === "user" ? "user-turn" : "assistant-turn"}`}
              >
                {msg.role === "user" ? (
                  <div className="user-bubble-container">
                    <div className="user-speech-bubble">
                      <p>{msg.queryText}</p>
                      <span className="speech-timestamp">{msg.timestamp}</span>
                    </div>
                  </div>
                ) : (
                  <div className="assistant-bubble-container">
                    <div className="assistant-avatar-badge">🤖</div>

                    <div className="assistant-content-wrapper">
                      {/* 1. Loading State */}
                      {msg.isLoading && (
                        <div className="assistant-loading-card">
                          <div className="assistant-pulsing-spinner" />
                          <div className="loading-copy">
                            <h4>Multi-Agent Research in Progress...</h4>
                            <p>Research Agent is querying live web/news tools, while Analyst prepares synthesis.</p>
                          </div>
                        </div>
                      )}

                      {/* 2. Error State */}
                      {msg.error && (
                        <div className="assistant-error-banner">
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <line x1="12" y1="16" x2="12.01" y2="16" />
                          </svg>
                          <p>{msg.error}</p>
                        </div>
                      )}

                      {/* 3. Completed Response */}
                      {msg.response && (
                        <div className="assistant-response-body">
                          {/* Agent Activity Log Area (LangGraph Workflow Execution) */}
                          {msg.response.steps && msg.response.steps.length > 0 && (
                            <div className="chat-activity-bar">
                              <button
                                type="button"
                                className="chat-activity-toggle"
                                onClick={() => toggleActivity(msg.id)}
                              >
                                <div className="activity-toggle-left">
                                  <span className="activity-success-dot">⚡</span>
                                  <span className="activity-toggle-text">
                                    Agent Activity Log ({msg.response.steps.length} LangGraph workflow events)
                                  </span>
                                </div>
                                <span className="activity-toggle-arrow">
                                  {expandedActivities[msg.id] !== false ? "▲ Hide Log" : "▼ View Activity Log"}
                                </span>
                              </button>

                              {expandedActivities[msg.id] !== false && (
                                <ul className="chat-activity-steps">
                                  {msg.response.steps.map((step, sIdx) => {
                                    let icon = "✓";
                                    let itemClass = "chat-step-item completed";
                                    const text = step.summary;
                                    if (step.status === "failed" || step.action === "error" || text.includes("⚠") || text.toLowerCase().includes("failed")) {
                                      icon = "⚠";
                                      itemClass = "chat-step-item failed";
                                    } else if (text.includes("↻") || text.toLowerCase().includes("replan")) {
                                      icon = "↻";
                                      itemClass = "chat-step-item replan";
                                    } else if (step.status === "running") {
                                      icon = "•";
                                      itemClass = "chat-step-item running";
                                    }
                                    return (
                                      <li key={sIdx} className={itemClass}>
                                        <span className="step-bullet">{icon}</span>
                                        <span className="step-text">{text}</span>
                                      </li>
                                    );
                                  })}
                                </ul>
                              )}
                            </div>
                          )}


                          {/* Synthesized Analysis / Intelligence Report */}
                          {msg.response.answer && (
                            <div className="chat-markdown-report">
                              {msg.response.answer.split("\n\n").map((para, pIdx) => {
                                if (para.startsWith("###") || para.startsWith("##") || para.startsWith("#")) {
                                  return (
                                    <h3 key={pIdx} className="chat-report-heading">
                                      {para.replace(/^[#]+\s*/, "")}
                                    </h3>
                                  );
                                }
                                if (para.startsWith("- ") || para.startsWith("* ")) {
                                  const bulletLines = para.split("\n");
                                  return (
                                    <ul key={pIdx} className="chat-report-bullets">
                                      {bulletLines.map((line, bIdx) => (
                                        <li key={bIdx}>{line.replace(/^[-*]\s*/, "")}</li>
                                      ))}
                                    </ul>
                                  );
                                }
                                return (
                                  <p key={pIdx} className="chat-report-paragraph">
                                    {para}
                                  </p>
                                );
                              })}
                            </div>
                          )}

                          {/* Inline Section: 🏢 Company Cards */}
                          {msg.response.companies && msg.response.companies.length > 0 && (
                            <div className="chat-inline-section">
                              <div className="inline-section-header">
                                <span>🏢</span>
                                <h4>Company Profiles</h4>
                              </div>
                              <div className="chat-companies-grid">
                                {msg.response.companies.map((comp: CompanyCardData, cIdx: number) => (
                                  <div key={cIdx} className="chat-company-card">
                                    <div className="company-card-top-row">
                                      <div className="company-logo-wrap">
                                        {comp.logo_url ? (
                                          /* eslint-disable-next-line @next/next/no-img-element */
                                          <img
                                            src={comp.logo_url}
                                            alt={`${comp.name} logo`}
                                            className="company-logo-img"
                                            onError={(e) => {
                                              (e.target as HTMLElement).style.display = "none";
                                            }}
                                          />
                                        ) : (
                                          <span className="company-initials">
                                            {comp.name.slice(0, 2).toUpperCase()}
                                          </span>
                                        )}
                                      </div>
                                      <div>
                                        <h5 className="company-name-text">{comp.name}</h5>
                                        {comp.industry && (
                                          <span className="company-industry-tag">{comp.industry}</span>
                                        )}
                                      </div>
                                    </div>

                                    {comp.overview && (
                                      <p className="company-overview-text">{comp.overview}</p>
                                    )}

                                    <div className="company-actions-bar">
                                      <button
                                        type="button"
                                        className="btn-chat-source-inspect"
                                        onClick={() =>
                                          setActiveSourceModal({
                                            category: "company",
                                            title: comp.name,
                                            sourceName: comp.industry || "Corporate Profile",
                                            snippet: comp.overview || comp.description || "Verified company profile retrieved during multi-agent research.",
                                            url: comp.website,
                                            badgeLabel: "Corporate Intelligence",
                                            badgeIcon: "🏢",
                                          })
                                        }
                                      >
                                        Inspect Source ↗
                                      </button>
                                      {onNavigateToCompany && (
                                        <button
                                          type="button"
                                          className="btn-chat-view-company"
                                          onClick={() => onNavigateToCompany(comp.name)}
                                        >
                                          View Company →
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Inline Section: 📰 News Cards */}
                          {msg.response.news && msg.response.news.length > 0 && (
                            <div className="chat-inline-section">
                              <div className="inline-section-header">
                                <span>📰</span>
                                <h4>Latest News Signals</h4>
                              </div>
                              <div className="ai-news-grid">
                                {msg.response.news.map((item: NewsArticleData, nIdx: number) => (
                                  <div key={nIdx} className="ai-news-card">
                                    <div className="ai-news-img-wrap">
                                      {item.image_url ? (
                                        /* eslint-disable-next-line @next/next/no-img-element */
                                        <img
                                          src={item.image_url}
                                          alt={item.title}
                                          className="ai-news-img"
                                          onError={(e) => {
                                            const target = e.target as HTMLElement;
                                            target.style.display = "none";
                                            const fallback = target.nextElementSibling as HTMLElement;
                                            if (fallback) fallback.style.display = "flex";
                                          }}
                                        />
                                      ) : null}
                                      <div
                                        className="ai-news-img-fallback"
                                        style={{ display: item.image_url ? "none" : "flex" }}
                                      >
                                        <div className="fallback-badge">
                                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                                            <path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2" />
                                            <path d="M18 14h-8" />
                                            <path d="M15 18h-5" />
                                            <path d="M10 6h8v4h-8V6Z" />
                                          </svg>
                                          <span>{item.source || "News Signal"}</span>
                                        </div>
                                      </div>
                                    </div>

                                    <div className="ai-news-content">
                                      <div className="ai-news-meta">
                                        <span className="ai-news-source">{item.source || "News"}</span>
                                        {item.published_at && (
                                          <span className="ai-news-date">
                                            {new Date(item.published_at).toLocaleDateString(undefined, {
                                              month: "short",
                                              day: "numeric",
                                              year: "numeric",
                                            })}
                                          </span>
                                        )}
                                      </div>

                                      <h4 className="ai-news-title" title={item.title}>
                                        {item.title}
                                      </h4>

                                      {item.description && (
                                        <p className="ai-news-desc">{item.description}</p>
                                      )}

                                      <div className="ai-news-footer">
                                        <button
                                          type="button"
                                          className="btn-news-preview"
                                          onClick={() =>
                                            setActiveSourceModal({
                                              category: "news",
                                              title: item.title,
                                              sourceName: item.source,
                                              publishedDate: item.published_at,
                                              snippet: item.description,
                                              imageUrl: item.image_url,
                                              url: item.url,
                                              badgeLabel: "News Signal",
                                              badgeIcon: "📰",
                                            })
                                          }
                                        >
                                          Inspect
                                        </button>

                                        {item.url ? (
                                          <a
                                            href={item.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-open-article-link"
                                          >
                                            <span>Open Article</span>
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
                                              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                              <polyline points="15 3 21 3 21 9" />
                                              <line x1="10" y1="14" x2="21" y2="3" />
                                            </svg>
                                          </a>
                                        ) : (
                                          <button
                                            type="button"
                                            className="btn-open-article-link"
                                            onClick={() =>
                                              setActiveSourceModal({
                                                category: "news",
                                                title: item.title,
                                                sourceName: item.source,
                                                publishedDate: item.published_at,
                                                snippet: item.description,
                                                imageUrl: item.image_url,
                                                url: item.url,
                                                badgeLabel: "News Signal",
                                                badgeIcon: "📰",
                                              })
                                            }
                                          >
                                            <span>View Details</span>
                                            <span>↗</span>
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Inline Section: 🔬 Research Papers */}
                          {msg.response.research && msg.response.research.length > 0 && (
                            <div className="chat-inline-section">
                              <div className="inline-section-header">
                                <span>🔬</span>
                                <h4>Academic & Research Papers</h4>
                              </div>
                              <div className="ai-research-grid">
                                {msg.response.research.map((paper: ResearchPaperData, pIdx: number) => (
                                  <div
                                    key={pIdx}
                                    className="ai-paper-card ai-card-clickable"
                                    onClick={() =>
                                      setActiveSourceModal({
                                        category: "research",
                                        title: paper.title,
                                        sourceName: paper.source || "Academic Repository",
                                        publishedDate: paper.published_date,
                                        authors: paper.authors,
                                        snippet: paper.abstract,
                                        url: paper.url,
                                        badgeLabel: "Academic Publication",
                                        badgeIcon: "🔬",
                                      })
                                    }
                                  >
                                    <div className="ai-paper-header">
                                      <span className="paper-source-badge">
                                        {paper.source || "Academic Repository"}
                                      </span>
                                      {paper.published_date && (
                                        <span className="paper-date">{paper.published_date}</span>
                                      )}
                                    </div>
                                    <h4 className="ai-paper-title">{paper.title}</h4>
                                    {paper.authors && (
                                      <p className="ai-paper-authors">Authors: {paper.authors}</p>
                                    )}
                                    {paper.abstract && (
                                      <p className="ai-paper-abstract">{paper.abstract}</p>
                                    )}
                                    <div className="ai-card-btn-row">
                                      <span className="btn-card-preview-action">
                                        View Abstract & Details ↗
                                      </span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Inline Section: 🔗 Verified Sources */}
                          {msg.response.sources && msg.response.sources.length > 0 && (
                            <div className="chat-inline-section">
                              <div className="inline-section-header">
                                <span>🔗</span>
                                <h4>Verified Sources ({msg.response.sources.length})</h4>
                              </div>
                              <div className="sources-chips-wrap">
                                {msg.response.sources.map((src: SourceItemData, sIdx: number) => (
                                  <button
                                    key={sIdx}
                                    type="button"
                                    className="source-chip"
                                    onClick={() =>
                                      setActiveSourceModal({
                                        category: "source",
                                        title: src.title,
                                        sourceName: extractDomain(src.url) || "Verified Citation",
                                        snippet: src.snippet || "Verified external source cited and analyzed by the Research Agent.",
                                        url: src.url,
                                        badgeLabel: "Verified Web Citation",
                                        badgeIcon: "🔗",
                                      })
                                    }
                                    title="Click to view details inside current page"
                                  >
                                    <span className="source-chip-title">{src.title}</span>
                                    <span className="source-chip-arrow">👁 Preview</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* ChatGPT-Style Sticky Message Composer */}
      <div className="chat-composer-sticky">
        <form
          className="chat-composer-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <textarea
            ref={textareaRef}
            rows={1}
            className="chat-composer-textarea"
            placeholder="Message AI Intelligence..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={isSubmitting}
          />

          <div className="composer-actions">
            {isSubmitting ? (
              <button
                type="button"
                className="btn-composer-stop"
                onClick={handleStop}
                title="Stop generation"
              >
                <span className="stop-square" />
              </button>
            ) : (
              <button
                type="submit"
                className="btn-composer-send"
                disabled={!inputValue.trim()}
                title="Send message"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width="18" height="18">
                  <path d="M12 19V5M5 12l7-7 7 7" />
                </svg>
              </button>
            )}
          </div>
        </form>

        <p className="composer-disclaimer">
          AI Intelligence uses autonomous multi-agent verification across Tavily, GNews & academic sources.
        </p>
      </div>

      {/* In-Page Source Details Inspector Modal */}
      {activeSourceModal && (
        <div
          className="source-modal-overlay"
          onClick={() => setActiveSourceModal(null)}
        >
          <div
            className="source-modal-container"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="source-modal-header">
              <div className="source-modal-badge">
                <span className="badge-icon">{activeSourceModal.badgeIcon}</span>
                <span className="badge-text">{activeSourceModal.badgeLabel}</span>
              </div>
              <button
                type="button"
                className="source-modal-close"
                onClick={() => setActiveSourceModal(null)}
                title="Close preview"
              >
                ✕
              </button>
            </div>

            <div className="source-modal-body">
              {activeSourceModal.imageUrl && (
                <div className="source-modal-img-wrap">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={activeSourceModal.imageUrl}
                    alt={activeSourceModal.title}
                    className="source-modal-img"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = "none";
                    }}
                  />
                </div>
              )}

              <h3 className="source-modal-title">{activeSourceModal.title}</h3>

              <div className="source-modal-meta-row">
                {activeSourceModal.sourceName && (
                  <div className="source-meta-chip">
                    <span className="meta-label">Source:</span>
                    <span className="meta-val">{activeSourceModal.sourceName}</span>
                  </div>
                )}
                {activeSourceModal.publishedDate && (
                  <div className="source-meta-chip">
                    <span className="meta-label">Published:</span>
                    <span className="meta-val">
                      {new Date(activeSourceModal.publishedDate).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </div>
                )}
                {activeSourceModal.authors && (
                  <div className="source-meta-chip">
                    <span className="meta-label">Authors:</span>
                    <span className="meta-val">{activeSourceModal.authors}</span>
                  </div>
                )}
              </div>

              {activeSourceModal.snippet && (
                <div className="source-modal-section">
                  <h4 className="section-subtitle">
                    <span>📋</span> Relevant Content & Key Information
                  </h4>
                  <div className="source-snippet-box">
                    <p>{activeSourceModal.snippet}</p>
                  </div>
                </div>
              )}

              {activeSourceModal.url && (
                <div className="source-modal-section">
                  <h4 className="section-subtitle">
                    <span>🔗</span> Original Verified URL
                  </h4>
                  <div className="source-url-display">
                    <span className="url-text">{activeSourceModal.url}</span>
                  </div>
                </div>
              )}
            </div>

            <div className="source-modal-footer">
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setActiveSourceModal(null)}
              >
                Close Details
              </button>

              {activeSourceModal.url && (
                <a
                  href={activeSourceModal.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-modal-open-external"
                >
                  <span>Open Original Source</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
