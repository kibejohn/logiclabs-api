from fastapi import APIRouter
from .auth import router as auth_router
from .businesses import router as businesses_router
from .users import router as users_router
from .scorecards import router as scorecards_router
from .scoring import router as scoring_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(businesses_router)
api_router.include_router(users_router)
api_router.include_router(scorecards_router)
api_router.include_router(scoring_router)