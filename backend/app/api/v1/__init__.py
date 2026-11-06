from fastapi import APIRouter

from app.api.v1.profiles import router as profiles_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.evaluation import router as evaluation_router
from app.api.v1.saved import router as saved_router
from app.api.v1.skills import router as skills_router
from app.api.v1.auth import router as auth_router, users_router
from app.api.v1.events import router as events_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(profiles_router)
api_v1_router.include_router(opportunities_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(evaluation_router)
api_v1_router.include_router(saved_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(events_router)

__all__ = ["api_v1_router"]
