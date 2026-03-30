"""
Lead Management API routes.
POST /api/leads/ - Create lead
GET /api/leads/ - List all leads
POST /api/leads/{id}/analyze - Run lead analyst agent
POST /api/leads/{id}/convert - Convert to project
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from database import Lead, Project, AuditResult, get_db
from seed_checklists import create_project_checklists
from agents.lead_analyst import LeadAnalystAgent
import csv
import io
import json
import os

router = APIRouter(prefix="/api/leads", tags=["leads"])


class LeadCreate(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = None
    city: str = ""
    trade: str = ""
    lead_source: str = None
    notes: str = None


class LeadUpdate(BaseModel):
    status: str = None
    analysis_score: int = None
    geo_score: int = None
    notes: str = None


class LeadResponse(BaseModel):
    id: int
    company_name: str
    contact_name: str
    phone: str
    email: str
    website_url: str = None
    city: str
    trade: str
    lead_source: str = None
    status: str
    analysis_score: int
    geo_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LeadConvertRequest(BaseModel):
    fixed_price: float = 2000.0
    hourly_rate: float = 45.0
    ai_tool_costs: float = 50.0
    assigned_person: str = "KOMPAGNON-Team"


@router.post("/", response_model=LeadResponse)
def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """Create a new lead in the pipeline."""
    db_lead = Lead(
        company_name=lead.company_name,
        contact_name=lead.contact_name,
        phone=lead.phone,
        email=lead.email,
        website_url=lead.website_url,
        city=lead.city,
        trade=lead.trade,
        lead_source=lead.lead_source,
        notes=lead.notes,
        status="new",
    )
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.get("/", response_model=list[LeadResponse])
def list_leads(
    status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """List all leads, optionally filtered by status."""
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    leads = query.offset(skip).limit(limit).all()
    return leads


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a specific lead by ID."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, lead: LeadUpdate, db: Session = Depends(get_db)):
    """Update a lead."""
    db_lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not db_lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status:
        db_lead.status = lead.status
    if lead.analysis_score is not None:
        db_lead.analysis_score = lead.analysis_score
    if lead.geo_score is not None:
        db_lead.geo_score = lead.geo_score
    if lead.notes:
        db_lead.notes = lead.notes

    db_lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_lead)
    return db_lead


@router.post("/{lead_id}/analyze")
def analyze_lead(lead_id: int, db: Session = Depends(get_db)):
    """Run lead analyst agent on a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    try:
        # Initialize agent
        use_mock = not os.getenv("ANTHROPIC_API_KEY")
        agent = LeadAnalystAgent() if not use_mock else None

        if agent:
            result = agent.analyze_lead(
                website_url=lead.website_url or "https://example.com",
                company_name=lead.company_name,
                city=lead.city,
                trade=lead.trade,
            )
        else:
            # Use mock for testing
            result = LeadAnalystAgent.get_mock_analysis(lead.company_name, lead.trade)

        # Store scores
        lead.analysis_score = result.get("overall_score", 0)
        lead.geo_score = result.get("geo_visibility_score", 0)
        lead.status = "qualified" if result.get("overall_score", 0) >= 60 else "contacted"
        db.commit()

        return {
            "lead_id": lead_id,
            "analysis": result,
            "updated_lead": {
                "analysis_score": lead.analysis_score,
                "geo_score": lead.geo_score,
                "status": lead.status,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/{lead_id}/convert")
def convert_lead(
    lead_id: int,
    convert_request: LeadConvertRequest,
    db: Session = Depends(get_db),
):
    """Convert lead to a project (create Project)."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Check if already converted
    existing_project = db.query(Project).filter(Project.lead_id == lead_id).first()
    if existing_project:
        raise HTTPException(status_code=400, detail="Lead already converted to project")

    try:
        # Create project
        project = Project(
            lead_id=lead_id,
            status="phase_1",
            start_date=datetime.utcnow(),
            fixed_price=convert_request.fixed_price,
            hourly_rate=convert_request.hourly_rate,
            ai_tool_costs=convert_request.ai_tool_costs,
        )
        db.add(project)
        db.flush()  # Get the project ID

        # Create checklists for all 7 phases
        create_project_checklists(db, project.id)

        # Update lead status
        lead.status = "won"
        db.commit()
        db.refresh(project)

        return {
            "project_id": project.id,
            "lead_id": lead_id,
            "status": project.status,
            "created_at": project.created_at,
            "message": f"Lead converted to Project #{project.id}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


# ===== IMPORT ENDPOINTS =====

class ManualLeadImport(BaseModel):
    company_name: str
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    website_url: str = ""
    city: str = ""
    trade: str = ""


@router.post("/import/csv")
async def import_leads_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import leads from a CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien erlaubt.")

    try:
        content = await file.read()

        # Encoding erkennen
        try:
            text = content.decode("utf-8-sig")  # BOM entfernen
        except UnicodeDecodeError:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

        # Delimiter manuell erkennen — KEIN Sniffer
        first_line = text.split("\n")[0] if text else ""

        if ";" in first_line:
            delimiter = ";"
        elif "\t" in first_line:
            delimiter = "\t"
        else:
            delimiter = ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        imported = 0
        errors = 0
        skipped = 0

        for row in reader:
            try:
                # Spaltennamen bereinigen
                clean_row = {}
                for k, v in row.items():
                    if k:
                        clean_key = k.strip().lower().lstrip('\ufeff')
                        clean_row[clean_key] = v.strip() if v else ""

                # Firmenname ist Pflicht
                company = (
                    clean_row.get("company_name")
                    or clean_row.get("firmenname")
                    or clean_row.get("firma")
                    or clean_row.get("unternehmen")
                    or clean_row.get("name")
                    or ""
                )

                if not company:
                    skipped += 1
                    continue

                lead = Lead(
                    company_name=company,
                    contact_name=(
                        clean_row.get("contact_name")
                        or clean_row.get("ansprechpartner")
                        or clean_row.get("kontakt")
                        or ""
                    ),
                    phone=(
                        clean_row.get("phone")
                        or clean_row.get("telefon")
                        or clean_row.get("tel")
                        or ""
                    ),
                    email=(
                        clean_row.get("email")
                        or clean_row.get("e-mail")
                        or clean_row.get("mail")
                        or ""
                    ),
                    website_url=(
                        clean_row.get("website_url")
                        or clean_row.get("website")
                        or clean_row.get("url")
                        or clean_row.get("homepage")
                        or ""
                    ),
                    city=(
                        clean_row.get("city")
                        or clean_row.get("stadt")
                        or clean_row.get("ort")
                        or ""
                    ),
                    trade=(
                        clean_row.get("trade")
                        or clean_row.get("gewerk")
                        or clean_row.get("branche")
                        or "Sonstiges"
                    ),
                    lead_source="csv_import",
                    status="new",
                )
                db.add(lead)
                imported += 1

            except Exception:
                errors += 1
                continue

        db.commit()

        return {
            "success": True,
            "imported": imported,
            "errors": errors,
            "skipped": skipped,
            "message": (
                f"{imported} Kontakte erfolgreich importiert"
                + (f", {skipped} übersprungen" if skipped > 0 else "")
                + (f", {errors} Fehler" if errors > 0 else "")
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Import fehlgeschlagen: {str(e)}",
        )


@router.post("/import/manual", response_model=LeadResponse)
def import_lead_manual(
    lead_data: ManualLeadImport,
    db: Session = Depends(get_db),
):
    """Import a single lead manually."""
    if not lead_data.company_name.strip():
        raise HTTPException(status_code=400, detail="Firmenname ist Pflichtfeld.")

    lead = Lead(
        company_name=lead_data.company_name.strip(),
        contact_name=lead_data.contact_name.strip(),
        phone=lead_data.phone.strip(),
        email=lead_data.email.strip(),
        website_url=lead_data.website_url.strip(),
        city=lead_data.city.strip(),
        trade=lead_data.trade.strip(),
        lead_source="Manuell",
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id}/audits")
def get_lead_audits(lead_id: int, db: Session = Depends(get_db)):
    """Get all audits linked to a lead, newest first."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    audits = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id, AuditResult.status == "completed")
        .order_by(AuditResult.created_at.desc())
        .all()
    )

    results = []
    for a in audits:
        try:
            top_issues = json.loads(a.top_issues) if a.top_issues else []
        except (json.JSONDecodeError, TypeError):
            top_issues = []
        results.append({
            "id": a.id,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "total_score": a.total_score,
            "level": a.level,
            "website_url": a.website_url,
            "top_issues": top_issues,
            "ai_summary": a.ai_summary,
        })
    return results
