"""Wartungsvertraege und Rechnungen.

**Zugriff (22.08.2026, L-05).** Bis dahin trugen alle sieben Routen nur
`get_current_user` — also jeden Angemeldeten, auch die Rolle `kunde`.
`GET /api/invoices` gab dabei `SELECT * FROM invoices` **ohne Filter** heraus:
alle Rechnungen aller Kunden, mit Namen, E-Mail und Betrag. Zwei Routen
schrieben sogar (`POST /api/invoices`, `PUT /api/retainer/{id}`).

Die Absicht war eine andere — `GET /api/invoices/my` filtert nach der eigenen
E-Mail und ist der Kundenweg. Die Innendienst-Routen waren nur nie zugesperrt.

Jetzt haengen sie an `view_billing` und `manage_billing`. Bewusst am **Recht**
und nicht an `require_innendienst`: Die Rechtematrix gibt beide an admin und
superadmin, nicht an den Auditor. So stimmt der Haken im Bildschirm „Rollen"
mit dem ueberein, was die Route tut.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from routers.auth_router import get_current_user, verlangt_recht
from services.invoice_pdf import generate_invoice_pdf
from datetime import date, timedelta

router = APIRouter(tags=["retainer"])


def _next_invoice_number(db):
    """Die naechste Rechnungsnummer aus dem gemeinsamen Kreis.

    **Hier stand bis zum 29.08.2026 `COUNT(*) + 1`.** ORDERS_07 warnt vor
    `MAX(...) + 1` als unsicher bei gleichzeitigen Vorgaengen; `COUNT(*)` ist
    schlechter: Wird eine Rechnung geloescht, **sinkt** die Zahl, und die
    naechste Vergabe wiederholt eine bereits vergebene Nummer. Die GoBD
    verlangen lueckenlos **und** fortlaufend — COUNT-basiert ist keines von
    beidem.

    Aufgefallen beim Lesen von ORDERS_07, das genau dieses Muster zu melden
    verlangt: „unabhaengig vom Shop ein Mangel".

    Der Zaehler steht jetzt in `invoice_counters` und wird mit einer Sperre auf
    die Zeile vergeben; das Format wechselt dabei von `KAS-2026-0001` auf
    `KAS-26-0001` (Entscheidung David). Der Kreis setzt auf dem Bestand auf,
    liest also die alten Nummern mit — sonst begaenne er bei eins und vergaebe
    Nummern, die es schon gibt.
    """
    from services.rechnungsnummer import naechste

    return naechste(db)


@router.get("/api/retainer", dependencies=[Depends(verlangt_recht("view_billing"))])
def list_retainer(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.execute(text(
        "SELECT * FROM retainer_contracts ORDER BY created_at DESC"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/api/retainer", dependencies=[Depends(verlangt_recht("manage_billing"))])
def create_retainer(body: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    db.execute(text("""
        INSERT INTO retainer_contracts
        (project_id, lead_id, package_name, price_net,
         customer_email, customer_name, start_date, next_billing_date, status)
        VALUES (:pid, :lid, :pkg, :price, :email, :name,
                :start, :next, 'aktiv')
    """), {
        "pid": body.get("project_id"),
        "lid": body.get("lead_id"),
        "pkg": body.get("package_name", "SEO-Pflege"),
        "price": body.get("price_net", 89),
        "email": body.get("customer_email", ""),
        "name": body.get("customer_name", ""),
        "start": body.get("start_date", str(date.today())),
        "next": body.get("next_billing_date",
                         str(date.today() + timedelta(days=30))),
    })
    db.commit()
    return {"success": True}


@router.put("/api/retainer/{rid}", dependencies=[Depends(verlangt_recht("manage_billing"))])
def update_retainer(rid: int, body: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    blocked = {"id", "created_at"}
    data = {k: v for k, v in body.items() if k not in blocked and v is not None}
    data["rid"] = rid
    sets = ", ".join(f"{k}=:{k}" for k in data if k != "rid")
    db.execute(text(f"UPDATE retainer_contracts SET {sets} WHERE id=:rid"), data)
    db.commit()
    return {"success": True}


@router.get("/api/invoices/my")
def my_invoices(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Rechnungen des eingeloggten Kunden (nach E-Mail)."""
    rows = db.execute(text(
        "SELECT * FROM invoices WHERE customer_email = :email ORDER BY created_at DESC"
    ), {"email": current_user.email}).fetchall()
    return [dict(r._mapping) for r in rows]


@router.get("/api/invoices", dependencies=[Depends(verlangt_recht("view_billing"))])
def list_invoices(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.execute(text(
        "SELECT * FROM invoices ORDER BY created_at DESC"
    )).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/api/invoices", dependencies=[Depends(verlangt_recht("manage_billing"))])
def create_invoice(body: dict, db: Session = Depends(get_db), _=Depends(get_current_user)):
    inv_num = _next_invoice_number(db)
    net = float(body.get("amount_net", 89))
    gross = round(net * 1.19, 2)
    db.execute(text("""
        INSERT INTO invoices
        (retainer_id, project_id, invoice_number, amount_net,
         amount_gross, customer_email, customer_name,
         line_item, due_date, status)
        VALUES (:rid, :pid, :num, :net, :gross,
                :email, :name, :item, :due, 'offen')
    """), {
        "rid": body.get("retainer_id"),
        "pid": body.get("project_id"),
        "num": inv_num,
        "net": net, "gross": gross,
        "email": body.get("customer_email", ""),
        "name": body.get("customer_name", ""),
        "item": body.get("line_item", "Website-Pflege & SEO-Paket"),
        "due": body.get("due_date",
                        str(date.today() + timedelta(days=14))),
    })
    db.commit()
    return {"success": True, "invoice_number": inv_num}


@router.get("/api/invoices/{inv_id}/pdf", dependencies=[Depends(verlangt_recht("view_billing"))])
def download_invoice_pdf(inv_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    row = db.execute(text(
        "SELECT * FROM invoices WHERE id=:id"), {"id": inv_id}
    ).fetchone()
    if not row:
        raise HTTPException(404)
    pdf_bytes = generate_invoice_pdf(dict(row._mapping))
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f"attachment; filename=Rechnung-{row.invoice_number}.pdf"})
