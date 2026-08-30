"""Was der Dienst über sich selbst sagt — Gesundheit, Scheduler, Auskunft.

**Warum getrennt von `main.py`.** Diese Endpunkte beantworten Anfragen wie
jeder andere Router auch; dass sie in der Einstiegsdatei standen, war
Gewohnheit und nicht Zuständigkeit. Am 2026-08-30 herausgelöst (L-25) —
239 der damals 1.221 Zeilen von `main.py`.

**Der Startzustand wohnt hier, nicht dort.** `/health` ist sein einziger
Leser; `main.py` meldet ihn über `start_melden` und `startfehler_melden`.
Bis zum 30.08.2026 war es ein Wörterbuch im Modulkopf von `main.py`, in das
`lifespan` hineinschrieb — dieselbe Sache an zwei Stellen. Wer den Zustand
melden will, ruft jetzt eine Funktion mit Namen, statt einen Schlüssel zu
treffen; ein Tippfehler im Schlüssel wäre stumm geblieben.
"""
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from automations import get_scheduler, start_scheduler
from automations.scheduler import scheduler_ist_eingeschaltet
from routers.auth_router import require_innendienst

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Betriebszustand"])

# Was der Start geschafft hat. `/health` gibt es aus, damit ein unvollstaendiger
# Start von aussen sichtbar ist — produktiv fielen sieben von acht Phasen aus,
# und ohne Blick ins Log war das nirgends zu sehen.
_STARTZUSTAND = {"vollstaendig": None, "ausgefallen": [], "fehler": ""}


def start_melden(vollstaendig: bool, ausgefallen: list) -> None:
    """Ergebnis der Startphasen festhalten — aufgerufen aus `main.lifespan`."""
    _STARTZUSTAND["vollstaendig"] = vollstaendig
    _STARTZUSTAND["ausgefallen"] = list(ausgefallen)


def startfehler_melden(grund: str) -> None:
    """Der Start kam gar nicht erst bis zu den Phasen."""
    _STARTZUSTAND["fehler"] = grund


def startzustand() -> dict:
    """Nur zum Lesen — eine Kopie, damit niemand von aussen hineinschreibt."""
    return dict(_STARTZUSTAND)


# Health check endpoint
@router.get("/api/health")
async def api_health():
    """Lightweight keepalive — no DB call, responds instantly."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "service": "kompagnon-backend"}


@router.get("/api/ping")
async def api_ping():
    """Ultra-lightweight keepalive alias."""
    return "pong"


def _ablage_zustand() -> dict:
    """Zustand der Dateiablage fuer die Gesundheitspruefung."""
    try:
        from services.dateiablage import ablage_zustand
        return ablage_zustand()
    except Exception as fehler:
        return {"grund": f"{type(fehler).__name__}: {fehler}"}


def _browser_zustand() -> dict:
    """Zwei Fragen, nicht eine.

    „Nicht eingeschaltet" und „eingeschaltet, aber Playwright fehlt" sind
    verschiedene Zustaende, und der zweite ist ein Einrichtungsfehler, der
    auffallen soll. Ein einzelnes `browser: false` wuerde beide zu derselben
    Achselzucken-Antwort verschmelzen.
    """
    try:
        from services.seitenbrowser import browser_erwuenscht, browser_verfuegbar

        an = bool(browser_erwuenscht())
        da = bool(browser_verfuegbar())
    except Exception:                       # noqa: BLE001
        # `/health` selbst darf daran nicht scheitern — es ist die Auskunft,
        # die man liest, wenn sonst nichts mehr geht.
        return {"eingeschaltet": False, "verfuegbar": False, "bereit": False}
    return {"eingeschaltet": an, "verfuegbar": da, "bereit": an and da}


#: Die Umgebungswerte, ohne die kein Geld ankommt — und wozu jeder gehoert.
_ZAHLUNGSWERTE = {
    "STRIPE_SECRET_KEY": "Kasse eroeffnen",
    "STRIPE_WEBHOOK_SECRET": "/api/payments/webhook",
    "STRIPE_WEBHOOK_SECRET_BUCH": "/api/book/webhook",
    "STRIPE_WEBHOOK_SECRET_GEO": "/api/geo-payments/webhook",
}


def _zahlungszustand() -> dict:
    """Ob die Zahlungskette eingerichtet ist — von aussen abfragbar.

    **Der Anlass (27.08.2026).** Beim Einrichten der drei Stripe-Adressen ging
    eine Stunde damit verloren, herauszufinden, **ob** die Geheimnisse im
    laufenden Prozess ankommen. Das Render-Dashboard zeigt eine Zeile mit
    leerem Wert genauso an wie eine mit Inhalt — beide als Punkte. Die
    Protokolle sagten „nicht gesetzt", der Bildschirm sagte „steht da", und
    zwischen beiden gab es keine Instanz, die man haette fragen koennen.

    Dieselbe Fehlerfamilie wie die Uploads am 16.08. und der Browserlauf am
    27.08. (L-136): Ein Zustand, der **nicht im Quelltext** steht, sondern in
    der Umgebung, und den man deshalb im Dashboard „ablesen" muss statt am
    Gegenstand zu messen. Ein Dashboard zeigt die **Einstellung**. Hier steht,
    was der Prozess tatsaechlich hat.

    **Es wird die Laenge gemeldet, nicht der Wert** — und das ist die ganze
    Absicht: Sie unterscheidet „leer", „aus Versehen abgeschnitten" und
    „vollstaendig", ohne dass ein Geheimnis ueber eine offene Auskunft geht.
    Ein `whsec_` ist um die 38 Zeichen lang; steht dort 3, hat jemand beim
    Einfuegen etwas verloren.

    Gemeldet wird ausserdem der **Praefix**, aber nur, ob er stimmt: Wer den
    API-Schluessel und das Signaturgeheimnis vertauscht, sieht sonst zwei
    gesetzte Werte und einen Fehler ohne Ursache.
    """
    zustand = {}
    for name, wofuer in _ZAHLUNGSWERTE.items():
        wert = (os.getenv(name) or "").strip()
        eintrag = {"gesetzt": bool(wert), "laenge": len(wert), "wofuer": wofuer}
        if wert:
            erwartet = "whsec_" if "WEBHOOK" in name else ("sk_", "rk_")
            eintrag["praefix_stimmt"] = wert.startswith(erwartet)
        zustand[name] = eintrag
    zustand["bereit"] = all(e.get("gesetzt") and e.get("praefix_stimmt", True)
                            for k, e in zustand.items() if k in _ZAHLUNGSWERTE)
    return zustand


@router.get("/health")
def health_check():
    """Check if backend and database are running."""
    from database import SessionLocal
    db_status = "unknown"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)[:80]}"

    try:
        scheduler = get_scheduler()
        return {
            "status": "ok" if db_status == "connected" else "degraded",
            "service": "KOMPAGNON Backend",
            "database": db_status,
            "scheduler_running": scheduler.scheduler.running,
            # **Abgeschaltet ist nicht abgestuerzt.** Waehrend des Umzugs
            # (L-34) faehrt der Dienst ohne Verkehr `SCHEDULER_ENABLED=false`,
            # damit nicht zwei Scheduler auf derselben Jobtabelle arbeiten.
            # Ohne dieses Feld sieht das von aussen aus wie ein Ausfall — und
            # der naechste, der hinsieht, „repariert" einen gewollten Zustand.
            "scheduler_enabled": scheduler_ist_eingeschaltet(),
            # Ob der Start durchlief. Ohne diese Auskunft blieb produktiv
            # monatelang unbemerkt, dass sieben von acht Startphasen ausfielen.
            "startup_complete": _STARTZUSTAND["vollstaendig"],
            "startup_missing": _STARTZUSTAND["ausgefallen"],
            # Ob hochgeladene Dateien den naechsten Deploy ueberleben. Ohne
            # eingehaengten Datentraeger schreibt der Dienst munter weiter —
            # und beim Deploy ist alles weg (16.08.2026). Von aussen abfragbar,
            # damit man es nicht im Dashboard nachsehen muss.
            "uploads": _ablage_zustand(),
            # Ob der Browserlauf der Erhebung wirklich laufen kann. Er haengt
            # an zwei Dingen, die **nicht im Quelltext** stehen, sondern in
            # Render: dem Buildbefehl (`playwright install chromium`) und
            # `AUDIT_BROWSER=true`. Fehlt eines, misst die Erhebung eine
            # React-Seite als leer — und das steht dann als Befund im
            # Kundenbericht (L-107). Am Gegenstand fragen statt im Dashboard
            # ablesen, wie schon bei den Uploads.
            "browser": _browser_zustand(),
            # Ob Geld ankommen kann. Vier Werte, die nur in Render stehen —
            # und ein Dashboard zeigt die Einstellung, nicht den Zustand des
            # Prozesses. Gemeldet werden Laenge und Praefix, nie der Wert.
            "zahlungen": _zahlungszustand(),
            "timestamp": os.popen("date").read().strip(),
        }
    except Exception as e:
        return {"status": "degraded", "database": db_status, "detail": str(e)}


# Der Scheduler verrät die interne Jobliste und lässt sich neu starten.
# Beides stand bis zum 19.08.2026 ohne Anmeldung offen; der Neustart
# antwortete beim Nachmessen mit 200 und startete tatsächlich neu.
@router.get("/api/scheduler/status", dependencies=[Depends(require_innendienst)])
def scheduler_status():
    """Check if scheduler is running and list active jobs."""
    try:
        scheduler = get_scheduler()
        return {
            "running": scheduler.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                }
                for job in scheduler.scheduler.get_jobs()
            ],
        }
    except Exception as e:
        return {"running": False, "error": str(e)}


@router.post("/api/scheduler/restart", dependencies=[Depends(require_innendienst)])
def scheduler_restart():
    """Manually (re)start the scheduler — useful if background_init failed."""
    try:
        start_scheduler()
        scheduler = get_scheduler()
        return {
            "status": "ok",
            "running": scheduler.scheduler.running,
            "job_count": len(scheduler.scheduler.get_jobs()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scheduler-Neustart fehlgeschlagen: {e}")


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nAllow: /\n"


@router.get("/")
@router.head("/")
def root():
    """API root with documentation link."""
    return {
        "message": "🚀 KOMPAGNON Automation System",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "features": [
            "Lead Management Pipeline",
            "7-Phase Project Workflow",
            "KI-powered Content Generation",
            "Real-time Margin Tracking",
            "Automated Post-Launch Sequences",
            "Local SEO Schema Generation",
            "QA Automation & Testing",
            "Customer Relationship Management",
        ],
    }


# (Der zweite, gleichnamige Handler stand hier und ueberschrieb den oberen.
#  Entfernt am 18.08.2026 — siehe dort.)


# Info endpoint for deployment
@router.get("/info")
def get_info():
    """Auskunft darüber, was eingerichtet ist — nie darüber, womit.

    Bis 2026-08-15 gab dieser Endpunkt `DATABASE_URL` unverändert aus, also
    Benutzer, Passwort und Host der Postgres-Instanz, ohne Anmeldung, auf dem
    Produktivserver ebenso wie auf Staging. Alle übrigen Felder waren schon
    immer boolesch; die Datenbank war die Ausnahme.
    """
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "api_key_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "smtp_configured": bool(os.getenv("SMTP_HOST")),
        "debug": os.getenv("DEBUG", "false").lower() == "true",
    }
