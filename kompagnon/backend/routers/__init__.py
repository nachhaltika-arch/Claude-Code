"""API routers for KOMPAGNON."""

from .fehler import router as fehler_router
from .usercards import router as usercards_router
from .usercards import kunden_router as usercards_kunden_router
from .leads import router as leads_router
from .projects import router as projects_router
from .agents import router as agents_router
from .customers import router as customers_router
from .automations import router as automations_router
from .audit import router as audit_router
from .diagnostics import router as diagnostics_router
from .widget import router as widget_router
from .acquisition import router as acquisition_router
from .auth_router import router as auth_router
from .auth_router import admin_router
from .admin_settings import router as settings_router
from .payments import router as payments_router
from .tickets import router as tickets_router
from .scraper import router as scraper_router
from .cms_connect import router as cms_connect_router
from .portal import router as portal_router
from .newsletter import router as newsletter_router
from .versand import router as versand_router

__all__ = [
    "cms_connect_router",
    "portal_router",
    "newsletter_router",
    "versand_router",
    "fehler_router",
    "usercards_router",
    "usercards_kunden_router",
    "leads_router",
    "projects_router",
    "agents_router",
    "customers_router",
    "automations_router",
    "audit_router",
    "diagnostics_router",
    "widget_router",
    "acquisition_router",
    "auth_router",
    "admin_router",
    "scraper_router",
    "settings_router",
    "payments_router",
    "tickets_router",
]
