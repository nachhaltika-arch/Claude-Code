"""
Betriebsdiagnose: welche Integrationen sind im laufenden Prozess konfiguriert?

Entstanden, weil sich nicht feststellen ließ, ob eine im Render-Dashboard
eingetragene Variable auch tatsächlich im Prozess ankommt. Ein leerer Wert
sieht im Dashboard aus wie „gesetzt", verhält sich im Code aber wie „fehlt".

Es werden ausschließlich Metadaten zurückgegeben — nie ein Wert. Die Länge
unterscheidet „nicht gesetzt" von „gesetzt, aber leer" und von „gesetzt, aber
offensichtlich zu kurz", ohne das Geheimnis preiszugeben.
"""
import os

from fastapi import APIRouter, Depends

from database import User
from routers.auth_router import require_admin

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

# (Anzeigename, Umgebungsvariable, wofür sie gebraucht wird)
WATCHED_SETTINGS = (
    ("PageSpeed Insights", "GOOGLE_PAGESPEED_API_KEY",
     "Performance und Barrierefreiheit im Website-Audit"),
    ("Anthropic", "ANTHROPIC_API_KEY",
     "KI-Bewertung von Design, Conversion und Textqualität"),
    ("Datenbank", "DATABASE_URL", "Persistenz"),
    ("Brevo", "BREVO_API_KEY", "E-Mail-Versand"),
    ("Stripe", "STRIPE_SECRET_KEY", "Zahlungen"),
    ("Netlify", "NETLIFY_API_TOKEN", "Kunden-Hosting"),
)


def _describe(env_var: str) -> dict:
    raw = os.getenv(env_var)
    if raw is None:
        return {"status": "fehlt", "configured": False, "length": 0}
    if not raw.strip():
        return {"status": "leer", "configured": False, "length": len(raw)}
    return {"status": "gesetzt", "configured": True, "length": len(raw.strip())}


@router.get("/config")
def config_status(_: User = Depends(require_admin)):
    """Zeigt je Integration, ob der laufende Prozess sie sieht — ohne Werte."""
    settings = [
        {"name": name, "env_var": env_var, "purpose": purpose, **_describe(env_var)}
        for name, env_var, purpose in WATCHED_SETTINGS
    ]
    return {
        "settings": settings,
        "missing": [s["env_var"] for s in settings if not s["configured"]],
    }
