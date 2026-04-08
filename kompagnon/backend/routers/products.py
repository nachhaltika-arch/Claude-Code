from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from routers.auth_router import require_admin, get_current_user
from datetime import datetime
import json, os, logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/products", tags=["products"])


def _row(r):
    d = dict(r)
    for f in ["features", "checkout_fields", "webhook_actions"]:
        if isinstance(d.get(f), str):
            try:
                d[f] = json.loads(d[f])
            except Exception:
                d[f] = []
    return d


@router.get("/")
def list_products(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM products ORDER BY sort_order ASC, id ASC"
    )).mappings().all()
    return [_row(r) for r in rows]


@router.get("/public")
def list_public_products(db: Session = Depends(get_db)):
    rows = db.execute(text(
        "SELECT * FROM products WHERE status='live' ORDER BY sort_order ASC"
    )).mappings().all()
    return [_row(r) for r in rows]


@router.get("/{slug}")
def get_product(slug: str, db: Session = Depends(get_db)):
    row = db.execute(text(
        "SELECT * FROM products WHERE slug=:s"
    ), {"s": slug}).mappings().first()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    return _row(row)


@router.post("/", status_code=201)
def create_product(data: dict, db: Session = Depends(get_db),
                   _=Depends(require_admin)):
    slug = data.get("slug", "").strip()
    if not slug:
        raise HTTPException(400, "Slug fehlt")
    db.execute(text("""
        INSERT INTO products (slug, name, short_desc, long_desc,
          price_brutto, price_netto, tax_rate, payment_type,
          delivery_days, highlighted, highlight_label,
          features, checkout_fields, webhook_actions, status, sort_order)
        VALUES (:slug, :name, :sd, :ld, :pb, :pn, :tr, :pt,
          :dd, :hl, :hll, :feat::jsonb, :cf::jsonb, :wa::jsonb, :status, :so)
    """), {
        "slug":   slug,
        "name":   data.get("name", ""),
        "sd":     data.get("short_desc", ""),
        "ld":     data.get("long_desc", ""),
        "pb":     float(data.get("price_brutto", 0)),
        "pn":     float(data.get("price_netto", 0)),
        "tr":     float(data.get("tax_rate", 19)),
        "pt":     data.get("payment_type", "once"),
        "dd":     int(data.get("delivery_days", 14)),
        "hl":     bool(data.get("highlighted", False)),
        "hll":    data.get("highlight_label", "Empfehlung"),
        "feat":   json.dumps(data.get("features", [])),
        "cf":     json.dumps(data.get("checkout_fields", [])),
        "wa":     json.dumps(data.get("webhook_actions", [])),
        "status": data.get("status", "draft"),
        "so":     int(data.get("sort_order", 0)),
    })
    db.commit()
    return get_product(slug, db)


@router.put("/{slug}")
def update_product(slug: str, data: dict,
                   db: Session = Depends(get_db),
                   _=Depends(require_admin)):
    fields, params = [], {"slug": slug}
    mapping = {
        "name":             "name",
        "short_desc":       "sd",
        "long_desc":        "ld",
        "price_brutto":     "pb",
        "price_netto":      "pn",
        "tax_rate":         "tr",
        "payment_type":     "pt",
        "delivery_days":    "dd",
        "highlighted":      "hl",
        "highlight_label":  "hll",
        "status":           "status",
        "stripe_price_id":  "spid",
        "stripe_product_id":"sprodid",
        "sort_order":       "so",
    }
    for k, p in mapping.items():
        if k in data:
            fields.append(f"{k}=:{p}")
            params[p] = data[k]
    for f in ["features", "checkout_fields", "webhook_actions"]:
        if f in data:
            fields.append(f"{f}=:{f}::jsonb")
            params[f] = json.dumps(data[f])
    if not fields:
        return get_product(slug, db)
    fields.append("updated_at=NOW()")
    db.execute(text(
        f"UPDATE products SET {','.join(fields)} WHERE slug=:slug"
    ), params)
    db.commit()
    return get_product(slug, db)


@router.delete("/{slug}")
def delete_product(slug: str, db: Session = Depends(get_db),
                   _=Depends(require_admin)):
    db.execute(text("DELETE FROM products WHERE slug=:s"), {"s": slug})
    db.commit()
    return {"success": True}
