"""
KOMPAGNON Automation System - FastAPI Entry Point
Runs the complete backend with scheduler, DB, and all routers.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import asyncio
import os
import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# Custom JSONResponse that does NOT escape Unicode (ä, ö, ü, ß, €)
class UnicodeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# Initialize database and seeders
from database import init_db, get_db
from seed_checklists import seed_checklists
# Die Migrationen, die beim Start laufen. Sie standen bis zum 22.08.2026
# hier in dieser Datei — 1.234 ihrer damals 2.209 Zeilen (L-25).
from migrations_runtime import run_migrations

# Import all routers
from routers import (
    fehler_router,
    usercards_router,
    usercards_kunden_router,
    leads_router,
    projects_router,
    agents_router,
    customers_router,
    automations_router,
    audit_router,
    buch_router,
    diagnostics_router,
    widget_router,
    acquisition_router,
    auth_router,
    admin_router,
    scraper_router,
    settings_router,
    payments_router,
    tickets_router,
    cms_connect_router,
    portal_router,
    newsletter_router,
    versand_router,
)

# Gesundheit, Scheduler-Steuerung und `/info` — eigener Router seit dem
# 30.08.2026 (L-25). `start_melden` traegt das Ergebnis der Startphasen dorthin,
# wo `/health` es ausgibt.
from routers.betriebszustand import (
    router as betriebszustand_router,
    start_melden,
    startfehler_melden,
)

# Import scheduler
from automations import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Geheimnisse aus dem Protokoll halten (L-98). `httpx` protokolliert jede
# Anfrage mit vollstaendiger URL — ein Schluessel als Abfrageparameter stand
# damit im Klartext im Render-Protokoll.
#
# Der Filter haengt an den **Handlern der Wurzel**, nicht am httpx-Logger:
# Eine Bibliothek, die morgen dazukommt, soll nicht erst wieder auffallen
# muessen. Wo der Schluessel gar nicht in die URL muss, steht der bessere
# Riegel eine Ebene tiefer (services.audit_pagespeed.auth_headers).
#
# **Und an `uvicorn.access` eigens — die Wurzel genuegt dort nicht.**
# Gefunden am 31.08.2026, indem der laufende Dienst gefragt wurde statt der
# Code gelesen: Ein Aufruf auf `/api/posteingang/brevo/pruefwert…` stand
# danach **unveraendert** im Staging-Protokoll. Uvicorn setzt fuer seine
# beiden Logger eigene Handler und `propagate = False`; ein Filter an der
# Wurzel sieht ihre Saetze nie. Ausgerechnet die Anfragezeile traegt aber den
# Pfad — und damit das Geheimnis der beiden Brevo-Webhooks.
#
# **Am Logger, nicht am Handler:** Uvicorn haengt seine Handler beim Start
# selbst ein, teils nach diesem Modul. Ein Filter am Logger gilt fuer alles,
# was dort durchgeht, unabhaengig davon, wann welcher Handler dazukommt.
from services.protokoll_schwaerzung import Schwaerzung  # noqa: E402

for _wurzel_handler in logging.getLogger().handlers:
    _wurzel_handler.addFilter(Schwaerzung())

for _name in ("uvicorn.access", "uvicorn.error", "uvicorn"):
    logging.getLogger(_name).addFilter(Schwaerzung())

# Die Startphasen, die einmal beim Hochfahren laufen. Sie standen bis zum
# 30.08.2026 hier in dieser Datei — 335 ihrer damals 1.221 Zeilen (L-25).
from startphase import (  # noqa: E402
    _create_default_admin,
    _disable_demo_accounts_in_production,
    _kurse_zusammenfuehren,
    _lebenszyklus_phasen_nachtragen,
    _zuweisungs_kennungen_nachziehen,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 KOMPAGNON Backend Starting...")

    # Uploads-Ordner — das einzige was synchron laufen muss
    try:
        os.makedirs("uploads", exist_ok=True)
    except Exception as e:
        logger.warning(f"⚠ uploads: {e}")

    # Port SOFORT öffnen — yield muss vor jeder DB-Operation kommen
    logger.info("✅ Port wird geöffnet...")

    async def _background_init():
        """Sequenzielle Initialisierung mit DB-Retry für Render Free Tier.

        PHASE 1: DB-Verbindung herstellen (3 Versuche à 45s)
        PHASE 2: Migrations (60s)
        PHASE 3: DB init (30s)
        PHASE 4: Default admin + Academy seed (10s je)
        PHASE 5: Scheduler ZULETZT (nach DB ready)
        """
        import time
        start = time.time()
        await asyncio.sleep(3)  # 3s warten bis Server stabil ist
        logger.info("🔄 Hintergrund-Init gestartet...")

        def _wiederherstellbarkeit_melden():
            from services.wiederherstellbarkeit import beim_start_melden
            beim_start_melden()

        def _betriebsschalter_melden():
            """Was dieser Dienst tut, sobald der Scheduler laeuft (L-104).

            **Nach dem Scheduler, nicht davor** — und das ist der ganze
            Punkt: `CompagnonScheduler.__init__` legt den Probemodus fest.
            Wer vorher meldet, meldet den Wert aus der Umgebung und nicht
            den, der gilt. Genau diese Verwechslung war L-104.
            """
            from automations.scheduler import scheduler_ist_eingeschaltet
            from automations.versandmodus import probemodus

            if probemodus():
                logger.info("✉ Probemodus: Mails werden protokolliert, "
                            "nicht zugestellt")
            else:
                logger.warning("✉ Echter Mailversand: Mails gehen an die "
                               "hinterlegten Adressen")
            if not scheduler_ist_eingeschaltet():
                logger.info("⏸ Zeitauftraege abgeschaltet (SCHEDULER_ENABLED)")

        def _academy_seed():
            from routers.academy_zuweisung import seed_academy_courses
            from database import SessionLocal
            _db = SessionLocal()
            try:
                seed_academy_courses(_db)
            finally:
                _db.close()

        def _deals_migration():
            from routers.deals import migrate_leads_to_deals
            from database import SessionLocal
            _db = SessionLocal()
            try:
                migrate_leads_to_deals(_db)
            finally:
                _db.close()

        def _component_library_seed():
            """Step C: HTML-Block-Templates aus Frontend-Repo in DB syncen."""
            from seeds.seed_component_library import seed_component_library
            from database import SessionLocal
            _db = SessionLocal()
            try:
                seed_component_library(_db)
            finally:
                _db.close()

        def _ping_db():
            """Simple DB ping to ensure connection is ready."""
            from sqlalchemy import text
            from database import SessionLocal
            _db = SessionLocal()
            try:
                _db.execute(text("SELECT 1"))
                _db.commit()
            finally:
                _db.close()

        async def _warte_auf_db() -> bool:
            """Bis zu drei Versuche, die Datenbank zu erreichen."""
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as ping_pool:
                for versuch in range(1, 4):
                    schritt = time.time()
                    logger.info(f"  DB-Verbindung Versuch {versuch}/3...")
                    try:
                        await asyncio.wait_for(
                            loop.run_in_executor(ping_pool, _ping_db), timeout=45.0)
                        logger.info(f"  \u2713 DB verbunden ({time.time() - schritt:.1f}s)")
                        return True
                    except asyncio.TimeoutError:
                        logger.warning(f"  \u26a0 DB-Versuch {versuch} Timeout nach 45s")
                    except Exception as e:  # noqa: BLE001
                        logger.warning(f"  \u26a0 DB-Versuch {versuch}: {e}")
                    if versuch < 3:
                        await asyncio.sleep(2)
            return False

        # Die Phasen laufen nacheinander mit einem gemeinsamen Zeitbudget.
        # Vorher hatte jede ihr eigenes Timeout bei nur einem Worker im Pool —
        # die lange Migration hielt ihn, und die folgenden sieben Phasen liefen
        # in ihre Timeouts, ohne je gestartet worden zu sein. Produktiv fehlten
        # dadurch Scheduler und Demokonten-Abschaltung, und im Log stand nur
        # „übersprungen". Siehe services/startphasen.py.
        from services.startphasen import Phase, fuehre_phasen_aus

        db_bereit = await _warte_auf_db()
        if not db_bereit:
            logger.error("❌ DB-Verbindung fehlgeschlagen — Server läuft ohne DB")
            startfehler_melden("Keine Datenbankverbindung")
            return

        phasen = [
            Phase("Migrations", run_migrations),
            Phase("DB init", init_db),
            Phase("Default admin", _create_default_admin),
            Phase("Disable demo accounts", _disable_demo_accounts_in_production),
            Phase("Academy seed", _academy_seed),
            # Muss nach "DB init" laufen: Sie schreibt in
            # `academy_courses`, und die legt erst `create_all` an.
            Phase("Kurse zusammenführen", _kurse_zusammenfuehren),
            # Muss nach "Kurse zusammenführen" laufen: Beide schreiben in
            # die Akademie, und der Nachtrag will alle Zeilen sehen.
            Phase("Zuweisungs-Kennungen", _zuweisungs_kennungen_nachziehen),
            Phase("Lebenszyklus-Phasen", _lebenszyklus_phasen_nachtragen),
            Phase("Deals migration", _deals_migration),
            Phase("Component library seed", _component_library_seed),
            Phase("Scheduler", start_scheduler),
            # **Keine Startphase im eigentlichen Sinn, aber der Ort, an dem
            # es jemand sieht (L-11).** Fehlt ein Wiederherstellungs-
            # Schluessel, laeuft der Dienst trotzdem — nur waere eine
            # Wiederherstellung unvollstaendig, und das faellt sonst erst
            # auf, wenn man sie braucht.
            Phase("Wiederherstellbarkeit", _wiederherstellbarkeit_melden),
            # Ebenfalls keine Startphase, sondern die Stelle, an der sichtbar
            # wird, **was dieser Dienst tut** (L-104). Muss nach "Scheduler"
            # stehen: Der legt den Probemodus fest.
            Phase("Betriebsschalter", _betriebsschalter_melden),
        ]
        ergebnis = await fuehre_phasen_aus(phasen)

        start_melden(ergebnis.vollstaendig,
                     ergebnis.ausgefallen + ergebnis.gescheitert)

        if ergebnis.vollstaendig:
            logger.info(f"✅ {ergebnis.bericht()}")
        else:
            # Fehler, nicht Warnung: Ein unvollständiger Start ist genau das,
            # was hier monatelang unbemerkt blieb.
            logger.error(f"❌ {ergebnis.bericht()}")

    try:
        task = asyncio.create_task(_background_init())
    except Exception as e:
        logger.warning(f"⚠ Background-Task konnte nicht gestartet werden: {e}")
        task = None

    yield  # ← Port öffnet HIER — immer, unabhängig von DB-Init

    # Shutdown
    if task is not None:
        task.cancel()
    try:
        stop_scheduler()
    except Exception:
        pass
    logger.info("🛑 Shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="KOMPAGNON Automation System",
    description="Complete WordPress website automation for German handcraft businesses",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UnicodeJSONResponse,
)

# CORS Middleware — must be before all routers
#
# **Die Liste steht in `cors_herkuenfte.py`, nicht hier** (BUCH-09,
# 01.09.2026). Sie hat einen zweiten Leser bekommen — `GET /api/health/cors` —
# und zwei Stellen, die dieselbe Liste je eigen zusammenbauen, sind zwei
# Wahrheiten. Ausgerechnet die Diagnose waere dann falsch, wenn man sie
# braucht.
#
# `allow_credentials=True` verlangt ausdrueckliche Herkuenfte, nie "*".
import cors_herkuenfte

_cors_origins = cors_herkuenfte.herkuenfte()

# **Beim Start ins Protokoll, und zwar in einer Zeile.** CORS ist der einzige
# Fehler hier, der nirgends ein Protokoll erzeugt: Der Browser haelt die
# Anfrage an, bevor sie ankommt. Wer nach einem Deploy wissen will, ob die neue
# Adresse angekommen ist, liest diese Zeile — statt einen Testkauf auszuloesen
# und im Nichts zu suchen.
logger.info("CORS erlaubte Origins: %s", _cors_origins)
for _mangel in cors_herkuenfte.beanstandungen(_cors_origins):
    # Kein Abbruch: Der Eintrag bleibt in der Liste, damit ihn derjenige
    # wiederfindet, der ihn gesetzt hat. Gemeldet wird er trotzdem — still
    # wirkungslos ist genau der Zustand, den BUCH-09 verhindern soll.
    logger.warning("CORS: %s", _mangel)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=cors_herkuenfte.NETLIFY_MUSTER,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include all routers — specific routers BEFORE alias/fallback routers
# Zuerst der Kundenweg: Die Profilroute liegt dort und prueft je Zeile.
# Danach der geschlossene Hauptrouter.
app.include_router(fehler_router)
app.include_router(usercards_kunden_router)
app.include_router(usercards_router)
app.include_router(leads_router)                      # real leads router first
# Die ausdrücklich öffentlichen Lead-Routen: Formular der Landingpage und der
# Kundenzugang über Einmal-Token. Alles andere hängt am `leads_router` und
# verlangt eine Anmeldung.
# Die Wege ohne Innendienst-Anmeldung liegen seit dem 22.08.2026 in
# `routers/leads_portal.py` (L-25) — Formular der Landingpage und
# Kundenportal ueber Einmal-Token.
from routers.leads_portal import public_router as leads_public_router
app.include_router(leads_public_router)

# Der Import von Betrieben liegt seit dem 22.08.2026 in einer eigenen Datei
# (L-25): neun Routen, die Daten von aussen entgegennehmen — CSV,
# Domainlisten, Einzelanlage, Ausfuhr. Mit dem Rest von `leads.py` teilten
# sie nichts ausser dem Router und dem Auftragszustand.
from routers import leads_import
app.include_router(leads_import.router)

# Ebenso getrennt (L-25): die Kaltakquise (eine Route, 257 Zeilen) und das
# Nachtragen fehlender Felder an vorhandenen Betrieben.
from routers import leads_anreicherung, leads_kaltakquise
app.include_router(leads_kaltakquise.router)
app.include_router(leads_anreicherung.router)

# Weiter geteilt am 23.08.2026 (L-25), `leads.py` von 1.186 auf 790 Zeilen:
# das Blatt eines Betriebs (Profil mit 139 Zeilen, Auditverlauf, QR-Code) und
# was nach dem Erstkontakt kommt (Mailstrecke, Leistungsbericht). Beide tragen
# dieselbe Innendienst-Sperre am Router.
from routers import leads_nachfassen, leads_profil
app.include_router(leads_profil.router)
# Die Briefing-Bruecke, herausgeloest am 30.08.2026 (L-25). Eigener Router mit
# demselben Praefix — ohne diese Zeile fehlt die Route lautlos.
from routers import leads_briefing
app.include_router(leads_briefing.router)
# Die Abo-Achse der Zeiterfassung (L-101, 31.08.2026) — Pflegestunden je Monat
# und Betrieb. Wieder eigener Router mit demselben Praefix, und wieder gilt:
# ohne diese Zeile fehlen die zwei Routen lautlos.
from routers import leads_abo
app.include_router(leads_abo.router)
app.include_router(leads_nachfassen.router)
# Der eigene Betrieb im Kundenportal. Der Bestand bleibt Innendienst.
from routers.leads_portal import kunden_router as leads_kunden_router
app.include_router(leads_kunden_router)
# Mehrere Menschen an einem Betrieb (25.08.2026). Der Innendienst laedt ein;
# `manage_users` sperrt die drei Routen. Steht **nach** `leads_router`, weil
# der dort registrierte `DELETE /{lead_id}` sonst `/{lead_id}/zugaenge/{id}`
# nicht ueberdeckt — die Pfade sind verschieden lang, FastAPI trennt sie
# sauber; die Reihenfolge ist hier nur der Lesbarkeit wegen.
from routers import betriebszugaenge
app.include_router(betriebszugaenge.router)
# Die drei Alias-Router sind am 21.08.2026 entfernt (Modulkarte, Nahtstelle
# `/api/customers`). Der Kommentar hier sagte „real customers router first" —
# er war es nicht: `usercards_customers_alias_router` stand eine Zeile davor
# und ueberdeckte ihn samt seiner Antwortform.
app.include_router(customers_router)
app.include_router(projects_router)

# **Ausdruecklich einbinden, nicht dem Zufall ueberlassen (L-25, 22.08.2026).**
# `projects_erhebung` und `projects_anlegen` haengen am selben Router aus
# `projects_router.py`; ihre Routen registrieren sich beim **Import** des
# Moduls. Ohne diese Zeilen waeren sie trotzdem da — weil `projects.py` die
# Go-live-Kette holt und damit die Kette anstoesst. Genau das ist die stille
# Kopplung, die man nicht will: Naehme jemand diesen einen Import weg,
# verschwaenden elf Routen, und keine Meldung sagte es.
from routers import projects_anlegen, projects_erhebung  # noqa: F401
# Freigabe des Kunden über den Link aus der E-Mail. Alles andere hängt am
# `projects_router` und verlangt eine Anmeldung.
from routers.projects import public_router as projects_public_router
app.include_router(projects_public_router)
# Das eigene Projekt im Kundenportal. Alles Übrige bleibt Innendienst.
from routers.projects import kunden_router as projects_kunden_router
app.include_router(projects_kunden_router)
app.include_router(agents_router)
app.include_router(automations_router)
app.include_router(cms_connect_router)
app.include_router(portal_router)
app.include_router(audit_router)
app.include_router(buch_router)
# Die Warteschlange der Druckbestellungen (BUCH-07). Eigenes Modul, weil
# `routers/buch.py` die Kasse traegt und beides zusammen die Datei ueber
# die Groessengrenze aus L-25 gehoben haette.
from routers.buch_versand import router as buch_versand_router
app.include_router(buch_versand_router)
app.include_router(diagnostics_router)
app.include_router(widget_router)
app.include_router(acquisition_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(scraper_router)
app.include_router(settings_router)
app.include_router(payments_router)
app.include_router(tickets_router)
app.include_router(newsletter_router)
app.include_router(versand_router)

# Der Posteingang des Innendienstes: was vom Kunden hereinkommt (L-18,
# 26.08.2026). Ticket, Chat — und E-Mail, sobald es einen Posteingang gibt.
from routers import benachrichtigungen
app.include_router(benachrichtigungen.router)

from routers import briefings
app.include_router(briefings.router)      # Innendienst
# Kunde: Freigabe (L-27) und seit dem 26.08.2026 das eigene Briefing unter
# `/mein/…`. **Eigene Adressen, keine Ueberdeckung** — der erste Entwurf
# stuetzte sich auf die Reihenfolge der Registrierung, und genau das
# verbietet `test_briefing_zusammengelegt.py` aus gutem Grund.
app.include_router(briefings.kunden_router)

# Die KI-Vorbefuellung liegt seit dem 22.08.2026 in einer eigenen Datei
# (L-25): sechs Routen, die alle ein Modell fragen und die Antwort in ein
# Briefing-Feld schreiben — mit den Stammdaten haben sie nur den Gegenstand
# gemeinsam. Geschnitten nach Zustaendigkeit, nicht nach Groesse.
from routers import briefings_ki
app.include_router(briefings_ki.router)

# `routers/briefing.py` ist am 22.08.2026 in `briefings.py` aufgegangen
# (L-27) — zwei Router auf demselben Praefix, getrennt nach HTTP-Verb.

from routers.kampagne import router as kampagne_router
app.include_router(kampagne_router)

# `routers/courses.py` ist am 19.08.2026 entfallen. Es bediente eine
# strukturlose Tabelle neben der Akademie — siehe
# services/kurse_zusammenfuehren.py.

# **Vier Router statt einem, seit dem 23.08.2026 (L-25).** `academy.py` hatte
# 1.109 Zeilen; die Abschnitte sind nach Zustaendigkeit ausgezogen. Alle
# tragen dasselbe Praefix `/api/academy` — fuer die Oberflaeche aendert sich
# nichts, kein Pfad hat sich verschoben.
#
# **Einzeln geladen, mit einzelner Meldung.** Faellt einer aus, sagt das
# Protokoll welcher; eine Sammelmeldung „Academy Router nicht geladen" haette
# vier Moeglichkeiten offengelassen.
for _name in ('academy', 'academy_fortschritt', 'academy_zertifikate',
              'academy_zuweisung'):
    try:
        _modul = __import__(f'routers.{_name}', fromlist=['router'])
        app.include_router(_modul.router)
        logger.info(f"✓ Academy Router geladen: {_name}")
    except Exception as e:
        logger.warning(f"⚠ Academy Router nicht geladen ({_name}): {e}")

try:
    from routers.crawler import router as _crawler_router
    app.include_router(_crawler_router)
    logger.info("✓ Crawler Router geladen")
except Exception as e:
    logger.warning(f"⚠ Crawler Router nicht geladen: {e}")

try:
    from routers.files import kunden_router as _files_kunden_router
    from routers.files import router as _files_router
    app.include_router(_files_router)
    # Der angemeldete Kunde: eigene Dateien, eigene Eigentumspruefung
    # (26.08.2026). Eigenes Praefix `/api/files/mein`, deshalb keine
    # Ueberdeckung — anders als beim Briefing, wo die Reihenfolge zaehlt.
    app.include_router(_files_kunden_router)
    logger.info("✓ Files Router geladen (Innendienst + Kunde)")
except Exception as e:
    logger.warning(f"⚠ Files Router nicht geladen: {e}")

try:
    from routers import website_mockup
    app.include_router(website_mockup.router, prefix="/api")
    logger.info("✓ Website-Mockup Router geladen")
except Exception as e:
    logger.warning(f"⚠ Website-Mockup Router nicht geladen: {e}")

from routers import sitemap
app.include_router(sitemap.router)
# Die Seitenbearbeitung (Editor, Qualitaetspruefung) liegt seit dem
# 22.08.2026 in `routers/sitemap_seiten.py` (L-25): Sie handelt vom Inhalt
# einer einzelnen Seite, nicht von der Struktur der Website.
from routers import sitemap_seiten
app.include_router(sitemap_seiten.pages_router)

# Erzeugen und Austausch liegen seit dem 22.08.2026 in eigenen Dateien
# (L-25): sieben Routen, die ein Modell fragen, und der Weg hinein und
# hinaus. Beide holen die geteilten Helfer aus `sitemap.py`.
from routers import sitemap_austausch, sitemap_erzeugen
app.include_router(sitemap_erzeugen.router)
app.include_router(sitemap_austausch.router)

from routers import content
app.include_router(content.router)

from routers import designs
app.include_router(designs.router)

# Der Canvas liest dieselben Zeilen wie die vier KAS-Ansichten und schreibt
# ueber `mockup_versions` zurueck — deshalb steht er direkt hinter `designs`.
from routers import design_canvas
app.include_router(design_canvas.router)

# **Entfernt am 26.08.2026 (Entscheidung David: „der crawler ist der
# richtige, den anderen weg").** `content_scraper_router` fuehrte fuenf
# Routen, die keine Oberflaeche rief, und startete beim Anlegen eines
# Projekts einen Hintergrundlauf. Was er ablegte (`projects.scrape_full_data`)
# las **nur sein eigenes Modul**. Der Weg, den die Oberflaeche geht, ist
# `/api/crawler/…`.

from routers.branddesign import router as branddesign_router
app.include_router(branddesign_router)

# Erhebung und Leitfaden liegen seit dem 22.08.2026 in eigenen Dateien
# (L-25): zwei Bloecke mit je ueber 200 Zeilen. Beide haengen am selben
# Router — ausdruecklich einbinden, damit ihre Routen nicht von einer
# zufaelligen Importkette abhaengen.
from routers import branddesign_erhebung, branddesign_leitfaden  # noqa: F401

from routers import templates as templates_router
app.include_router(templates_router.router)

# `website_templates` ist am 21.08.2026 in `templates` aufgegangen (L-28):
# derselbe Tabellenzugriff unter zwei Praefixen, und das zweite rief
# nachweislich nichts auf. Die Tabelle heisst weiterhin so.

from routers import messages as messages_router
app.include_router(messages_router.router)

from routers import webhooks
app.include_router(webhooks.router)

from routers import retainer
app.include_router(retainer.router)

# Bausteinbibliothek und Wireframe-Generator (Step D des Online-Fertig-
# Redesigns). Die beiden Router lagen bis zum 22.08.2026 in **einer** Datei
# mit 2.143 Zeilen; der Wireframe-Teil hat seither seine eigene (L-25) — mit
# eigenen Modellen, drei Job-Speichern und sechs Helfern, die sonst niemand
# braucht.
from routers.component_library import component_router as component_library_router
from routers.component_library_wireframe import wireframe_router

# **Ausdruecklich einbinden (L-25).** `component_library_ki` haengt am selben
# `component_router`; seine Routen registrieren sich beim Import. Ohne diese
# Zeile waeren sie nur da, solange irgendeine Importkette sie zufaellig
# anstoesst — genau die stille Kopplung, die bei `projects` heute schon der
# Befund war.
from routers import component_library_ki  # noqa: F401

app.include_router(component_library_router)
app.include_router(wireframe_router)


from routers.products import router as products_router
app.include_router(products_router)

from routers.deals import router as deals_router
app.include_router(deals_router)

from routers.campaigns import router as campaigns_router
app.include_router(campaigns_router)

from routers import webhooks_trackdesk as trackdesk_router
app.include_router(trackdesk_router.router)

from routers import assets as assets_router
app.include_router(assets_router.router)

from routers import pages as public_pages_router
app.include_router(public_pages_router.router)

from routers.export import router as export_router
app.include_router(export_router)

from routers.kas_router import router as kas_router
app.include_router(kas_router)

from routers.geo import router as geo_router
app.include_router(geo_router)
# Der Kunde sieht seinen GEO-Wert — verkuerzt, mit Eigentumspruefung
# (26.08.2026, L-95). Eigenes Praefix `/api/geo/mein`, keine Ueberdeckung.
from routers.geo import kunden_router as geo_kunden_router
app.include_router(geo_kunden_router)

from routers.geo_payments import router as geo_payments_router
app.include_router(geo_payments_router)

# Projekt-Assistent (Ausbau 1: Begleitung durch das Briefing)
from routers.assistant import router as assistant_router
app.include_router(assistant_router)

# Zustellungsstörungen von Brevo — ohne sie meldet der Versand Erfolg und
# niemand erfährt, dass die Mail beim Empfänger abgewiesen wurde.
from routers.mail_events import router as mail_events_router
app.include_router(mail_events_router)

# Eingehende Kundenmails (Brevo Inbound Parsing) — L-18.
from routers.posteingang import router as posteingang_router
app.include_router(posteingang_router)

# Der Bezahlvorgang fuer digitale Produkte (L-100, ORDERS_03). Oeffentlich:
# Wer kaufen will, hat noch kein Konto.
from routers.shop import router as shop_router
app.include_router(shop_router)

# Gesundheit, Scheduler und Auskunft. Sie standen bis zum 30.08.2026 als
# `@app.get` unten in dieser Datei — 239 ihrer damals 1.221 Zeilen (L-25).
app.include_router(betriebszustand_router)


# Was der Server nicht verarbeiten konnte — ins Log **und** in die Tabelle.
#
# Bis zum 18.08.2026 stand hier nur `logger.error`. Ins Serverlog sieht
# niemand taeglich, und so blieb der 500er beim Anlegen einer Lektion
# monatelang unbemerkt (L-10). Seitdem landet dasselbe zusaetzlich in
# `fehlerprotokoll` und ist unter `/api/fehler/` abrufbar.
#
# Es gab hier **zwei** gleichnamige Handler; der zweite ueberschrieb den
# ersten stillschweigend. Jetzt einer.
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    spur = traceback.format_exc()
    logger.error(f'Unbehandelter Fehler: {type(exc).__name__}: {exc}\n{spur}')

    try:
        from services.fehlerprotokoll import merke_fehler
        benutzer = getattr(getattr(request, "state", None), "user_id", None)
        merke_fehler(
            pfad=str(getattr(request, "url", "")).split("?")[0][:500],
            methode=getattr(request, "method", ""),
            art=type(exc).__name__,
            meldung=str(exc),
            spur=spur,
            benutzer_id=benutzer,
        )
    except Exception:      # pragma: no cover — das Protokoll reisst nichts mit
        pass

    return JSONResponse(
        status_code=500,
        content={'detail': 'Interner Serverfehler', 'type': type(exc).__name__},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
