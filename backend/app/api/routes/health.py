from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "competitive-intelligence-agent-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
    }
