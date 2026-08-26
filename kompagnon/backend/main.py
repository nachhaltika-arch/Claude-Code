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
import secrets
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Was der Start geschafft hat. `/health` gibt es aus, damit ein unvollstaendiger
# Start von aussen sichtbar ist — produktiv fielen sieben von acht Phasen aus,
# und ohne Blick ins Log war das nirgends zu sehen.
_STARTZUSTAND = {"vollstaendig": None, "ausgefallen": [], "fehler": ""}


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

# Import scheduler
from automations import start_scheduler, stop_scheduler, get_scheduler
from automations.scheduler import scheduler_ist_eingeschaltet

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
from services.protokoll_schwaerzung import Schwaerzung  # noqa: E402

for _wurzel_handler in logging.getLogger().handlers:
    _wurzel_handler.addFilter(Schwaerzung())


def _kurse_zusammenfuehren():
    """Startphase: die alte Kurstabelle in die Akademie überführen."""
    from services.kurse_zusammenfuehren import zusammenfuehren_beim_start

    zusammenfuehren_beim_start()


def _zuweisungs_kennungen_nachziehen():
    """Startphase: Altzeilen der Akademie-Zuweisung auf die Benutzer-ID ziehen."""
    from services.zuweisung_kennung import nachziehen_beim_start

    nachziehen_beim_start()


def _lebenszyklus_phasen_nachtragen():
    """Startphase: Lebenszyklus-Phase fuer Bestandsbetriebe nachtragen."""
    from services.lebenszyklus_nachtrag import nachtragen_beim_start

    nachtragen_beim_start()


def _create_default_admin():
    """Create demo users for all 4 roles — only in explicit non-production environments.

    Whitelist: laeuft nur bei ENVIRONMENT in {development, dev, local, staging}.
    Passwoerter kommen ausschliesslich aus ENV-Vars; fehlen sie, wird ein
    Zufallspasswort generiert und einmalig geloggt.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    if env not in ("development", "dev", "local", "staging"):
        logger.info(f"⏭  Demo-User-Erstellung übersprungen (ENVIRONMENT={env})")
        return

    from database import SessionLocal, User
    from auth import hash_password
    db = SessionLocal()
    try:
        demo_users = [
            {"email": os.getenv("ADMIN_EMAIL",   "admin@kompagnon.de"),   "password": os.getenv("ADMIN_PASSWORD",   ""), "first_name": "Admin",  "last_name": "KOMPAGNON",  "role": "admin"},
            {"email": os.getenv("AUDITOR_EMAIL", "auditor@kompagnon.de"), "password": os.getenv("AUDITOR_PASSWORD", ""), "first_name": "Max",    "last_name": "Auditor",    "role": "auditor", "position": "Senior Auditor"},
            {"email": os.getenv("NUTZER_EMAIL",  "nutzer@kompagnon.de"),  "password": os.getenv("NUTZER_PASSWORD",  ""), "first_name": "Lisa",   "last_name": "Nutzer",     "role": "nutzer"},
            {"email": os.getenv("KUNDE_EMAIL",   "kunde@kompagnon.de"),   "password": os.getenv("KUNDE_PASSWORD",   ""), "first_name": "Thomas", "last_name": "Mustermann", "role": "kunde"},
        ]
        created = 0
        for ud in demo_users:
            if not db.query(User).filter(User.email == ud["email"]).first():
                pw = ud.pop("password")
                if not pw:
                    pw = secrets.token_urlsafe(12)
                    logger.warning(
                        f"⚠ Demo-User {ud['email']}: kein Passwort in ENV gesetzt, "
                        f"generiertes Dev-Passwort: {pw}  (NUR einmalig beim Anlegen)"
                    )
                pos = ud.pop("position", "")
                user = User(**ud, password_hash=hash_password(pw), position=pos, is_active=True, is_verified=True)
                db.add(user)
                created += 1
                logger.info(f"✓ Demo-User angelegt: {ud['email']} ({ud['role']})")
        if created:
            db.commit()
        else:
            logger.info("Alle Demo-User bereits vorhanden")
    except Exception as e:
        db.rollback()
        logger.error(f"Demo-User Fehler: {e}")
    finally:
        db.close()

    # ── Demo-Kunde vollständig aufbauen ──────────────────────
    try:
        from database import Lead, Project, AuditResult
        from seed_checklists import create_project_checklists

        _db2 = SessionLocal()

        # 1. Demo-Kunde User holen
        demo_kunde = _db2.query(User).filter(
            User.email == "kunde@kompagnon.de"
        ).first()
        if not demo_kunde:
            _db2.close()
            return

        # 2. Prüfen ob bereits vollständig eingerichtet
        if demo_kunde.lead_id:
            _db2.close()
            logger.info("Demo-Kunde bereits vollständig eingerichtet")
            return

        # 3. Portal-Token erzeugen (qr_service oder uuid-Fallback)
        try:
            from services.qr_service import generate_token
            _token = generate_token()
        except Exception:
            import uuid as _uuid
            _token = _uuid.uuid4().hex

        # 4. Demo-Lead anlegen
        demo_lead = Lead(
            company_name         = "Mustermann Sanitär GmbH",
            contact_name         = "Thomas Mustermann",
            email                = "kunde@kompagnon.de",
            phone                = "+49 261 987654",
            website_url          = "https://mustermann-sanitaer.de",
            city                 = "Koblenz",
            trade                = "Sanitär",
            lead_source          = "stripe_checkout",
            status               = "won",
            notes                = "Demo-Kunde | Paket: KOMPAGNON | 2.000 EUR",
            customer_token       = _token,
            onboarding_completed = False,
        )
        _db2.add(demo_lead)
        _db2.flush()

        # 5. User mit Lead verknüpfen + Passwort sicherstellen
        demo_kunde.lead_id      = demo_lead.id
        demo_kunde.first_name   = "Thomas"
        demo_kunde.last_name    = "Mustermann"
        demo_kunde.is_active    = True
        demo_kunde.is_verified  = True
        from auth import hash_password
        demo_kunde.password_hash = hash_password("Kunde2025!")

        # 6. Projekt in Phase 1 anlegen
        demo_project = Project(
            lead_id       = demo_lead.id,
            status        = "phase_1",
            start_date    = datetime.utcnow(),
            fixed_price   = 2000.0,
            hourly_rate   = 45.0,
            ai_tool_costs = 50.0,
        )
        _db2.add(demo_project)
        _db2.flush()

        # 7. Alle Checklisten-Einträge anlegen
        create_project_checklists(_db2, demo_project.id)

        _db2.commit()

        logger.info(
            f"✓ Demo-Kunde vollständig angelegt: "
            f"Lead {demo_lead.id} | Projekt {demo_project.id} | "
            f"Portal-Token: {demo_lead.customer_token}"
        )

    except Exception as e:
        logger.warning(f"Demo-Kunde Setup Fehler: {e}")
    finally:
        try:
            _db2.close()
        except Exception:
            pass

    # ── Produkte seeden (nur wenn Tabelle leer) ──────────────
    try:
        from database import SessionLocal
        from sqlalchemy import text as _t
        _db3 = SessionLocal()
        count = _db3.execute(_t("SELECT COUNT(*) FROM products")).scalar()
        if count == 0:
            # Der Katalog einer frischen Datenbank. Bis zum 23.08.2026
            # standen hier Starter/KOMPAGNON/Premium zu 1.500/2.000/2.800 EUR
            # brutto, waehrend die Angebote Websprints zu 3.500/7.900/12.900
            # EUR **netto** fuehrten — zwei Produktlinien nebeneinander, und
            # aus dieser Zeile zieht die Stripe-Sitzung ihren Betrag (L-97).
            #
            # Die Bestandsprodukte werden nicht geloescht, sondern in der
            # Migration auf `archived` gesetzt: Ein Projekt aus dem Fruehjahr
            # traegt `package_type='kompagnon'`, und die Kundenmail liest den
            # Preis aus genau dieser Zeile. Wer sie entfernt, deutet eine
            # bezahlte Rechnung nachtraeglich um.
            #
            # Preise sind **netto** angegeben (B2B, Handwerksbetriebe sind
            # vorsteuerabzugsberechtigt); `price_brutto` ist der Betrag, den
            # Stripe abbucht, und muss dazu passen — `test_produktkatalog`
            # rechnet es nach.
            SEED = [
                {
                    "slug": "websprint_relaunch", "name": "Websprint Relaunch",
                    "sort_order": 1,
                    "short_desc": "Bestehende Website auf den Homepage-Standard heben",
                    "price_brutto": 4165.00, "price_netto": 3500.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    # Merkmale und Bauzeit aus dem Leistungsverzeichnis in
                    # docs/produkte/ws-rel-01.md. Das Blatt nannte als
                    # Freigabebedingung „nach Behebung L2 und L3" — beides ist
                    # am 23.08. am laufenden System widerlegt worden (der
                    # PageSpeed-Schluessel arbeitet, die Score-Schwellen sind
                    # beidseitig gleich). Damit ist das Paket verkaufbar.
                    "features": [
                        "Eingangsaudit nach Homepage-Standard, 100 Punkte",
                        "Strukturabgleich und Seitenplan",
                        "Aufbau im KOMPAGNON-Komponentensystem, bis 6 Seiten",
                        "Redaktionelle Ueberarbeitung der vorhandenen Texte",
                        "Bildaufbereitung, bis 30 Bilder",
                        "Kontaktformular mit Spam-Schutz",
                        "Grundlagen der Barrierefreiheit",
                        "Technische Grundoptimierung",
                        "Hosting, SSL, Weiterleitungen, Domainumstellung",
                        "Eine Korrekturschleife",
                        "Abnahmeaudit mit schriftlichem Protokoll",
                        "Einweisung, 30 Minuten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "websprint_neubau", "name": "Websprint Neubau",
                    "sort_order": 2,
                    "short_desc": "Neuaufbau nach Homepage-Standard, bis 12 Seiten",
                    "price_brutto": 9401.00, "price_netto": 7900.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 28, "status": "live",
                    "highlighted": True, "highlight_label": "Empfehlung",
                    "features": ["Positionierungsgespraech, 90 Minuten",
                        "Bauplan als Freigabedokument, eine Ueberarbeitung",
                        "Texterstellung fuer bis zu 12 Seiten",
                        "Bildkonzept und Fotobriefing",
                        "Aufbau im KOMPAGNON-Komponentensystem, responsiv",
                        "Technische Optimierung und strukturierte Auszeichnung",
                        "Hosting, SSL, Weiterleitungen, Domainumstellung",
                        "Zwei Korrekturschleifen",
                        "Abnahmeaudit mit schriftlichem Protokoll",
                        "Einweisung, 60 Minuten",
                        "Pflege Basic fuer 3 Monate",
                        "Re-Audit nach 3 Monaten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "websprint_system", "name": "Websprint System",
                    "sort_order": 3,
                    "short_desc": "Neubau mit GEO/GAIO, Karriereseite und Messgrundlage",
                    "price_brutto": 15351.00, "price_netto": 12900.00, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 42, "status": "draft",
                    # `draft`, nicht `live`: Die Kernleistung dieses Pakets —
                    # Auslieferung von llms.txt, schema.org und Ground Page an
                    # die Kundenseite — ist nicht implementiert (L-99). Das
                    # Datenblatt WS-SYS-01 fuehrt es selbst als 🔴 gesperrt.
                    "features": ["Alles aus dem Websprint Neubau",
                        "Erweiterter Seitenumfang, bis 20 Seiten",
                        "Karriereseite mit Bewerbungsformular",
                        "GEO/GAIO-Layer: llms.txt, schema.org, Ground Page",
                        "Messgrundlage mit Consent-Layer und EU-Datenhaltung",
                        "Auftragsverarbeitungsvertrag",
                        "Pflege Pro fuer 12 Monate",
                        "Quartalsweises Re-Audit mit Massnahmenliste",
                        "Jahresgespraech, 90 Minuten"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
            ]
            import json as _j
            for p in SEED:
                _db3.execute(_t("""
                    INSERT INTO products
                    (slug, name, short_desc, price_brutto, price_netto,
                     tax_rate, payment_type, delivery_days, status,
                     highlighted, highlight_label, features,
                     checkout_fields, webhook_actions, sort_order)
                    VALUES (:slug, :name, :sd, :pb, :pn, :tr, :pt, :dd,
                     :status, :hl, :hll, :feat::jsonb, :cf::jsonb, :wa::jsonb, :so)
                """), {
                    "slug": p["slug"], "name": p["name"], "sd": p["short_desc"],
                    "pb": p["price_brutto"], "pn": p["price_netto"],
                    "tr": p["tax_rate"], "pt": p["payment_type"],
                    "dd": p["delivery_days"], "status": p["status"],
                    "hl": p.get("highlighted", False),
                    "hll": p.get("highlight_label", ""),
                    "feat": _j.dumps(p["features"]),
                    "cf":   _j.dumps(p["checkout_fields"]),
                    "wa":   _j.dumps(p["webhook_actions"]),
                    "so":   p["sort_order"],
                })
            _db3.commit()
            logger.info("✓ 3 Produkte geseedet")
        _db3.close()
    except Exception as e:
        logger.warning(f"Produkt-Seed Fehler: {e}")

    # Der Block „Produkte seeden" stand hier bis zum 22.08.2026 ein
    # **zweites** Mal, wortgleich bis auf Zeilenumbrueche (L-29). Er war
    # wirkungslos — `count == 0` trifft nicht mehr zu, wenn der Block
    # darueber gerade geseedet hat. Die Falle lag im Aendern: Wer einen
    # Preis in der zweiten Vorlage anpasste, aenderte nichts, und nichts
    # sagte es ihm. `tests/test_produktvorlage.py` haelt es bei einer.


def _disable_demo_accounts_in_production():
    """Deaktiviert Demo-Konten wenn ENVIRONMENT=production gesetzt ist."""
    if os.getenv("ENVIRONMENT", "development").lower() != "production":
        return

    DEMO_EMAILS = [
        "admin@kompagnon.de",
        "auditor@kompagnon.de",
        "nutzer@kompagnon.de",
        "kunde@kompagnon.de",
    ]

    from database import SessionLocal, User
    db = SessionLocal()
    try:
        deactivated = 0
        for email in DEMO_EMAILS:
            user = db.query(User).filter(User.email == email).first()
            if user and user.is_active:
                user.is_active = False
                deactivated += 1
                logger.warning(f"🔒 Demo-Konto deaktiviert: {email}")
        if deactivated:
            db.commit()
            logger.warning(f"🔒 {deactivated} Demo-Konten in Produktion deaktiviert")
        else:
            logger.info("✓ Keine aktiven Demo-Konten gefunden")
    except Exception as e:
        db.rollback()
        logger.error(f"Demo-Deaktivierung fehlgeschlagen: {e}")
    finally:
        db.close()


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
            _STARTZUSTAND["fehler"] = "Keine Datenbankverbindung"
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

        _STARTZUSTAND["vollstaendig"] = ergebnis.vollstaendig
        _STARTZUSTAND["ausgefallen"] = ergebnis.ausgefallen + ergebnis.gescheitert

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
# Build allowed origins from environment or use sensible defaults.
# NOTE: allow_credentials=True requires explicit origins (not "*").
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] if _cors_origins_env else []

# Always include known origins
_default_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    # Die eigene Domain der Oberfläche, seit 16.08. Sie steht bewusst *auch*
    # hier und nicht nur in CORS_ALLOWED_ORIGINS: Geht die Variable verloren,
    # lädt das Tool sonst und scheitert an jeder Anfrage — ohne dass irgendwo
    # „CORS" stünde.
    "https://kas.kompagnon.group",
    "https://kompagnon-frontend.onrender.com",  # alte Adresse, bleibt gültig
    "https://websprint.kompagnon.eu",  # WebSprint-Landingpage (eingebetteter Website-Check)
]
for _o in _default_origins:
    if _o not in _cors_origins:
        _cors_origins.append(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https://.*\.netlify\.app",
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


# Health check endpoint
@app.get("/api/health")
async def api_health():
    """Lightweight keepalive — no DB call, responds instantly."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat(), "service": "kompagnon-backend"}

@app.get("/api/ping")
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


@app.get("/health")
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
            "timestamp": os.popen("date").read().strip(),
        }
    except Exception as e:
        return {"status": "degraded", "database": db_status, "detail": str(e)}


# Der Scheduler verrät die interne Jobliste und lässt sich neu starten.
# Beides stand bis zum 19.08.2026 ohne Anmeldung offen; der Neustart
# antwortete beim Nachmessen mit 200 und startete tatsächlich neu.
from routers.auth_router import require_innendienst

@app.get("/api/scheduler/status", dependencies=[Depends(require_innendienst)])
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


@app.post("/api/scheduler/restart", dependencies=[Depends(require_innendienst)])
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


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nAllow: /\n"


@app.get("/")
@app.head("/")
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
@app.get("/info")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
