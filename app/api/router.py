from fastapi import APIRouter

from app.api.v1.router import api_v1_router
from app.config.settings import get_settings

# from app.api.v1.agents import router as agents_router
# from app.api.v1.research import router as research_router

settings = get_settings()
main_api_router = APIRouter()

# Include the v1 router at the API_V1_STR prefix (default: /api/v1)
main_api_router.include_router(api_v1_router, prefix=settings.API_V1_STR)
