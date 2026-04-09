"""
SQLAlchemy database setup and models for KOMPAGNON system.
"""
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError
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
        pool_size=2,              # Lean for Render free tier
        max_overflow=3,
        pool_timeout=60,          # Wait up to 60s for free connection
        connect_args={
            "connect_timeout": 30,   # Free tier DB can take up to 30s to wake
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 3,
            "options": "-c statement_timeout=30000",  # 30s query timeout
        },
    )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Lead(Base):
    """Lead model for sales pipeline."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), default="")
    contact_name = Column(String(255), nullable=True, default=None)
    phone = Column(String(20), nullable=True, default=None)
    mobile = Column(String(20), nullable=True, default=None)
    email = Column(String(255), nullable=True, default=None)
    website_url = Column(String(500), default="")
    city = Column(String(100), nullable=True, default=None)
    trade = Column(String(100), nullable=True, default=None)
    lead_source = Column(String(100), default="")
    status = Column(String(50), default="new")
    analysis_score = Column(Integer, default=0)
    geo_score = Column(Integer, default=0)
    notes = Column(Text, nullable=True, default=None)
    website_screenshot = Column(Text, nullable=True, default=None)

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

    # Domain check
    domain_reachable = Column(Boolean)
    domain_status_code = Column(Integer)
    domain_checked_at = Column(DateTime)

    # Go-Live PageSpeed after
    pagespeed_after_mobile = Column(Integer)
    pagespeed_after_desktop = Column(Integer)

    # Screenshots before/after
    screenshot_before       = Column(Text)
    screenshot_before_date  = Column(DateTime)
    screenshot_after        = Column(Text)
    screenshot_after_date   = Column(DateTime)
    screenshot_url_before   = Column(String(500))
    screenshot_url_after    = Column(String(500))

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
    gewerk = Column(String(100))
    leistungen = Column(Text)
    einzugsgebiet = Column(String(100))
    usp = Column(Text)
    mitbewerber = Column(Text)
    vorbilder = Column(Text)
    farben = Column(String(100))
    wunschseiten = Column(Text)
    stil = Column(String(50))
    logo_vorhanden = Column(Boolean, default=False)
    fotos_vorhanden = Column(Boolean, default=False)
    sonstige_hinweise = Column(Text)
    status = Column(String(50), default='entwurf')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AcademyCourse(Base):
    """Academy course."""
    __tablename__ = "academy_courses"
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default='')
    thumbnail_url = Column(String(500), default='')
    is_published = Column(Boolean, default=False)
    target_audience = Column(String(20), default='both')   # 'customer'|'employee'|'both'
    category = Column(String(100), default='')
    category_color = Column(String(50), default='primary')
    audience = Column(String(20), default='employee')
    formats = Column(Text, default='["text"]')
    linear_progress = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AcademyChecklistItem(Base):
    """Checklist item for an academy course."""
    __tablename__ = "academy_checklist_items"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    label = Column(String(500), nullable=False)
    sort_order = Column(Integer, default=0)


class AcademyModule(Base):
    """Module within an academy course."""
    __tablename__ = "academy_modules"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)


class AcademyLesson(Base):
    """Lesson within a module."""
    __tablename__ = "academy_lessons"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey('academy_modules.id', ondelete='CASCADE'), nullable=False)
    title = Column(String(255), nullable=False)
    position = Column(Integer, default=0)
    type = Column(String(20), default='text')         # 'video'|'text'|'quiz'
    content_text = Column(Text, default='')
    content_url = Column(String(500), default='')
    video_url = Column(String(500), default='')
    file_url = Column(String(500), default='')
    duration_minutes = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)


class AcademyLessonProgress(Base):
    """User progress on a lesson (legacy)."""
    __tablename__ = "academy_lesson_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)


class AcademyProgress(Base):
    """User progress per lesson (with quiz score)."""
    __tablename__ = "academy_progress"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'))
    completed_at = Column(DateTime, nullable=True)
    score = Column(Float, nullable=True)


class AcademyCertificate(Base):
    """Course completion certificate."""
    __tablename__ = "academy_certificates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'))
    issued_at = Column(DateTime, default=datetime.utcnow)
    certificate_code = Column(String(64), unique=True, nullable=False)


class AcademyQuizQuestion(Base):
    """Quiz question belonging to a lesson."""
    __tablename__ = "academy_quiz_questions"
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('academy_lessons.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    answers_json = Column(Text, default='[]')   # [{text, is_correct}]
    sort_order = Column(Integer, default=0)


class AcademyCustomerAccess(Base):
    """Which courses a customer (lead) has been granted access to."""
    __tablename__ = "academy_customer_access"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey('academy_courses.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, nullable=True)


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


class CrawlJob(Base):
    """Background crawl job."""
    __tablename__ = "crawl_jobs"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=True)
    status = Column(String(20), default='pending')   # pending|running|completed|failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_urls = Column(Integer, default=0)


class CrawlResult(Base):
    """Single URL result from a crawl job."""
    __tablename__ = "crawl_results"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, nullable=True)
    job_id = Column(Integer, ForeignKey('crawl_jobs.id', ondelete='CASCADE'), nullable=True)
    url = Column(String(2000), nullable=False)
    status_code = Column(Integer, nullable=True)
    depth = Column(Integer, default=0)
    load_time = Column(Float, nullable=True)
    crawled_at = Column(DateTime, default=datetime.utcnow)


class Course(Base):
    """Internal / customer / product training courses."""
    __tablename__ = "courses"
    id                = Column(Integer, primary_key=True, index=True)
    title             = Column(String(255), nullable=False)
    description       = Column(Text, default="")
    category          = Column(String(50), default="intern")   # intern | kunde | produkt
    thumbnail_color   = Column(String(20), default="#008eaa")
    chapter_count     = Column(Integer, default=0)
    participant_count = Column(Integer, default=0)
    duration_minutes  = Column(Integer, default=0)
    created_at        = Column(DateTime, default=datetime.utcnow)
    created_by        = Column(Integer, ForeignKey("users.id"), nullable=True)


class ProjectScrapedPage(Base):
    __tablename__ = "project_scraped_pages"
    id                = Column(Integer, primary_key=True)
    project_id        = Column(Integer, ForeignKey("projects.id"), nullable=False)
    url               = Column(String, nullable=False)
    page_title        = Column(String)
    meta_description  = Column(Text)
    h1                = Column(String)
    h2_list           = Column(Text)       # JSON-Array als String
    paragraphs        = Column(Text)       # JSON-Array als String
    images            = Column(Text)       # JSON-Array {src, alt} als String
    contact_phone     = Column(String)
    contact_email     = Column(String)
    contact_address   = Column(Text)
    scraped_at        = Column(DateTime, default=datetime.utcnow)


class ProjectScrapeJob(Base):
    __tablename__ = "project_scrape_jobs"
    id           = Column(Integer, primary_key=True)
    project_id   = Column(Integer, nullable=False)
    status       = Column(String, default="pending")  # pending/running/done/failed
    total_pages  = Column(Integer, default=0)
    started_at   = Column(DateTime)
    completed_at = Column(DateTime)


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


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for getting DB session with retry on connection errors."""
    db = SessionLocal()
    try:
        yield db
    except OperationalError:
        db.close()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    finally:
        db.close()
