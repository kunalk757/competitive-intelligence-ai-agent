# Competitive Intelligence Agent - Backend

FastAPI backend server for the Competitive Intelligence AI Agent.

## Setup & Running

### 1. Create and activate a virtual environment (recommended)
```bash
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```

### 4. Run the server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Health check: `http://localhost:8000/health`
- Swagger UI docs: `http://localhost:8000/docs`
