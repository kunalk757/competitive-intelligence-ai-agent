from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.ai import router as ai_router
from app.api.routes.agent import router as agent_router
from app.api.routes.news import router as news_router
from app.api.routes.companies import router as companies_router
from app.api.routes.research_papers import router as research_papers_router
from app.api.routes.observability import router as observability_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(ai_router)
api_router.include_router(agent_router)
api_router.include_router(news_router)
api_router.include_router(companies_router)
api_router.include_router(research_papers_router)
api_router.include_router(observability_router)

