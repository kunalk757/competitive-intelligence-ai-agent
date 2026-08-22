"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage, AgentRunResponse, CompanyCardData, NewsArticleData, ResearchPaperData, SourceItemData } from "@/types/agent";

interface AIIntelligenceViewProps {
  onNavigateToCompany?: (companyName: string) => void;
}

const STARTER_QUERIES = [
  "NVIDIA latest AI developments",
  "Latest news about AMD",
  "Research papers about large language models",
  "Compare NVIDIA and AMD in AI chips",
];

export default function AIIntelligenceView({ onNavigateToCompany }: AIIntelligenceViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedActivities, setExpandedActivities] = useState<{ [msgId: string]: boolean }>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const rawBackendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  const backendUrl = rawBackendUrl.replace(/\/+$/, "");
  const activeAbortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSubmitting]);

  useEffect(() => {
    return () => {
      // Clean up any ongoing fetch on component unmount
      if (activeAbortControllerRef.current) {
        activeAbortControllerRef.current.abort();
      }
    };
  }, []);

  const toggleActivity = (id: string) => {
    setExpandedActivities((prev) => ({ ...prev, [id]: !prev[id] }));
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
      };

      const newAssistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        isLoading: true,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      // Construct recent chat history context for multi-turn follow-ups
      const historyContext = messages
        .filter((m) => !m.isLoading && !m.error)
        .map((m) => ({
          role: m.role,
          content: m.role === "user" ? m.queryText || "" : m.response?.answer || "",
        }));

      setMessages((prev) => [...prev, newUserMsg, newAssistantMsg]);
      setInputValue("");
      setIsSubmitting(true);

      const controller = new AbortController();
      activeAbortControllerRef.current = controller;

      try {
        console.debug(`[AIIntelligence] Calling agent endpoint at: ${backendUrl}/agent/run with goal: "${q}"`);
        const res = await fetch(`${backendUrl}/agent/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            goal: q,
            max_iterations: 5,
            chat_history: historyContext,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          console.error("Backend /agent/run returned error status:", res.status, errData);
          throw new Error(errData.detail || `Agent returned HTTP ${res.status}`);
        }

        const rawData = await res.json();
        console.debug("[AIIntelligence] Received agent response payload:", rawData);

        // Small adapter / normalizer for the AI Intelligence page
        const normalizedData: AgentRunResponse = {
          success: rawData.success ?? true,
          answer: rawData.answer || "Investigation concluded with no report generated.",
          steps: Array.isArray(rawData.steps) ? rawData.steps : [],
          tools_used: Array.isArray(rawData.tools_used) ? rawData.tools_used : [],
          iterations: typeof rawData.iterations === "number" ? rawData.iterations : 1,
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

        console.error("AI Intelligence investigation request failed:", {
          error: err,
          name: errorObj?.name,
          message: errorObj?.message,
          endpoint: `${backendUrl}/agent/run`,
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
    [inputValue, isSubmitting, messages, backendUrl]
  );

  return (
    <div className="ai-intelligence-container">
      {/* Page Header */}
      <div className="ai-intelligence-header">
        <div className="header-title-wrap">
          <div className="header-icon-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-4 4 4 4 0 0 1-4-4V6a4 4 0 0 1 4-4Z" />
              <path d="M18 14v1a6 6 0 0 1-12 0v-1" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </div>
          <div>
            <h1 className="page-heading">AI Intelligence</h1>
            <p className="page-subtitle">
              Ask anything about companies, news, technologies, competitors, and research.
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            className="btn-new-chat"
            onClick={() => setMessages([])}
            title="Start new research thread"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
              <path d="M21 3v5h-5" />
              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
              <path d="M3 21v-5h5" />
            </svg>
            <span>New Research</span>
          </button>
        )}
      </div>

      {/* Main Chat/Results Area */}
      <div className="ai-chat-thread">
        {messages.length === 0 ? (
          <div className="ai-starter-hero">
            <div className="hero-icon-large">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10" />
                <path d="m4.93 4.93 4.24 4.24" />
                <path d="m14.83 9.17 4.24-4.24" />
                <path d="m14.83 14.83 4.24 4.24" />
                <path d="m9.17 14.83-4.24 4.24" />
                <circle cx="12" cy="12" r="4" />
              </svg>
            </div>
            <h2>What would you like to investigate?</h2>
            <p>
              Our Autonomous ReAct Agent dynamically searches live web intelligence, news feeds,
              company profiles, and research papers to synthesize competitive reports.
            </p>

            <div className="starter-chips-grid">
              {STARTER_QUERIES.map((query, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="starter-chip"
                  onClick={() => handleSend(query)}
                >
                  <span className="chip-icon">⚡</span>
                  <span className="chip-text">{query}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`chat-bubble-row ${msg.role === "user" ? "user-row" : "assistant-row"}`}
            >
              {msg.role === "user" ? (
                <div className="user-message-bubble">
                  <p>{msg.queryText}</p>
                  <span className="bubble-timestamp">{msg.timestamp}</span>
                </div>
              ) : (
                <div className="assistant-response-container">
                  {/* Loading State */}
                  {msg.isLoading && (
                    <div className="ai-loading-card">
                      <div className="ai-spinner" />
                      <div className="loading-text-wrap">
                        <h3>Agent Investigating...</h3>
                        <p>Deciding tools, querying Tavily & GNews, and synthesizing findings.</p>
                      </div>
                    </div>
                  )}

                  {/* Error State */}
                  {msg.error && (
                    <div className="ai-error-banner">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      <p>{msg.error}</p>
                    </div>
                  )}

                  {/* Multi-Source Results Card */}
                  {msg.response && (
                    <div className="ai-results-wrapper">
                      {/* High-level Agent Activity Log */}
                      {msg.response.steps && msg.response.steps.length > 0 && (
                        <div className="agent-activity-box">
                          <button
                            type="button"
                            className="activity-toggle-btn"
                            onClick={() => toggleActivity(msg.id)}
                          >
                            <div className="activity-status-left">
                              <span className="activity-dot" />
                              <span className="activity-title">
                                Agent executed {msg.response.tools_used.length} tool(s) in {msg.response.iterations} iteration(s)
                              </span>
                            </div>
                            <span className="activity-arrow">
                              {expandedActivities[msg.id] ? "▲ Hide Steps" : "▼ View Activity"}
                            </span>
                          </button>

                          {expandedActivities[msg.id] && (
                            <ul className="activity-steps-list">
                              {msg.response.steps.map((step, sIdx) => (
                                <li key={sIdx} className={`step-item ${step.status}`}>
                                  <span className="step-icon">
                                    {step.status === "completed" ? "✓" : step.status === "failed" ? "✕" : "•"}
                                  </span>
                                  <span className="step-summary">{step.summary}</span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}

                      {/* 1. 🏢 Company Information Section (Only if present) */}
                      {msg.response.companies && msg.response.companies.length > 0 && (
                        <div className="multi-source-section">
                          <div className="section-header">
                            <span className="section-icon">🏢</span>
                            <h3>Company Information</h3>
                          </div>
                          <div className="company-results-grid">
                            {msg.response.companies.map((comp: CompanyCardData, cIdx: number) => (
                              <div key={cIdx} className="ai-company-card">
                                <div className="ai-company-card-top">
                                  <div className="ai-company-logo-badge">
                                    {comp.logo_url ? (
                                      /* eslint-disable-next-line @next/next/no-img-element */
                                      <img
                                        src={comp.logo_url}
                                        alt={`${comp.name} logo`}
                                        className="ai-company-logo-img"
                                        onError={(e) => {
                                          (e.target as HTMLElement).style.display = "none";
                                        }}
                                      />
                                    ) : (
                                      <span className="ai-company-initials">
                                        {comp.name.slice(0, 2).toUpperCase()}
                                      </span>
                                    )}
                                  </div>
                                  <div className="ai-company-meta">
                                    <h4>{comp.name}</h4>
                                    {comp.industry && (
                                      <span className="ai-company-industry">{comp.industry}</span>
                                    )}
                                  </div>
                                </div>

                                {comp.overview && (
                                  <p className="ai-company-overview">{comp.overview}</p>
                                )}

                                <div className="ai-company-card-actions">
                                  {comp.website && (
                                    <a
                                      href={comp.website}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="btn-link-out"
                                    >
                                      Official Website ↗
                                    </a>
                                  )}
                                  {onNavigateToCompany && (
                                    <button
                                      type="button"
                                      className="btn-view-company"
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

                      {/* 2. 📰 News Cards Section (Only if present) */}
                      {msg.response.news && msg.response.news.length > 0 && (
                        <div className="multi-source-section">
                          <div className="section-header">
                            <span className="section-icon">📰</span>
                            <h3>Latest News</h3>
                          </div>
                          <div className="ai-news-grid">
                            {msg.response.news.map((item: NewsArticleData, nIdx: number) => (
                              <div key={nIdx} className="ai-news-card">
                                {item.image_url && (
                                  <div className="ai-news-img-wrap">
                                    {/* eslint-disable-next-line @next/next/no-img-element */}
                                    <img
                                      src={item.image_url}
                                      alt={item.title}
                                      className="ai-news-img"
                                      onError={(e) => {
                                        (e.target as HTMLElement).style.display = "none";
                                      }}
                                    />
                                  </div>
                                )}
                                <div className="ai-news-content">
                                  <div className="ai-news-meta">
                                    <span className="ai-news-source">{item.source}</span>
                                    {item.published_at && (
                                      <span className="ai-news-date">
                                        {new Date(item.published_at).toLocaleDateString()}
                                      </span>
                                    )}
                                  </div>
                                  <h4 className="ai-news-title">{item.title}</h4>
                                  {item.description && (
                                    <p className="ai-news-desc">{item.description}</p>
                                  )}
                                  {item.url && (
                                    <a
                                      href={item.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="btn-read-article"
                                    >
                                      Read Article →
                                    </a>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 3. 🔬 Research Paper Cards Section (Only if present) */}
                      {msg.response.research && msg.response.research.length > 0 && (
                        <div className="multi-source-section">
                          <div className="section-header">
                            <span className="section-icon">🔬</span>
                            <h3>Related Research Papers</h3>
                          </div>
                          <div className="ai-research-grid">
                            {msg.response.research.map((paper: ResearchPaperData, pIdx: number) => (
                              <div key={pIdx} className="ai-paper-card">
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
                                {paper.url && (
                                  <a
                                    href={paper.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-view-paper"
                                  >
                                    View Paper →
                                  </a>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 4. 📊 AI Intelligence / Analysis Section */}
                      {msg.response.answer && (
                        <div className="multi-source-section intelligence-section">
                          <div className="section-header">
                            <span className="section-icon">📊</span>
                            <h3>Competitive Intelligence & Synthesis</h3>
                          </div>
                          <div className="intelligence-report-content">
                            {msg.response.answer.split("\n\n").map((para, pIdx) => {
                              if (para.startsWith("###") || para.startsWith("##") || para.startsWith("#")) {
                                return (
                                  <h4 key={pIdx} className="report-heading">
                                    {para.replace(/^[#]+\s*/, "")}
                                  </h4>
                                );
                              }
                              if (para.startsWith("- ") || para.startsWith("* ")) {
                                const bulletLines = para.split("\n");
                                return (
                                  <ul key={pIdx} className="report-bullet-list">
                                    {bulletLines.map((line, bIdx) => (
                                      <li key={bIdx}>{line.replace(/^[-*]\s*/, "")}</li>
                                    ))}
                                  </ul>
                                );
                              }
                              return (
                                <p key={pIdx} className="report-paragraph">
                                  {para}
                                </p>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* 5. 🔗 Verified External Sources */}
                      {msg.response.sources && msg.response.sources.length > 0 && (
                        <div className="multi-source-section sources-section">
                          <div className="section-header">
                            <span className="section-icon">🔗</span>
                            <h3>Verified External Sources</h3>
                          </div>
                          <div className="sources-chips-wrap">
                            {msg.response.sources.map((src: SourceItemData, sIdx: number) => (
                              <a
                                key={sIdx}
                                href={src.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="source-chip"
                              >
                                <span className="source-chip-title">{src.title}</span>
                                <span className="source-chip-arrow">↗</span>
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Search Input Bar */}
      <div className="ai-input-wrapper">
        <form
          className="ai-input-form"
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
        >
          <input
            ref={inputRef}
            type="text"
            className="ai-input-field"
            placeholder="What would you like to research? (e.g. NVIDIA AI chips, AMD datacenter, LLM papers)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isSubmitting}
          />
          <button
            type="submit"
            className="ai-send-btn"
            disabled={isSubmitting || !inputValue.trim()}
          >
            {isSubmitting ? (
              <div className="ai-btn-spinner" />
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            )}
            <span>{isSubmitting ? "Researching..." : "Send"}</span>
          </button>
        </form>
      </div>
    </div>
  );
}
