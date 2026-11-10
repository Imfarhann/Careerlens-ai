from fastapi import APIRouter

from app.api.routes import (
    analysis,
    auth,
    cv,
    dashboard,
    jobs,
    profile,
    skills,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(cv.router, prefix="/cv", tags=["cv"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(
    analysis.router, prefix="/analysis", tags=["analysis"]
)
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["dashboard"]
)
