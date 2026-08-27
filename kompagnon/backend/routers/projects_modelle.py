"""Die Datenformate der Projekt-Schnittstelle (L-25).

**Warum eigene Datei, 23.08.2026.** `routers/projects.py` hatte 1.006 Zeilen,
und 165 davon waren acht Pydantic-Modelle am Stueck — die Beschreibung dessen,
was hinein- und herausgeht, vor der ersten Route.

Sie stehen hier, weil sie **keine Logik** enthalten und weil man sie beim
Lesen einer Route nachschlagen will, nicht durchblaettern muss. Vor dem
Schnitt geprueft: **keines** der acht wird ausserhalb von `projects.py`
verwendet — der Umzug beruehrt also nichts anderes.

`ProjekteLoeschenRequest` und `ApprovalRequest` sind bewusst **nicht** hier:
Sie gehoeren je zu einer einzigen Route und stehen bei ihr.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    id: int
    lead_id: Optional[int] = None
    name: Optional[str] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[int] = None
    website_url: Optional[str] = None
    cms_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    wz_code: Optional[str] = None
    wz_title: Optional[str] = None
    package_type: Optional[str] = None
    payment_status: Optional[str] = None
    desired_pages: Optional[str] = None
    top_problems: Optional[str] = None
    customer_email: Optional[str] = None
    hosting_provider: Optional[str] = None
    domain_registrar: Optional[str] = None
    nameserver1: Optional[str] = None
    nameserver2: Optional[str] = None
    ftp_credentials: Optional[str] = None
    wp_admin_url: Optional[str] = None
    hosting_notes: Optional[str] = None
    fixed_price: Optional[float] = None
    actual_hours: Optional[float] = None
    hourly_rate: Optional[float] = None
    ai_tool_costs: Optional[float] = None
    margin_percent: Optional[float] = None
    scope_creep_flags: Optional[int] = None
    pagespeed_mobile: Optional[int] = None
    pagespeed_desktop: Optional[int] = None
    analysis_score: Optional[int] = None
    audit_score: Optional[int] = None
    has_logo: Optional[bool] = None
    has_briefing: Optional[bool] = None
    has_photos: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    start_date: datetime = None
    target_go_live: datetime = None
    actual_go_live: datetime = None
    go_live_date: datetime = None
    created_at: datetime = None

    class Config:
        from_attributes = True


class TimeLogRequest(BaseModel):
    hours: float
    phase: int = None
    #: **Freiwillig seit dem 26.08.2026.** Stand hier als Pflichtfeld: Wer
    #: eintippt, wer gearbeitet hat, kann eintippen, was er will — dieselbe
    #: Schwaeche, die bei `POST /{id}/abnahme` der Grund war, den Endpunkt
    #: ganz zu entfernen. Fehlt der Wert, traegt der Server den angemeldeten
    #: Benutzer ein.
    logged_by: str = None
    activity_description: str = None


class ChecklistItemResponse(BaseModel):
    id: int
    phase: int
    item_key: str
    item_label: str
    responsible: str
    is_critical: bool
    is_completed: bool
    completed_at: datetime = None
    completed_by: str = None

    class Config:
        from_attributes = True


class ChecklistItemUpdate(BaseModel):
    is_completed: bool
    completed_by: str = None


class PhaseChangeRequest(BaseModel):
    new_status: str


class ProjectUpdateRequest(BaseModel):
    customer_name: str = None
    website_url: str = None
    cms_type: str = None
    contact_name: str = None
    contact_phone: str = None
    contact_email: str = None
    go_live_date: str = None        # ISO date string, e.g. "2025-09-01"
    package_type: str = None
    payment_status: str = None
    desired_pages: str = None
    has_logo: bool = None
    has_briefing: bool = None
    has_photos: bool = None
    pagespeed_mobile: int = None
    pagespeed_desktop: int = None
    audit_score: int = None
    audit_level: str = None
    top_problems: str = None
    industry: str = None
    wz_code: str = None
    wz_title: str = None
    email_notifications_enabled: bool = None
    customer_email: str = None
    fixed_price: float = None
    target_go_live: str = None
    status: str = None
    current_phase: int = None
    hosting_provider: str = None
    domain_registrar: str = None
    nameserver1: str = None
    nameserver2: str = None
    ftp_credentials: str = None
    wp_admin_url: str = None
    hosting_notes: str = None


class MarginResponse(BaseModel):
    human_hours: float
    human_costs: float
    ai_tool_costs: float
    total_costs: float
    margin_eur: float
    margin_percent: float
    hours_remaining_at_target: float
    status: str  # green, yellow, red
    alert: bool
    target_margin: float
    min_acceptable_margin: float


class LeistungsseitenCreate(BaseModel):
    """Fragebogen-Eingabe fuer eine neue Leistungsseite (Teil 1 Stub).

    Pflichtfelder werden client-seitig im Wizard validiert; server-seitig
    sind alle Felder optional, damit Teil-2-Erweiterungen problemlos moeglich
    sind und kein 422 den Stub-Save blockiert.
    """
    # Schritt 1 — Leistung definieren
    leistung: str = ""
    gebiet: str = ""
    zielgruppe: str = ""
    # Schritt 2 — Zielkunde & Problem
    idealer_kunde: str = ""
    problem: str = ""
    problem_folgen: str = ""
    # Schritt 3 — USP & Preis
    usp: str = ""
    einstiegspreis: str = ""
    inkludiert: str = ""
    # Schritt 4 — Beweis & Vertrauen
    referenzen: str = ""
    projekt_anzahl: str = ""
    kundenstimmen: str = ""
    zertifikate: str = ""
    # Schritt 5 — Kontakt & CTA
    kontakt_kanal: str = ""
    telefon: str = ""
    cta_text: str = ""
    dringlichkeit: str = ""
