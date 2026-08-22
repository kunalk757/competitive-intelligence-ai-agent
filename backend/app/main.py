import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.api.routes import api_router
from app.services.scheduler import start_scheduler, stop_scheduler

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background news scheduler
    start_scheduler()
    yield
    # Shutdown: Stop the scheduler
    stop_scheduler()


app = FastAPI(
    title="Competitive Intelligence AI Agent Backend",
    description="Backend API supporting agentic research and competitive intelligence collection.",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins_raw = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes under root and under /api
app.include_router(api_router)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Competitive Intelligence AI Agent API is running.",
        "docs_url": "/docs",
        "health_check": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
