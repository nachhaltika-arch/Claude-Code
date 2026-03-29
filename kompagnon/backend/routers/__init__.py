"""API routers for KOMPAGNON."""

from .leads import router as leads_router
from .projects import router as projects_router
from .agents import router as agents_router
from .customers import router as customers_router
from .automations import router as automations_router

__all__ = [
    "leads_router",
    "projects_router",
    "agents_router",
    "customers_router",
    "automations_router",
]
