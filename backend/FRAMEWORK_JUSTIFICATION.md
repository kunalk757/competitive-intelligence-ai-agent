# LangGraph Framework Selection & Architecture Justification

## Executive Summary

The **Competitive Intelligence AI Agent** utilizes **LangGraph** (version `1.2.11`+) as its dynamic multi-agent orchestration and stateful execution engine. LangGraph was selected over conventional sequential pipelines and monolithic ReAct loops to provide dynamic planning, conditional routing, concurrent branch execution, robust fault tolerance, autonomous replanning, and state checkpointing while maintaining clean separation of concerns.

---

## Architectural Comparison

| Capability | Static Sequential Pipeline | Monolithic ReAct Loop | LangGraph Multi-Agent Architecture |
| :--- | :--- | :--- | :--- |
| **Workflow Adaptability** | Fixed, rigid hardcoded stages | Free-form unbounded tool calls | **Dynamic Directed Acyclic & Cyclic Graphs** tailored to query intent |
| **State Management** | Ad-hoc variable passing | Single flat prompt string | **Typed Shared State channels** passed reliably across nodes |
| **Parallelism** | None (sequential blocking) | None (sequential single-action) | **Concurrent Parallel Branches** for independent entity/domain research |
| **Failure Recovery** | Fails entire request | May loop blindly on failure | **Autonomous Circuit Breakers & Fallback Routing** |
| **Replanning** | None | Prompt-dependent hallucination | **Deterministic Replanning Node** triggered on failure/uncertainty |
| **Conflict Resolution** | Ignored / Overwritten | Overwritten | **Structured Multi-Source Evidence & Contradiction Evaluation** |
| **Uncertainty & Confidence** | Fabricated certainty | Uncalibrated | **Multi-dimensional Confidence Scoring ('high', 'medium', 'low')** |
| **Self-Evaluation** | None | Ad-hoc | **Dedicated Pre-Finalization Verification Node** |
| **Loop/Deadlock Guard** | N/A | Risk of infinite loops | **Deadlock & Circuit Breaker State Guard** |
| **State Checkpointing** | None | None | **Pluggable Checkpointers (`MemorySaver` / Supabase ready)** |
| **Privacy & Safety** | N/A | Leaks internal prompt thoughts | **Safe High-Level StepActivity Logs (No private CoT exposed)** |

---

## Key Core Architectural Pillars

### 1. Typed Shared State (`GraphInvestigationState`)
Rather than passing unstructured text strings or accumulating unbounded chat histories, LangGraph maintains a strongly typed shared investigation state (`GraphInvestigationState`). This state tracks:
- `user_query`, `session_id`, `investigation_goal`, `relevant_context`
- `task_plan`, `subtasks`, `completed_tasks`, `remaining_tasks`
- Structured entity collections (`collected_companies`, `collected_news`, `collected_research`, `collected_patents`, `collected_sources`)
- Structured evidence items (`EvidenceItem`), contradictions (`EvidenceConflict`), and testable hypotheses (`HypothesisRecord`)
- Uncertainty & quality metrics (`confidence`, `self_evaluation`, `evaluation_passed`)
- Execution health & resource limits (`tool_errors`, `tool_call_count`, `max_tool_calls`, `iteration_count`, `max_iterations`, `unavailable_tools`, `repeated_action_count`)
- Safe public step activities (`StepActivity`) without internal chain-of-thought leakage.

### 2. Dynamic Planning & Intent Decomposition
The investigation workflow dynamically analyzes the user query instead of executing one generic template:
- **Single Entity Research** (e.g., *"What is NVIDIA?"*): Targeted company intelligence + recent news + strategic analyst synthesis.
- **Comparative Intelligence** (e.g., *"Compare NVIDIA and AMD's latest AI chips"*): Dispatches parallel entity research branches, fetches cross-cutting hardware news, formulates comparison hypotheses, evaluates evidence conflicts, and runs comparative synthesis.
- **Frontier Scientific Research** (e.g., *"Find recent research on LLM reasoning"*): Queries arXiv/OpenReview repositories, searches technical web publications, and executes scientific synthesis.

### 3. Concurrency & Parallel Execution Branches
For multi-entity or multi-domain investigations, LangGraph coordinates parallel branch dispatching. Independent subtasks (such as querying NVIDIA corporate profile, AMD corporate profile, and AI chip news) execute concurrently via asynchronous subtask gathering, slashing latency and merging results into the shared state.

### 4. Dynamic Conditional Routing & Failure Recovery Loops
LangGraph's conditional edge routing dynamically chooses the next node based on execution health:
- Primary tools (Tavily, GNews, Company Services) are tried first.
- If a tool fails (e.g., rate limit, timeout, service error), the failure is recorded in `tool_errors`.
- The graph conditionally routes to the **Autonomous Replanning Node (`replan_node`)** or alternative fallback tools (e.g., GNews / Company Data fallback when Tavily is unavailable) without terminating the entire investigation.

### 5. Multi-Source Conflict Resolution & Uncertainty Awareness
When sources provide conflicting numbers or claims:
- Discrepancies are isolated in `EvidenceConflict` records.
- Source reliability (official filings > peer-reviewed papers > accredited news > broad web) and publication recency are compared.
- An uncertainty-aware confidence rating (`high`, `medium`, `low`) is computed and disclosed transparently in the final report.

### 6. Pre-Finalization Self-Evaluation
Before returning the final report to the user, the **Self-Evaluation Node (`self_eval_node`)** checks:
1. Did we answer the user's objective?
2. Are all required comparison entities represented?
3. Are citations and evidence sufficient?
4. Are conflicts resolved or explained?
5. Is confidence acceptable?
If verification fails and the iteration budget allows, the workflow loops back to dynamic replanning.

### 7. Resource Budgeting & Deadlock/Loop Prevention
The orchestrator tracks `tool_call_count` (bounded by `max_tool_calls`) and `iteration_count` (bounded by `max_iterations`). Additionally, a circuit breaker detects repeated failing actions (2+ consecutive failures of the same tool) or identical plan loops, marking the tool unavailable and forcing safe termination with the best-supported answer.

### 8. Checkpointing & Extensible Persistence
The graph is compiled with a LangGraph checkpointer (`MemorySaver`). Every state transition across nodes is checkpointed under `session_id:thread_id`. The abstraction allows drop-in replacement with persistent storage (such as Supabase, Postgres, or Redis) in future releases without modifying graph topology.

### 9. Preservation of Existing Multi-Agent Assets & Zero Breaking Changes
The LangGraph framework wraps the existing backend components:
- Reuses `ResearchAgent` and `IntelligenceAnalystAgent`
- Reuses `ToolRegistry`, `TavilyService`, `GNewsService`, `CompanyDataService`
- Reuses `ContextManager` and `SessionMemoryService`
- Preserves the REST API endpoint contracts (`POST /agent/run`) and ChatGPT-style AI Intelligence frontend UI.
