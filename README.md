# Competitive Intelligence AI Agent

An autonomous AI-powered Competitive Intelligence Agent that collects relevant information across web, industry news, academic research, and patent databases, reasons via a ReAct loop, and delivers structured, decision-grade intelligence reports.

## Project Structure

```
competitive-intelligence-agent/
├── frontend/          # Next.js (React + TypeScript) user dashboard
└── backend/           # FastAPI (Python 3.11+) backend service
```

---

## Getting Started

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Health Check: `http://localhost:8000/health`
- Interactive API Docs: `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Run Next.js development server
npm run dev
```
- Web Application: `http://localhost:3000`

---

## Initial MVP Verification

1. Start the backend (`http://localhost:8000`).
2. Start the frontend (`http://localhost:3000`).
3. Open `http://localhost:3000` in your browser.
4. Verify the **Backend: Online** status badge and response payload.

