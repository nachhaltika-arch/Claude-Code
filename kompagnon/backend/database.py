"""
SQLAlchemy database setup and models for KOMPAGNON system.
"""
import os
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Numeric, Text, ForeignKey, JSON, UniqueConstraint, create_engine
from sqlalchemy import text as sa_text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError
from sqlalchemy.dialects.postgresql import JSONB
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=5,          # 5 pro Worker × max 2 Worker = 10 Verbindungen
        max_overflow=5,       # Burst bis max 20 total — weit unter 97 Limit
        pool_timeout=20,      # 20s warten dann Fehler (nicht 60s)
        echo=False,
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 3,
            "options": "-c statement_timeout=10000",  # 10s Query-Timeout
        },
    )

    # Connection Pool Event-Handler für besseres Logging
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        pass  # Verbindung etabliert

    @event.listens_for(engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        pass  # Verbindung aus Pool geholt

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Lead(Base):
    """Lead model for sales pipeline."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), default="")

    # ── Nachgezogene Spalten ─────────────────────────────────────────
    # Diese Spalten legt `migrations_runtime.py::run_migrations` beim Start an. Im Modell
    # fehlten sie — und wer sie zuweist, verliert den Wert stillschweigend:
    # SQLAlchemy legt ihn auf dem Python-Objekt ab und schreibt ihn nie.
    # Gefunden am 18.08.2026 beim Vergleich Migration gegen Modell.
    onboarding_completed = Column(Boolean, default=False)
    onboarding_completed_at = Column(DateTime, nullable=True)
    unread_messages = Column(Integer, default=0)

    # Woher der Betrieb kam, wenn er ueber eine Anzeige hereinkam (L-86).
    # Dieselbe Falle, ein zweites Mal: Die Spalten stehen seit langem in
    # `migrations_runtime.py`, im Modell fehlten sie — und weil
    # `routers/kampagne.py` sie mit rohem SQL schreibt, fiel es nie auf.
    # Erst als der oeffentliche Weg sie zuweisen wollte, kam der Fehler.
    utm_source = Column(String(200), nullable=True)
    utm_medium = Column(String(200), nullable=True)
    utm_campaign = Column(String(200), nullable=True)
    pagespeed_mobile_score = Column(Integer, nullable=True)
    pagespeed_desktop_score = Column(Integer, nullable=True)
    pagespeed_lcp_mobile = Column(Float, nullable=True)
    pagespeed_cls_mobile = Column(Float, nullable=True)
    pagespeed_inp_mobile = Column(Float, nullable=True)
    pagespeed_fcp_mobile = Column(Float, nullable=True)
    pagespeed_checked_at = Column(DateTime, nullable=True)
    contact_name = Column(String(255), nullable=True, default=None)
    phone = Column(String(20), nullable=True, default=None)
    mobile = Column(String(20), nullable=True, default=None)
    email = Column(String(255), nullable=True, default=None)
    website_url = Column(String(500), default="")
    city = Column(String(100), nullable=True, default=None)
    trade = Column(String(100), nullable=True, default=None)
    lead_source = Column(String(100), default="")
    status = Column(String(50), default="new")
    # Wo im Trichter — getrennt davon, wie weit die Bearbeitung ist.
    # `status` beantwortete beides gleichzeitig und deshalb keines richtig
    # (19.08.2026, aus dem HubSpot-Vergleich). Wird **nicht** von Hand
    # gepflegt: Ein Ereignis unten zieht sie beim Setzen von `status` mit.
    # `None` heisst „nicht einzuordnen" und ist ein sichtbarer Zustand, kein
    # Fehler — siehe services/lebenszyklus.py.
    lifecycle_phase = Column(String(30), nullable=True, index=True)
    analysis_score = Column(Integer, default=0)
    geo_score = Column(Integer, default=0)
    notes = Column(Text, nullable=True, default=None)
    website_screenshot = Column(Text, nullable=True, default=None)

    # Befunde der automatischen Anreicherung. Sie standen bis zum 17.08.2026
    # nur als Textzeile in `notes` — im Feld fuer die Notizen eines Menschen,
    # und bei jedem Lauf erneut davorgesetzt. `None` heisst „noch nicht
    # geprueft" und ist ausdruecklich nicht dasselbe wie „nicht vorhanden".
    has_ssl = Column(Boolean, nullable=True, default=None)
    has_impressum = Column(Boolean, nullable=True, default=None)
    enriched_at = Column(DateTime, nullable=True)

    # Address
    street = Column(String(255), default="")
    house_number = Column(String(20), default="")
    postal_code = Column(String(10), default="")

    # Company details
    legal_form = Column(String(50), default="")
    vat_id = Column(String(30), default="")
    register_number = Column(String(50), default="")
    register_court = Column(String(100), default="")
    ceo_first_name = Column(String(100), default="")
    ceo_last_name = Column(String(100), default="")
    display_name = Column(String(255), default="")

    customer_token = Column(String, unique=True, nullable=True)
    customer_token_created_at = Column(DateTime, nullable=True)

    # PageSpeed Insights (stored per-lead)
    pagespeed_mobile_score  = Column(Integer, nullable=True)
    pagespeed_desktop_score = Column(Integer, nullable=True)
    pagespeed_lcp_mobile    = Column(Float,   nullable=True)
    pagespeed_cls_mobile    = Column(Float,   nullable=True)
    pagespeed_inp_mobile    = Column(Float,   nullable=True)
    pagespeed_fcp_mobile    = Column(Float,   nullable=True)
    pagespeed_checked_at    = Column(DateTime, nullable=True)
    geschaeftsfuehrer       = Column(String, nullable=True)
    favicon_url             = Column(String(500), default='')

    # Brand Design (stored per-lead from website scrape)
    brand_primary_color   = Column(String(20), nullable=True)
    brand_secondary_color = Column(String(20), nullable=True)
    brand_font_primary    = Column(String(100), nullable=True)
    brand_font_secondary  = Column(String(100), nullable=True)
    brand_logo_url        = Column(Text, nullable=True)
    brand_colors          = Column(Text, nullable=True)
    brand_fonts           = Column(Text, nullable=True)
    brand_scrape_failed   = Column(Boolean, default=False, nullable=True)
    brand_scraped_at      = Column(DateTime, nullable=True)
    brand_design_json     = Column(Text, nullable=True)
    brand_design_style    = Column(String(100), nullable=True)
    brand_notes           = Column(Text, nullable=True)
    brand_pdf_filename    = Column(String(255), nullable=True)
    brand_guideline_json         = Column(Text, nullable=True)
    brand_guideline_generated_at = Column(DateTime, nullable=True)
    brand_font_heading           = Column(String(100), nullable=True)
    brand_font_body              = Column(String(100), nullable=True)
    brand_font_accent            = Column(String(100), nullable=True)
    brand_design_tokens_json     = Column(Text, nullable=True)

    # Google Analytics detection
    ga_status         = Column(String(50), nullable=True)
    ga_type           = Column(String(50), nullable=True)
    ga_measurement_id = Column(String(50), nullable=True)
    ga_checked_at     = Column(DateTime, nullable=True)

    # E-Mail-Sequenz (Drip-Campaign)
    sequence_active    = Column(Boolean, default=False, nullable=True)
    sequence_step      = Column(Integer, default=0,     nullable=True)
    sequence_paused    = Column(Boolean, default=False, nullable=True)
    sequence_last_sent = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="lead", cascade="all, delete-orphan",
                            foreign_keys="[Project.lead_id]")


class LeadDomain(Base):
    __tablename__ = "lead_domains"
    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    url = Column(String(500), nullable=False)
    label = Column(String(100), default="")  # e.g. "Hauptseite", "Shop", "Karriere"
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    lead = relationship("Lead", backref="domains", foreign_keys=[lead_id])


class Project(Base):
    """Project model for WordPress website builds."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)

    # ── Nachgezogene Spalten ─────────────────────────────────────────
    # Siehe Lead: von `_run_migrations` angelegt, im Modell vergessen — jede
    # Zuweisung ging still verloren.
    current_phase = Column(Integer, default=1)
    auftragsbestaetigung_pdf = Column(String(500), nullable=True)
    status = Column(String(50), default="phase_1")  # phase_1 to phase_7, completed
    start_date = Column(DateTime)
    target_go_live = Column(DateTime)
    actual_go_live = Column(DateTime)
    fixed_price = Column(Float, default=2000.0)  # €2000 default
    actual_hours = Column(Float, default=0.0)  # Updated by TimeTracking
    hourly_rate = Column(Float, default=45.0)  # €45/h default
    ai_tool_costs = Column(Float, default=50.0)  # €50 default
    margin_percent = Column(Float, default=0.0)  # Computed
    scope_creep_flags = Column(Integer, default=0)  # Count of scope creep incidents
    customer_approved_at = Column(DateTime)  # When customer approved Phase 5
    review_received = Column(Boolean, default=False)
    review_platform = Column(String(50))  # google, provenexpert
    review_rating = Column(Float)  # 1-5 stars
    review_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Redesign / extra columns (added via ALTER TABLE in migrations)
    company_name = Column(String(255))
    website_url = Column(String(500))
    cms_type = Column(String(50))
    contact_name = Column(String(255))
    contact_phone = Column(String(50))
    contact_email = Column(String(255))
    go_live_date = Column(String(20))  # stored as ISO date string
    package_type = Column(String(50), default="kompagnon")
    payment_status = Column(String(50), default="offen")
    # Project-Type ('standard' oder 'impuls') — orthogonal zu package_type.
    # ISB-158-Förder-Felder werden nur bei project_type='impuls' gefüllt.
    project_type = Column(String(20), default="standard")
    isb_antrag_datum = Column(Date, nullable=True)
    isb_bewilligung_datum = Column(Date, nullable=True)
    foerder_volumen = Column(Numeric(10, 2), nullable=True)
    isb_tagewerke = Column(Integer, nullable=True)
    desired_pages = Column(Text)
    has_logo = Column(Boolean, default=False)
    has_briefing = Column(Boolean, default=False)
    has_photos = Column(Boolean, default=False)
    pagespeed_mobile = Column(Integer)
    pagespeed_desktop = Column(Integer)
    audit_score = Column(Integer)
    audit_level = Column(String(100))
    top_problems = Column(Text)
    industry = Column(String(100))
    email_notifications_enabled = Column(Boolean, default=True)
    customer_email = Column(String(255))

    # QA Scanner
    qa_result = Column(Text)         # JSON from KI QA evaluation
    qa_score = Column(Integer)       # 0-100
    qa_golive_ok = Column(Boolean)   # Go-Live recommendation
    qa_run_at = Column(DateTime)     # Last scan timestamp

    # Briefing-Submit-Timestamp — wird von routers/briefings.py beim ersten
    # meaningful-content-Save gesetzt. Ohne diese Spalte crashte POST /api/briefings/{id}
    # mit AttributeError (das manuelle SQL-Migration 2026-05-04-backfill-phase2.sql
    # befuellte die Spalte, aber das ALTER TABLE wurde nie automatisch ausgefuehrt).
    briefing_submitted_at = Column(DateTime, nullable=True)

    # Domain check
    domain_reachable = Column(Boolean)
    domain_status_code = Column(Integer)
    domain_checked_at = Column(DateTime)

    # Go-Live PageSpeed after
    pagespeed_after_mobile = Column(Integer)
    pagespeed_after_desktop = Column(Integer)

    # Scrape Cache (persistierte Scraper-Ergebnisse)
    scrape_full_data = Column(Text)      # JSON: SEO + text + assets + links
    scrape_full_at   = Column(DateTime)  # Zeitpunkt des letzten Scrapes

    # Netlify-Integration
    netlify_site_id       = Column(String(100))
    netlify_site_url      = Column(String(500))
    netlify_deploy_id     = Column(String(100))
    netlify_domain        = Column(String(255))
    netlify_domain_status = Column(String(50))
    netlify_ssl_active    = Column(Boolean, default=False)
    netlify_last_deploy   = Column(DateTime)

    # Screenshots before/after
    screenshot_before       = Column(Text)
    screenshot_before_date  = Column(DateTime)
    screenshot_after        = Column(Text)
    screenshot_after_date   = Column(DateTime)
    screenshot_url_before   = Column(String(500))
    screenshot_url_after    = Column(String(500))

    # Freigabe-Gates
    briefing_approved_at    = Column(DateTime)
    content_approval_token  = Column(String(255))

    # Wireframe (Block-Zuweisungen pro Sitemap-Seite, vom KI-Agent gefuellt)
    # Struktur: {"pages": [{"page_id": int, "blocks": [{"slug": str, "order": int, "slots": {...}}]}]}
    wireframe_data          = Column(JSONB, default=list)

    # Vom Nutzer bestaetigte Editor-Schritte, als JSON-Text:
    # {"<step_id>": {"confirmed": true, "confirmed_at": "<iso>"}}
    #
    # Die Spalte legt `migrations_runtime.py::run_migrations` per rohem SQL an. Hier fehlte
    # sie — und ohne den Eintrag im Modell schreibt SQLAlchemy sie nicht:
    # `project.steps_confirmed = …` setzte nur ein Attribut am Python-Objekt,
    # `commit()` tat nichts, und die Antwort las denselben Speicher zurueck.
    # Nach aussen sah jede Bestaetigung erfolgreich aus und war nach dem
    # naechsten Laden weg — mit ihr blieben Wireframe, Style-Guide und Design
    # gesperrt.
    steps_confirmed         = Column(Text, default="{}")

    # Relationships
    lead = relationship("Lead", back_populates="projects", foreign_keys=[lead_id])
    checklists = relationship("ProjectChecklist", back_populates="project", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="project", cascade="all, delete-orphan")
    automations = relationship("AutomationLog", back_populates="project", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="project", uselist=False, cascade="all, delete-orphan")
    time_trackings = relationship("TimeTracking", back_populates="project", cascade="all, delete-orphan")


class ProjectChecklist(Base):
    """Checklists for each project phase."""
    __tablename__ = "project_checklists"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    phase = Column(Integer, nullable=False)  # 1-7
    item_key = Column(String(50), nullable=False)  # e.g., "AKQ-01"
    item_label = Column(String(255), nullable=False)  # German label
    responsible = Column(String(50), default="both")  # 'ki', 'human', 'both'
    is_critical = Column(Boolean, default=False)  # PFLICHT items
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    completed_by = Column(String(100))  # Username or "KI"
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="checklists")


class Communication(Base):
    """Track all communications (emails, calls, meetings)."""
    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    type = Column(String(50), nullable=False)  # email, call, meeting
    direction = Column(String(50), nullable=False)  # inbound, outbound
    channel = Column(String(100))  # e.g., "email", "phone", "whatsapp"
    subject = Column(String(255))
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_automated = Column(Boolean, default=False)  # KI-generated
    template_key = Column(String(100))  # e.g., "welcome", "day_5_followup"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="communications")


class Fehlerprotokoll(Base):
    """Was der Server nicht verarbeiten konnte — zusammengefasst.

    Luecke L-10: Produktiv gab es keine Fehlerauskunft. Der 500er beim Anlegen
    einer Lektion stand monatelang, ohne dass jemand davon wusste; die
    Oberflaeche verschluckte ihn, und ins Log sieht niemand taeglich.

    Zusammengefasst statt gesammelt: Gleiche Art an gleicher Stelle zaehlt
    hoch. Ein kaputter Endpunkt schreibt sonst tausende gleiche Zeilen, und
    eine unlesbare Liste ist so gut wie keine.

    Die Spur wird gekuerzt aufbewahrt — in einem Traceback koennen Werte aus
    Kundendaten stehen, und was nicht gebraucht wird, wird nicht gespeichert.
    """
    __tablename__ = "fehlerprotokoll"

    id = Column(Integer, primary_key=True, index=True)
    kennung = Column(String(64), index=True)     # Art + Pfad + erste Spurzeile
    art = Column(String(120))                    # TypeError, ProgrammingError, …
    pfad = Column(String(500))
    methode = Column(String(10))
    meldung = Column(Text, default="")
    spur = Column(Text, default="")
    benutzer_id = Column(Integer, nullable=True)
    anzahl = Column(Integer, default=1)
    zuerst = Column(DateTime, default=datetime.utcnow)
    zuletzt = Column(DateTime, default=datetime.utcnow, index=True)


class AutomationLog(Base):
    """Log of automation triggers and execution."""
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    automation_id = Column(String(100), nullable=False)  # e.g., "on_payment_received"
    trigger_event = Column(String(100), nullable=False)  # The event that triggered it
    executed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50))  # success, failed, skipped
    output_summary = Column(Text)  # Brief description of what happened
    error_message = Column(Text)  # If failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="automations")


class Customer(Base):
    """Post-project customer management and upsells."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # ── Nachgezogene Spalten ─────────────────────────────────────────
    # Siehe Lead: von `_run_migrations` angelegt, im Modell vergessen — jede
    # Zuweisung ging still verloren.
    pagespeed_mobile_score = Column(Integer, nullable=True)
    pagespeed_desktop_score = Column(Integer, nullable=True)
    pagespeed_lcp_mobile = Column(Float, nullable=True)
    pagespeed_cls_mobile = Column(Float, nullable=True)
    pagespeed_inp_mobile = Column(Float, nullable=True)
    pagespeed_fcp_mobile = Column(Float, nullable=True)
    pagespeed_checked_at = Column(DateTime, nullable=True)
    next_touchpoint_date = Column(DateTime)  # When to contact next
    next_touchpoint_type = Column(String(100))  # e.g., "maintenance_offer", "feature_request"
    upsell_status = Column(String(50), default="none")  # none, offered, accepted
    upsell_package = Column(String(255))  # e.g., "SEO-Paket", "Blog-Verwaltung"
    recurring_revenue = Column(Float, default=0.0)  # € / month
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # CMS connection
    cms_type               = Column(String(50),  nullable=True)
    cms_url                = Column(String(500),  nullable=True)
    cms_username           = Column(String(200),  nullable=True)
    cms_password_encrypted = Column(Text,         nullable=True)

    # Relationships
    project = relationship("Project", back_populates="customer")


class TimeTracking(Base):
    """Track hours spent on each project phase."""
    __tablename__ = "time_tracking"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    phase = Column(Integer)  # 1-7, or NULL for general project work
    logged_by = Column(String(100), nullable=False)  # Username or "KI"
    hours = Column(Float, nullable=False)
    activity_description = Column(String(255))
    logged_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="time_trackings")


class AuditResult(Base):
    """Website audit results based on Homepage Standard framework."""
    __tablename__ = "audit_results"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    # Gesetzt, wenn dieses Audit eine Eigenprüfung ist: die Qualitätsschleife
    # deployt eine selbst gebaute Seite als Vorschau und misst sie mit
    # demselben Katalog, den wir Kunden vorhalten. `website_url` zeigt dann auf
    # die Vorschau, nicht auf den Auftritt des Kunden.
    sitemap_page_id = Column(Integer, nullable=True, index=True)
    website_url = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    city = Column(String(100))
    trade = Column(String(100))

    # Async status: pending -> running -> completed / failed
    status = Column(String(50), default="pending")
    error_message = Column(Text)

    # Das Geheimnis, mit dem ein Interessent ohne Konto sein eigenes Ergebnis
    # abholt. Ohne das war die Kennung eine fortlaufende Zahl, und wer sie
    # hochzaehlte, las fremde Audits (L-52, 19.08.2026). Das Widget macht es
    # unter `/api/widget/report/{token}` seit jeher so.
    # Bestandsdaten haben keins und bleiben damit nur ueber eine Anmeldung
    # erreichbar — ein Audit von gestern holt niemand mehr ueber die
    # Landingpage ab.
    public_token = Column(String(64), nullable=True, index=True)

    # Scores (6 categories)
    total_score = Column(Integer, default=0)  # 0-100
    level = Column(String(50))  # Nicht konform, Bronze, Silber, Gold, Platin
    rc_score = Column(Integer, default=0)  # Rechtliche Compliance (max 30)
    tp_score = Column(Integer, default=0)  # Technische Performance (max 20)
    bf_score = Column(Integer, default=0)  # Barrierefreiheit (max 20)
    si_score = Column(Integer, default=0)  # Sicherheit & Datenschutz (max 15)
    se_score = Column(Integer, default=0)  # SEO & Sichtbarkeit (max 10)
    ux_score = Column(Integer, default=0)  # Inhalt & Nutzererfahrung (max 5)

    # Granular item scores (per-criterion)
    rc_impressum = Column(Integer, default=0)
    rc_datenschutz = Column(Integer, default=0)
    rc_cookie = Column(Integer, default=0)
    rc_bfsg = Column(Integer, default=0)
    rc_urheberrecht = Column(Integer, default=0)
    rc_ecommerce = Column(Integer, default=0)
    tp_lcp = Column(Integer, default=0)
    tp_cls = Column(Integer, default=0)
    tp_inp = Column(Integer, default=0)
    tp_mobile = Column(Integer, default=0)
    tp_bilder = Column(Integer, default=0)
    ho_anbieter = Column(Integer, default=0)
    ho_uptime = Column(Integer, default=0)
    ho_http = Column(Integer, default=0)
    ho_backup = Column(Integer, default=0)
    ho_cdn = Column(Integer, default=0)
    bf_kontrast = Column(Integer, default=0)
    bf_tastatur = Column(Integer, default=0)
    bf_screenreader = Column(Integer, default=0)
    bf_lesbarkeit = Column(Integer, default=0)
    si_ssl = Column(Integer, default=0)
    si_header = Column(Integer, default=0)
    si_drittanbieter = Column(Integer, default=0)
    si_formulare = Column(Integer, default=0)
    se_seo = Column(Integer, default=0)
    se_schema = Column(Integer, default=0)
    se_lokal = Column(Integer, default=0)
    ux_erstindruck = Column(Integer, default=0)
    ux_cta = Column(Integer, default=0)
    ux_navigation = Column(Integer, default=0)
    ux_vertrauen = Column(Integer, default=0)
    ux_content = Column(Integer, default=0)
    ux_kontakt = Column(Integer, default=0)

    # Kriterienkatalog ab 2026-08-11 (siehe services/audit_criteria.py).
    # JSON statt Einzelspalten, damit neue Kriterien keine Migration brauchen.
    # Die Einzelspalten oberhalb sind Altbestand und werden nicht mehr gefüllt.
    item_scores = Column(Text, default="{}")      # {kriterium: punkte}
    item_sources = Column(Text, default="{}")     # {kriterium: gemessen|abgeleitet|...}
    category_scores = Column(Text, default="[]")  # [{key, label, score, max, ...}]
    blockers = Column(Text, default="[]")         # K.-o.-Kriterien
    coverage = Column(Integer, default=0)         # Anteil erhobener Punkte in %
    collection_notes = Column(Text, default="{}") # warum eine Prüfung ausfiel

    # Über wie viele Seiten das Audit urteilt. Bis zum 21.08.2026 war es immer
    # genau eine — die Startseite. Ohne diese Zahl vergleicht jemand später
    # eine alte Note mit einer neuen, ohne zu merken, dass die eine über eine
    # Seite und die andere über zwanzig gefällt wurde. Die Vorgabe 1 ist für
    # Altzeilen deshalb keine Behelfszahl, sondern die Wahrheit.
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all`.
    seiten_geprueft = Column(Integer, default=1)
    seiten_gefunden = Column(Integer, nullable=True)

    # Wogegen bewertet wurde (Homepage Standard 2026.2, Branchenmodell). Die
    # Klasse entscheidet, welche Kriterien überhaupt gelten — ohne sie lässt
    # sich ein Bericht später weder erklären noch mit einem neueren vergleichen.
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all`.
    erkannte_branche = Column(String, default="")   # Freitext des Modells
    branchenklasse = Column(String, default="")     # K1…K6
    standard_version = Column(String, default="")   # Fassung des Standards

    # Raw check results
    ssl_ok = Column(Boolean, default=False)
    impressum_ok = Column(Boolean, default=False)
    datenschutz_ok = Column(Boolean, default=False)
    lcp_value = Column(Float)  # seconds
    cls_value = Column(Float)
    inp_value = Column(Float)  # ms
    mobile_score = Column(Integer)  # 0-100
    performance_score = Column(Integer)  # 0-100

    # Scraped data (auto-detected from website)
    scraped_phone = Column(String(50), default="")
    scraped_email = Column(String(255), default="")
    scraped_description = Column(Text, default="")
    screenshot_base64 = Column(Text, default="")

    # AI analysis
    ai_summary = Column(Text)  # 3-5 sentences plain language
    top_issues = Column(Text)  # JSON array of top issues
    recommendations = Column(Text)  # JSON array of recommendations

    # GEO / KI-Sichtbarkeit
    llms_txt = Column(Boolean, default=False)
    robots_ai_friendly = Column(Boolean, default=False)
    structured_data = Column(Boolean, default=False)
    ai_mentions = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", backref="audits", foreign_keys=[lead_id])


class User(Base):
    """User accounts with roles and 2FA support."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)

    # Profile
    first_name = Column(String(100), default="")
    last_name = Column(String(100), default="")
    phone = Column(String(30), default="")
    avatar_url = Column(String(500), default="")

    # Role: admin | auditor | nutzer | kunde
    role = Column(String(20), default="nutzer")

    # Auditor-specific
    position = Column(String(100), default="")
    signature_data = Column(Text, default="")

    # Customer link
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)

    # 2FA
    totp_secret = Column(String(64), nullable=True)
    totp_enabled = Column(Boolean, default=False)
    backup_codes = Column(Text, default="")

    # OAuth
    google_id = Column(String(255), nullable=True)
    apple_id = Column(String(255), nullable=True)
    oauth_provider = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verify_token = Column(String(100), nullable=True)
    password_reset_token = Column(String(100), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True)


class UserSession(Base):
    """Active login sessions."""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True)
    ip_address = Column(String(50), default="")
    user_agent = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_valid = Column(Boolean, default=True)


class SystemSettings(Base):
    """Key-value system settings."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(Integer, nullable=True)


class RolePermission(Base):
    """Permission assignments per role."""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False)
    permission = Column(String(50), nullable=False)
    is_allowed = Column(Boolean, default=True)

    # Ein Recht je Rolle, genau einmal. `services/rechte.hat_recht` liest mit
    # `.first()` und ohne Sortierung — zwei Zeilen mit verschiedenem
    # `is_allowed` haetten die Antwort dem Zufall ueberlassen, und ein
    # entzogenes Recht waere still zurueckgekommen (L-05, 21.08.2026).
    # Der Bestand wird in `migrations_runtime.py::run_migrations` zusammengefuehrt.
    __table_args__ = (
        UniqueConstraint("role", "permission", name="uq_role_permission"),
    )


class Briefing(Base):
    """Briefing questionnaire for web design projects."""
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, unique=True)
    # Legacy JSON sections (used by BriefingTab)
    projektrahmen = Column(Text, default='{}')
    positionierung = Column(Text, default='{}')
    zielgruppe = Column(Text, default='{}')
    wettbewerb = Column(Text, default='{}')
    inhalte = Column(Text, default='{}')
    funktionen = Column(Text, default='{}')
    branding = Column(Text, default='{}')
    struktur = Column(Text, default='{}')
    hosting = Column(Text, default='{}')
    seo = Column(Text, default='{}')
    projektplan = Column(Text, default='{}')
    freigaben = Column(Text, default='{}')
    # Flat project briefing fields
    project_id = Column(Integer, nullable=True)
    gewerk = Column(Text)
    leistungen = Column(Text)
    einzugsgebiet = Column(Text)
    usp = Column(Text)
    mitbewerber = Column(Text)
    vorbilder = Column(Text)
    farben = Column(Text)
    wunschseiten = Column(Text)
    stil = Column(Text)
    logo_vorhanden = Column(Boolean, default=False)
    fotos_vorhanden = Column(Boolean, default=False)
    sonstige_hinweise = Column(Text)
    status = Column(String(50), default='entwurf')
    hauptziel = Column(Text)
    aktionen = Column(Text)
    typischer_kunde = Column(Text)
    haeufige_anfrage = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)






















class UserCard(Base):
    """Unified contact card — merges leads + customer management (Part 1/3)."""
    __tablename__ = "usercards"

    id = Column(Integer, primary_key=True, index=True)

    # Core contact info (from leads)
    company_name  = Column(String(255), default="")
    contact_name  = Column(String(255), nullable=True, default=None)
    phone         = Column(String(20),  nullable=True, default=None)
    email         = Column(String(255), nullable=True, default=None)
    website_url   = Column(String(500), default="")
    city          = Column(String(100), nullable=True, default=None)
    trade         = Column(String(100), nullable=True, default=None)
    lead_source   = Column(String(100), default="")
    status        = Column(String(50),  default="new")
    analysis_score = Column(Integer, default=0)
    geo_score      = Column(Integer, default=0)
    notes          = Column(Text, nullable=True, default=None)
    website_screenshot = Column(Text, nullable=True, default=None)

    # Address
    street       = Column(String(255), default="")
    house_number = Column(String(20),  default="")
    postal_code  = Column(String(10),  default="")

    # Company details
    legal_form      = Column(String(50),  default="")
    vat_id          = Column(String(30),  default="")
    register_number = Column(String(50),  default="")
    register_court  = Column(String(100), default="")
    ceo_first_name  = Column(String(100), default="")
    ceo_last_name   = Column(String(100), default="")
    display_name    = Column(String(255), default="")

    # Portal access
    customer_token            = Column(String, unique=True, nullable=True)
    customer_token_created_at = Column(DateTime, nullable=True)

    # PageSpeed Insights
    pagespeed_mobile_score  = Column(Integer,  nullable=True)
    pagespeed_desktop_score = Column(Integer,  nullable=True)
    pagespeed_lcp_mobile    = Column(Float,    nullable=True)
    pagespeed_cls_mobile    = Column(Float,    nullable=True)
    pagespeed_inp_mobile    = Column(Float,    nullable=True)
    pagespeed_fcp_mobile    = Column(Float,    nullable=True)
    pagespeed_checked_at    = Column(DateTime, nullable=True)

    # Customer management fields (from customers table)
    next_touchpoint_date = Column(DateTime, nullable=True)
    next_touchpoint_type = Column(String(100), nullable=True)
    upsell_status        = Column(String(50),  default="none")
    upsell_package       = Column(String(255), nullable=True)
    recurring_revenue    = Column(Float, default=0.0)

    # Migration tracking
    legacy_type = Column(String(20), default="lead")   # 'lead' | 'customer'

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)






# `Course` (Tabelle `courses`) ist am 19.08.2026 entfallen. Es war das zweite
# von zwei Kurssystemen — ohne Module, ohne Lektionen, ohne Fortschritt: nur
# `chapter_count`, `participant_count` und `duration_minutes` als mitgeführte
# Zahlen, die niemand nachrechnete. Die Akademie (`AcademyCourse` und
# Nachbarn) kann alles davon und mehr.
#
# Die Tabelle bleibt vorerst in der Datenbank stehen — ein DROP ist nicht
# umkehrbar, und `services/kurse_zusammenfuehren.py` liest sie bei jedem Start,
# um von Hand angelegte Kurse nachzuholen. Sie fällt, wenn feststeht, dass
# nichts mehr darin ist.










class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True)
    lead_id     = Column(Integer, ForeignKey("leads.id"), nullable=False)
    sender_role = Column(String, nullable=False)   # "admin" | "kunde"
    sender_name = Column(String)                   # z.B. "David" oder Firmenname
    channel     = Column(String, default="in_app") # "in_app" | "email"
    subject     = Column(String)                   # nur bei channel="email"
    content     = Column(Text, nullable=False)
    is_read     = Column(Boolean, default=False)
    read_at     = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


# ── KAS Website (KOMPAGNON-eigene Seiten) ─────────────────────────────────────





class GeoAnalysis(Base):
    __tablename__ = "geo_analyses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    geo_score_total = Column(Integer, default=0)
    llms_txt_score = Column(Integer, default=0)
    robots_ai_score = Column(Integer, default=0)
    structured_data_score = Column(Integer, default=0)
    content_depth_score = Column(Integer, default=0)
    local_signal_score = Column(Integer, default=0)

    raw_checks = Column(JSONB, default=dict)
    recommendations = Column(JSONB, default=list)
    generated_files = Column(JSONB, default=dict)

    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    upsell_active = Column(Boolean, default=False)
    upsell_price = Column(Float, nullable=True)

    # Monitoring
    last_monitored_at = Column(DateTime, nullable=True)
    monitoring_history = Column(JSONB, default=list)
    monitoring_enabled = Column(Boolean, default=True)
    last_score_change = Column(Integer, nullable=True)

    # Ob eine KI den Betrieb auf eine Kundenfrage hin wirklich nennt (L-58 b).
    # Die Spalten legt `migrations_runtime.py::run_migrations` an, nicht `create_all` —
    # siehe die Nachbarn oben. NULL heisst „nie gelaufen", nicht „nicht
    # gefunden": Der Lauf kostet Geld und laeuft nur auf Anforderung.
    ki_sichtbarkeit = Column(JSONB, nullable=True)
    ki_sichtbarkeit_am = Column(DateTime, nullable=True)
    # Je Lauf die Trefferzahl je System — ohne die Antworttexte, die
    # den Verlauf in einem Jahr unlesbar machten (L-85). Nach oben
    # begrenzt: `services/ki_sichtbarkeit.VERLAUF_MAX`.
    ki_sichtbarkeit_verlauf = Column(JSONB, nullable=True)

    # Stripe Subscription
    stripe_subscription_id = Column(String(200), nullable=True)
    stripe_customer_id = Column(String(200), nullable=True)
    stripe_price_id = Column(String(200), nullable=True)
    subscription_status = Column(String(50), nullable=True)
    subscription_started_at = Column(DateTime, nullable=True)
    subscription_canceled_at = Column(DateTime, nullable=True)
    subscription_current_period_end = Column(DateTime, nullable=True)


class ComponentLibrary(Base):
    """
    Wireframe-Block-Bibliothek (41 HTML+Tailwind-Templates).

    Wird vom KI-Agent (siehe routers/component_library.py — Schritt D)
    zur Wireframe-Generation genutzt. HTML-Quelle liegt im Repo unter
    kompagnon/frontend/src/components/library/{slug}.html, Seed via
    kompagnon/backend/seeds/seed_component_library.py.

    Kategorien: NAV, HERO, LEIST, TRUST, SEO, CTA, HW, FOOT.
    """
    __tablename__ = "component_library"

    id              = Column(Integer, primary_key=True, index=True)
    slug            = Column(String(50), unique=True, nullable=False, index=True)
    name            = Column(String(100), nullable=False)
    category        = Column(String(50), nullable=False, index=True)
    tags            = Column(JSONB, default=list)
    html_template   = Column(Text, nullable=False)
    # slots: [{"key": "headline", "label": "Hauptueberschrift", "type": "text", "default": "..."}, ...]
    slots           = Column(JSONB, default=list)
    # "approved" | "draft". Von Claude erzeugte Bloecke starten als Entwurf und
    # sind fuer den Wireframe-Generator unsichtbar, bis jemand sie freigibt —
    # sonst landet ungeprueftes Markup auf einer Kundenseite.
    #
    # server_default ist Pflicht, nicht Kosmetik: `default=` wirkt nur beim
    # ORM-Insert. Der Bibliotheks-Seed schreibt per rohem SQL ohne diese
    # Spalte — ohne DB-seitigen Default kaemen dort NULL-Werte an, und die
    # sind unsichtbar (siehe _nur_freigegebene in routers/component_library.py).
    status          = Column(String(20), default="approved",
                             server_default=sa_text("'approved'"), index=True)
    ki_prompt_hint  = Column(Text, nullable=True)
    preview_note    = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """DB-Session Dependency — mit sauberem Cleanup."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()






# ── Die Phase folgt dem Status ────────────────────────────────────────────────
#
# Als Ereignis und nicht als Zeile in jedem Schreibweg: `Lead.status` wird an
# fuenf Stellen im Backend gesetzt und ueber `PATCH /api/leads/{id}` per
# `setattr` an beliebig vielen weiteren. Wer die Phase dort ueberall von Hand
# mitpflegen muesste, vergaesse sie — und ein Feld, das manchmal stimmt, ist
# schlechter als keines.
#
# Gefunden am 19.08.2026 beim Lifecycle-Umbau.
from sqlalchemy import event as _sa_event  # noqa: E402


@_sa_event.listens_for(Lead.status, "set", propagate=True)
def _phase_mitziehen(ziel, wert, alt, initiator):
    """Setzt `lifecycle_phase` neu, sobald `status` gesetzt wird."""
    from services.lebenszyklus import phase_zu

    ziel.lifecycle_phase = phase_zu(wert)


@_sa_event.listens_for(Lead, "before_insert")
def _phase_beim_anlegen(mapper, verbindung, ziel):
    """Auch ein Betrieb, dem niemand einen Status gibt, bekommt seine Phase.

    Der Haken oben greift nur, wenn `status` **zugewiesen** wird. Wird ein
    Lead ohne Status angelegt, setzt erst die Datenbank die Vorgabe `new` —
    und die Phase bliebe leer, bis der naechste Nachtrag laeuft.
    """
    from services.lebenszyklus import phase_zu

    if ziel.lifecycle_phase is None:
        ziel.lifecycle_phase = phase_zu(ziel.status or "new")


# ── Die Modelle der Randbereiche (L-25, 22.08.2026) ──────────────────
#
# Sie stehen in eigenen Dateien, **muessen aber hier geladen werden**:
# Die `relationship()`-Aufrufe nennen ihre Gegenseite als Zeichenkette,
# und SQLAlchemy loest den Namen erst beim ersten Zugriff auf. Fehlt eine
# Datei, faellt das nicht beim Start auf, sondern bei irgendeiner Abfrage.
from modelle_akademie import *      # noqa: E402,F401,F403
from modelle_assistent import *     # noqa: E402,F401,F403
from modelle_crawler import *       # noqa: E402,F401,F403
from modelle_kas import *           # noqa: E402,F401,F403
from modelle_widget import *        # noqa: E402,F401,F403