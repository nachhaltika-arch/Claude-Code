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

# (Anzeigename, Umgebungsvariable, Zweck, alternative Schreibweisen)
WATCHED_SETTINGS = (
    ("PageSpeed Insights", "GOOGLE_PAGESPEED_API_KEY",
     "Performance und Barrierefreiheit im Website-Audit", ("PAGESPEED_API_KEY",)),
    ("Anthropic", "ANTHROPIC_API_KEY",
     "KI-Bewertung von Design, Conversion und Textqualität", ()),
    ("Datenbank", "DATABASE_URL", "Persistenz", ()),
    ("Brevo", "BREVO_API_KEY", "E-Mail-Versand", ()),
    ("Stripe", "STRIPE_SECRET_KEY", "Zahlungen", ()),
    ("Netlify", "NETLIFY_API_TOKEN", "Kunden-Hosting", ()),
)


def _describe(env_var: str, aliases: tuple = ()) -> dict:
    raw = os.getenv(env_var)
    if raw is None or not raw.strip():
        for alias in aliases:
            alt = os.getenv(alias)
            if alt and alt.strip():
                return {"status": "gesetzt (als " + alias + ")", "configured": True,
                        "length": len(alt.strip())}
    if raw is None:
        return {"status": "fehlt", "configured": False, "length": 0}
    if not raw.strip():
        return {"status": "leer", "configured": False, "length": len(raw)}
    return {"status": "gesetzt", "configured": True, "length": len(raw.strip())}


def _betriebsschalter() -> list:
    """Der **wirksame** Zustand der Schalter, die das Verhalten bestimmen.

    **Warum das nicht dieselbe Frage ist wie oben (L-104, 24.08.2026).**
    `_describe` meldet „gesetzt" oder „fehlt". Für einen Schalter ist das die
    falsche Auskunft: ``USE_MOCK_EMAIL=false`` ist **gesetzt** und bedeutet
    „versendet echt an Kunden".

    **Und genau darin lag der Fehler:** Die Umgebung sagte ``true``, der
    Scheduler setzte den Schalter beim Start auf ``False`` zurück. Wer nur die
    Umgebungsvariable liest, sieht das nie. Gelesen wird deshalb über
    ``probemodus()`` und ``scheduler_ist_eingeschaltet()`` — die Funktionen,
    an denen das Verhalten wirklich hängt.
    """
    from automations.scheduler import scheduler_ist_eingeschaltet
    from automations.versandmodus import probemodus

    probe = probemodus()
    zeit = scheduler_ist_eingeschaltet()
    return [
        {
            "name": "Mailversand",
            "env_var": "USE_MOCK_EMAIL",
            "wirksam": "Probemodus" if probe else "versendet echt",
            "bedeutung": (
                "Mails werden nur protokolliert, nicht zugestellt."
                if probe else
                "Mails gehen tatsaechlich an die hinterlegten Adressen."
            ),
        },
        {
            "name": "Zeitauftraege",
            "env_var": "SCHEDULER_ENABLED",
            "wirksam": "laeuft" if zeit else "abgeschaltet",
            "bedeutung": (
                "Der Scheduler fuehrt seine Jobs aus, darunter versendende."
                if zeit else
                "Dieser Dienst faehrt keine Hintergrundjobs."
            ),
        },
    ]


@router.get("/config")
def config_status(_: User = Depends(require_admin)):
    """Zeigt je Integration, ob der laufende Prozess sie sieht — ohne Werte."""
    settings = [
        {"name": name, "env_var": env_var, "purpose": purpose,
         **_describe(env_var, aliases)}
        for name, env_var, purpose, aliases in WATCHED_SETTINGS
    ]
    return {
        "settings": settings,
        "missing": [s["env_var"] for s in settings if not s["configured"]],
        "schalter": _betriebsschalter(),
    }


@router.get("/wiederherstellbarkeit")
def wiederherstellbarkeit(_: User = Depends(require_admin)):
    """Waere eine Wiederherstellung vollstaendig? (L-11)

    **Eine andere Frage als `/config`.** Dort geht es darum, ob eine
    Integration heute arbeitet. Hier darum, ob der Betrieb nach einem
    Datenverlust **zurueckzuholen** waere — und das haengt an Schluesseln, die
    im laufenden Betrieb monatelang niemand vermisst.

    Ohne `CREDENTIALS_KEY` bekommt man nach einer vollstaendigen
    Wiederherstellung einen laufenden Dienst mit unlesbaren Kundenzugaengen:
    kein Fehler, keine Meldung, nur leere Felder.

    Gibt **keine** Schluesselwerte zurueck, auch nicht gekuerzt.
    """
    from services.wiederherstellbarkeit import schluessel_bericht

    return schluessel_bericht()
