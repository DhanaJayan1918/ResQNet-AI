"""
ResQNet AI - API v1 Router
Aggregates all v1 endpoint routers.
"""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router

# Import additional routers as they are built in later phases
from app.api.v1.incidents import router as incidents_router
# from app.api.v1.resources import router as resources_router
# from app.api.v1.shelters import router as shelters_router
# from app.api.v1.hospitals import router as hospitals_router
# from app.api.v1.ai import router as ai_router
# from app.api.v1.analytics import router as analytics_router
# from app.api.v1.simulation import router as simulation_router

router = APIRouter(prefix="/api/v1")

# Register routers
router.include_router(auth_router)
router.include_router(incidents_router)
# router.include_router(resources_router)
# router.include_router(shelters_router)
# router.include_router(hospitals_router)
# router.include_router(ai_router)
# router.include_router(analytics_router)
# router.include_router(simulation_router)
