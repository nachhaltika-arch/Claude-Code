"""
Customer Management API routes (Post-Project).
GET /api/customers/ - List all customers
GET /api/customers/{id} - Customer detail
PATCH /api/customers/{id} - Update customer/upsell status
POST /api/customers/{id}/pagespeed - Run PageSpeed analysis and persist
GET  /api/customers/{id}/pagespeed - Return persisted PageSpeed values
"""
import os
import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel
from database import Customer, Project, get_db, SessionLocal
from routers.auth_router import require_innendienst
from services.audit_pagespeed import api_key as pagespeed_api_key

# Vorgabe: geschlossen. Bis zum 14.08.2026 trug keine der sieben Routen eine
# Anmeldung — der Kundenbestand war produktiv ohne Token abrufbar und änderbar.
#
# **21.08.2026: von `require_any_auth` auf `require_innendienst`.** Der
# schwächere Wächter fiel bisher nicht auf, weil `GET /api/customers/` gar
# nicht hier ankam: `usercards.customers_alias_router` ist eine Zeile früher
# eingebunden (`main.py`) und hat die Route überdeckt — mitsamt seiner
# strengeren Sperre. Die Überdeckung hat also die Sicherheitsarbeit gemacht.
# Wer den Alias entfernt, ohne das hier zu ändern, öffnet den Kundenbestand
# für jeden angemeldeten Kunden. Dieselbe Lücke wie L-12, nur verdeckt.
router = APIRouter(prefix="/api/customers", tags=["customers"],
                   dependencies=[Depends(require_innendienst)])


# `x: datetime = None` heisst in Pydantic v2 **nicht** „darf None sein": Es ist
# ein Pflichtfeld vom Typ `datetime` mit einer Vorgabe, die den Typ verletzt.
# Beim Serialisieren einer echten `None`-Spalte schlaegt die Antwortpruefung zu
# und die Route antwortet **500** — dieselbe Familie wie L-53, wo `NULL > 0`
# ein `TypeError` war.
#
# Aufgefallen ist es erst am 21.08.2026, als der ueberdeckende Alias-Router
# entfernt wurde (Modulkarte, Nahtstelle `/api/customers`). Die Route war
# vorher unerreichbar — und damit war auch der Fehler unsichtbar. Eine tote
# Route ist nicht nur ungenutzt; sie ist ungeprueft.
class CustomerResponse(BaseModel):
    id: int
    project_id: int
    next_touchpoint_date: Optional[datetime] = None
    next_touchpoint_type: Optional[str] = None
    upsell_status: str
    upsell_package: Optional[str] = None
    recurring_revenue: float
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerUpdate(BaseModel):
    next_touchpoint_date: Optional[datetime] = None
    next_touchpoint_type: Optional[str] = None
    upsell_status: Optional[str] = None
    upsell_package: Optional[str] = None
    recurring_revenue: Optional[float] = None
    notes: Optional[str] = None


class CustomerDetailResponse(CustomerResponse):
    company_name: str
    contact_name: str
    email: str
    website_url: Optional[str] = None
    trade: str


@router.get("/", response_model=list[CustomerResponse])
def list_customers(
    upsell_status: str = Query(None),
    skip: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
):
    """List all customers, optionally filtered by upsell status."""
    query = db.query(Customer)
    if upsell_status:
        query = query.filter(Customer.upsell_status == upsell_status)
    customers = query.offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get customer detail with project/lead information."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    project = customer.project
    lead = project.lead if project else None

    return {
        "id": customer.id,
        "project_id": customer.project_id,
        "next_touchpoint_date": customer.next_touchpoint_date,
        "next_touchpoint_type": customer.next_touchpoint_type,
        "upsell_status": customer.upsell_status,
        "upsell_package": customer.upsell_package,
        "recurring_revenue": customer.recurring_revenue,
        "notes": customer.notes,
        "created_at": customer.created_at,
        "company_name": lead.company_name if lead else "N/A",
        "contact_name": lead.contact_name if lead else "N/A",
        "email": lead.email if lead else "N/A",
        "website_url": lead.website_url if lead else None,
        "trade": lead.trade if lead else "N/A",
    }


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    update: CustomerUpdate,
    db: Session = Depends(get_db),
):
    """Update customer record (typically for upsell tracking)."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if update.next_touchpoint_date is not None:
        customer.next_touchpoint_date = update.next_touchpoint_date
    if update.next_touchpoint_type is not None:
        customer.next_touchpoint_type = update.next_touchpoint_type
    if update.upsell_status is not None:
        customer.upsell_status = update.upsell_status
    if update.upsell_package is not None:
        customer.upsell_package = update.upsell_package
    if update.recurring_revenue is not None:
        customer.recurring_revenue = update.recurring_revenue
    if update.notes is not None:
        customer.notes = update.notes

    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    return customer


@router.post("/{project_id}/create")
def create_customer(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Create customer record for a project (called at go-live)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if customer already exists
    existing = db.query(Customer).filter(Customer.project_id == project_id).first()
    if existing:
        return {"project_id": project_id, "customer_id": existing.id, "message": "Customer already exists"}

    try:
        customer = Customer(
            project_id=project_id,
            upsell_status="none",
            next_touchpoint_date=datetime.utcnow() + timedelta(days=30),
            next_touchpoint_type="maintenance_offer",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        return {
            "project_id": project_id,
            "customer_id": customer.id,
            "message": f"Customer created for Project {project_id}",
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Customer creation failed: {str(e)}")


@router.get("/project/{project_id}/exists")
def customer_exists(project_id: int, db: Session = Depends(get_db)):
    """Check if customer exists for a project."""
    customer = db.query(Customer).filter(Customer.project_id == project_id).first()
    return {
        "project_id": project_id,
        "has_customer": customer is not None,
        "customer_id": customer.id if customer else None,
    }


def _pagespeed_payload(customer: Customer) -> dict:
    """Return the stored PageSpeed values as a dict."""
    return {
        "mobile_score":   customer.pagespeed_mobile_score,
        "desktop_score":  customer.pagespeed_desktop_score,
        "lcp_mobile":     customer.pagespeed_lcp_mobile,
        "cls_mobile":     customer.pagespeed_cls_mobile,
        "inp_mobile":     customer.pagespeed_inp_mobile,
        "fcp_mobile":     customer.pagespeed_fcp_mobile,
        "checked_at":     customer.pagespeed_checked_at.isoformat() if customer.pagespeed_checked_at else None,
    }


@router.post("/{customer_id}/pagespeed")
async def run_pagespeed(customer_id: int, db: Session = Depends(get_db)):
    """Call Google PageSpeed Insights for mobile + desktop, persist results.
    customer_id accepts either Customer.id or Lead.id (lead_id lookup as fallback)."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        customer = (
            db.query(Customer)
            .join(Project, Project.id == Customer.project_id)
            .filter(Project.lead_id == customer_id)
            .first()
        )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Resolve website_url via project → lead
    project = customer.project
    lead = project.lead if project else None
    website_url = lead.website_url if lead else None
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    real_customer_id = customer.id

    # DB-Verbindung vor externem PageSpeed-Call freigeben
    db.close()

    api_key = pagespeed_api_key()
    base = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    # Ohne Schlüssel muss der Parameter WEG, nicht leer mitgeschickt werden:
    # `key=` beantwortet Google mit 400, während ein Aufruf ganz ohne `key`
    # auf dem anonymen Kontingent funktioniert. Alle Nachbarstellen machen es
    # so; diese eine nicht — und sie fiel nie auf, weil `_score` jede
    # Fehlerantwort still zu `None` macht.
    params = {"url": website_url}
    if api_key:
        params["key"] = api_key

    async with httpx.AsyncClient(timeout=60.0) as client:
        mobile_resp, desktop_resp = await asyncio.gather(
            client.get(base, params={**params, "strategy": "mobile"}),
            client.get(base, params={**params, "strategy": "desktop"}),
        )

    def _score(resp) -> int | None:
        try:
            return round((resp.json()["categories"]["performance"]["score"] or 0) * 100)
        except Exception:
            return None

    def _audit(resp, key) -> float | None:
        try:
            return resp.json()["lighthouseResult"]["audits"][key]["numericValue"]
        except Exception:
            return None

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        customer = db2.query(Customer).filter(Customer.id == real_customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer.pagespeed_mobile_score  = _score(mobile_resp)
        customer.pagespeed_desktop_score = _score(desktop_resp)
        customer.pagespeed_lcp_mobile    = _audit(mobile_resp, "largest-contentful-paint")
        customer.pagespeed_cls_mobile    = _audit(mobile_resp, "cumulative-layout-shift")
        customer.pagespeed_inp_mobile    = _audit(mobile_resp, "interaction-to-next-paint")
        customer.pagespeed_fcp_mobile    = _audit(mobile_resp, "first-contentful-paint")
        customer.pagespeed_checked_at    = datetime.utcnow()
        db2.commit()
        db2.refresh(customer)
        return _pagespeed_payload(customer)
    finally:
        db2.close()


@router.get("/{customer_id}/pagespeed")
def get_pagespeed(customer_id: int, db: Session = Depends(get_db)):
    """Return the last stored PageSpeed values without a new API call.
    customer_id accepts either Customer.id or Lead.id (lead_id lookup as fallback)."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        customer = (
            db.query(Customer)
            .join(Project, Project.id == Customer.project_id)
            .filter(Project.lead_id == customer_id)
            .first()
        )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _pagespeed_payload(customer)
