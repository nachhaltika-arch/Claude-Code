"""API routers for KOMPAGNON."""

from .fehler import router as fehler_router
from .usercards import router as usercards_router
from .usercards import kunden_router as usercards_kunden_router
from .leads import router as leads_router
# **Vor `projects` — und das ist keine Kosmetik.** Aus `projects.py` ist am
# 23.08.2026 das Entfernen eines Projekts ausgezogen (L-25). Es traegt feste
# Pfade wie `/loeschvorschau`; `projects.py` traegt den Platzhalter
# `/{project_id}`. FastAPI nimmt die **zuerst registrierte** Route, also
# verdeckt der Platzhalter jede feste, die nach ihm kommt.
#
# Beim ersten Anlauf stand dieser Import unten bei den uebrigen, und
# `GET /api/projects/loeschvorschau` war nicht mehr erreichbar — gefunden von
# `test_keine_route_wird_von_einem_platzhalter_verdeckt`, nicht beim Lesen.
# Die Datenformate (`projects_modelle.py`) brauchen keinen Eintrag hier: Sie
# haengen an keinem Router, `projects.py` holt sie sich selbst.
from . import projects_loeschen  # noqa: F401
from .projects import router as projects_router
# Nur wegen der Nebenwirkung: Der Import haengt die Netlify-Routen an
# denselben Router. Ohne ihn waeren sie nicht registriert (L-25).
from . import projects_netlify  # noqa: F401
from . import projects_content  # noqa: F401
from . import projects_public  # noqa: F401
from . import projects_sichtbarkeit  # noqa: F401
# Die Content-Werkstatt, herausgeloest am 22.08.2026 (L-25): drei
# Funktionen mit zusammen 392 Zeilen. Sie haengt am selben Router — ohne
# diesen Import fehlten drei Routen, und die Endpunktzaehlung fiel von
# 391 auf 388. Genau dafuer wird nach jedem Schnitt gezaehlt.
from . import projects_werkstatt  # noqa: F401
# Weiter geteilt am 23.08.2026 (L-25), `projects_content.py` von 1.017 auf 456
# Zeilen: die drei KI-Entwuerfe (312 Zeilen, der teuerste Teil der Kette) und
# der QA-Scanner samt Checkliste. Beide haengen am selben Router — derselbe
# Grund wie oben, dieselbe Falle: ohne diesen Import fehlen sie lautlos.
# Zeiterfassung, Marge und Checkliste, herausgeloest am 30.08.2026 (L-25):
# `projects.py` war mit 887 Zeilen wieder ueber der Grenze. Auch diese haengen
# am selben Router — ohne den Import fehlten fuenf Routen lautlos.
from . import projects_fortschritt  # noqa: F401
from . import projects_versionen  # noqa: F401
from . import projects_qa  # noqa: F401
from .agents import router as agents_router
from .customers import router as customers_router
from .automations import router as automations_router
from .audit import router as audit_router
from .buch import router as buch_router
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
