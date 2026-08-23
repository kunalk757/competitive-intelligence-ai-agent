"use client";

import { useState } from "react";
import { NewsItemData } from "./NewsCard";

interface StepActivity {
  step: number;
  action: "tool" | "final" | "error";
  tool?: string;
  summary: string;
  status: "running" | "completed" | "failed";
  timestamp: string;
}

interface AgentRunResponse {
  success: boolean;
  answer: string;
  steps: StepActivity[];
  tools_used: string[];
  iterations: number;
  news_results?: NewsItemData[];
  error?: string;
}

interface ResearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialGoal?: string;
  backendUrl: string;
  onNewsReceived?: (news: NewsItemData[]) => void;
}

export default function ResearchModal({
  isOpen,
  onClose,
  initialGoal = "Analyze the competitive landscape for AI chips.",
  backendUrl,
  onNewsReceived,
}: ResearchModalProps) {
  const [goal, setGoal] = useState(initialGoal);
  const [maxIterations, setMaxIterations] = useState(5);
  const [isRunning, setIsRunning] = useState(false);
  const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);
  const [agentError, setAgentError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleStartAgent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;

    setIsRunning(true);
    setAgentError(null);
    setAgentResult(null);

    try {
      const res = await fetch(`${backendUrl}/api/agent/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal: goal.trim(),
          max_iterations: maxIterations,
        }),
      });

      const data: AgentRunResponse = await res.json();
      if (!res.ok) {
        throw new Error(data.error || `Server returned error ${res.status}`);
      }

      setAgentResult(data);

      // If the agent collected real news results, pass them up to the dashboard state
      if (data.news_results && data.news_results.length > 0 && onNewsReceived) {
        onNewsReceived(data.news_results);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setAgentError(err.message);
      } else {
        setAgentError("Failed to execute agent reasoning loop");
      }
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-header">
          <div className="modal-title">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ color: "var(--primary)" }}
            >
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            Autonomous Intelligence Investigation
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            ✕
          </button>
        </div>

        <div className="modal-body">
          <form onSubmit={handleStartAgent} style={{ marginBottom: "1.5rem" }}>
            <div className="form-group">
              <label htmlFor="modal-goal" className="form-label">
                Investigation Objective or Competitor Topic
              </label>
              <textarea
                id="modal-goal"
                className="form-textarea"
                rows={2}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                placeholder="e.g., Analyze the competitive landscape for AI chips and compute architectures."
                required
              />
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                <label
                  htmlFor="modal-iterations"
                  style={{
                    fontSize: "0.825rem",
                    color: "var(--text-secondary)",
                    fontWeight: 500,
                  }}
                >
                  Reasoning Limit:
                </label>
                <select
                  id="modal-iterations"
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(Number(e.target.value))}
                  style={{
                    padding: "0.35rem 0.65rem",
                    borderRadius: "6px",
                    border: "1px solid var(--border-subtle)",
                    fontSize: "0.85rem",
                    color: "var(--text-main)",
                    outline: "none",
                  }}
                >
                  <option value={3}>3 Iterations</option>
                  <option value={5}>5 Iterations (Recommended)</option>
                  <option value={8}>8 Iterations</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={isRunning}
                className="btn-primary"
                style={{ padding: "0.6rem 1.4rem" }}
              >
                {isRunning ? "🔄 Agent Reasoning..." : "🚀 Launch Agent"}
              </button>
            </div>
          </form>

          {agentError && (
            <div
              style={{
                padding: "0.85rem 1rem",
                backgroundColor: "var(--danger-light)",
                border: "1px solid #fecaca",
                borderRadius: "8px",
                marginBottom: "1.25rem",
              }}
            >
              <strong style={{ color: "var(--danger)", fontSize: "0.85rem" }}>
                ⚠️ Agent Error:{" "}
              </strong>
              <span style={{ color: "#7f1d1d", fontSize: "0.85rem" }}>{agentError}</span>
            </div>
          )}

          {/* Results Grid inside Modal */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1.3fr",
              gap: "1.25rem",
            }}
          >
            {/* Step activity */}
            <div
              style={{
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "1rem",
                backgroundColor: "#fafbfc",
              }}
            >
              <h4
                style={{
                  fontSize: "0.9rem",
                  fontWeight: 700,
                  color: "var(--text-main)",
                  marginBottom: "0.75rem",
                }}
              >
                ⚡ Agent Activity Log
              </h4>

              {isRunning && (
                <div
                  style={{
                    textAlign: "center",
                    padding: "1.5rem 0",
                    color: "var(--primary)",
                    fontSize: "0.85rem",
                  }}
                >
                  <p style={{ fontWeight: 600 }}>Autonomous agent is reasoning & executing tools...</p>
                  <p
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      marginTop: "0.25rem",
                    }}
                  >
                    (Goal → Gemini → Tool Selection → Observation → Synthesis)
                  </p>
                </div>
              )}

              {!isRunning && !agentResult && (
                <p
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    textAlign: "center",
                    padding: "1.5rem 0",
                  }}
                >
                  Click &ldquo;Launch Agent&rdquo; to start the autonomous investigation loop.
                </p>
              )}

              {!isRunning && agentResult && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.5rem",
                    maxHeight: "320px",
                    overflowY: "auto",
                  }}
                >
                  {agentResult.steps.map((s, idx) => (
                    <div
                      key={idx}
                      style={{
                        padding: "0.55rem 0.75rem",
                        borderRadius: "6px",
                        backgroundColor: "#ffffff",
                        border: "1px solid var(--border-subtle)",
                        fontSize: "0.8rem",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                        <span
                          style={{
                            color: s.status === "failed" ? "var(--danger)" : "var(--success)",
                            fontWeight: "bold",
                          }}
                        >
                          {s.status === "failed" ? "✕" : "✓"}
                        </span>
                        <strong style={{ color: "var(--text-main)" }}>Step {s.step}:</strong>
                        <span style={{ color: "var(--text-secondary)" }}>{s.summary}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Intelligence Report */}
            <div
              style={{
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "1rem",
                backgroundColor: "#ffffff",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.75rem",
                }}
              >
                <h4
                  style={{
                    fontSize: "0.9rem",
                    fontWeight: 700,
                    color: "var(--text-main)",
                  }}
                >
                  📊 Intelligence Report
                </h4>
                {agentResult && (
                  <div style={{ display: "flex", gap: "0.3rem" }}>
                    {agentResult.tools_used.map((t) => (
                      <span key={t} className="tag-pill tag-company" style={{ fontSize: "0.65rem" }}>
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {!agentResult && (
                <p
                  style={{
                    fontSize: "0.8rem",
                    color: "var(--text-muted)",
                    textAlign: "center",
                    padding: "1.5rem 0",
                  }}
                >
                  The completed intelligence synthesis will appear here.
                </p>
              )}

              {agentResult && (
                <div
                  style={{
                    maxHeight: "320px",
                    overflowY: "auto",
                    fontSize: "0.85rem",
                    lineHeight: 1.6,
                    color: "var(--text-main)",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {agentResult.answer}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
