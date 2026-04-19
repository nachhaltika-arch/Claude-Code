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
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from datetime import datetime
from sqlalchemy import text
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiter — shared instance, imported by routers as well
limiter = Limiter(key_func=get_remote_address)

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

# Import all routers
from routers import (
    usercards_router,
    leads_alias_router,
    usercards_customers_alias_router,
    leads_router,
    customers_alias_router,
    projects_router,
    agents_router,
    customers_router,
    automations_router,
    audit_router,
    auth_router,
    admin_router,
    scraper_router,
    settings_router,
    payments_router,
    tickets_router,
    cms_connect_router,
    portal_router,
    newsletter_router,
)

# Import scheduler
from automations import start_scheduler, stop_scheduler, get_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _run_migrations():
    """
    Fuehrt alle Datenbankmigrationen ueber die zentrale db_migrations.py aus.

    Zusaetzlich: academy_tables-Sanity-Check und Base.metadata.create_all()
    fuer ORM-Tabellen, die noch nicht versioniert sind.
    """
    from database import engine
    from db_migrations import run_migrations

    stats = run_migrations(engine)
    if stats["failed"]:
        logger.error(f"⚠️  {stats['failed']} Migration(en) fehlgeschlagen — Server laeuft trotzdem")

    # Academy-Tabellen Sanity-Check (historisch hier, bleibt als Boot-Diagnostik)
    academy_tables = [
        'academy_courses', 'academy_modules', 'academy_lessons',
        'academy_progress', 'academy_lesson_progress',
        'academy_certificates', 'academy_quiz_questions',
        'academy_customer_access', 'academy_checklist_items',
    ]
    try:
        with engine.connect() as conn:
            for tbl in academy_tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {tbl} LIMIT 1"))
                except Exception as e:
                    logger.warning(f"academy-Tabelle {tbl} fehlt: {e}")
    except Exception as e:
        logger.warning(f"academy sanity check Warnung: {e}")

    # Create any ORM-defined tables that don't exist yet
    # (z.B. project_scraped_pages, project_scrape_jobs — noch nicht versioniert)
    try:
        from database import Base, engine as db_engine
        Base.metadata.create_all(bind=db_engine)
        logger.info("✓ Base.metadata.create_all abgeschlossen")
    except Exception as e:
        logger.warning(f"create_all Warnung: {e}")


def _create_default_admin():
    """Create demo users for all 4 roles — only in development environment."""
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        logger.info("⏭  Demo-User-Erstellung übersprungen (ENVIRONMENT=production)")
        return

    from database import SessionLocal, User
    from auth import hash_password
    db = SessionLocal()
    try:
        demo_users = [
            {"email": os.getenv("ADMIN_EMAIL", "admin@kompagnon.de"), "password": os.getenv("ADMIN_PASSWORD", "Admin2025!"), "first_name": "Admin", "last_name": "KOMPAGNON", "role": "admin"},
            {"email": "auditor@kompagnon.de", "password": "Auditor2025!", "first_name": "Max", "last_name": "Auditor", "role": "auditor", "position": "Senior Auditor"},
            {"email": "nutzer@kompagnon.de", "password": "Nutzer2025!", "first_name": "Lisa", "last_name": "Nutzer", "role": "nutzer"},
            {"email": "kunde@kompagnon.de", "password": "Kunde2025!", "first_name": "Thomas", "last_name": "Mustermann", "role": "kunde"},
        ]
        created = 0
        for ud in demo_users:
            if not db.query(User).filter(User.email == ud["email"]).first():
                pw = ud.pop("password")
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
        _token_expires = None
        try:
            from services.qr_service import generate_token, token_expires_at
            _token = generate_token()
            _token_expires = token_expires_at()
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
            customer_token_expires = _token_expires,
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
            SEED = [
                {
                    "slug": "starter", "name": "Starter-Paket", "sort_order": 1,
                    "short_desc": "5 Seiten, SEO Basic, Mobiloptimierung",
                    "price_brutto": 1500.00, "price_netto": 1260.50, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    "features": ["5-seitige WordPress-Website",
                        "Mobile-First Design", "SEO-Grundoptimierung",
                        "SSL-Zertifikat & DSGVO-konform", "Kontaktformular",
                        "30 Tage Support"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "kompagnon", "name": "KOMPAGNON-Paket", "sort_order": 2,
                    "short_desc": "8 Seiten, SEO + GEO, Workshop, Nachbetreuung",
                    "price_brutto": 2000.00, "price_netto": 1680.67, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    "highlighted": True, "highlight_label": "Empfehlung",
                    "features": ["8-seitige WordPress-Website",
                        "SEO + GEO-Optimierung", "Strategy Workshop (60 Min.)",
                        "Schema Markup & KI-Optimierung",
                        "Google Business Verknuepfung", "30 Tage Support"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user",
                        "create_project", "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "premium", "name": "Premium-Paket", "sort_order": 3,
                    "short_desc": "12 Seiten, Shop-Ready, Fotoshooting",
                    "price_brutto": 2800.00, "price_netto": 2352.94, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 21, "status": "live",
                    "features": ["12-seitige WordPress-Website",
                        "Individual-Design nach CI", "SEO + GEO + KI-Volloptimierung",
                        "Strategy Workshop (90 Min.)", "Professioneller Fotoshooting-Tag",
                        "Google Ads Einrichtung", "3 Monate Support"],
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

    # ── Produkte seeden (nur wenn Tabelle leer) ──────────────
    try:
        from database import SessionLocal
        from sqlalchemy import text as _t
        _db3 = SessionLocal()
        count = _db3.execute(_t("SELECT COUNT(*) FROM products")).scalar()
        if count == 0:
            import json as _j
            SEED = [
                {
                    "slug": "starter", "name": "Starter-Paket", "sort_order": 1,
                    "short_desc": "5 Seiten, SEO Basic, Mobiloptimierung",
                    "price_brutto": 1500.00, "price_netto": 1260.50, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    "category": "website",
                    "features": ["5-seitige WordPress-Website", "Mobile-First Design",
                                 "SEO-Grundoptimierung", "SSL-Zertifikat & DSGVO-konform",
                                 "Kontaktformular", "30 Tage Support"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user", "create_project",
                                        "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "kompagnon", "name": "KOMPAGNON-Paket", "sort_order": 2,
                    "short_desc": "8 Seiten, SEO + GEO, Workshop, Nachbetreuung",
                    "price_brutto": 2000.00, "price_netto": 1680.67, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 14, "status": "live",
                    "highlighted": True, "highlight_label": "Empfehlung",
                    "category": "website",
                    "features": ["8-seitige WordPress-Website", "SEO + GEO-Optimierung",
                                 "Strategy Workshop (60 Min.)", "Schema Markup & KI-Optimierung",
                                 "Google Business Verknuepfung", "30 Tage Support"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user", "create_project",
                                        "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "premium", "name": "Premium-Paket", "sort_order": 3,
                    "short_desc": "12 Seiten, Shop-Ready, Fotoshooting",
                    "price_brutto": 2800.00, "price_netto": 2352.94, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 21, "status": "live",
                    "category": "website",
                    "features": ["12-seitige WordPress-Website", "Individual-Design nach CI",
                                 "SEO + GEO + KI-Volloptimierung", "Strategy Workshop (90 Min.)",
                                 "Professioneller Fotoshooting-Tag", "Google Ads Einrichtung",
                                 "3 Monate Support"],
                    "checkout_fields": ["name", "company", "email", "phone"],
                    "webhook_actions": ["create_lead", "create_user", "create_project",
                                        "send_welcome_email", "send_pdf"],
                },
                {
                    "slug": "impuls", "name": "IMPULS by KOMPAGNON", "sort_order": 10,
                    "short_desc": "Geförderte Unternehmensberatung — 50 % vom Land RLP",
                    "long_desc": (
                        "IMPULS ist das ISB-158-Beratungsprogramm von KOMPAGNON für KMU in Rheinland-Pfalz. "
                        "Das Land Rheinland-Pfalz übernimmt 50 % der Beratungskosten (max. 500 €/Tagewerk). "
                        "Beratungsschwerpunkte: Strategie, Marketing, Digitalisierung, Kommunikationsdesign. "
                        "Finanzierung des Eigenanteils über MMV Leasing in 36 Monatsraten. "
                        "Alle Ergebnisse werden in einem persönlichen, passwortgeschützten Online-Portal bereitgestellt."
                    ),
                    "price_brutto": 20000.00, "price_netto": 16806.72, "tax_rate": 19,
                    "payment_type": "once", "delivery_days": 90, "status": "draft",
                    "highlighted": True, "highlight_label": "50 % Förderung",
                    "category": "beratung",
                    "features": [
                        "ISB-158 Förderung: 50 % vom Land Rheinland-Pfalz",
                        "Bis zu 20 Tagewerke à 8 Stunden Beratung",
                        "Strategie, Marketing & Vertriebsoptimierung",
                        "Digitalisierung & KI-Einsatz im Unternehmen",
                        "Kommunikations- & Designberatung (max. 3 TW)",
                        "Persönliches Ergebnis-Portal (passwortgeschützt)",
                        "Leasingfinanzierung: ~145 €/Monat über MMV",
                        "Wir übernehmen Antragstellung & Dokumentation",
                    ],
                    "checkout_fields": ["name", "company", "email", "phone", "message"],
                    "webhook_actions": ["create_lead", "send_welcome_email"],
                },
            ]
            for p in SEED:
                _db3.execute(_t("""
                    INSERT INTO products
                    (slug, name, short_desc, long_desc, price_brutto, price_netto,
                     tax_rate, payment_type, delivery_days, status,
                     highlighted, highlight_label, features,
                     checkout_fields, webhook_actions, sort_order, category)
                    VALUES (:slug, :name, :sd, :ld, :pb, :pn, :tr, :pt, :dd,
                     :status, :hl, :hll, :feat::jsonb, :cf::jsonb, :wa::jsonb, :so, :cat)
                    ON CONFLICT (slug) DO UPDATE SET category = EXCLUDED.category
                """), {
                    "slug": p["slug"], "name": p["name"], "sd": p["short_desc"],
                    "ld": p.get("long_desc", ""),
                    "pb": p["price_brutto"], "pn": p["price_netto"],
                    "tr": p["tax_rate"], "pt": p["payment_type"],
                    "dd": p["delivery_days"], "status": p["status"],
                    "hl": p.get("highlighted", False),
                    "hll": p.get("highlight_label", ""),
                    "feat": _j.dumps(p["features"]),
                    "cf": _j.dumps(p["checkout_fields"]),
                    "wa": _j.dumps(p["webhook_actions"]),
                    "so": p["sort_order"],
                    "cat": p.get("category", "sonstige"),
                })
            _db3.commit()
            logger.info("✓ 4 Produkte geseedet")
        _db3.close()
    except Exception as e:
        logger.warning(f"Produkt-Seed Fehler: {e}")


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


def _create_default_superadmin():
    """
    Bootstrap-Funktion fuer den initialen Superadmin.

    Laeuft in ALLEN Umgebungen (auch production), aber NUR wenn die
    beiden Env-Vars SUPERADMIN_EMAIL und SUPERADMIN_PASSWORD gesetzt sind.
    KEINE hardcoded Fallback-Credentials — bei fehlenden Env-Vars wird
    die Funktion stumm uebersprungen.

    Verhalten:
      - User existiert noch nicht → neu anlegen mit role=superadmin
      - User existiert bereits mit anderer Rolle → zu superadmin promoten
      - User existiert bereits als superadmin → no-op
      - Passwort wird NUR beim Neu-Anlegen gesetzt. Bei bestehenden
        Usern wird das aktuelle Passwort NIE ueberschrieben, damit
        User-Edits (via Admin-UI) nicht beim Deploy rueckgaengig gemacht werden.
    """
    email = os.getenv("SUPERADMIN_EMAIL", "").strip().lower()
    password = os.getenv("SUPERADMIN_PASSWORD", "")

    if not email or not password:
        # Beide Env-Vars muessen gesetzt sein — sonst ueberspringen
        logger.info("⏭  Superadmin-Bootstrap uebersprungen (SUPERADMIN_EMAIL/SUPERADMIN_PASSWORD nicht gesetzt)")
        return

    # Leichte Passwort-Warnung (entspricht Security Fix 11 Minimum)
    if len(password) < 12:
        logger.warning(
            f"⚠️  SUPERADMIN_PASSWORD fuer {email} ist schwach "
            f"(<12 Zeichen) — bitte nach dem Bootstrap via "
            f"/api/auth/change-password aendern"
        )

    from database import SessionLocal, User
    from auth import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()

        if existing:
            # Bestehenden User nicht ueberschreiben, nur Rolle setzen
            if existing.role == "superadmin":
                logger.info(f"✓ Superadmin {email} bereits vorhanden — no-op")
            else:
                old_role = existing.role
                existing.role = "superadmin"
                existing.is_active = True  # Sicherstellen dass nicht deaktiviert
                db.commit()
                logger.info(
                    f"✓ User {email} von '{old_role}' zu 'superadmin' promoted "
                    f"(Passwort unveraendert)"
                )
        else:
            # Neuen Superadmin anlegen
            user = User(
                email=email,
                password_hash=hash_password(password),
                first_name=os.getenv("SUPERADMIN_FIRST_NAME", "Super"),
                last_name=os.getenv("SUPERADMIN_LAST_NAME", "Admin"),
                role="superadmin",
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            db.commit()
            logger.info(f"✓ Superadmin {email} neu angelegt")
    except Exception as e:
        db.rollback()
        logger.error(f"Superadmin-Bootstrap fehlgeschlagen: {e}")
    finally:
        db.close()


def _migrate_backup_codes():
    """Einmalig: Klartext-Backup-Codes in der DB hashen."""
    from database import SessionLocal, User
    from auth import hash_password

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.backup_codes.isnot(None)).all()
        migrated = 0
        for user in users:
            if not user.backup_codes:
                continue
            try:
                codes = json.loads(user.backup_codes)
                if not codes:
                    continue
                # Pruefen ob bereits gehasht (bcrypt-Hash beginnt mit $2a$/$2b$/$2y$)
                first = codes[0] if isinstance(codes, list) else ""
                if isinstance(first, str) and first.startswith(("$2a$", "$2b$", "$2y$")):
                    continue  # Bereits gehasht — ueberspringen
                # Klartext → hashen
                user.backup_codes = json.dumps([hash_password(c) for c in codes])
                migrated += 1
            except Exception:
                continue
        if migrated:
            db.commit()
            logger.info(f"✓ {migrated} Nutzer: Backup-Codes gehasht")
        else:
            logger.info("✓ Keine Klartext-Backup-Codes mehr in der DB")
    except Exception as e:
        logger.error(f"Backup-Code-Migration fehlgeschlagen: {e}")
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

        def _academy_seed():
            from routers.academy import seed_academy_courses
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

        with ThreadPoolExecutor(max_workers=1) as pool:
            loop = asyncio.get_event_loop()

            async def _run(fn, timeout):
                def _wrap():
                    try:
                        fn()
                        return None
                    except Exception as ex:
                        return ex
                return await asyncio.wait_for(loop.run_in_executor(pool, _wrap), timeout=timeout)

            # PHASE 1: DB connection with retry
            db_ready = False
            for attempt in range(1, 4):
                step_start = time.time()
                logger.info(f"  DB-Verbindung Versuch {attempt}/3...")
                try:
                    result = await _run(_ping_db, 45.0)
                    if result is None:
                        db_ready = True
                        logger.info(f"  ✓ DB verbunden ({time.time() - step_start:.1f}s)")
                        break
                    logger.warning(f"  ⚠ DB-Versuch {attempt}: {result}")
                except asyncio.TimeoutError:
                    logger.warning(f"  ⚠ DB-Versuch {attempt} Timeout nach 45s")
                except Exception as e:
                    logger.warning(f"  ⚠ DB-Versuch {attempt} Fehler: {e}")
                if attempt < 3:
                    await asyncio.sleep(2)

            if not db_ready:
                logger.error(f"❌ DB-Verbindung fehlgeschlagen — Server läuft ohne DB (Scheduler übersprungen)")
                return

            # PHASE 2-5: Each step isolated
            phases = [
                ("Migrations",    _run_migrations,       60.0),
                ("DB init",       init_db,               30.0),
                ("Default admin", _create_default_admin, 10.0),
                ("Disable demo accounts", _disable_demo_accounts_in_production, 10.0),
                ("Default superadmin", _create_default_superadmin, 10.0),
                ("Hash backup codes", _migrate_backup_codes, 20.0),
                ("Academy seed",  _academy_seed,         10.0),
                ("Deals migration", _deals_migration,    15.0),
                ("Scheduler",     start_scheduler,       15.0),
            ]
            for name, fn, timeout in phases:
                step_start = time.time()
                try:
                    result = await _run(fn, timeout)
                    dt = time.time() - step_start
                    if result is None:
                        logger.info(f"  ✓ {name} ({dt:.1f}s)")
                    else:
                        logger.warning(f"  ⚠ {name} Fehler: {result}")
                except asyncio.TimeoutError:
                    logger.warning(f"  ⚠ {name} Timeout nach {timeout}s — übersprungen")
                except Exception as e:
                    logger.warning(f"  ⚠ {name} unerwarteter Fehler: {e}")

        total = time.time() - start
        logger.info(f"✅ Hintergrund-Init abgeschlossen in {total:.1f}s")

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

# Register rate limiter with the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Globaler Exception-Handler ─────────────────────────────
# Fängt jede nicht-HTTPException ab, loggt den vollständigen Stack-Trace
# und sendet an den Client nur eine generische Fehlermeldung ohne
# Systemdetails. Verhindert Leaks von DB-Schemas, Dateipfaden,
# Stack-Traces, etc.
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc} "
        f"| Path: {request.url.path}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Interner Fehler"},
    )


# CORS Middleware — must be before all routers
# Explicit origin list — NO wildcard, NO env-var injection.
# Localhost-Origins werden nur ausserhalb von production erlaubt.
_ALLOWED_ORIGINS = [
    "https://kompagnon-frontend.onrender.com",
]
if os.getenv("ENVIRONMENT", "development").lower() != "production":
    _ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.netlify\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ── Security-HTTP-Header ───────────────────────────────────
# Setzt Defense-in-Depth Header auf jede API-Response.
# Kein CSP hier — die API liefert JSON, kein HTML. CSP steht
# auf den Netlify-Kunden-Seiten (Fix 07) und optional im
# React-Frontend (public/_headers).
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"]       = "1; mode=block"
    response.headers["Permissions-Policy"]     = "camera=(), microphone=(), geolocation=()"
    return response


# Include all routers — specific routers BEFORE alias/fallback routers
app.include_router(usercards_router)
app.include_router(leads_router)                      # real leads router first
app.include_router(leads_alias_router)                # alias after
app.include_router(usercards_customers_alias_router)
app.include_router(customers_router)                  # real customers router first
app.include_router(customers_alias_router)            # alias after
app.include_router(projects_router)
app.include_router(agents_router)
app.include_router(automations_router)
app.include_router(cms_connect_router)
app.include_router(portal_router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(scraper_router)
app.include_router(settings_router)
app.include_router(payments_router)
app.include_router(tickets_router)
app.include_router(newsletter_router)

from routers import briefings
# Alle /api/briefings/* Endpunkte leben jetzt in einem einzigen Router:
# GET + POST + PUT + PATCH + PATCH/freigabe + POST/suggest-field +
# POST/ki-prefill + POST/submit + POST/zielgruppenanalyse + POST/wettbewerbsanalyse
app.include_router(briefings.router)

from routers.kampagne import router as kampagne_router
app.include_router(kampagne_router)

from routers.courses import router as courses_router
app.include_router(courses_router)

try:
    from routers.academy import router as _academy_router
    app.include_router(_academy_router)
    logger.info("✓ Academy Router geladen")
except Exception as e:
    logger.warning(f"⚠ Academy Router nicht geladen: {e}")

try:
    from routers.crawler import router as _crawler_router
    app.include_router(_crawler_router)
    logger.info("✓ Crawler Router geladen")
except Exception as e:
    logger.warning(f"⚠ Crawler Router nicht geladen: {e}")

try:
    from routers.files import router as _files_router
    app.include_router(_files_router)
    logger.info("✓ Files Router geladen")
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
app.include_router(sitemap.pages_router)

from routers import content
app.include_router(content.router)

from routers import designs
app.include_router(designs.router)

from routers import content_scraper_router
app.include_router(content_scraper_router.router)

from routers.branddesign import router as branddesign_router
app.include_router(branddesign_router)

from routers.seo_router import router as seo_router
app.include_router(seo_router)

from routers import templates as templates_router
app.include_router(templates_router.router)

from routers import website_templates as website_templates_router
app.include_router(website_templates_router.router)

from routers import messages as messages_router
app.include_router(messages_router.router)

from routers import webhooks
app.include_router(webhooks.router)

from routers import retainer
app.include_router(retainer.router)


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

from routers.impuls import router as impuls_router
app.include_router(impuls_router)


# Global exception handler — catches unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(
        f'Unbehandelter Fehler: {type(exc).__name__}: {exc}\n{traceback.format_exc()}'
    )
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


@app.get("/api/health/full")
async def api_health_full():
    """Vollstaendiger Self-Check fuer alle kritischen Subsysteme.

    Pruef-Strategie: Nur Existenz-Checks (Env-Vars + DB-connect), KEINE
    externen API-Aufrufe an Anthropic / Netlify / SMTP. Damit ist der
    Endpunkt schnell, kostenlos und faellt nicht bei externen Ausfaellen.

    status:
      - "ok"        — alles gruen
      - "degraded"  — mindestens ein nicht-kritischer Check fehlt
      - "error"     — DB nicht erreichbar (kritisch)

    Antwort enthaelt KEINE Secrets, nur boolesche "ist gesetzt" Flags.
    """
    from database import SessionLocal
    from db_migrations import MIGRATIONS

    checks = {}
    info = {}

    # ── DB connect + Migrations-Vergleich ───────────────────────────
    db_ok = False
    db_detail = "unknown"
    db_max_version = None
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
            db_detail = "connected"
            try:
                row = db.execute(
                    text("SELECT MAX(version) FROM schema_migrations")
                ).fetchone()
                db_max_version = row[0] if row and row[0] is not None else 0
            except Exception as e:
                db_detail = f"connected, schema_migrations read failed: {str(e)[:80]}"
        finally:
            db.close()
    except Exception as e:
        db_detail = f"error: {str(e)[:120]}"
    checks["db"] = {"ok": db_ok, "detail": db_detail}

    # Migration-State: erwartete Version vs. angewandte Version
    code_max_version = max((v for v, _name, _sql in MIGRATIONS), default=0)
    if db_max_version is None:
        mig_ok = False
        mig_detail = "schema_migrations table not readable"
    elif db_max_version >= code_max_version:
        mig_ok = True
        mig_detail = f"v{db_max_version} applied (code expects v{code_max_version})"
    else:
        mig_ok = False
        mig_detail = (
            f"v{db_max_version} applied, but code expects v{code_max_version} "
            f"— {code_max_version - db_max_version} pending"
        )
    checks["migrations"] = {"ok": mig_ok, "detail": mig_detail}

    # ── Env-Var-Existenz (keine Werte loggen!) ──────────────────────
    def _env_set(key: str) -> bool:
        return bool((os.getenv(key) or "").strip())

    anthropic_ok = _env_set("ANTHROPIC_API_KEY")
    checks["anthropic"] = {
        "ok": anthropic_ok,
        "detail": "ANTHROPIC_API_KEY set" if anthropic_ok else "ANTHROPIC_API_KEY missing",
    }

    netlify_ok = _env_set("NETLIFY_API_TOKEN")
    checks["netlify"] = {
        "ok": netlify_ok,
        "detail": "NETLIFY_API_TOKEN set" if netlify_ok else "NETLIFY_API_TOKEN missing",
    }

    smtp_keys = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_SENDER_EMAIL"]
    smtp_missing = [k for k in smtp_keys if not _env_set(k)]
    smtp_ok = len(smtp_missing) == 0
    checks["smtp"] = {
        "ok": smtp_ok,
        "detail": "all 4 SMTP env vars set" if smtp_ok else f"missing: {', '.join(smtp_missing)}",
    }

    # ── Info (nicht im Status-Aggregat enthalten) ───────────────────
    try:
        info["routes"] = sum(1 for r in app.routes if hasattr(r, "path"))
    except Exception:
        info["routes"] = None

    info["git_sha"] = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or os.getenv("COMMIT_SHA")
        or None
    )
    info["python_env"] = "production" if os.getenv("RENDER") else "local"

    # ── Status aggregieren ──────────────────────────────────────────
    if not checks["db"]["ok"]:
        status = "error"
    elif not all(c["ok"] for c in checks.values()):
        status = "degraded"
    else:
        status = "ok"

    return {
        "status":    status,
        "timestamp": datetime.utcnow().isoformat(),
        "service":   "kompagnon-backend",
        "checks":    checks,
        "info":      info,
    }


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
            "timestamp": os.popen("date").read().strip(),
        }
    except Exception as e:
        return {"status": "degraded", "database": db_status, "detail": str(e)}


@app.get("/api/scheduler/status")
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


@app.post("/api/scheduler/restart")
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


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__,
        },
    )


# Info endpoint for deployment
@app.get("/info")
def get_info():
    """Get system information."""
    return {
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db"),
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
