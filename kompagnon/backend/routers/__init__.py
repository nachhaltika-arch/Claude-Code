"""API routers for KOMPAGNON."""

from .leads import router as leads_router
from .leads import customers_alias_router
from .projects import router as projects_router
from .agents import router as agents_router
from .customers import router as customers_router
from .automations import router as automations_router
from .audit import router as audit_router
from .auth_router import router as auth_router
from .auth_router import admin_router
from .admin_settings import router as settings_router
from .payments import router as payments_router
from .tickets import router as tickets_router
from .scraper import router as scraper_router

__all__ = [
    "leads_router",
    "customers_alias_router",
    "projects_router",
    "agents_router",
    "customers_router",
    "automations_router",
    "audit_router",
    "auth_router",
    "admin_router",
    "scraper_router",
    "settings_router",
    "payments_router",
    "tickets_router",
]
