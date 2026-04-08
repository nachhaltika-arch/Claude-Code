import os
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from routers.auth_router import require_admin

router = APIRouter(prefix="/products", tags=["products"])


def _slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r'[äöüß]', lambda m: {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss'}[m.group()], s)
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s).strip('-')
    return s


@router.get("/")
def list_products(db: Session = Depends(get_db), _=Depends(require_admin)):
    rows = db.execute(text(
        "SELECT * FROM products ORDER BY sort_order, created_at DESC"
    )).mappings().all()
    return [dict(r) for r in rows]


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    row = db.execute(text(
        "SELECT * FROM products WHERE id = :id"
    ), {"id": product_id}).mappings().fetchone()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    return dict(row)


@router.post("/", status_code=201)
def create_product(body: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    name = body.get("name", "")
    if not name.strip():
        raise HTTPException(400, "Name erforderlich")
    slug = _slugify(name)
    frontend_url = os.getenv("FRONTEND_URL", "https://kompagnon-frontend.onrender.com")
    checkout_url = f"{frontend_url}/checkout/{slug}"
    db.execute(text("""
        INSERT INTO products
        (name, slug, beschreibung, leistungsumfang, typ, zielgruppe,
         preis_einmalig, preis_monatlich, landing_page_url, checkout_url, sort_order)
        VALUES (:name, :slug, :beschreibung, :leistungsumfang, :typ, :zielgruppe,
                :preis_einmalig, :preis_monatlich, :landing_page_url, :checkout_url, :sort_order)
    """), {
        "name": name, "slug": slug,
        "beschreibung": body.get("beschreibung"),
        "leistungsumfang": body.get("leistungsumfang"),
        "typ": body.get("typ", "paket"),
        "zielgruppe": body.get("zielgruppe", "oeffentlich"),
        "preis_einmalig": body.get("preis_einmalig"),
        "preis_monatlich": body.get("preis_monatlich"),
        "landing_page_url": body.get("landing_page_url"),
        "checkout_url": checkout_url,
        "sort_order": body.get("sort_order", 0),
    })
    db.commit()
    row = db.execute(text(
        "SELECT * FROM products WHERE slug = :slug"
    ), {"slug": slug}).mappings().fetchone()
    return dict(row)


@router.put("/{product_id}")
def update_product(product_id: int, body: dict, db: Session = Depends(get_db), _=Depends(require_admin)):
    blocked = {"id", "created_at", "slug"}
    data = {k: v for k, v in body.items() if k not in blocked and v is not None}
    if not data:
        return {"success": True}
    data["updated_at"] = datetime.now(timezone.utc)
    data["pid"] = product_id
    sets = ", ".join(f"{k} = :{k}" for k in data if k != "pid")
    db.execute(text(f"UPDATE products SET {sets} WHERE id = :pid"), data)
    db.commit()
    row = db.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id}).mappings().fetchone()
    return dict(row)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    row = db.execute(text("SELECT ist_live FROM products WHERE id = :id"), {"id": product_id}).mappings().fetchone()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    if row["ist_live"]:
        raise HTTPException(400, "Aktives Produkt kann nicht geloescht werden")
    db.execute(text("DELETE FROM products WHERE id = :id"), {"id": product_id})
    db.commit()
    return {"success": True}


@router.post("/{product_id}/stripe-connect")
def stripe_connect(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(500, "STRIPE_SECRET_KEY nicht konfiguriert")

    row = db.execute(text("SELECT * FROM products WHERE id = :id"), {"id": product_id}).mappings().fetchone()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    product = dict(row)

    try:
        stripe_product = stripe.Product.create(
            name=product["name"],
            description=product["beschreibung"] or "",
            metadata={"kompagnon_product_id": str(product["id"])},
        )

        stripe_price = None
        if product.get("preis_monatlich"):
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=product["preis_monatlich"],
                currency=product.get("waehrung") or "eur",
                recurring={"interval": "month"},
            )
        elif product.get("preis_einmalig"):
            stripe_price = stripe.Price.create(
                product=stripe_product.id,
                unit_amount=product["preis_einmalig"],
                currency=product.get("waehrung") or "eur",
            )

        stripe_link_url = None
        if stripe_price:
            stripe_link = stripe.PaymentLink.create(
                line_items=[{"price": stripe_price.id, "quantity": 1}],
            )
            stripe_link_url = stripe_link.url

        db.execute(text("""
            UPDATE products SET
                stripe_product_id = :spid,
                stripe_price_id = :sprid,
                stripe_payment_link = :spl,
                updated_at = :now
            WHERE id = :id
        """), {
            "spid": stripe_product.id,
            "sprid": stripe_price.id if stripe_price else None,
            "spl": stripe_link_url,
            "now": datetime.now(timezone.utc),
            "id": product_id,
        })
        db.commit()

        return {
            "success": True,
            "stripe_product_id": stripe_product.id,
            "stripe_price_id": stripe_price.id if stripe_price else None,
            "stripe_payment_link": stripe_link_url,
        }
    except Exception as e:
        raise HTTPException(502, f"Stripe Fehler: {e}")


@router.get("/{product_id}/stripe-status")
def stripe_status(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    row = db.execute(text(
        "SELECT stripe_product_id, stripe_price_id FROM products WHERE id = :id"
    ), {"id": product_id}).mappings().fetchone()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    if not row["stripe_product_id"]:
        return {"connected": False}
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        sp = stripe.Product.retrieve(row["stripe_product_id"])
        price_amount = None
        livemode = sp.get("livemode", False)
        if row["stripe_price_id"]:
            pr = stripe.Price.retrieve(row["stripe_price_id"])
            price_amount = pr.get("unit_amount")
            livemode = pr.get("livemode", livemode)
        return {"connected": True, "active": sp.get("active", False), "livemode": livemode, "price": price_amount}
    except Exception as e:
        return {"connected": True, "error": str(e)}


@router.post("/{product_id}/toggle-live")
def toggle_live(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    row = db.execute(text("SELECT ist_live FROM products WHERE id = :id"), {"id": product_id}).mappings().fetchone()
    if not row:
        raise HTTPException(404, "Produkt nicht gefunden")
    new_live = not row["ist_live"]
    new_status = "live" if new_live else "entwurf"
    db.execute(text(
        "UPDATE products SET ist_live = :live, status = :status, updated_at = :now WHERE id = :id"
    ), {"live": new_live, "status": new_status, "now": datetime.now(timezone.utc), "id": product_id})
    db.commit()
    return {"ist_live": new_live, "status": new_status}
