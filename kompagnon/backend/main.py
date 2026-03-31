"""
KOMPAGNON Automation System - FastAPI Entry Point
Runs the complete backend with scheduler, DB, and all routers.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text


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
    leads_router,
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
    """Führt alle fehlenden Spalten-Migrationen aus."""
    from database import engine
    migrations = [
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_phone VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_email VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS scraped_description VARCHAR DEFAULT ''",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_impressum INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_datenschutz INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_cookie INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_bfsg INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_urheberrecht INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS rc_ecommerce INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_lcp INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_cls INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_inp INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_mobile INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS tp_bilder INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_anbieter INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_uptime INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_http INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_backup INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ho_cdn INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_kontrast INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_tastatur INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_screenreader INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS bf_lesbarkeit INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_ssl INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_header INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_drittanbieter INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS si_formulare INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_seo INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_schema INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS se_lokal INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_erstindruck INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_cta INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_navigation INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_vertrauen INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_content INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS ux_kontakt INTEGER DEFAULT 0",
        "ALTER TABLE audit_results ADD COLUMN IF NOT EXISTS screenshot_base64 TEXT DEFAULT ''",
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS website_screenshot TEXT DEFAULT ''",
        # Note: users + user_sessions tables are created by init_db() via SQLAlchemy
    ]
    try:
        with engine.connect() as conn:
            for sql in migrations:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass  # Spalte existiert bereits
            conn.commit()
        logger.info("✓ Migrationen abgeschlossen")
    except Exception as e:
        logger.warning(f"Migration Warnung: {e}")


def _create_default_admin():
    """Create demo users for all 4 roles if they don't exist."""
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("🚀 KOMPAGNON Backend Starting...")
    try:
        _run_migrations()
        init_db()
        logger.info("✓ Database initialized")

        # Create default admin if no users exist
        try:
            _create_default_admin()
        except Exception as e:
            logger.warning(f"⚠ Default admin: {e}")

        # Start scheduler (non-critical — don't block app start)
        try:
            start_scheduler()
            logger.info("✓ Scheduler started")
        except Exception as e:
            logger.warning(f"⚠ Scheduler failed to start (non-critical): {e}")

        yield

    except Exception as e:
        logger.error(f"✗ Startup failed: {str(e)}")
        raise

    finally:
        logger.info("🛑 KOMPAGNON Backend Shutting Down...")
        try:
            stop_scheduler()
        except Exception:
            pass
        logger.info("✓ Shutdown complete")


# Create FastAPI app with lifespan
app = FastAPI(
    title="KOMPAGNON Automation System",
    description="Complete WordPress website automation for German handcraft businesses",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UnicodeJSONResponse,
)

# CORS Middleware
origins = [
    "https://kompagnon-frontend.onrender.com",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(leads_router)
app.include_router(projects_router)
app.include_router(agents_router)
app.include_router(customers_router)
app.include_router(automations_router)
app.include_router(audit_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(scraper_router)
app.include_router(settings_router)
app.include_router(payments_router)


# Health check endpoint
@app.get("/health")
def health_check():
    """Check if backend is running."""
    try:
        scheduler = get_scheduler()
        return {
            "status": "ok",
            "service": "KOMPAGNON Backend",
            "scheduler_running": scheduler.scheduler.running,
            "timestamp": os.popen("date").read().strip(),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/")
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
