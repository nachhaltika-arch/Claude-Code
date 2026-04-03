"""API routers for KOMPAGNON."""

from .usercards import router as usercards_router
from .usercards import leads_alias_router, customers_alias_router as usercards_customers_alias_router
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
from .cms_connect import router as cms_connect_router
from .portal import router as portal_router

__all__ = [
    "cms_connect_router",
    "portal_router",
    "usercards_router",
    "leads_alias_router",
    "usercards_customers_alias_router",
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
