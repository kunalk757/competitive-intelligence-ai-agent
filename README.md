# Competitive Intelligence AI Agent

An autonomous, multi-agent AI system designed to gather, synthesize, evaluate, and track real-time competitive intelligence across technology companies, market movements, dynamic news signals, and industry benchmarks.

Powered by **FastAPI**, **Next.js**, **Google Gemini**, and a state-of-the-art **LangGraph Dynamic Agent Framework**.

---

## 📌 Problem Statement

In fast-paced technology markets, tracking competitor moves, product launches, architectural advances, and strategic signals requires monitoring disparate information sources (press releases, news feeds, financial filings, technical benchmarks). Manual intelligence gathering is:
- **Fragmented & Time-Consuming**: Analysts spend hours sifting through noisy, duplicate articles.
- **Vulnerable to Static Pipelines**: Fixed-chain workflows fail when external search APIs hit rate limits or downtime.
- **Unaware of Conflicting Evidence**: Traditional LLM prompts often hallucinate certainty when conflicting claims exist across early leaks vs verified reports.

## 💡 Solution

The **Competitive Intelligence AI Agent** provides an autonomous multi-agent platform that:
1. **Dynamically Plans & Decomposes Goals**: Evaluates user queries into parallelized subtasks.
2. **Executes Multi-Source Research**: Concurrently gathers verified data from web search, news aggregators, and corporate filings.
3. **Resolves Conflicting Claims**: Normalizes evidence, compares source recency/reliability, and flags contradictions with calibrated confidence ratings (`HIGH`, `MEDIUM`, `LOW`).
4. **Recovers Autonomously**: Dynamically replans workflows upon tool errors or service timeouts without terminating the investigation.
5. **Synthesizes Executive Reports**: Generates structured markdown intelligence reports with citations, verified metrics, and hypothesis evaluations.

---

## 👥 Team

- **Shruti Mandhane** — Team Member
- **Shreya Karhekar** — Team Member
- **Rohit Vinchu** — Backend / AI Agent
- **Kunal Kasar** — Frontend / Full-Stack

---

## ⚡ Task 5 — LangGraph Agent Framework

Task 5 introduces **LangGraph** as the dynamic multi-agent orchestration layer. Unlike rigid, linear chains, LangGraph provides stateful cyclic graphs, conditional routing, shared state schemas, memory checkpointing, and dynamic failure recovery loops.

### Why LangGraph?
- **Dynamic Graph Execution**: Dynamically constructs task plans based on query intent (`single_company`, `multi_comparison`, `scientific_research`, `market_overview`).
- **Shared Investigation State**: Strongly-typed state tracks collected evidence, tool errors, task budgets, and hypotheses across nodes.
- **Parallel Branching**: Dispatches concurrent research subtasks simultaneously using non-blocking asynchronous execution.
- **Failure Recovery & Replanning**: Graph cycles allow the agent to detect tool faults, re-route to alternative evidence sources, and continue investigation.
- **Circuit Breakers**: Monitors action frequency to break infinite loops and deadlocks.

---

### Implemented Core Capabilities (Task 5)

1. **LangGraph Agent Framework**: Stateful multi-node execution graph compiled with `StateGraph(GraphInvestigationState)`.
2. **Dynamic Planning**: Query classification, dynamic task decomposition, and strategy selection.
3. **Conditional Routing**: State-driven edge transitions (`route_after_planner`, `route_after_research`, `route_after_self_eval`).
4. **Multi-Agent Orchestration**: Seamless collaboration between Research Agents, Tools, and the Intelligence Analyst Agent.
5. **Parallel Execution**: Concurrent asynchronous dispatch for independent entity research branches.
6. **Shared Investigation State**: Centralized state tracking subtasks, evidence findings, hypotheses, and confidence.
7. **Checkpointing**: Memory persistence using LangGraph `MemorySaver` with session isolation.
8. **Autonomous Replanning**: Dynamic replanner that rebuilds remaining tasks when tools fail.
9. **Failure Recovery**: Intelligent recovery loops routing around broken endpoints.
10. **Tool Fallback**: Automatic redirection to alternative information providers (e.g., GNews/Company Profiles when Web Search fails).
11. **Conflicting Evidence Resolution**: Cross-source comparison evaluating source credibility, dates, and claims.
12. **Uncertainty-Aware Decisions**: Calibrated investigation confidence scoring (`HIGH`, `MEDIUM`, `LOW`).
13. **Hypothesis Verification**: Generation and empirical scoring of testable intelligence hypotheses.
14. **Self-Evaluation**: Quality gate validating goal completeness and entity coverage before response generation.
15. **Memory-Based Reasoning**: Context-aware disambiguation integrating session history.
16. **Adaptive Task Decomposition**: Entity-specific query generation tailored to the investigation target.
17. **Resource-Aware Execution**: Hard budgets for tool-call counts and maximum graph iterations.
18. **Loop / Deadlock Detection**: Circuit breaker monitoring repeated action counts ($\ge 2$) to prevent infinite cycles.
19. **Configurable Iteration Limits**: User- and system-governed iteration boundaries.
20. **Adversarial Testing**: Dedicated developer testing panel and backend fault-injection hooks.

---

## 🔄 Task 5 Dynamic Investigation Workflow

```
User Goal
   ↓
Context & Memory Retrieval
   ↓
Dynamic Planner (Intent & Hypotheses)
   ↓
Conditional Router
   ↓
Multi-Agent Research Dispatch
   ↓
Parallel Tool Execution (Async Gather)
   ↓
Evidence Collection & Conflict Detection
   ↓
Intelligence Analyst Synthesis
   ↓
Self-Evaluation Quality Gate
   ├── [If Failed / Insufficient] ──→ Autonomous Replanning ──→ Research Loop
   └── [If Passed] ──────────────────→ Memory Update & Final Intelligence Report
```

> **Note**: If evidence is insufficient, a tool fails, or verification is incomplete, the graph dynamically routes back to the planner/researcher nodes rather than failing or outputting empty reports. Internal chain-of-thought is never exposed; all user-facing telemetry is provided as clean high-level execution milestones.

---

## 🧠 Dynamic Planning & Parallel Execution

### Dynamic Planning Example
When a user submits:
> *"Compare NVIDIA and AMD's latest AI chips."*

The Dynamic Planner analyzes the comparison intent and breaks it into parallelized, testable subtasks:
- **Subtask 1**: Retrieve NVIDIA company intelligence & architecture specifications.
- **Subtask 2**: Retrieve NVIDIA recent news & market signals.
- **Subtask 3**: Retrieve AMD company intelligence & architecture specifications.
- **Subtask 4**: Retrieve AMD recent news & market signals.
- **Subtask 5**: Perform comparative web intelligence across H100/B200 vs MI300X/MI325X.

### Parallel Execution Architecture
```
                     Planner
                        ↓
    ┌───────────────────┼───────────────────┐
    ↓                   ↓                   ↓
  NVIDIA               AMD                News /
 Research            Research          Web Intelligence
    ↓                   ↓                   ↓
    └───────────────────┼───────────────────┘
                        ↓
                 Evidence Merging
                        ↓
            Cross-Source Verification
                        ↓
               Intelligence Analyst
```

Independent research branches execute concurrently via `asyncio.gather()`, maximizing throughput while respecting tool rate limits.

---

## 🗄️ Shared State & Checkpointing

LangGraph maintains a strongly-typed `GraphInvestigationState` TypedDict containing:
- `user_query`: Raw user prompt.
- `session_id`: Unique thread identifier.
- `relevant_context`: Conversational memory and active entities.
- `task_plan` & `subtasks`: Structured execution plan.
- `collected_companies`, `collected_news`, `collected_research`, `collected_sources`: Aggregated multi-source findings.
- `evidence`: Normalized atomic factual observations.
- `conflicting_evidence`: Contradictory statements detected across sources.
- `hypotheses`: Testable propositions evaluated against evidence.
- `confidence`: Overall rating (`high`, `medium`, `low`).
- `tool_errors`: Structured log of encountered failures.
- `completed_tasks` & `remaining_tasks`: Dynamic progress trackers.
- `tool_call_count` & `iteration_count`: Budget counters.
- `steps`: High-level user-facing execution event log.

**Checkpointing**: Uses LangGraph `MemorySaver` to checkpoint state snapshots after each node transition, enabling session isolation, state auditability, and recovery.

---

## 🛡️ Autonomous Replanning & Tool Fallback

When a data source encounters an error (HTTP 503, 429 rate limit, or timeout), the system does **not** stop or crash.

```
Initial Research Subtask
   ↓
Tool Error / API Failure Encountered
   ↓
Failure Recorded in Shared State
   ↓
Autonomous Replanning Node Triggered
   ↓
Alternative Available Sources Selected
   ↓
Parallel Investigation Resumed
   ↓
Evidence Evaluated & Synthesized
```

1. **Failure Recording**: The failing tool is logged with its error message and subtask ID.
2. **Circuit Breaker Check**: If a specific tool fails repeatedly ($\ge 2$), it is marked permanently unavailable for the remainder of the session.
3. **Dynamic Re-routing**: Subtasks mapped to the failed tool are converted to fallback providers (e.g., swapping Tavily Web Search $\rightarrow$ GNews / Company Intelligence).
4. **Execution Continuation**: Graph loops back to `parallel_research` with updated subtasks.

---

## ⚖️ Conflicting Evidence & Uncertainty Scoring

The agent evaluates multi-source corroboration and flags contradictions:

```
Source A (e.g., Blog Leak) ────────→ Claim: "Bandwidth under 4 TB/s"
                                          ≠ [Conflict Detected]
Source B (e.g., IEEE / MLPerf) ────→ Claim: "Verified 5.3 TB/s Bandwidth"
                                          ↓
                             Evaluator Source Weighting
                             (Recency, Reputation, Data)
                                          ↓
                             Calibrated Confidence Score
                                          ↓
                         Transparent Disclosure in Report
```

- **Weighting Criteria**: Evaluates source reliability ratings, publication dates (recency bias for evolving market news), and empirical corroboration.
- **Uncertainty Calibration**: If critical facts remain disputed, the confidence score drops to `MEDIUM` or `LOW`, and an explicit *"Cross-Source Verification & Evidence Conflicts"* disclosure section is added to the report.

---

## 🔬 Hypothesis Verification & Self-Evaluation

### Hypothesis Verification
For analytical queries, the planner formulates testable hypotheses:
- *Hypothesis*: *"NVIDIA holds a software developer ecosystem advantage over AMD in datacenter AI."*
- *Evidence Scoring*: Gathers supporting vs contradicting evidence, assigning an evaluation score $[0.0, 1.0]$.
- *Status*: Marked `supported`, `refuted`, or `inconclusive` in the final intelligence report.

### Self-Evaluation Quality Gate
Before delivering the report, the `self_eval_node` verifies:
- Was the user's core question answered?
- Were all requested entities researched?
- Is evidence volume sufficient?
- Are unresolved tool failures blocking completeness?

If self-evaluation fails, the graph initiates a replan cycle; if it passes, the response is delivered to the user.

---

## 🔁 Loop / Deadlock Detection & Resource Awareness

- **Action History Tracking**: Prevents repetitive state transitions.
- **Deadlock Breaker**: If the graph detects the same action sequence executing more than twice without new evidence, it terminates the loop and forces synthesis.
- **Resource Constraints**:
  - `max_tool_calls`: Default limit of 8 calls per investigation.
  - `max_iterations`: Default limit of 5 graph iterations.

---

## 🧠 Memory-Based Contextual Reasoning

Integrates with conversational session memory to resolve anaphoric follow-up queries:
- **Turn 1**: *"Tell me about NVIDIA's datacenter revenue."*
- **Turn 2**: *"What are its main competing AI chips?"*
- **Resolution**: Context Manager extracts active entities (`NVIDIA`) and topics (`AI chips`), rewriting the investigation goal to *"What are NVIDIA's main competing AI chips?"*.

---

## 🔥 Adversarial Live Test — Demonstrated Results

A live demonstration was conducted to test the failure recovery and replanning engine under deliberate fault conditions.

### Test Scenario: Simulated Tavily Search Outage
- **Query**: `"Compare NVIDIA and AMD latest AI chips"`
- **Adversarial Config**: `force_tavily_fail: true`

### Observed Execution Flow:
```
Tavily Search Dispatched
   ↓
⚠ Simulated Tavily 503 API Outage
   ↓
Failure Recorded & Logged in Event Stream
   ↓
↻ Autonomous Replanning Initiated
   ↓
✓ Fallback Selected (GNews & Company Intelligence Profiles)
   ↓
✓ Parallel Research Branches Completed (NVIDIA & AMD)
   ↓
✓ 35 Multi-Source Evidence Findings Collected
   ↓
✓ Hypothesis Verification & Evidence Evaluation Completed
   ↓
✓ Intelligence Analyst Report Synthesized
   ↓
✓ Self-Evaluation Verified & Passed
   ↓
✓ Session Memory Updated & Final Report Generated
```

> **Key Result**: The investigation **did not terminate** when Tavily failed. The agent detected the failure, autonomously replanned the investigation, routed to fallback research sources, continued collecting evidence, evaluated the findings, and successfully completed the comprehensive intelligence report.

### Supported Adversarial Test Scenarios:
1. **Tavily Web Search Failure** (`force_tavily_fail: true`): ✅ *Demonstrated*
2. **GNews API Rate Limit / Failure** (`force_gnews_fail: true`): ✅ *Demonstrated*
3. **Repeated Tool Failure & Circuit Breaker** (`force_repeated_tool_fail: "search_news"`): ✅ *Demonstrated*
4. **Conflicting Evidence Injection & Resolution** (`inject_conflicting_evidence: {...}`): ✅ *Demonstrated*

---

## 📊 Task 5 Implementation Status Table

| Capability | Status | Description |
| :--- | :---: | :--- |
| **LangGraph Framework** | ✅ Implemented | Stateful `StateGraph` dynamic orchestration layer |
| **Dynamic Planning** | ✅ Implemented | Intent-aware task plan generation |
| **Conditional Routing** | ✅ Implemented | Dynamic state-based branching |
| **Multi-Agent Orchestration** | ✅ Implemented | Collaborative Research & Analyst agents |
| **Parallel Execution** | ✅ Implemented | Concurrent asynchronous subtask dispatch |
| **Shared State** | ✅ Implemented | Typed `GraphInvestigationState` schema |
| **Checkpointing** | ✅ Implemented | LangGraph `MemorySaver` thread isolation |
| **Autonomous Replanning** | ✅ Implemented | Dynamic task plan regeneration on failure |
| **Failure Recovery** | ✅ Implemented | Loop-based recovery around broken tools |
| **Tool Fallback** | ✅ Implemented | Automatic re-routing to alternative sources |
| **Conflicting Evidence** | ✅ Implemented | Cross-source conflict detection & weighing |
| **Confidence / Uncertainty** | ✅ Implemented | Calibrated confidence ratings (`HIGH`/`MED`/`LOW`) |
| **Hypothesis Verification** | ✅ Implemented | Empirical hypothesis scoring and tracking |
| **Self-Evaluation** | ✅ Implemented | Quality gate prior to report delivery |
| **Memory-Based Reasoning** | ✅ Implemented | Multi-turn contextual query disambiguation |
| **Adaptive Task Decomposition** | ✅ Implemented | Entity-specific research subtask creation |
| **Resource-Aware Execution** | ✅ Implemented | Tool-call budgets and iteration limits |
| **Loop / Deadlock Detection** | ✅ Implemented | Action frequency tracking & circuit breakers |
| **Adversarial Test Workflow** | ✅ Implemented | Interactive UI panel & backend fault injector |
| **Tavily Failure Recovery Demo**| ✅ Demonstrated | Live failure, replan, fallback, and synthesis |

---

## 🏢 Additional Implemented Features

### AI Intelligence Agent
- **Gemini API Integration**: Powers deep reasoning, hypothesis verification, and executive synthesis.
- **ReAct-Style Tool Calling**: Autonomous tool invocation with high-level activity telemetry.
- **Agent Activity Log**: Real-time event log with clear milestone icons (`✓`, `⚠`, `↻`, `•`).
- **Intelligence Report**: Structured markdown output complete with metrics, executive summaries, citations, and conflict disclosures.

### Real-Time News System
- **GNews Integration**: Live competitor and market news retrieval.
- **News Deduplication**: URL and title deduplication.
- **Persistent Storage**: Cached in Supabase PostgreSQL with published timestamps and source links.
- **Resilient Fallback**: Previously saved news remains available even if external APIs experience downtime.
- **Scheduled Refresh**: Configured for 10:00 AM and 10:00 PM IST refresh cycles.

### Company Intelligence Dashboard
- **20 Predefined Tech Giants**:
  1. NVIDIA
  2. AMD
  3. Intel
  4. Microsoft
  5. Google
  6. Apple
  7. Amazon
  8. Meta
  9. OpenAI
  10. Anthropic
  11. Tesla
  12. Samsung
  13. Qualcomm
  14. TSMC
  15. Broadcom
  16. IBM
  17. Oracle
  18. Salesforce
  19. Adobe
  20. Cisco
- **Company Search & Detail Profiles**: Real-time business metrics, executive summaries, latest company-specific news, and direct source links.
- **Supabase Caching**: Cached with `fetched_at` timestamps to avoid redundant external API calls.

---

## 🔒 Security Best Practices

- **Backend-Only API Keys**: Gemini, Tavily, GNews, and Supabase credentials are stored exclusively in backend environment variables.
- **No Client-Side Secrets**: Next.js frontend interacts only with backend REST endpoints and never touches third-party API keys.
- **Git Protection**: `.env` and local secrets are excluded via `.gitignore`.
- **Template Configuration**: `.env.example` provides placeholder keys without exposing actual credentials.

```env
# Backend .env example
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
GNEWS_API_KEY=your_gnews_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_key_here
```

---

## 💻 Technology Stack

- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Vanilla CSS Design System.
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2.
- **Agent Framework**: LangGraph (v1.2+), LangChain Core.
- **AI Models**: Google Gemini 2.5 Flash / Pro via Google GenAI SDK.
- **Data Providers**:
  - **Tavily API**: Deep web search and company intelligence.
  - **GNews API**: Real-time news aggregation.
  - **Semantic Scholar API**: Academic research papers (*upcoming / in progress*).
  - **USPTO Open Data**: Patent filings (*upcoming / in progress*).
- **Database**: Supabase PostgreSQL.

---

## 🏗️ System Architecture

### Multi-Agent Architecture
```
                     User / Browser
                           ↓
                   Next.js Frontend
                           ↓
                    FastAPI Backend
                           ↓
               LangGraph Agent Framework
                           ↓
                 Context & Session Memory
                           ↓
                    Dynamic Planner
                           ↓
                   Conditional Router
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
    Tavily Web         GNews API       Company Profiles
    Intelligence      Live Signals       & Filings
         ↓                 ↓                 ↓
         └─────────────────┼─────────────────┘
                           ↓
               Evidence & Conflict Engine
                           ↓
               Intelligence Analyst Agent
                           ↓
                 Self-Evaluation Gate
                           ↓
                  Supabase PostgreSQL
                           ↓
                 Intelligence Report UI
```

### Company Intelligence Flow
```
User Selection (e.g., NVIDIA)
   ↓
Company Details View
   ↓
FastAPI Company Service
   ↓
Tavily Search + GNews Retrieval
   ↓
Supabase Cache Validation & Storage
   ↓
Interactive Company Intelligence Dashboard
```

---

## 📌 Feature Roadmap: Implemented vs Upcoming

| Category | Status | Features |
| :--- | :---: | :--- |
| **Implemented** | ✅ Active | Executive Dashboard, AI Intelligence Agent, News Signals, Company Profiles, LangGraph Dynamic Framework, Parallel Execution, Checkpointing, Autonomous Replanning, Developer Adversarial Test Panel |
| **Coming Soon** | ⏳ Planned | Deep Academic Paper Search (Semantic Scholar), Patent Intelligence (USPTO), Custom Report Exports (PDF), Automated Email Alerts, Saved Research Collections |

---

## 🚀 Installation & Setup

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- API Keys: Google Gemini, Tavily, GNews, Supabase

### 1. Clone Repository
```bash
git clone https://github.com/kunalk757/competitive-intelligence-ai-agent.git
cd competitive-intelligence-ai-agent
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in backend/.env

# Start FastAPI server:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
cp .env.example .env.local

# Start Next.js development server:
npm run dev
```

The application will be accessible at **`http://localhost:3000`** with the backend running on **`http://localhost:8000`**.

### 4. Running Automated Tests
```bash
cd backend
.\venv\Scripts\activate
pytest tests/ -v
```

---

## 📸 Screenshots & Demo Placeholders

### Application Views
- **Executive Dashboard**: `[ Dashboard Screenshot Placeholder ]`
- **Latest News & Market Signals**: `[ News Feed Screenshot Placeholder ]`
- **Company Intelligence**: `[ Company Grid Screenshot Placeholder ]`
- **Company Detail Profile**: `[ Company Detail View Screenshot Placeholder ]`
- **Multi-Agent Investigation**: `[ AI Intelligence Chat Screenshot Placeholder ]`
- **LangGraph Activity Log & Adversarial Test**: `[ Agent Activity Log & Dev Panel Screenshot Placeholder ]`

### Demo Links
- **Live Application**: `[ Demo URL Placeholder ]`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Video Walkthrough**: `[ Video Link Placeholder ]`
- **GitHub Repository**: `https://github.com/kunalk757/competitive-intelligence-ai-agent`
