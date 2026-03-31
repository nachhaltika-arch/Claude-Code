"""
SQLAlchemy database setup and models for KOMPAGNON system.
"""
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from decimal import Decimal

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Lead(Base):
    """Lead model for sales pipeline."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    email = Column(String(255), nullable=False)
    website_url = Column(String(500))
    city = Column(String(100), nullable=False)
    trade = Column(String(100), nullable=False)  # Gewerk (e.g., "Klempner", "Elektrik")
    lead_source = Column(String(100))  # e.g., "Google", "Empfehlung", "Kaltakquise"
    status = Column(String(50), default="new")  # new, contacted, qualified, proposal_sent, won, lost
    analysis_score = Column(Integer, default=0)  # 0-100
    geo_score = Column(Integer, default=0)  # 0-100
    notes = Column(Text)
    website_screenshot = Column(Text, default="")

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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="lead", cascade="all, delete-orphan")


class Project(Base):
    """Project model for WordPress website builds."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
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

    # Relationships
    lead = relationship("Lead", back_populates="projects")
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
    next_touchpoint_date = Column(DateTime)  # When to contact next
    next_touchpoint_type = Column(String(100))  # e.g., "maintenance_offer", "feature_request"
    upsell_status = Column(String(50), default="none")  # none, offered, accepted
    upsell_package = Column(String(255))  # e.g., "SEO-Paket", "Blog-Verwaltung"
    recurring_revenue = Column(Float, default=0.0)  # € / month
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    website_url = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255))
    city = Column(String(100))
    trade = Column(String(100))

    # Async status: pending -> running -> completed / failed
    status = Column(String(50), default="pending")
    error_message = Column(Text)

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

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    lead = relationship("Lead", backref="audits")


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


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting DB session in FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
