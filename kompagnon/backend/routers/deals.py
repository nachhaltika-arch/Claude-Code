"""
Deal / CRM Pipeline Router
POST   /api/deals/                  - Create deal
GET    /api/deals/                  - List deals (optional filter: status, company_id)
GET    /api/deals/stats             - Dashboard metrics
GET    /api/deals/{deal_id}         - Get deal with items
PUT    /api/deals/{deal_id}         - Update deal
DELETE /api/deals/{deal_id}         - Delete deal
POST   /api/deals/{deal_id}/create-project  - Convert won deal to project
"""
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/deals", tags=["deals"])


# ── Schemas ──────────────────────────────────────────────────────

class DealItem(BaseModel):
    position: str
    quantity: float = 1
    unit_price: float = 0
    product_id: Optional[int] = None
    sort_order: int = 0


class DealCreate(BaseModel):
    title: str
    company_id: Optional[int] = None
    status: str = "neu"
    notes: Optional[str] = None
    items: List[DealItem] = []


class DealUpdate(BaseModel):
    title: Optional[str] = None
    company_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[DealItem]] = None


# ── Helpers ──────────────────────────────────────────────────────

def _calculate_total(items):
    return sum(float(i.quantity or 0) * float(i.unit_price or 0) for i in items)


def _deal_row_to_dict(row, items=None):
    return {
        "id":          row.id,
        "title":       row.title,
        "company_id":  row.company_id,
        "company_name": getattr(row, "company_name", None),
        "status":      row.status,
        "total_value": float(row.total_value or 0),
        "currency":    row.currency or "EUR",
        "notes":       row.notes or "",
        "assigned_to": row.assigned_to,
        "won_at":      str(row.won_at)[:19] if row.won_at else None,
        "lost_at":     str(row.lost_at)[:19] if row.lost_at else None,
        "created_at":  str(row.created_at)[:19] if row.created_at else None,
        "updated_at":  str(row.updated_at)[:19] if row.updated_at else None,
        "items":       items or [],
    }


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/")
def list_deals(
    status: Optional[str] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Alle Deals — optional gefiltert nach Status oder Unternehmen."""
    where = ["1=1"]
    params = {}
    if status:
        where.append("d.status = :status")
        params["status"] = status
    if company_id:
        where.append("d.company_id = :company_id")
        params["company_id"] = company_id

    rows = db.execute(text(f"""
        SELECT d.*, l.company_name
        FROM deals d
        LEFT JOIN leads l ON d.company_id = l.id
        WHERE {' AND '.join(where)}
        ORDER BY d.created_at DESC
    """), params).fetchall()
    return [_deal_row_to_dict(r) for r in rows]


@router.get("/stats")
def deal_stats(db: Session = Depends(get_db), _=Depends(get_current_user)):
    """Dashboard-Metriken: heute gewonnen, Monat, Pipeline-Wert."""
    stats = db.execute(text("""
        SELECT
          COALESCE(SUM(CASE
            WHEN status='gewonnen' AND DATE(won_at) = CURRENT_DATE
            THEN total_value END), 0) AS won_today,
          COALESCE(SUM(CASE
            WHEN status='gewonnen'
              AND DATE_TRUNC('month', won_at) = DATE_TRUNC('month', NOW())
            THEN total_value END), 0) AS won_this_month,
          COALESCE(SUM(CASE
            WHEN status NOT IN ('gewonnen','verloren')
            THEN total_value END), 0) AS pipeline_value,
          COUNT(CASE WHEN status='gewonnen' AND DATE(won_at) = CURRENT_DATE
                THEN 1 END) AS deals_won_today,
          COUNT(CASE WHEN status NOT IN ('gewonnen','verloren')
                THEN 1 END) AS deals_open
        FROM deals
    """)).fetchone()

    return {
        "won_today":       float(stats.won_today or 0),
        "won_this_month":  float(stats.won_this_month or 0),
        "pipeline_value":  float(stats.pipeline_value or 0),
        "deals_won_today": int(stats.deals_won_today or 0),
        "deals_open":      int(stats.deals_open or 0),
    }


@router.get("/{deal_id}")
def get_deal(deal_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    row = db.execute(text("""
        SELECT d.*, l.company_name
        FROM deals d
        LEFT JOIN leads l ON d.company_id = l.id
        WHERE d.id = :id
    """), {"id": deal_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Deal nicht gefunden")

    items = db.execute(text("""
        SELECT * FROM deal_items
        WHERE deal_id = :id
        ORDER BY sort_order, id
    """), {"id": deal_id}).fetchall()

    items_list = [{
        "id":          i.id,
        "position":    i.position,
        "quantity":    float(i.quantity or 0),
        "unit_price":  float(i.unit_price or 0),
        "total_price": float((i.quantity or 0) * (i.unit_price or 0)),
        "product_id":  i.product_id,
        "sort_order":  i.sort_order,
    } for i in items]

    return _deal_row_to_dict(row, items_list)


@router.post("/")
def create_deal(
    data: DealCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total = _calculate_total(data.items)
    # Set won_at/lost_at immediately if initial status is already final
    won_at_expr = "NOW()" if data.status == "gewonnen" else "NULL"
    lost_at_expr = "NOW()" if data.status == "verloren" else "NULL"

    result = db.execute(text(f"""
        INSERT INTO deals (title, company_id, status, total_value, notes, assigned_to, won_at, lost_at)
        VALUES (:title, :company_id, :status, :total, :notes, :assigned_to, {won_at_expr}, {lost_at_expr})
        RETURNING id
    """), {
        "title":       data.title,
        "company_id":  data.company_id,
        "status":      data.status,
        "total":       total,
        "notes":       data.notes,
        "assigned_to": current_user.id,
    })
    deal_id = result.fetchone()[0]

    for i, item in enumerate(data.items):
        tp = float(item.quantity or 0) * float(item.unit_price or 0)
        db.execute(text("""
            INSERT INTO deal_items (deal_id, position, quantity, unit_price, total_price, product_id, sort_order)
            VALUES (:deal_id, :position, :quantity, :unit_price, :total_price, :product_id, :sort_order)
        """), {
            "deal_id":     deal_id,
            "position":    item.position,
            "quantity":    item.quantity,
            "unit_price":  item.unit_price,
            "total_price": tp,
            "product_id":  item.product_id,
            "sort_order":  i,
        })

    db.commit()
    return get_deal(deal_id, db, current_user)


@router.put("/{deal_id}")
def update_deal(
    deal_id: int,
    data: DealUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deal = db.execute(
        text("SELECT id, status FROM deals WHERE id = :id"),
        {"id": deal_id}
    ).fetchone()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal nicht gefunden")

    fields = []
    updates = {"id": deal_id}

    if data.title is not None:
        fields.append("title = :title")
        updates["title"] = data.title
    if data.company_id is not None:
        fields.append("company_id = :company_id")
        updates["company_id"] = data.company_id
    if data.notes is not None:
        fields.append("notes = :notes")
        updates["notes"] = data.notes
    if data.status is not None:
        fields.append("status = :status")
        updates["status"] = data.status
        if data.status == "gewonnen" and deal.status != "gewonnen":
            fields.append("won_at = NOW()")
        elif data.status == "verloren" and deal.status != "verloren":
            fields.append("lost_at = NOW()")

    if data.items is not None:
        total = _calculate_total(data.items)
        fields.append("total_value = :total_value")
        updates["total_value"] = total
        db.execute(text("DELETE FROM deal_items WHERE deal_id = :id"), {"id": deal_id})
        for i, item in enumerate(data.items):
            tp = float(item.quantity or 0) * float(item.unit_price or 0)
            db.execute(text("""
                INSERT INTO deal_items
                  (deal_id, position, quantity, unit_price, total_price, product_id, sort_order)
                VALUES
                  (:deal_id, :position, :quantity, :unit_price, :total_price, :product_id, :sort_order)
            """), {
                "deal_id":     deal_id,
                "position":    item.position,
                "quantity":    item.quantity,
                "unit_price":  item.unit_price,
                "total_price": tp,
                "product_id":  item.product_id,
                "sort_order":  i,
            })

    if fields:
        fields.append("updated_at = NOW()")
        db.execute(
            text(f"UPDATE deals SET {', '.join(fields)} WHERE id = :id"),
            updates,
        )
    db.commit()
    return get_deal(deal_id, db, current_user)


@router.delete("/{deal_id}")
def delete_deal(deal_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db.execute(text("DELETE FROM deal_items WHERE deal_id = :id"), {"id": deal_id})
    db.execute(text("DELETE FROM deals WHERE id = :id"), {"id": deal_id})
    db.commit()
    return {"deleted": deal_id}


@router.post("/{deal_id}/create-project")
def create_project_from_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Gewonnener Deal → Projekt anlegen."""
    deal = db.execute(text("""
        SELECT d.*, l.id as lead_id
        FROM deals d LEFT JOIN leads l ON d.company_id = l.id
        WHERE d.id = :id
    """), {"id": deal_id}).fetchone()

    if not deal:
        raise HTTPException(status_code=404, detail="Deal nicht gefunden")
    if deal.status != "gewonnen":
        raise HTTPException(status_code=400, detail="Nur gewonnene Deals können zu Projekten werden")

    existing = db.execute(
        text("SELECT id FROM projects WHERE deal_id = :id"),
        {"id": deal_id}
    ).fetchone()
    if existing:
        return {"project_id": existing.id, "already_exists": True}

    result = db.execute(text("""
        INSERT INTO projects (lead_id, deal_id, status, start_date, created_at, updated_at, fixed_price)
        VALUES (:lead_id, :deal_id, 'phase_1', NOW(), NOW(), NOW(), :value)
        RETURNING id
    """), {
        "lead_id": deal.lead_id,
        "deal_id": deal_id,
        "value":   float(deal.total_value or 0),
    })
    project_id = result.fetchone()[0]
    db.commit()

    return {"project_id": project_id, "already_exists": False}


# ── Einmalige Migration bestehender Leads zu Deals ───────────────

def migrate_leads_to_deals(db: Session) -> int:
    """Einmalige Migration: Leads → Deals. Läuft nur wenn deals leer."""
    try:
        count = db.execute(text("SELECT COUNT(*) FROM deals")).scalar()
        if count and count > 0:
            return 0

        leads = db.execute(text("""
            SELECT id, company_name, status, created_at
            FROM leads
            WHERE status IS NOT NULL
        """)).fetchall()

        status_map = {
            'new':           'neu',
            'contacted':     'kontaktiert',
            'qualified':     'kontaktiert',
            'proposal_sent': 'angebot_gesendet',
            'won':           'gewonnen',
            'lost':          'verloren',
        }

        for lead in leads:
            deal_status = status_map.get(lead.status, 'neu')
            won_at_expr = "NOW()" if deal_status == "gewonnen" else "NULL"
            lost_at_expr = "NOW()" if deal_status == "verloren" else "NULL"

            db.execute(text(f"""
                INSERT INTO deals
                  (title, company_id, status, total_value, won_at, lost_at, created_at)
                VALUES
                  (:title, :company_id, :status, 0, {won_at_expr}, {lost_at_expr}, :created_at)
            """), {
                "title":      f"Deal — {lead.company_name or 'Unbekannt'}",
                "company_id": lead.id,
                "status":     deal_status,
                "created_at": lead.created_at,
            })

        db.commit()
        logger.info(f"Deals-Migration abgeschlossen: {len(leads)} Leads → Deals")
        return len(leads)
    except Exception as e:
        logger.warning(f"Deals-Migration Fehler: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return 0
