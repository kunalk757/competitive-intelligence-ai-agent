Update the EXISTING README.md in this repository.

IMPORTANT:
Do NOT create a new README.
Do NOT replace the README with a completely different structure.
Preserve the existing README structure, headings, formatting, and project explanation.

Update the existing README to accurately document everything that has been implemented so far in the Competitive Intelligence AI Agent.

## TEAM

Keep:

- Shruti Mandhane — Team Member
- Shreya Karhekar — Team Member
- Rohit Vinchu — Backend / AI Agent
- Kunal Kasar — Frontend

## ADD / UPDATE IMPLEMENTED FEATURES

Document these features as currently implemented:

### AI Agent
- Gemini API integration
- ReAct-style AI Agent
- Tool calling
- Agent Activity Log
- Intelligence Report
- Configurable iteration limit
- Agent investigation workflow

Explain the workflow:

User Goal
↓
AI Agent
↓
Tool Selection
↓
Tool Execution
↓
Observation
↓
Further Decision
↓
AI Analysis
↓
Intelligence Report

Do NOT expose private chain-of-thought.

### NEWS SYSTEM

Document that the project now has:

- GNews API integration
- Real news retrieval
- Latest News dashboard
- Persistent news storage
- Supabase PostgreSQL storage
- News deduplication
- Source URLs
- Published timestamps
- Saved news remains available even if a later API request fails
- Backend-controlled GNews API access
- News refresh architecture
- Update schedule planned/configured for 10:00 AM and 10:00 PM IST

Do not claim a scheduler is fully deployed if it is only configured/prepared.

### COMPANIES

Add a complete Companies section describing:

- Companies dashboard
- 20 predefined companies
- Company search
- Company cards
- Official/company logos
- Company Details page
- Dynamic company information
- Tavily integration for company/web information
- GNews integration for company-specific latest news
- Source URLs
- Supabase caching/storage
- fetched_at timestamps
- Duplicate news prevention
- Error handling when Tavily or GNews fails
- Backend company service
- Company API endpoint

Explain the company flow:

User
↓
Companies
↓
Select Company
↓
FastAPI
↓
Tavily + GNews
↓
Supabase
↓
Company Details

### COMPANY LIST

Document the current 20-company MVP list:

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

### DATA STORAGE

Document Supabase PostgreSQL as the persistent storage layer for:

- News
- Company information
- Cached company data
- News metadata
- Fetch/update timestamps

### API SECURITY

Add a security section explaining:

- API keys are stored in backend environment variables.
- API keys are never exposed to frontend code.
- `.env` is excluded from Git.
- `.env.example` contains variable names only.
- Gemini, Tavily, GNews, and Supabase secrets must not be committed to GitHub.

Example:

GEMINI_API_KEY=
TAVILY_API_KEY=
GNEWS_API_KEY=

Do NOT put real values in README.

## TECHNOLOGY STACK

Keep and update:

Frontend:
- Next.js
- React
- TypeScript
- HTML
- CSS

Backend:
- Python
- FastAPI
- REST APIs

AI:
- Gemini API
- ReAct-style Agent
- Tool Calling
- AI Summarization
- Competitive Analysis

APIs/Data Sources:
- Tavily — Web Search / Company Information
- GNews — News
- Semantic Scholar — Research Papers (planned / upcoming if not yet implemented)
- USPTO Open Data — Patents (planned / upcoming if not yet implemented)

Database:
- Supabase PostgreSQL

## SIDEBAR / UPCOMING FEATURES

Clearly distinguish implemented and upcoming features.

Implemented:
- Dashboard
- Research / Agent Investigation
- News
- Companies

Coming Soon / Next Tasks:
- Research Papers
- Patents
- Reports
- Alerts
- Saved Items

Do not claim these are implemented if they are not.

## INSTALLATION

Keep the existing installation instructions.

Make sure the environment variable section includes:

GEMINI_API_KEY=
TAVILY_API_KEY=
GNEWS_API_KEY=

Add Supabase variables only if they are actually required by the current implementation.

## HOW IT WORKS

Update the architecture diagram to include:

User
↓
Next.js Frontend
↓
FastAPI Backend
↓
Gemini ReAct Agent
↓
Tools / APIs
├── Tavily
├── GNews
├── Research APIs (future)
└── Patent APIs (future)
↓
Supabase PostgreSQL
↓
Dashboard / Intelligence Report

Also document the Company flow separately:

Companies
↓
Company Details
↓
Tavily + GNews
↓
Supabase
↓
Company Intelligence

## SCREENSHOTS

Keep the existing screenshot placeholders.

Add/update placeholders for:

- Dashboard
- Latest News
- Companies
- Company Details
- Agent Investigation
- Intelligence Report

Do not invent screenshot URLs.

## DEMO

Keep placeholders for:
- Live Demo
- Backend API
- Demo Video
- GitHub Repository

Do not invent URLs.

## IMPORTANT ACCURACY RULE

Only document functionality that currently exists or has actually been implemented.

Do NOT claim:
- Research Papers are complete
- Patents are complete
- Reports are complete
- Alerts are complete
- Saved Items are complete
- Google Apps Script scheduler is deployed

unless the codebase clearly shows that they are implemented.

## FINAL README

Make the README professional and hackathon-ready.

Preserve the existing content wherever it is still accurate.

Do not remove the Problem Statement or Solution sections.

Add:
- Features
- Architecture
- Current implementation status
- API/Data Sources
- Company Intelligence workflow
- News workflow
- Security
- Future improvements
- Hackathon MVP section

After updating README.md:

1. Check that the Markdown formatting is valid.
2. Check that no API keys/secrets appear anywhere.
3. Check that the README accurately reflects the current codebase.
4. Do not modify application code.
5. Only update README.md.
