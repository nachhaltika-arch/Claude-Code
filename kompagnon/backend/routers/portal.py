"""
Kundenportal endpoints — only for JWT-authenticated users with role 'kunde'.

GET  /api/portal/me                — project + phase progress
GET  /api/portal/messages          — message thread
POST /api/portal/messages          — send a message
GET  /api/portal/documents         — list uploaded files
POST /api/portal/documents/upload  — upload a file (multipart)
"""
import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db, MitwirkungStand, Project, ProjectChecklist, Lead
from routers.auth_router import get_current_user

router = APIRouter(prefix="/api/portal", tags=["portal"])

# ── Phase metadata ────────────────────────────────────────────────

PHASE_META = [
    (1, "Kickoff & Strategie",    "Ziele, Zielgruppe und Sitemap definiert"),
    (2, "Texterstellung",          "Alle Seiteninhalte verfasst und freigegeben"),
    (3, "Design & Mockup",         "Startseite & Unterseiten im Design-Tool"),
    (4, "Entwicklung",             "Technische Umsetzung im CMS"),
    (5, "SEO & GEO-Optimierung",  "Meta-Tags, Ladezeit, lokale Sichtbarkeit"),
    (6, "Review & Freigabe",       "Gemeinsame Abnahme aller Seiten"),
    (7, "Go-live & Übergabe",      "Domain live schalten, Einweisung, Support"),
]

STATUS_LABEL = {
    "phase_1": "Kickoff läuft",    "phase_2": "Texterstellung",
    "phase_3": "Design & Mockup",  "phase_4": "In Entwicklung",
    "phase_5": "SEO & Optimierung","phase_6": "Review",
    "phase_7": "Go-live",          "completed": "Abgeschlossen",
}


def _phase_number(status: str) -> int:
    for i in range(1, 8):
        if status == f"phase_{i}":
            return i
    return 7 if status == "completed" else 1


def _customer_id(user) -> int:
    """Stable identifier for a customer's portal data."""
    return user.lead_id if user.lead_id else user.id


# ── GET /api/portal/me ────────────────────────────────────────────

@router.get("/me")
def get_portal_me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)

    # Resolve lead
    lead = db.query(Lead).filter(Lead.id == cid).first() if user.lead_id else None
    project_name = (lead.company_name if lead else None) or "Mein Projekt"

    # Try to find a project
    project = None
    if user.lead_id:
        project = (
            db.query(Project)
            .filter(Project.lead_id == user.lead_id)
            .order_by(Project.created_at.desc())
            .first()
        )

    if not project:
        return {
            "project_name": project_name,
            "project_status": "In Vorbereitung",
            "current_phase": 1,
            "phases": [
                {
                    "number": n, "label": lbl, "description": desc,
                    "done": 0, "total": 0,
                    "state": "active" if n == 1 else "locked",
                }
                for n, lbl, desc in PHASE_META
            ],
        }

    current = _phase_number(project.status)

    # Aggregate checklist progress per phase
    items = db.query(ProjectChecklist).filter(ProjectChecklist.project_id == project.id).all()
    counts = {i: {"done": 0, "total": 0} for i in range(1, 8)}
    for it in items:
        if 1 <= it.phase <= 7:
            counts[it.phase]["total"] += 1
            if it.is_completed:
                counts[it.phase]["done"] += 1

    phases = [
        {
            "number": n, "label": lbl, "description": desc,
            "done": counts[n]["done"], "total": counts[n]["total"],
            "state": "done" if n < current else ("active" if n == current else "locked"),
        }
        for n, lbl, desc in PHASE_META
    ]

    # Inspiration URLs aus Lead (für Portal-Anzeige)
    inspirations = {
        "url_1": getattr(lead, "inspiration_url_1", None) if lead else None,
        "url_2": getattr(lead, "inspiration_url_2", None) if lead else None,
        "url_3": getattr(lead, "inspiration_url_3", None) if lead else None,
    }

    # Website-Versionen (KI-Entwürfe zur Auswahl)
    versions_list = []
    try:
        from sqlalchemy import text as _text
        version_rows = db.execute(_text("""
            SELECT id, version_label, selected, ki_reasoning, template_id
            FROM website_versions
            WHERE project_id = :pid
            ORDER BY version_label
        """), {"pid": project.id}).fetchall()
        for vr in version_rows:
            versions_list.append({
                "id":            vr.id,
                "version_label": vr.version_label,
                "selected":      bool(vr.selected),
                "ki_reasoning":  vr.ki_reasoning,
                "template_id":   vr.template_id,
            })
    except Exception:
        pass

    # Netlify / DNS-Guide Daten für den Kunden (optional)
    netlify_info = None
    try:
        from services.netlify_service import generate_dns_guide
        netlify_domain = getattr(project, "netlify_domain", None)
        netlify_status = getattr(project, "netlify_domain_status", None)
        netlify_site_url = getattr(project, "netlify_site_url", None)
        if netlify_domain:
            netlify_info = {
                "domain":     netlify_domain,
                "status":     netlify_status or "pending",
                "site_url":   netlify_site_url,
                "ssl_active": bool(getattr(project, "netlify_ssl_active", False)),
                "guide":      generate_dns_guide(netlify_domain, netlify_site_url or ""),
            }
    except Exception:
        pass

    return {
        "project_id": project.id,
        "lead_id": user.lead_id,
        "project_name": project_name,
        "project_status": STATUS_LABEL.get(project.status, "In Bearbeitung"),
        "current_phase": current,
        "phases": phases,
        "netlify": netlify_info,
        "inspirations": inspirations,
        "versions": versions_list,
    }


# ── Messages ──────────────────────────────────────────────────────

class MessageIn(BaseModel):
    text: str


@router.get("/messages")
def get_messages(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)
    rows = db.execute(
        text("SELECT id, sender_role, text, created_at FROM portal_messages "
             "WHERE customer_id = :cid ORDER BY created_at ASC"),
        {"cid": cid},
    ).fetchall()
    return [
        {"id": r[0], "sender_role": r[1], "text": r[2], "created_at": str(r[3])}
        for r in rows
    ]


@router.post("/messages", status_code=201)
def post_message(data: MessageIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not data.text.strip():
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    cid = _customer_id(user)
    db.execute(
        text("INSERT INTO portal_messages (customer_id, sender_role, text, created_at) "
             "VALUES (:cid, :role, :text, :now)"),
        {"cid": cid, "role": user.role, "text": data.text.strip(), "now": datetime.utcnow()},
    )
    db.commit()
    return {"ok": True}


# ── Documents ─────────────────────────────────────────────────────

@router.get("/documents")
def get_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    cid = _customer_id(user)
    rows = db.execute(
        text("SELECT id, filename, filepath, created_at FROM portal_documents "
             "WHERE customer_id = :cid ORDER BY created_at DESC"),
        {"cid": cid},
    ).fetchall()
    return [
        {"id": r[0], "filename": r[1], "filepath": r[2], "created_at": str(r[3])}
        for r in rows
    ]


@router.post("/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cid = _customer_id(user)
    upload_dir = f"/uploads/portal/{cid}"
    os.makedirs(upload_dir, exist_ok=True)

    safe_name = os.path.basename(file.filename or "upload")
    dest = os.path.join(upload_dir, safe_name)

    content = await file.read()
    with open(dest, "wb") as f:
        f.write(content)

    db.execute(
        text("INSERT INTO portal_documents (customer_id, filename, filepath, created_at) "
             "VALUES (:cid, :fn, :fp, :now)"),
        {"cid": cid, "fn": safe_name, "fp": dest, "now": datetime.utcnow()},
    )
    db.commit()
    return {"ok": True, "filename": safe_name}


# ── Website-Versionen (Kunde wählt aus 3 KI-Entwürfen) ──────────────────

@router.post("/versions/{version_id}/select")
def portal_select_version(
    version_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Kunde wählt aus seinem eigenen Projekt eine der 3 Versionen aus."""
    if not user.lead_id:
        raise HTTPException(403, "Kein Projekt verknüpft")

    # Prüfe ob version_id zu einem Projekt dieses Kunden gehört
    row = db.execute(text("""
        SELECT v.id, v.project_id, p.lead_id
        FROM website_versions v
        JOIN projects p ON v.project_id = p.id
        WHERE v.id = :vid
    """), {"vid": version_id}).fetchone()

    if not row:
        raise HTTPException(404, "Version nicht gefunden")
    if row.lead_id != user.lead_id:
        raise HTTPException(403, "Kein Zugriff auf diese Version")

    # Alle anderen Versionen dieses Projekts deselektieren, diese auswählen
    db.execute(
        text("UPDATE website_versions SET selected=FALSE WHERE project_id = :pid"),
        {"pid": row.project_id},
    )
    db.execute(
        text("UPDATE website_versions SET selected=TRUE WHERE id = :vid"),
        {"vid": version_id},
    )
    db.commit()
    return {"selected": version_id, "project_id": row.project_id}


@router.get("/versions/{version_id}/preview")
def portal_version_preview(
    version_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """HTML-Preview einer Version — nur wenn sie zum eigenen Projekt gehört."""
    from fastapi.responses import HTMLResponse
    row = db.execute(text("""
        SELECT v.html, v.css, p.lead_id
        FROM website_versions v
        JOIN projects p ON v.project_id = p.id
        WHERE v.id = :vid
    """), {"vid": version_id}).fetchone()
    if not row:
        raise HTTPException(404, "Version nicht gefunden")
    if row.lead_id != user.lead_id:
        raise HTTPException(403, "Kein Zugriff auf diese Version")
    html = row.html or "<p>Kein Inhalt</p>"
    css  = row.css or ""
    from services.seiten_huelle import vorschau_huelle
    return HTMLResponse(vorschau_huelle(html, css, f"Vorschau — Version {version_id}"))


# ══════════════════════════════════════════════════════════════════════
# Mitwirkungsleistungen (L-159)
# ══════════════════════════════════════════════════════════════════════
#
# **Warum das ins Kundenkonto gehoert und nicht in eine Mahnmail.** Bis heute
# schickte `job_check_missing_materials` dem Betrieb gestaffelt die Nachricht,
# dass Materialien fehlen — ohne zu sagen **welche**, und ohne dass er den
# Stand irgendwo nachsehen konnte. Aus einer Mahnung wird hier eine Liste, die
# er abarbeiten kann.
#
# **Und sie traegt die Frist.** Die Bauzeit beginnt an dem Werktag, an dem alle
# Fristbeginn-Punkte vorliegen; die beiden Freigaben pausieren sie. Ohne
# festgehaltenes Eingangsdatum je Punkt ist die Bauzeitgarantie entweder
# unverbindlich oder ruinoes (Blocker L6).


def _merkmale(project) -> set:
    """Welche bedingten Punkte fuer dieses Projekt gelten.

    Vorerst aus dem Projekt selbst abgeleitet. Sobald der Auftrag die
    Leistungen einzeln fuehrt, kommt es von dort — die Stelle ist bewusst
    **eine**, damit die Ableitung nicht an drei Orten auseinanderlaeuft.
    """
    merkmale = set()
    if getattr(project, "migration_noetig", False):
        merkmale.add("migration")
    if getattr(project, "karriereseite", False):
        merkmale.add("karriereseite")
    return merkmale


@router.get("/mitwirkung")
def get_mitwirkung(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was wir vom Kunden brauchen — mit Stand und gerechnetem Fristbeginn."""
    from services import mitwirkung as kat

    project = None
    if user.lead_id:
        project = (db.query(Project).filter(Project.lead_id == user.lead_id)
                   .order_by(Project.created_at.desc()).first())
    if not project:
        return {"punkte": [], "offen": 0, "erledigt": 0, "start_moeglich": False}

    staende = {s.kennung: s for s in db.query(MitwirkungStand)
               .filter(MitwirkungStand.project_id == project.id).all()}
    punkte = kat.gilt_fuer(_merkmale(project))
    erledigt = {k for k, s in staende.items() if s.erledigt_am}

    def zeile(p):
        stand = staende.get(p.kennung)
        return {
            "kennung": p.kennung, "titel": p.titel, "warum": p.warum,
            "wirkung": p.wirkung, "vertragstext": p.vertragstext,
            "erledigt": bool(stand and stand.erledigt_am),
            "erledigt_am": stand.erledigt_am.isoformat() if stand and stand.erledigt_am else None,
            "bestaetigt_von": (stand.bestaetigt_von or "") if stand else "",
        }

    vor_start = [p for p in punkte if p.wirkung == kat.FRISTBEGINN]
    spaeter = [p for p in punkte if p.wirkung == kat.FRISTPAUSE]
    offen = kat.fristbeginn_offen(punkte, erledigt)

    # `Project` traegt keinen eigenen Namen — der Betrieb schon. Dieselbe
    # Ableitung wie in `/me`; zwei Wege zum selben Namen laufen auseinander.
    lead = db.query(Lead).filter(Lead.id == project.lead_id).first()
    return {
        "projekt": (lead.company_name if lead else "") or "Ihr Projekt",
        # Getrennt ausgegeben, nicht in einer Liste mit einem Merkmal:
        # Lieferungen vor dem Start und Freigaben mittendrin sind zwei Dinge,
        # und gemischt sieht die Aufgabe doppelt so gross aus.
        "punkte": [zeile(p) for p in vor_start],
        "spaeter": [zeile(p) for p in spaeter],
        "offen": len(offen),
        "erledigt": len([p for p in vor_start if p.kennung in erledigt]),
        "gesamt": len(vor_start),
        "start_moeglich": not offen,
    }


class MitwirkungEintrag(BaseModel):
    notiz: str = ""


@router.post("/mitwirkung/{kennung}")
def setze_mitwirkung(kennung: str, body: MitwirkungEintrag,
                     user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Einen Punkt als erledigt eintragen — mit Datum und Namen.

    Das Datum ist nicht Zierrat: Aus ihm entsteht der Fristbeginn. Und der
    Name unterscheidet beim spaeteren Streit eine Aussage von einem Nachweis.
    """
    from services import mitwirkung as kat

    if kennung not in kat.NACH_KENNUNG:
        raise HTTPException(404, f"Unbekannter Mitwirkungspunkt: {kennung}")

    project = None
    if user.lead_id:
        project = (db.query(Project).filter(Project.lead_id == user.lead_id)
                   .order_by(Project.created_at.desc()).first())
    if not project:
        raise HTTPException(404, "Kein Projekt gefunden")

    stand = (db.query(MitwirkungStand)
             .filter(MitwirkungStand.project_id == project.id,
                     MitwirkungStand.kennung == kennung).first())
    if not stand:
        stand = MitwirkungStand(project_id=project.id, kennung=kennung)
        db.add(stand)

    # **Der erste Eingang zaehlt.** Ein zweiter Klick darf das Datum nicht
    # nach hinten schieben — sonst haette der Fristbeginn zwei Antworten.
    if not stand.erledigt_am:
        stand.erledigt_am = datetime.utcnow()
        stand.bestaetigt_von = user.email or ""
    if body.notiz:
        stand.notiz = body.notiz
    db.commit()
    return {"ok": True, "kennung": kennung,
            "erledigt_am": stand.erledigt_am.isoformat()}


# ══════════════════════════════════════════════════════════════════════
# Zahlungen: Abo, Rechnungen, Zahlungsart (04.09.2026)
# ══════════════════════════════════════════════════════════════════════
#
# **Drei Dinge an einer Stelle**, weil der Kunde sie als eines denkt: Was zahle
# ich, womit zahle ich, und was habe ich bezahlt.
#
# **Die Zahlungsart aendert er bei Stripe, nicht bei uns.** Ein eigenes
# Kartenformular hiesse, Kartendaten durch unseren Server zu fuehren. Stripes
# Billing-Portal ist dafuer da; wir erzeugen eine Sitzung und leiten weiter.


@router.get("/zahlungen")
def get_zahlungen(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Abos, Rechnungen und der Zustand des Zahlungskontos."""
    from services import abo_vertrag, zahlungsportal

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        return {"abos": [], "rechnungen": [], "zahlungskonto": "kein_betrieb"}

    abos = [{"produkt": v.produkt, "start_monat": v.start_monat,
             "end_monat": v.end_monat, "notiz": v.notiz or ""}
            for v in abo_vertrag.vertraege(db, lead.id)]

    # Rechnungen ueber die Mailadresse — derselbe Weg wie `/api/invoices/my`.
    # Zwei Wege zu denselben Zeilen laufen auseinander.
    zeilen = db.execute(text(
        "SELECT invoice_number, amount_gross, status, due_date, paid_at, created_at, "
        "line_item FROM invoices WHERE customer_email = :mail "
        "ORDER BY created_at DESC LIMIT 24"), {"mail": user.email}).fetchall()
    rechnungen = [dict(r._mapping) for r in zeilen]

    # **Der Zustand des Zahlungskontos, nicht ein Ja/Nein.** „Kein Konto" und
    # „Stripe nicht eingerichtet" sind zwei verschiedene Lagen: die eine
    # betrifft den Kunden, die andere uns.
    try:
        zustand = "vorhanden" if zahlungsportal.kundenkennung(db, lead) else "keins"
    except zahlungsportal.StripeNichtEingerichtet:
        zustand = "dienst_fehlt"

    return {"abos": abos, "rechnungen": rechnungen, "zahlungskonto": zustand}


class PortalZiel(BaseModel):
    rueckkehr: str = ""


@router.post("/zahlungen/verwalten")
def zahlungen_verwalten(body: PortalZiel, user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Eine Sitzung im Billing-Portal — die Adresse gilt einmal und kurz."""
    from services import zahlungsportal
    from services.base_urls import public_base_url

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        raise HTTPException(404, "Kein Betrieb gefunden")

    # Die Rueckkehradresse kommt aus der Umgebung, nicht aus dem Rumpf: Ein
    # mitgeschickter Wert waere eine offene Weiterleitung.
    ziel = f"{public_base_url()}/app/portal"
    try:
        return {"url": zahlungsportal.portal_sitzung(db, lead, ziel)}
    except zahlungsportal.KeinZahlungskonto as fehler:
        raise HTTPException(409, str(fehler))
    except zahlungsportal.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")


# ══════════════════════════════════════════════════════════════════════
# Inhaltsänderungen: Guthaben und Wünsche (Rang 1, 04.09.2026)
# ══════════════════════════════════════════════════════════════════════
#
# **Der Kontostand kommt aus der Zeiterfassung**, nicht aus einer zweiten
# Rechnung. `abo_stunden.monatsstand` liefert Kontingent, Verbrauch und Rest
# seit dem 31.08.; hier wird nur ausgewaehlt, was der Kunde davon sieht.
#
# Ein Guthaben ohne Kontostand wird entweder nicht genutzt oder ueberzogen.
# Das erste kostet Vertrauen, das zweite Geld.


@router.get("/inhalt")
def get_inhalt(monat: str = "", user=Depends(get_current_user),
               db: Session = Depends(get_db)):
    """Guthaben des Monats und die eigenen Änderungswünsche."""
    from services import abo_stunden, inhaltsanfrage

    if not user.lead_id:
        return {"guthaben": None, "anfragen": []}

    stand = abo_stunden.monatsstand(db, lead_id=user.lead_id,
                                    monat=monat or abo_stunden.monat_von())
    kontingent = stand.get("kontingent_stunden")
    verbraucht = stand.get("verbraucht") or 0

    # **In Minuten, nicht in Stunden.** Das Datenblatt sagt „bis 30 Minuten";
    # „0,5 h verbleibend" waere dieselbe Zahl in einer Sprache, die der Kunde
    # nicht spricht. Gerechnet wird weiter in Stunden, wo es immer stand.
    def minuten(h):
        return None if h is None else int(round(float(h) * 60))

    guthaben = None
    if stand.get("abo"):
        guthaben = {
            "monat": stand["monat"],
            "produkt": stand["abo"]["produkt"],
            "kontingent_minuten": minuten(kontingent),
            "verbraucht_minuten": minuten(verbraucht),
            "rest_minuten": max(0, minuten(kontingent) - minuten(verbraucht)),
            "ueberzogen": bool(stand.get("ueberzogen")),
            # Nur Zeitpunkt und Dauer — was der Kunde pruefen kann. Der Name
            # des Bearbeiters ist unsere Betriebsfrage.
            "eintraege": [{"minuten": minuten(e["stunden"]),
                           "taetigkeit": e["taetigkeit"],
                           "erfasst_am": e["erfasst_am"]}
                          for e in stand.get("eintraege", [])],
        }

    return {
        "guthaben": guthaben,
        "hinweis": stand.get("hinweis", ""),
        "anfragen": [inhaltsanfrage.nach_aussen(a)
                     for a in inhaltsanfrage.liste(db, lead_id=user.lead_id)],
    }


class InhaltsWunsch(BaseModel):
    beschreibung: str
    seite: str = ""


@router.post("/inhalt", status_code=201)
def post_inhalt(body: InhaltsWunsch, user=Depends(get_current_user),
                db: Session = Depends(get_db)):
    """Einen Änderungswunsch aufnehmen.

    **Ueber dem Guthaben wird nicht blockiert.** Der Wunsch wird angenommen und
    im Bericht als „ueber dem Guthaben" ausgewiesen. Zu blockieren hiesse, eine
    Zusage zu machen, die im Datenblatt nicht steht.
    """
    from services import inhaltsanfrage

    if not user.lead_id:
        raise HTTPException(404, "Kein Betrieb gefunden")
    try:
        anfrage = inhaltsanfrage.anlegen(
            db, lead_id=user.lead_id, beschreibung=body.beschreibung,
            seite=body.seite, wer=user.email or "")
    except inhaltsanfrage.AnfrageFehler as fehler:
        raise HTTPException(400, str(fehler))
    return inhaltsanfrage.nach_aussen(anfrage)
