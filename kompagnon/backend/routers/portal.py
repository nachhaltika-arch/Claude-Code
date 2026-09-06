"""
Kundenportal endpoints — only for JWT-authenticated users with role 'kunde'.

GET  /api/portal/me                — project + phase progress
GET  /api/portal/messages          — message thread
POST /api/portal/messages          — send a message
GET  /api/portal/documents         — list uploaded files
POST /api/portal/documents/upload  — upload a file (multipart)
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from database import get_db, MitwirkungStand, Project, ProjectChecklist, Lead, User
from auth import oauth2_scheme
from routers.auth_router import get_current_user

logger = logging.getLogger(__name__)

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
    """Was wir vom Kunden brauchen — mit Stand und gerechneter Bauzeit."""
    from services import bauzeit_projekt
    from services import mitwirkung as kat

    project = None
    if user.lead_id:
        project = (db.query(Project).filter(Project.lead_id == user.lead_id)
                   .order_by(Project.created_at.desc()).first())
    if not project:
        return {"punkte": [], "spaeter": [], "offen": 0, "erledigt": 0,
                "gesamt": 0, "start_moeglich": False, "frist": None,
                "termin_link": "", "lead_id": user.lead_id}

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
            # **Was der Kunde hier tun kann** (04.09.2026). Bis dahin war die
            # Liste eine zum Abhaken: lesen, anderswo erledigen, bestaetigen.
            # Die Handlung gehoert zum Punkt und kommt aus dem Katalog —
            # eine Verzweigung nach Kennung in der Oberflaeche waere der
            # zweite Ort, an dem der Katalog gepflegt werden muss.
            "aktion": p.aktion,
            "dateiart": p.dateiart,
            "felder": [{"name": f, "beschriftung": b}
                       for f, b in kat.felder_fuer(p.kennung)],
            "wahlen": ([{"wert": w, "text": s} for w, s in kat.WER_TRAEGT_EIN.items()]
                       if p.aktion == kat.AKTION_DOMAIN
                       else [{"wert": w, "text": s} for w, s in kat.WER_SCHREIBT.items()]
                       if p.aktion == kat.AKTION_TEXTE else []),
            "notiz": (stand.notiz or "") if stand else "",
            # **Wann wir es vorgelegt haben** (L-166, 06.09.2026). Nur bei den
            # beiden Freigaben belegt. Ohne diesen Zeitpunkt ist die Fuenf-
            # Werktage-Zusage aus dem Angebot nicht nachpruefbar: Der Kunde
            # saehe eine Frist, deren Anfang nirgends steht.
            "vorgelegt_am": (stand.vorgelegt_am.isoformat()
                             if stand and stand.vorgelegt_am else None),
        }

    vor_start = [p for p in punkte if p.wirkung == kat.FRISTBEGINN]
    spaeter = [p for p in punkte if p.wirkung == kat.FRISTPAUSE]
    offen = kat.fristbeginn_offen(punkte, erledigt)

    # `Project` traegt keinen eigenen Namen — der Betrieb schon. Dieselbe
    # Ableitung wie in `/me`; zwei Wege zum selben Namen laufen auseinander.
    lead = db.query(Lead).filter(Lead.id == project.lead_id).first()

    # **Der Terminlink steht in den Einstellungen, nicht im Code.** Er
    # wechselt, wenn David den Kalender wechselt; ein fest verdrahteter Link
    # fuehrt dann ins Leere, und niemand merkt es, weil ein Link nicht rot
    # wird. Fehlt er, zeigt die Oberflaeche keinen toten Knopf, sondern
    # sagt, dass wir uns melden.
    termin_link = ""
    try:
        from database import SystemSettings
        eintrag = (db.query(SystemSettings)
                     .filter(SystemSettings.key == "termin_link").first())
        termin_link = (eintrag.value or "").strip() if eintrag else ""
    except Exception:  # noqa: BLE001 — eine fehlende Einstellung kippt die Seite nicht
        db.rollback()

    return {
        "projekt": (lead.company_name if lead else "") or "Ihr Projekt",
        "termin_link": termin_link,
        "lead_id": project.lead_id,
        # Getrennt ausgegeben, nicht in einer Liste mit einem Merkmal:
        # Lieferungen vor dem Start und Freigaben mittendrin sind zwei Dinge,
        # und gemischt sieht die Aufgabe doppelt so gross aus.
        "punkte": [zeile(p) for p in vor_start],
        "spaeter": [zeile(p) for p in spaeter],
        "offen": len(offen),
        "erledigt": len([p for p in vor_start if p.kennung in erledigt]),
        "gesamt": len(vor_start),
        "start_moeglich": not offen,
        # **Die Frist, gerechnet statt behauptet** (L-166, 06.09.2026). Der
        # Angebotsfuss sagt ein Bauzeitende zu und laesst es ruhen, wenn eine
        # Freigabe sich verzoegert. Bis heute stand die zweite Haelfte
        # nirgends — damit war das Ende von beiden Seiten nur behauptbar. Der
        # Block traegt alle Zwischenschritte, nicht nur das Datum: Wer es
        # prueft, muss sehen koennen, woraus es entstanden ist.
        "frist": bauzeit_projekt.frist_stand(db, project, staende=staende),
    }


class MitwirkungEintrag(BaseModel):
    notiz: str = ""
    #: Die Angaben zu diesem Punkt — Name je Feld, wie ihn `felder_fuer`
    #: nennt, dazu `wahl` und `hinweis`.
    #:
    #: **Bewusst ein freies Woerterbuch und trotzdem eng gefuehrt:** Was
    #: davon uebernommen wird, entscheidet `mitwirkung.notiz_bauen` anhand
    #: des Katalogs. Ein Feld, das dort nicht steht, faellt heraus — ein
    #: Aufrufer kann also nichts Fremdes in die Notiz schreiben, und ein
    #: neues Feld im Katalog wirkt hier ohne Aenderung.
    angaben: Dict[str, str] = {}


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

    # **Der Kunde schreibt seine Notiz nicht selbst.** `body.notiz` bleibt
    # fuer den freien Fall, aber wo der Katalog Felder kennt, entsteht die
    # Zeile aus ihnen — ein Aufrufer soll nicht bestimmen koennen, was im
    # Nachweis steht, aus dem spaeter der Fristbeginn abgeleitet wird.
    aus_angaben = kat.notiz_bauen(kennung, body.angaben or {})
    notiz = aus_angaben or (body.notiz or "")

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
    # Die Angaben ueberschreiben eine aeltere Notiz — wer nachtraegt, hat
    # etwas berichtigt. Ein leerer Aufruf loescht nichts.
    if notiz:
        stand.notiz = notiz
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


# ── Wer darf ans Geld? (L-160 Rang 4) ─────────────────────────────────
#
# **Steht hier oben, weil drei Bloecke darunter sie brauchen** — Zahlungen,
# Vertragsunterlagen und Rechnungen. FastAPI wertet die Abhaengigkeit beim
# Import aus; eine Sperre, die spaeter in der Datei steht, gibt es zu dem
# Zeitpunkt noch nicht.


def _stufe(user) -> str:
    from services.kundenzugang import stufe_von
    return stufe_von(user)


def verlangt_geldblick(user=Depends(get_current_user)):
    """Sperrt die schwache Stufe vor Rechnungen, Zahlungsart und Unterlagen.

    **Ohne diese Sperre waere die Stufe eine Behauptung.** Der Entwurf sagt
    dem Betrieb zu: „sieht alles ausser Rechnungen, Zahlungsart und
    Vertragsunterlagen." Steht die Zusage im Konto und wirkt nicht, ist sie
    schlimmer als keine — der Betrieb hat dann im guten Glauben jemandem
    Einblick gegeben, den er ausdruecklich ausschliessen wollte.
    """
    from services.kundenzugang import darf_geld_sehen

    if not darf_geld_sehen(_stufe(user)):
        raise HTTPException(
            403, "Dieser Zugang darf keine Rechnungen und Zahlungsdaten sehen")
    return user


# ══════════════════════════════════════════════════════════════════════
# Auskunft und Loeschung — Art. 15 und 17 DSGVO (L-160 Rang 5)
# ══════════════════════════════════════════════════════════════════════
#
# **Beides ist ein gesetzlicher Anspruch**, und beides ging bisher nur ueber
# eine Mail an uns. Wer sie nicht beantwortet bekommt, hat einen Verstoss in
# der Hand — und keine Spur, dass er gefragt hat.


@router.get("/datenkopie")
def get_datenkopie(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was ueber diesen Betrieb gespeichert ist — Art. 15 DSGVO.

    **Auch die leeren Bereiche stehen drin.** Eine Auskunft, die nur
    Gefundenes nennt, beantwortet die Frage nicht: „Was habt ihr ueber mich?"
    schliesst „in diesem Bereich nichts" ein.

    **Und kein Kennwort, kein Zweitfaktor, kein Zuruecksetzen-Token.** Die
    Kopie wird heruntergeladen, weitergeschickt und liegt danach irgendwo.
    Art. 15 verlangt Auskunft ueber die Daten, nicht die Herausgabe der
    Zugangsmittel.
    """
    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None

    def zaehle(tabelle: str, spalte: str = "lead_id") -> int:
        if not user.lead_id:
            return 0
        try:
            zeile = db.execute(text(
                f"SELECT COUNT(*) FROM {tabelle} WHERE {spalte} = :w"),
                {"w": user.lead_id}).fetchone()
            return int(zeile[0]) if zeile else 0
        except Exception:  # noqa: BLE001 — eine fehlende Tabelle ist kein Datum
            db.rollback()
            return 0

    bereiche = [
        {"titel": "Projekte", "anzahl": zaehle("projects")},
        {"titel": "Hochgeladene Dateien", "anzahl": zaehle("project_files")},
        {"titel": "Rechnungen", "anzahl": zaehle("invoices")},
        {"titel": "Nachrichten und Mails", "anzahl": zaehle("communications")},
        {"titel": "Audits Ihrer Website", "anzahl": zaehle("audit_results")},
        {"titel": "Änderungswünsche", "anzahl": zaehle("inhalts_anfragen")},
        {"titel": "Leistungsberichte", "anzahl": zaehle("leistungsberichte")},
        {"titel": "Zugänge", "anzahl": zaehle("users")},
    ]

    return {
        "erstellt_am": datetime.utcnow().isoformat(),
        # Das Konto — ausdruecklich Feld fuer Feld, nicht als Abbild des
        # Datensatzes: Ein `dict(user.__dict__)` haette den Kennworthash
        # mitgenommen, und zwar still.
        "konto": {
            "email": user.email,
            "vorname": user.first_name or "",
            "nachname": user.last_name or "",
            "telefon": user.phone or "",
            "rolle": user.role,
            "angelegt_am": user.created_at.isoformat() if user.created_at else None,
            "zuletzt_angemeldet": user.last_login.isoformat() if user.last_login else None,
        },
        "betrieb": {
            "id": lead.id if lead else None,
            "name": (lead.company_name or "") if lead else "",
            "ansprechpartner": (lead.contact_name or "") if lead else "",
            "email": (lead.email or "") if lead else "",
            "telefon": (lead.phone or "") if lead else "",
            "website": (lead.website_url or "") if lead else "",
        } if lead else {},
        "bereiche": bereiche,
        "hinweis": ("Diese Übersicht nennt, was wir zu Ihrem Betrieb führen. "
                    "Möchten Sie die Inhalte eines Bereichs vollständig "
                    "erhalten, schreiben Sie uns — wir liefern sie binnen "
                    "eines Monats (Art. 12 DSGVO)."),
    }


class LoeschAntrag(BaseModel):
    bestaetigung: str = ""
    verstanden: bool = False


def _loesch_huerden(db: Session, user) -> tuple:
    """Die drei Dinge, die einer Loeschung im Weg stehen — und sie sind ungleich.

    Rueckgabe: (Huerdenliste, moeglich, Sperrgrund).
    """
    from services import abo_vertrag

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    laeuft = vertrag is not None

    huerden = [
        {
            "titel": f"Ihr Pflege-Abo ({vertrag.produkt}) läuft" if vertrag
                     else "Kein laufendes Pflege-Abo",
            "dazu": ("Solange es läuft, können wir das Konto nicht löschen — es "
                     "ist die Grundlage der monatlichen Abbuchung. Kündigen Sie "
                     "zuerst; danach merken wir die Löschung vor."
                     if laeuft else
                     "Es steht kein laufender Vertrag entgegen."),
            "erfuellt": not laeuft,
            "ausraeumbar": True,
        },
        {
            "titel": "Ihre Website läuft auf unserem Hosting",
            "dazu": ("Mit dem Konto endet das Hosting, und Ihre Seite ist nicht "
                     "mehr erreichbar. Die Domain gehört Ihnen; wir legen sie "
                     "auf Ihren neuen Anbieter um und geben Ihnen die Inhalte "
                     "mit. Schreiben Sie uns, bevor Sie löschen."),
            # **Keine Sperre, eine Warnung.** Wer trotzdem loeschen will, darf
            # das — es sind seine Daten. Aber er soll die Folge vorher kennen.
            "erfuellt": None,
            "ausraeumbar": True,
        },
        {
            "titel": "Rechnungen bleiben zehn Jahre",
            "dazu": ("Das ist keine Wahl, sondern eine Pflicht: § 147 "
                     "Abgabenordnung verlangt es. Sie liegen danach gesperrt "
                     "in der Buchhaltung und werden für nichts anderes "
                     "verwendet."),
            # Weder erfuellt noch offen — sie **gilt**. Sie als Hindernis
            # darzustellen, das man ausraeumen kann, waere falsch.
            "erfuellt": None,
            "ausraeumbar": False,
        },
    ]
    sperrgrund = ("Erst wenn Ihr Pflege-Abo gekündigt ist. Es ist die Grundlage "
                  "der monatlichen Abbuchung.") if laeuft else ""
    return huerden, not laeuft, sperrgrund


@router.get("/loeschung")
def get_loeschung(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was einer Loeschung im Weg steht — und ob schon eine beantragt ist."""
    huerden, moeglich, sperrgrund = _loesch_huerden(db, user)

    antrag = None
    try:
        zeile = db.execute(text(
            "SELECT beantragt_am, frist_bis, zustand FROM loeschantraege "
            "WHERE lead_id = :l"), {"l": user.lead_id}).fetchone()
        if zeile:
            antrag = {"beantragt_am": zeile[0].isoformat() if zeile[0] else None,
                      "frist_bis": zeile[1].isoformat() if zeile[1] else None,
                      "zustand": zeile[2]}
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keinen Antrag
        db.rollback()

    return {"huerden": huerden, "moeglich": moeglich, "sperrgrund": sperrgrund,
            "antrag": antrag,
            "folgen": [
                "Ihre Zugänge und die Ihrer Kollegen werden gelöscht. Niemand "
                "kann sich mehr anmelden.",
                "Ihre Website und das Hosting enden.",
                "Hochgeladene Dateien, Briefings und Berichte werden gelöscht.",
                "Rechnungen bleiben zehn Jahre gesperrt in der Buchhaltung "
                "(§ 147 AO).",
            ]}


@router.post("/loeschung")
def beantrage_loeschung(body: LoeschAntrag,
                        user=Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """Die Loeschung **beantragen** — Art. 17 DSGVO.

    **Sie geschieht nicht hier.** Eine Loeschung, die sofort greift, ist bei
    einem Betrieb ohne zweiten Zugang ein Ausfall ohne Rueckweg. Was hier
    entsteht, ist der **Nachweis des Eingangs**; ab ihm laeuft die Monatsfrist
    aus Art. 12.

    **Zwei Huerden, weil ein Klick zu wenig ist:** das Wort und das Haeckchen.
    """
    if (body.bestaetigung or "").strip().upper() != "LÖSCHEN":
        raise HTTPException(400, "Bitte tippen Sie LÖSCHEN, um fortzufahren")
    if not body.verstanden:
        raise HTTPException(400, "Bitte bestätigen Sie, dass Sie die Folgen kennen")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    _, moeglich, sperrgrund = _loesch_huerden(db, user)
    if not moeglich:
        # 409 und nicht 403: Es fehlt keine Berechtigung, es steht ein
        # Vertrag entgegen. Der Unterschied steht in der Meldung.
        raise HTTPException(409, sperrgrund)

    # **Der erste Antrag zaehlt.** Ein zweiter Klick darf die Monatsfrist
    # nicht neu starten — das waere zu unseren Gunsten, und niemand saehe es.
    vorhanden = db.execute(text(
        "SELECT beantragt_am, frist_bis FROM loeschantraege WHERE lead_id = :l"),
        {"l": user.lead_id}).fetchone()
    if vorhanden:
        return {"ok": True, "beantragt_am": vorhanden[0].isoformat(),
                "frist_bis": vorhanden[1].isoformat() if vorhanden[1] else None,
                "schon_beantragt": True}

    jetzt = datetime.utcnow()
    frist = jetzt + timedelta(days=30)
    db.execute(text(
        "INSERT INTO loeschantraege (lead_id, beantragt_von, beantragt_am, "
        "frist_bis, zustand) VALUES (:l, :v, :a, :f, 'offen')"),
        {"l": user.lead_id, "v": user.email, "a": jetzt, "f": frist})
    db.commit()
    logger.warning("Loeschantrag nach Art. 17 DSGVO: Betrieb %s durch %s, "
                   "Frist bis %s", user.lead_id, user.email, frist.date())

    return {"ok": True, "beantragt_am": jetzt.isoformat(),
            "frist_bis": frist.isoformat(), "schon_beantragt": False}


# ══════════════════════════════════════════════════════════════════════
# Vertragsunterlagen (L-160 Rang 7)
# ══════════════════════════════════════════════════════════════════════
#
# **Der Befund:** Angebot, AGB-Fassung und Auftragsbestaetigung liegen im
# System, und der Kunde kommt nicht heran. Die Auftragsbestaetigung gibt es
# als PDF am Projekt; ihr einziger Auslieferungsweg verlangt `require_admin`.
#
# **Was hier ausdruecklich nicht geschieht: etwas erfinden.** Wo eine
# Unterlage nicht vorliegt, sagt die Antwort das — mit Grund. Eine Liste mit
# fuenf Zeilen, von denen drei ins Leere fuehren, ist schlechter als eine mit
# zwei.


@router.get("/vertragsunterlagen")
def get_vertragsunterlagen(user=Depends(verlangt_geldblick),
                           db: Session = Depends(get_db)):
    """Alles, was der Kunde unterschrieben hat — in der Fassung seines Auftrags."""
    import os as _os

    unterlagen = []
    projekt = None
    if user.lead_id:
        projekt = (db.query(Project).filter(Project.lead_id == user.lead_id)
                   .order_by(Project.created_at.desc()).first())

    # ── Auftragsbestaetigung ──────────────────────────────────────────
    pfad = getattr(projekt, "auftragsbestaetigung_pdf", None) if projekt else None
    hat_datei = bool(pfad and _os.path.exists(pfad))
    unterlagen.append({
        "titel": "Auftragsbestätigung",
        "stand": (projekt.created_at.date().isoformat()
                  if projekt and projekt.created_at else ""),
        "vorhanden": hat_datei,
        # **`art` statt Praefix-Raten in der Oberflaeche.** Die erste Fassung
        # liess den Bildschirm `adresse.startsWith("/api/")` pruefen — also
        # aus der Form der Adresse schliessen, wie sie abzurufen ist. Wie
        # eine Unterlage geholt wird, ist eine Eigenschaft der Unterlage.
        "art": "pdf" if hat_datei else "",
        "adresse": (f"/api/portal/vertragsunterlagen/auftragsbestaetigung/{projekt.id}"
                    if hat_datei else ""),
        "grund": "" if hat_datei else (
            "Für diesen Auftrag liegt keine Auftragsbestätigung als PDF vor. "
            "Sie entsteht beim Kauf über die Kasse; bei älteren oder von Hand "
            "angelegten Aufträgen fehlt sie. Schreiben Sie uns, dann schicken "
            "wir sie nach."),
    })

    # ── AGB-Fassung ───────────────────────────────────────────────────
    #
    # **Zwei Quellen, und nur eine trägt.** Der Shop haelt die Fassung je
    # Bestellung fest (`bestellungen.terms_version`, ORDERS_05). Der
    # **Websprint**-Kauf ueber Stripe tut das **nicht** — dort entsteht kein
    # Nachweis, welche Fassung galt. Das steht als eigener Eintrag im
    # Lagebild; hier wird es benannt statt verschwiegen.
    fassung, wann = "", ""
    try:
        zeile = db.execute(text(
            "SELECT terms_version, terms_accepted_at FROM bestellungen "
            "WHERE email = :mail AND terms_version <> '' "
            "ORDER BY created_at DESC LIMIT 1"), {"mail": user.email}).fetchone()
        if zeile:
            fassung = zeile[0] or ""
            wann = zeile[1].date().isoformat() if zeile[1] else ""
    except Exception:  # noqa: BLE001 — ohne Shop-Tabelle bleibt es leer
        db.rollback()

    unterlagen.append({
        "titel": "AGB-Fassung",
        "stand": f"{fassung}, zugestimmt am {wann}" if fassung and wann else fassung,
        "vorhanden": bool(fassung),
        "art": "seite" if fassung else "",
        "adresse": "/agb" if fassung else "",
        "grund": "" if fassung else (
            "Für Ihren Auftrag ist keine AGB-Fassung festgehalten. Bei Käufen "
            "über den Shop wird sie mit dem Datum Ihrer Zustimmung gespeichert; "
            "beim Websprint über die Kasse geschieht das bisher nicht."),
    })

    # ── Angebot ───────────────────────────────────────────────────────
    #
    # Das Angebot entsteht heute **auf Abruf** aus dem Audit
    # (`routers/audit.py::download_angebot_pdf`) und wird nicht als Dokument
    # aufbewahrt. Ein Link darauf zeigte also auf ein Erzeugnis von heute,
    # nicht auf das, was der Kunde damals gelesen hat — und genau darauf
    # kommt es bei einer Vertragsunterlage an.
    unterlagen.append({
        "titel": "Angebot",
        "stand": "", "vorhanden": False, "art": "", "adresse": "",
        "grund": ("Ihr Angebot wird bei Bedarf neu aus dem Audit erzeugt und "
                  "nicht als Dokument aufbewahrt. Ein Abruf hier zeigte ein "
                  "Angebot von heute, nicht das, dem Sie zugestimmt haben. "
                  "Fordern Sie es bei uns an — wir schicken die Fassung, die "
                  "für Ihren Auftrag gilt."),
    })

    return {"unterlagen": unterlagen, "projekt_id": projekt.id if projekt else None}


@router.get("/vertragsunterlagen/auftragsbestaetigung/{projekt_id}")
def hole_auftragsbestaetigung(projekt_id: int,
                              user=Depends(verlangt_geldblick),
                              db: Session = Depends(get_db)):
    """Die Auftragsbestaetigung des **eigenen** Betriebs.

    **Der Filter steht auf `lead_id`, nicht nur auf der Projektnummer** —
    sonst waere eine fortlaufende Zahl der Schluessel zu jeder fremden
    Bestaetigung. 404 statt 403: Ob es die Nummer anderswo gibt, geht diesen
    Betrieb nichts an.
    """
    import os as _os

    from fastapi.responses import FileResponse

    projekt = (db.query(Project).filter(Project.id == projekt_id,
                                        Project.lead_id == user.lead_id).first())
    pfad = getattr(projekt, "auftragsbestaetigung_pdf", None) if projekt else None
    if not pfad or not _os.path.exists(pfad):
        raise HTTPException(404, "Auftragsbestätigung nicht vorhanden")

    return FileResponse(pfad, media_type="application/pdf",
                        filename="KOMPAGNON-Auftragsbestaetigung.pdf")


# ══════════════════════════════════════════════════════════════════════
# Zugaenge fuer Kollegen (L-160 Rang 4, K7)
# ══════════════════════════════════════════════════════════════════════
#
# **Ein Betrieb ist keine Person.** Bis heute hatte er genau ein Konto; wer
# einem Kollegen Zugang geben wollte, gab sein Kennwort weiter — und damit den
# Blick auf Rechnungen und Zahlungsart. Die Routen zum Anlegen von Konten gibt
# es laengst (`/api/admin/users`), aber sie verlangen `manage_users`, also
# Innendienst: Jeder Zugang musste bei uns beantragt werden.
#
# **Die Stufen und ihre Wirkung stehen in `services/kundenzugang.py`**, nicht
# hier. Sie gelten an mehreren Stellen, und eine Rechteregel an drei Orten ist
# eine, die an zweien veraltet.


class ZugangEinladung(BaseModel):
    email: str
    recht: str = "ansehen"


@router.get("/zugaenge")
def get_zugaenge(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Wer alles Zugang zu diesem Betrieb hat.

    **Lesen darf jeder Zugang des Betriebs**, auch die schwache Stufe: Wer
    hereinkommt, soll sehen, wer sonst noch hereinkommt. Verwalten darf nur
    die starke — sonst koennte ein Mitleser sich selbst hochstufen.
    """
    from services.kundenzugang import (BESCHREIBUNG, STUFEN, darf_verwalten,
                                       stufe_von)

    if not user.lead_id:
        return {"zugaenge": [], "darf_verwalten": False, "stufen": []}

    konten = (db.query(User).filter(User.lead_id == user.lead_id,
                                    User.role == "kunde")
              .order_by(User.created_at.asc()).all())

    return {
        "darf_verwalten": darf_verwalten(stufe_von(user)),
        "stufen": [{"wert": s, "text": BESCHREIBUNG[s]} for s in STUFEN],
        # **Kein Kennwort, kein Token, keine Sitzungskennung.** Diese Liste
        # steht auf einem Bildschirm, den mehrere Personen sehen.
        "zugaenge": [{
            "id": k.id,
            "email": k.email,
            "name": f"{k.first_name or ''} {k.last_name or ''}".strip(),
            "recht": stufe_von(k),
            "selbst": k.id == user.id,
            # Ein Konto ohne Kennwort hat die Einladung noch nicht angenommen.
            "eingeladen": not bool(k.password_hash),
            "zuletzt": k.last_login.isoformat() if k.last_login else None,
        } for k in konten],
    }


@router.post("/zugaenge")
def lade_zugang_ein(body: ZugangEinladung,
                    user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Einen Kollegen einladen — am eigenen Betrieb.

    **Der Betrieb kommt aus der Anmeldung, nicht aus dem Aufruf.** Ein
    `lead_id` im Rumpf waere die Einladung in einen fremden Betrieb.

    **Ohne Kennwort angelegt.** Es entsteht ueber den Zuruecksetzen-Weg, den
    es schon gibt — ein zweiter Weg, Kennwoerter zu vergeben, waere ein
    zweiter, der falsch sein kann.
    """
    from services.kundenzugang import darf_verwalten, pruefe_stufe, stufe_von

    if not darf_verwalten(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf keine weiteren einrichten")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    try:
        recht = pruefe_stufe(body.recht)
    except ValueError as fehler:
        raise HTTPException(400, str(fehler)) from fehler

    adresse = (body.email or "").strip().lower()
    if "@" not in adresse or len(adresse) < 5:
        raise HTTPException(400, "Bitte eine gültige E-Mail-Adresse angeben")

    vorhanden = db.query(User).filter(User.email == adresse).first()
    if vorhanden:
        # **Kein stilles Umhaengen.** Ein bestehendes Konto einem anderen
        # Betrieb zuzuschlagen waere ein Zugriff auf fremde Daten per
        # Einladung.
        raise HTTPException(400, "Zu dieser Adresse gibt es bereits ein Konto")

    neu = User(email=adresse, role="kunde", lead_id=user.lead_id,
               is_active=True, kunde_recht=recht, created_by=user.id)
    db.add(neu)
    db.commit()
    db.refresh(neu)

    # **Die Einladungsmail darf den Zugang nicht kosten** — sie ist der
    # bequeme Teil, das Konto der wesentliche. Scheitert sie, sagt die
    # Antwort das, statt den ganzen Vorgang zurueckzunehmen.
    versandt = False
    try:
        from services.email import send_password_reset_email
        from services.qr_service import generate_token

        neu.password_reset_token = generate_token()
        neu.password_reset_expires = datetime.utcnow() + timedelta(days=7)
        db.commit()
        versandt = bool(send_password_reset_email(
            neu.email, neu.password_reset_token, neu.email))
    except Exception as fehler:  # noqa: BLE001 — siehe Kommentar
        logger.warning("Einladung an %s: Mail nicht versandt (%s)",
                       adresse, type(fehler).__name__)

    return {"ok": True, "id": neu.id, "email": neu.email, "recht": recht,
            "mail_versandt": versandt}


@router.delete("/zugaenge/{zugang_id}")
def entferne_zugang(zugang_id: int, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Einen Zugang entfernen — nicht den eigenen.

    **Den eigenen nicht**, weil der letzte starke Zugang sonst verschwinden
    koennte und niemand mehr Zugaenge verwalten duerfte. Der Betrieb waere
    ausgesperrt und muesste beim Innendienst anrufen.
    """
    from services.kundenzugang import darf_verwalten, stufe_von

    if not darf_verwalten(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf keine anderen entfernen")
    if zugang_id == user.id:
        raise HTTPException(400, "Den eigenen Zugang können Sie hier nicht entfernen")

    konto = (db.query(User).filter(User.id == zugang_id,
                                   User.lead_id == user.lead_id,
                                   User.role == "kunde").first())
    if not konto:
        # 404 und nicht 403: Ob es die Kennung anderswo gibt, geht diesen
        # Betrieb nichts an.
        raise HTTPException(404, "Zugang nicht gefunden")

    db.delete(konto)
    db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════
# Was im Pflege-Abo steckt (L-160, Rang 3)
# ══════════════════════════════════════════════════════════════════════
#
# **Der Befund vom 04.09.2026:** Zwoelf Positionen, fuer die der Betrieb
# monatlich zahlt — und **keine einzige** war im Konto abrufbar. Weder was er
# bekommt, noch wie viel er genutzt hat, noch wie er es anfordert. Ein Abo,
# dessen Leistungen man nicht sieht, wird gekuendigt, weil es sich nach nichts
# anfuehlt.
#
# **Die Liste steht im Katalog, nicht hier.** `services/leistungsverzeichnis.py`
# fuehrt den Wortlaut des Datenblatts; dieser Endpunkt beantwortet nur, welches
# Abo laeuft und was daraus folgt.


@router.get("/leistungen")
def get_leistungen(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was der Kunde fuer sein Pflege-Abo bekommt — und was nicht.

    **Ohne laufendes Abo bleibt die Liste leer.** Kein Basic-Umfang als
    Vorgabe: Wer keinen Pflegevertrag hat, saehe sonst Zusagen, die niemand
    gegeben hat.
    """
    from services import abo_vertrag
    from services import leistungsverzeichnis as lz

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    produkt = vertrag.produkt if vertrag else None
    positionen = lz.fuer_produkt(produkt or "")

    return {
        "produkt": produkt,
        "seit": vertrag.start_monat if vertrag else None,
        # **Die Zusage getrennt herausgegeben**, obwohl sie auch in der Liste
        # steht. Der Support-Bildschirm braucht genau diesen einen Satz und
        # soll die zwoelf Positionen dafuer nicht durchsuchen muessen — sonst
        # entstuende dort eine zweite Auswahllogik.
        "reaktionszeit": lz.reaktionszeit(produkt or ""),
        "nicht_enthalten": list(lz.NICHT_ENTHALTEN) if produkt else [],
        "verfall_hinweis": lz.VERFALL_HINWEIS if produkt else "",
        "positionen": [{
            "nummer": p.nummer, "titel": p.titel, "warum": p.warum,
            "vertragstext": p.vertragstext, "frequenz": p.frequenz,
            "ort": p.ort, "zusage": p.zusage,
        } for p in positionen],
    }


# ══════════════════════════════════════════════════════════════════════
# Dazubuchen (Entwurf `kundenkonto-neu`)
# ══════════════════════════════════════════════════════════════════════
#
# **Die Buchung ist eine verbindliche Erklaerung, keine Automatik.** Ein
# Wechsel auf Pflege Pro heisst Lastschrift ueber 177,31 € im Monat. Den
# Vertrag zu wechseln **und** das Stripe-Abo umzustellen, waeren zwei
# Eingriffe ins Geld auf einen Klick, ohne dass ein Mensch dazwischen sieht.
# Was hier entsteht, ist die Erklaerung mit Zeitpunkt, Preis und Wortlaut;
# umgesetzt wird sie vom Innendienst.


class BuchungsWunsch(BaseModel):
    verstanden: bool = False
    notiz: str = ""


def _folgemonat() -> str:
    """Der kommende Monatserste, als `JJJJ-MM`.

    Der Wechsel gilt nie im laufenden Monat: `abo_vertrag.wechseln` weist das
    ausdruecklich ab, weil zwei Vertraege im selben Monat nicht
    unterscheidbar waeren.
    """
    jetzt = datetime.utcnow()
    jahr, monat = (jetzt.year + 1, 1) if jetzt.month == 12 else (jetzt.year, jetzt.month + 1)
    return f"{jahr}-{monat:02d}"


def _offene_buchungen(db: Session, lead_id: int) -> dict:
    try:
        return {z[0]: z[1] for z in db.execute(text(
            "SELECT kennung, gebucht_am FROM buchungen "
            "WHERE lead_id = :l AND zustand = 'offen'"), {"l": lead_id}).fetchall()}
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keine Buchungen
        db.rollback()
        return {}


@router.get("/dazubuchen")
def get_dazubuchen(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was dieser Kunde dazubuchen kann — mit Grund, wo nicht."""
    from services import abo_vertrag
    from services import dazubuchen as dz
    from services.kundenzugang import darf_handeln, stufe_von

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    offen = _offene_buchungen(db, user.lead_id) if user.lead_id else {}

    return {
        # **Wer nur ansehen darf, sieht die Angebote — und keinen Knopf.**
        # Eine Preisliste ist keine Handlung; das Buchen ist eine.
        "darf_buchen": darf_handeln(stufe_von(user)),
        "ab_monat": _folgemonat(),
        "angebote": [{
            "kennung": a.kennung, "titel": a.titel, "nummer": a.nummer,
            "netto_cent": a.netto_cent, "brutto_cent": a.brutto_cent,
            "steuersatz": dz.STEUERSATZ, "einmalig": a.einmalig,
            "dazu": a.dazu, "punkte": list(a.punkte),
            "zahlung": a.zahlung, "laufzeit": a.laufzeit,
            "rechtstext": a.rechtstext, "danach": a.danach,
            "buchbar": buchbar and a.kennung not in offen,
            "gebucht": a.kennung in offen,
            "gebucht_am": (offen[a.kennung].isoformat()
                           if a.kennung in offen and offen[a.kennung] else None),
            "grund": grund,
        } for a, buchbar, grund in dz.buchbar_fuer(
            vertrag.produkt if vertrag else "", offen)],
    }


@router.post("/dazubuchen/{kennung}")
def buche_dazu(kennung: str, body: BuchungsWunsch,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Ein Angebot verbindlich buchen.

    **Zwei Hürden vor dem Geld:** die Rechtestufe und die ausdrueckliche
    Bestaetigung, den Wortlaut gelesen zu haben. Ein Klick ist zu wenig fuer
    eine Lastschrift.

    **Der Wortlaut und der Preis von heute werden mitgeschrieben.** Aendern wir
    beides spaeter, belegt die Buchung sonst nur, dass jemand irgendwann
    geklickt hat — dieselbe Ueberlegung wie bei der AGB-Fassung (ORDERS_05).
    """
    from services import abo_vertrag
    from services import dazubuchen as dz
    from services.kundenzugang import darf_handeln, stufe_von

    angebot = dz.ANGEBOTE.get(kennung.upper())
    if not angebot:
        raise HTTPException(404, f"Unbekanntes Angebot: {kennung}")
    if not darf_handeln(stufe_von(user)):
        raise HTTPException(403, "Dieser Zugang darf nichts dazubuchen")
    if not body.verstanden:
        raise HTTPException(400, "Bitte bestätigen Sie, dass Sie die Bedingungen gelesen haben")
    if not user.lead_id:
        raise HTTPException(400, "Kein Betrieb am Konto")

    vertrag = abo_vertrag.laufender(db, user.lead_id)
    passend = [a for a, buchbar, _ in dz.buchbar_fuer(
        vertrag.produkt if vertrag else "", _offene_buchungen(db, user.lead_id))
        if a.kennung == angebot.kennung and buchbar]
    if not passend:
        raise HTTPException(409, "Dieses Angebot steht Ihnen gerade nicht offen")

    ab = _folgemonat() if not angebot.einmalig else ""
    jetzt = datetime.utcnow()
    db.execute(text(
        "INSERT INTO buchungen (lead_id, kennung, gebucht_von, gebucht_am, "
        "ab_monat, preis_netto_cent, preis_brutto_cent, rechtstext, zustand, notiz) "
        "VALUES (:l, :k, :v, :g, :ab, :n, :b, :r, 'offen', :no)"),
        {"l": user.lead_id, "k": angebot.kennung, "v": user.email, "g": jetzt,
         "ab": ab, "n": angebot.netto_cent, "b": angebot.brutto_cent,
         "r": angebot.rechtstext, "no": (body.notiz or "")[:1000]})
    db.commit()
    logger.warning("Buchung: Betrieb %s bucht %s (%s Cent brutto) durch %s",
                   user.lead_id, angebot.kennung, angebot.brutto_cent, user.email)

    return {"ok": True, "kennung": angebot.kennung,
            "gebucht_am": jetzt.isoformat(), "ab_monat": ab or _folgemonat(),
            "danach": angebot.danach}


# ══════════════════════════════════════════════════════════════════════
# Bezahlte Leistungen abrufen (L-160 Rang 6)
# ══════════════════════════════════════════════════════════════════════
#
# Zwei Positionen des Leistungsverzeichnisses konnte der Kunde **nicht
# anfordern**, obwohl er sie monatlich bezahlt: die Ruecksicherung und die
# eine neue Unterseite im Jahr. „Selten gebraucht, aber im Ernstfall dringend
# — und dann sucht niemand nach der Telefonnummer."


class AbrufWunsch(BaseModel):
    notiz: str = ""


def _abrufbare(db: Session, user):
    """Die Positionen, die dieses Abo abrufen laesst — leer ohne Vertrag."""
    from services import abo_vertrag
    from services import leistungsverzeichnis as lz

    vertrag = abo_vertrag.laufender(db, user.lead_id) if user.lead_id else None
    if not vertrag:
        return []
    return [p for p in lz.fuer_produkt(vertrag.produkt) if p.abruf]


@router.get("/abrufe")
def get_abrufe(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Was abrufbar ist und was schon angefordert wurde."""
    positionen = _abrufbare(db, user)

    offen = {}
    try:
        for zeile in db.execute(text(
                "SELECT position, angefordert_am FROM abrufe "
                "WHERE lead_id = :l AND zustand = 'offen'"),
                {"l": user.lead_id}).fetchall():
            offen[int(zeile[0])] = zeile[1]
    except Exception:  # noqa: BLE001 — ohne Tabelle gibt es keine Abrufe
        db.rollback()

    return {"abrufe": [{
        "nummer": p.nummer, "titel": p.titel, "warum": p.warum,
        "frequenz": p.frequenz, "knopf": p.abruf, "danach": p.abruf_danach,
        "offen": p.nummer in offen,
        "angefordert_am": (offen[p.nummer].isoformat()
                           if p.nummer in offen and offen[p.nummer] else None),
    } for p in positionen]}


@router.post("/abrufe/{position}")
def fordere_ab(position: int, body: AbrufWunsch,
               user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Eine bezahlte Leistung anfordern.

    **Der Abruf loest nichts aus, er meldet an.** Eine Ruecksicherung ist
    Handarbeit am Datenbestand; sie auf Knopfdruck zu starten waere die
    gefaehrlichste Automatik im Haus.
    """
    from services import leistungsverzeichnis as lz

    punkt = lz.NACH_NUMMER.get(position)
    if not punkt:
        raise HTTPException(404, f"Unbekannte Position: {position}")
    if not punkt.abruf:
        raise HTTPException(400, f"„{punkt.titel}“ wird nicht abgerufen")
    if punkt not in _abrufbare(db, user):
        # 403 und nicht 404: Die Position gibt es, sein Vertrag kennt sie
        # nicht. Der Unterschied steht in der Meldung.
        raise HTTPException(403, f"„{punkt.titel}“ gehört nicht zu Ihrem Vertrag")

    vorhanden = db.execute(text(
        "SELECT angefordert_am FROM abrufe WHERE lead_id = :l AND position = :p "
        "AND zustand = 'offen'"), {"l": user.lead_id, "p": position}).fetchone()
    if vorhanden:
        # **Der erste Klick zaehlt.** Sonst stuenden beim Innendienst zwei
        # Anforderungen fuer dieselbe Sache — mit zwei Anfangszeitpunkten fuer
        # dieselbe zugesagte Reaktionszeit.
        return {"ok": True, "angefordert_am": vorhanden[0].isoformat(),
                "danach": punkt.abruf_danach, "schon_offen": True}

    jetzt = datetime.utcnow()
    db.execute(text(
        "INSERT INTO abrufe (lead_id, position, angefordert_von, "
        "angefordert_am, notiz, zustand) VALUES (:l, :p, :v, :a, :n, 'offen')"),
        {"l": user.lead_id, "p": position, "v": user.email, "a": jetzt,
         "n": (body.notiz or "")[:2000]})
    db.commit()
    logger.info("Abruf: Betrieb %s fordert Position %s an (%s)",
                user.lead_id, position, punkt.titel)

    return {"ok": True, "angefordert_am": jetzt.isoformat(),
            "danach": punkt.abruf_danach, "schon_offen": False}


@router.get("/zahlungen")
def get_zahlungen(user=Depends(verlangt_geldblick), db: Session = Depends(get_db)):
    """Abos, Rechnungen und der Zustand des Zahlungskontos."""
    from services import abo_vertrag, zahlungsportal

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        return {"abos": [], "rechnungen": [], "zahlungskonto": "kein_betrieb"}

    from services import abo_stunden

    # **Der Kunde sieht, was er zahlt und wie es eingezogen wird.** Bis zum
    # 04.09.2026 stand hier nur Produkt und Zeitraum — ein Abo ohne Betrag
    # ist genau die Leerstelle aus L-160.
    abos = [{"produkt": v.produkt, "start_monat": v.start_monat,
             "end_monat": v.end_monat, "notiz": v.notiz or "",
             "abrechnung": v.abrechnung,
             "einzug_eingerichtet": bool(v.stripe_subscription_id),
             # **Netto, Steuersatz und brutto — alle drei** (Entscheidung
             # David, 04.09.2026: die Abo-Preise sind netto gemeint). Der
             # Betrieb hat „149 € netto" unterschrieben und bekommt 177,31 €
             # abgebucht. Nur eine der beiden Zahlen zu zeigen erzeugt den
             # Anruf, der mit „bei mir steht aber etwas anderes" beginnt.
             "brutto_cent": abo_stunden.preis_brutto_cent(v.produkt),
             "netto_cent": abo_stunden.preis_netto_cent(v.produkt),
             "steuersatz": abo_stunden.STEUERSATZ_ABO,
             "laeuft": v.end_monat is None}
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


@router.post("/zahlungen/einzug")
def zahlungen_einzug(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Den Einzug für das laufende Pflege-Abo einrichten (Entscheidung 04.09.2026).

    **Warum das der Kunde selbst tut.** Eine Einzugsermächtigung ist seine
    Zustimmung; sie lässt sich nicht im Innendienst setzen. Der Vertrag steht
    schon — hier wird nur der Weg eröffnet, auf dem Stripe die Erlaubnis
    einholt und das Abonnement startet.

    **Ein Vertrag auf `rechnung` bekommt hier nichts.** Er ist unter anderen
    Bedingungen geschlossen worden, und der Aufstellungslauf berechnet ihn.
    Ihm hier stillschweigend eine Abbuchung anzubieten hieße, die Bedingung
    zu wechseln, ohne dass jemand zustimmt.
    """
    from services import abo_stripe, abo_vertrag, zahlungsportal
    from services.base_urls import public_base_url

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        raise HTTPException(404, "Kein Betrieb gefunden")

    vertrag = abo_vertrag.laufender(db, lead.id)
    if vertrag is None:
        raise HTTPException(409, "Für Ihren Betrieb läuft kein Pflege-Abo.")
    if vertrag.abrechnung != "stripe":
        raise HTTPException(
            409, "Dieses Abo wird per Rechnung abgerechnet. Wenn Sie auf "
                 "Lastschrift wechseln möchten, sagen Sie uns kurz Bescheid.")
    if vertrag.stripe_subscription_id:
        raise HTTPException(409, "Der Einzug ist für dieses Abo bereits eingerichtet.")

    try:
        kennung = zahlungsportal.kundenkennung(db, lead) or ""
    except zahlungsportal.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")

    ziel = f"{public_base_url()}/app/portal"
    try:
        return abo_stripe.kaufweg(
            vertrag.produkt, lead_id=lead.id, email=user.email or "",
            betrieb=lead.company_name or "",
            erfolg_url=f"{ziel}?einzug=eingerichtet",
            abbruch_url=f"{ziel}?einzug=abgebrochen",
            kennung_kunde=kennung)
    except abo_stripe.StripeNichtEingerichtet:
        raise HTTPException(503, "Der Zahlungsdienst ist gerade nicht erreichbar.")
    except abo_stripe.UnbekanntesAbo as fehler:
        raise HTTPException(500, str(fehler))


@router.get("/leistung")
def get_leistung(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Leistungsbericht und Re-Audit — die zwei Zusagen, die automatisch
    liefen und beim Kunden nie ankamen (L-160, Rang 2).

    **Was hier zusammenkommt und warum ausgerechnet diese zwei.** Beide sind
    Positionen aus dem Leistungsverzeichnis der Pflege-Abos, für die der Kunde
    monatlich zahlt. Beide laufen seit Langem als Zeitauftrag. Der Bericht
    ging als Mail hinaus und war danach nirgends mehr abrufbar; das Re-Audit
    meldete dem **Innendienst**, wer dran ist, und dem Kunden gar nichts.

    **Ohne Abo bleibt beides leer.** Ein Re-Audit-Termin ohne Vertrag wäre
    eine Zusage, die niemand gegeben hat — und ein Verlauf, den niemand
    bestellt hat, sieht aus wie eine Leistung, die ausbleibt.
    """
    from services import leistungsbericht, quartals_reaudit

    lead = db.query(Lead).filter(Lead.id == user.lead_id).first() if user.lead_id else None
    if not lead:
        return {"berichte": [], "reaudit": None, "abo": None}

    reaudit = quartals_reaudit.naechste_pruefung(db, lead.id)
    return {
        "berichte": leistungsbericht.verlauf(db, lead.id),
        "reaudit": reaudit,
        # Damit die Oberfläche „noch kein Bericht" von „nicht gebucht"
        # unterscheiden kann. Das ist derselbe Unterschied wie zwischen
        # „nicht erhoben" und „null Punkte", und er ist genauso wichtig.
        "abo": (reaudit or {}).get("produkt"),
    }


# ══════════════════════════════════════════════════════════════════════
# Kontoverwaltung: Geräte, Benachrichtigungen, Downloads (06.09.2026)
# ══════════════════════════════════════════════════════════════════════
#
# **Warum diese drei hier und nicht im Innendienst.** Es sind die Fragen, die
# ein Kunde an sein eigenes Konto stellt und für die er sonst anrufen muss:
# Wo bin ich angemeldet? Welche Post bekomme ich? Wo liegt, was mir gehört?
#
# Profil, Passwort und zweiter Faktor liegen bewusst **nicht** hier — die
# bedient `/api/auth/me` und `/api/auth/2fa/*` seit Langem, für alle Rollen
# gleich. Ein zweiter Weg dorthin wäre ein zweiter Ort mit Passwortlogik.


@router.get("/geraete")
def get_geraete(token: str = Depends(oauth2_scheme),
                user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Wo dieses Konto angemeldet ist — ohne den Token, mit gekürzter Adresse."""
    from services import geraete

    return {"geraete": geraete.liste(db, user.id, aktueller_token=token or "")}


@router.post("/geraete/{sitzung_id}/abmelden")
def abmelden_geraet(sitzung_id: int, user=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    """Eine Anmeldung beenden — auch die eigene.

    **Die eigene abzumelden ist erlaubt und Absicht:** Wer am fremden Rechner
    sitzt und merkt, dass er eingeloggt bleibt, soll sich von dort werfen
    können, ohne zu wissen, welche Zeile das ist.
    """
    from services import geraete

    try:
        return geraete.abmelden(db, user_id=user.id, sitzung_id=sitzung_id)
    except geraete.NichtGefunden as fehler:
        # 404 und nicht 403: Wer fremde Nummern durchprobiert, soll nicht
        # erfahren, welche es gibt.
        raise HTTPException(404, str(fehler))


@router.get("/benachrichtigungen")
def get_benachrichtigungen(user=Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """Welche Mails der Kunde bekommt — und welche er nicht abwählen kann."""
    from services import benachrichtigungswahl

    return {"arten": benachrichtigungswahl.stand(db, user.id)}


class BenachrichtigungWahl(BaseModel):
    an: bool


@router.post("/benachrichtigungen/{schluessel}")
def setze_benachrichtigung(schluessel: str, body: BenachrichtigungWahl,
                           user=Depends(get_current_user),
                           db: Session = Depends(get_db)):
    """Eine Wahl speichern. Pflichtnachrichten werden abgewiesen."""
    from services import benachrichtigungswahl

    try:
        return benachrichtigungswahl.setze(db, user_id=user.id,
                                           schluessel=schluessel, an=body.an)
    except benachrichtigungswahl.NichtAbwaehlbar as fehler:
        # 409 und nicht 400: Die Anfrage ist wohlgeformt, sie widerspricht nur
        # dem Vertrag. Der Text sagt, warum — er steht im Katalog.
        raise HTTPException(409, str(fehler))
    except ValueError as fehler:
        raise HTTPException(404, str(fehler))


@router.get("/downloads")
def get_downloads(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Alles, was der Kunde herunterladen kann — an einer Stelle.

    **Zwei Quellen, ein Verzeichnis.** Dateien zum Betrieb liegen in
    `project_files` (Logo, Bilder, Unterlagen — auch die, die er selbst
    hochgeladen hat); gekaufte Erzeugnisse liegen als Bestellung mit
    Download-Kennung. Der Kunde denkt beides als „meine Sachen"; dass es
    zwei Tabellen sind, ist unsere Sache.

    **Die Adressen sind die bestehenden.** Ein eigener Auslieferungsweg wäre
    eine zweite Stelle mit Rechteprüfung — und eine Grenze, die nur an einer
    von zwei Türen hängt, ist keine.
    """
    if not user.lead_id:
        return {"dateien": [], "kaeufe": []}

    dateien = db.execute(text(
        "SELECT id, original_filename, file_type, file_size, uploaded_at, "
        "uploaded_by_role, note FROM project_files WHERE lead_id = :lid "
        "ORDER BY uploaded_at DESC LIMIT 100"), {"lid": user.lead_id}).fetchall()

    kaeufe = []
    try:
        zeilen = db.execute(text(
            "SELECT order_number, produkt_slug, download_token, created_at, status "
            "FROM bestellungen WHERE email = :mail AND status = 'bezahlt' "
            "ORDER BY created_at DESC LIMIT 50"), {"mail": user.email}).fetchall()
        kaeufe = [{"nummer": z[0], "produkt": z[1],
                   "adresse": f"/api/shop/download/{z[2]}" if z[2] else "",
                   "gekauft_am": z[3].isoformat() if z[3] else None}
                  for z in zeilen]
    except Exception:  # noqa: BLE001 — ohne Shop-Tabelle bleibt die Liste leer
        db.rollback()

    return {
        "dateien": [{
            "id": z[0], "name": z[1], "art": z[2], "groesse": z[3],
            "hochgeladen_am": z[4].isoformat() if z[4] else None,
            "von": "Ihnen" if z[5] == "kunde" else "uns",
            "notiz": z[6] or "",
            "adresse": f"/api/files/mein/download/{z[0]}",
        } for z in dateien],
        "kaeufe": kaeufe,
    }


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
