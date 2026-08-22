# Standardized Human Evaluation Rubric (1–5 Scale)

This document provides standardized guidelines for human expert evaluation of intelligence reports produced by the Competitive Intelligence AI Agent.

---

## 🎯 Evaluation Dimensions & Scoring Criteria

### 1. Accuracy & Factuality
- **Score 1 (Unacceptable)**: Contains blatant factual inaccuracies, wrong specifications, or hallucinated numbers.
- **Score 2 (Deficient)**: Multiple inaccurate or uncorroborated assertions.
- **Score 3 (Acceptable)**: Factually sound on primary claims; minor nuances or secondary metrics slightly off.
- **Score 4 (Good)**: High factual rigor with verifiable data across all covered entities.
- **Score 5 (Exemplary)**: 100% accurate, rigorously corroborated against primary corporate and technical records.

---

### 2. Relevance & Intent Fulfillment
- **Score 1 (Unacceptable)**: Ignores the user's objective or produces off-topic output.
- **Score 2 (Deficient)**: Only partially addresses the prompt; omits major requested aspects.
- **Score 3 (Acceptable)**: Answers the core question directly.
- **Score 4 (Good)**: Directly answers the prompt with meaningful strategic context.
- **Score 5 (Exemplary)**: Comprehensively addresses all explicit and implicit analytical dimensions of the user query.

---

### 3. Completeness & Multi-Entity Depth
- **Score 1 (Unacceptable)**: Fails to research requested comparison entities.
- **Score 2 (Deficient)**: Significant asymmetry (e.g. detailed on NVIDIA, single sentence on AMD).
- **Score 3 (Acceptable)**: Covers all primary entities with balanced high-level metrics.
- **Score 4 (Good)**: Balanced, deep technical and market comparisons across all entities.
- **Score 5 (Exemplary)**: Exhaustive, multi-dimensional intelligence covering architecture, financials, market moves, and roadmap.

---

### 4. Evidence & Citation Quality
- **Score 1 (Unacceptable)**: Zero citations, or links to irrelevant/broken sites.
- **Score 2 (Deficient)**: Generic search links without attribution.
- **Score 3 (Acceptable)**: Valid source URLs for major claims.
- **Score 4 (Good)**: Diverse high-credibility sources (reputable tech news, company filings).
- **Score 5 (Exemplary)**: Authoritative tier-1 citations (IEEE, MLPerf, SEC filings, official press releases) attached to specific claims.

---

### 5. Groundedness & Anti-Hallucination
- **Score 1 (Unacceptable)**: Majority of statements cannot be found in retrieved search evidence.
- **Score 2 (Deficient)**: Noticeable unsupported speculation presented as fact.
- **Score 3 (Acceptable)**: Most substantive statements derived from gathered evidence snippets.
- **Score 4 (Good)**: High fidelity to collected evidence; no unsupported assertions.
- **Score 5 (Exemplary)**: Every single claim is directly verifiable from the underlying evidence with zero unsupported leaps.

---

### 6. Synthesis & Executive Structure
- **Score 1 (Unacceptable)**: Disorganized, repetitive text dump.
- **Score 2 (Deficient)**: Poor formatting; difficult to extract key insights.
- **Score 3 (Acceptable)**: Clean markdown with headings and bullet points.
- **Score 4 (Good)**: Well-structured intelligence brief with executive summary, comparison tables, and takeaways.
- **Score 5 (Exemplary)**: Board-ready executive report with clear visual hierarchy, actionable takeaways, and crisp synthesis.

---

### 7. Uncertainty & Discrepancy Handling
- **Score 1 (Unacceptable)**: Presents early rumors or contradictory claims with false certainty.
- **Score 2 (Deficient)**: Fails to acknowledge evident discrepancies across sources.
- **Score 3 (Acceptable)**: Notes when data is unavailable or estimated.
- **Score 4 (Good)**: Explicitly surfaces conflicting claims and explains source credibility.
- **Score 5 (Exemplary)**: Calibrated uncertainty rating; dedicated cross-source verification section explaining timing, credibility, and verified truth.

---

## 📝 Reviewer Scoring Sheet Template

| Case ID | Query Summary | Accuracy (1–5) | Relevance (1–5) | Completeness (1–5) | Evidence (1–5) | Groundedness (1–5) | Structure (1–5) | Uncertainty (1–5) | Overall Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `TC-01` | NVIDIA Datacenter | 5 | 5 | 5 | 5 | 5 | 5 | 5 | **5.00** |
| `TC-02` | NVIDIA vs AMD | 5 | 5 | 5 | 4 | 5 | 5 | 5 | **4.86** |
| `TC-05` | Conflict Injection | 5 | 5 | 4 | 5 | 5 | 5 | 5 | **4.86** |
