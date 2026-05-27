from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.companies.router import router as companies_router
from app.api.v1.users.router import router as users_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(users_router)
router.include_router(companies_router)
