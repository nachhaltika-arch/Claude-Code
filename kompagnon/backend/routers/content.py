"""
Content Slots — Texte & Medien pro Seite
GET    /api/content/{lead_id}                          → alle Seiten mit Slots (gruppiert)
GET    /api/content/page/{sitemap_page_id}             → _ensure_slots, dann Slots laden
PUT    /api/content/section/{id}                       → inhalt_kunde, inhalt_final, status
POST   /api/content/section/{id}/generate              → KI-Textentwurf für einzelnen Slot
POST   /api/content/page/{sitemap_page_id}/generate-all → KI für alle Slots der Seite
PUT    /api/content/media/{id}                         → status setzen
POST   /api/content/media/{id}/upload                  → Datei-Upload (base64)
GET    /api/content/media/{id}/file                    → Datei abrufen (als Bild)
DELETE /api/content/media/{id}                        → Datei löschen
"""
import base64
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from database import Base, get_db, SessionLocal
from routers.auth_router import require_any_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/content", tags=["content"])

# ── ORM Models ────────────────────────────────────────────────────────────────

class ContentSection(Base):
    __tablename__ = "content_sections"
    __table_args__ = {"extend_existing": True}
    id                = Column(Integer, primary_key=True)
    sitemap_page_id   = Column(Integer, ForeignKey("sitemap_pages.id", ondelete="CASCADE"))
    lead_id           = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"))
    slot_typ          = Column(String(80), nullable=False)
    slot_label        = Column(String(150), nullable=False)
    hinweis           = Column(Text)
    inhalt_ki         = Column(Text)
    inhalt_kunde      = Column(Text)
    inhalt_final      = Column(Text)
    status            = Column(String(30), default="ausstehend")
    zeichenlimit      = Column(Integer)
    erstellt_am       = Column(DateTime, server_default=func.now())
    aktualisiert_am   = Column(DateTime, server_default=func.now(), onupdate=func.now())


class ContentMedia(Base):
    __tablename__ = "content_media"
    __table_args__ = {"extend_existing": True}
    id                = Column(Integer, primary_key=True)
    sitemap_page_id   = Column(Integer, ForeignKey("sitemap_pages.id", ondelete="CASCADE"))
    lead_id           = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"))
    slot_typ          = Column(String(80), nullable=False)
    slot_label        = Column(String(150), nullable=False)
    hinweis           = Column(Text)
    dateiname         = Column(String(255))
    dateityp          = Column(String(50))
    datei_base64      = Column(Text)
    dateigroesse_kb   = Column(Integer)
    status            = Column(String(30), default="ausstehend")
    erstellt_am       = Column(DateTime, server_default=func.now())


# ── Slot-Vorlagen ─────────────────────────────────────────────────────────────

PAGE_SLOTS = {
    "startseite": {
        "sections": [
            {"slot_typ": "hero_h1",  "slot_label": "Hero-Überschrift",
             "hinweis": "Max. 8 Wörter. Enthält Gewerk + Stadt.", "zeichenlimit": 60},
            {"slot_typ": "hero_sub", "slot_label": "Hero-Unterzeile",
             "hinweis": "1 Satz. Nutzen für den Kunden.", "zeichenlimit": 120},
            {"slot_typ": "intro",    "slot_label": "Einleitungstext",
             "hinweis": "2–3 Sätze. Wer sind wir, was machen wir?", "zeichenlimit": 300},
            {"slot_typ": "usp",      "slot_label": "3 Alleinstellungsmerkmale",
             "hinweis": "Je 1 kurzer Satz. Was macht uns besonders?", "zeichenlimit": 200},
        ],
        "media": [
            {"slot_typ": "logo",      "slot_label": "Firmen-Logo",
             "hinweis": "PNG oder SVG, möglichst auf transparentem Hintergrund."},
            {"slot_typ": "hero_foto", "slot_label": "Hero-Bild",
             "hinweis": "Querformat, mind. 1200×600px. Zeigt Team oder Arbeiten."},
        ],
    },
    "leistung": {
        "sections": [
            {"slot_typ": "leistung_h1",   "slot_label": "Leistungs-Überschrift",
             "hinweis": "Max. 6 Wörter. Enthält Leistung + ggf. Stadt.", "zeichenlimit": 60},
            {"slot_typ": "leistung_text", "slot_label": "Leistungsbeschreibung",
             "hinweis": "80–120 Wörter. Vorteile, Ablauf, Garantien.", "zeichenlimit": 800},
            {"slot_typ": "faq_1", "slot_label": "Häufige Frage 1 + Antwort",
             "hinweis": "Kurze Frage aus Kundensicht. Antwort max. 2 Sätze.", "zeichenlimit": 300},
            {"slot_typ": "faq_2", "slot_label": "Häufige Frage 2 + Antwort",
             "hinweis": "Kurze Frage aus Kundensicht. Antwort max. 2 Sätze.", "zeichenlimit": 300},
            {"slot_typ": "faq_3", "slot_label": "Häufige Frage 3 + Antwort",
             "hinweis": "Kurze Frage aus Kundensicht. Antwort max. 2 Sätze.", "zeichenlimit": 300},
        ],
        "media": [
            {"slot_typ": "leistung_foto", "slot_label": "Foto der Leistung",
             "hinweis": "Zeigt die Arbeit im Einsatz oder das Ergebnis. Querformat."},
            {"slot_typ": "referenz_foto", "slot_label": "Referenz-Foto (optional)",
             "hinweis": "Vorher/Nachher oder abgeschlossenes Projekt."},
        ],
    },
    "info": {
        "sections": [
            {"slot_typ": "team_text",      "slot_label": "Über-uns-Text",
             "hinweis": "150 Wörter. Wir-Perspektive. Geschichte, Werte, Team.", "zeichenlimit": 1000},
            {"slot_typ": "gruendungsjahr", "slot_label": "Gründungsjahr",
             "hinweis": "Nur die Jahreszahl, z.B. 2008.", "zeichenlimit": 10},
        ],
        "media": [
            {"slot_typ": "team_foto",    "slot_label": "Team-Foto",
             "hinweis": "Alle Mitarbeiter oder Inhaber. Freundlich, professionell."},
            {"slot_typ": "inhaber_foto", "slot_label": "Inhaber-Porträt (optional)",
             "hinweis": "Einzelfoto des Inhabers/der Inhaberin."},
        ],
    },
    "vertrauen": {
        "sections": [
            {"slot_typ": "referenz_intro",  "slot_label": "Referenzen-Einleitung",
             "hinweis": "2 Sätze. Wie viele Projekte, seit wann?", "zeichenlimit": 200},
            {"slot_typ": "kundenzitat_1",   "slot_label": "Kundenzitat 1",
             "hinweis": "Echtes Zitat + Name + Ort. Aus Google-Bewertung kopierbar.", "zeichenlimit": 300},
            {"slot_typ": "kundenzitat_2",   "slot_label": "Kundenzitat 2 (optional)",
             "hinweis": "Echtes Zitat + Name + Ort.", "zeichenlimit": 300},
        ],
        "media": [
            {"slot_typ": "referenz_foto_1", "slot_label": "Referenz-Foto 1",
             "hinweis": "Abgeschlossenes Projekt. Qualität wichtiger als Auflösung."},
            {"slot_typ": "referenz_foto_2", "slot_label": "Referenz-Foto 2", "hinweis": ""},
            {"slot_typ": "referenz_foto_3", "slot_label": "Referenz-Foto 3", "hinweis": ""},
        ],
    },
    "conversion": {
        "sections": [
            {"slot_typ": "kontakt_intro",   "slot_label": "Kontakt-Einladungstext",
             "hinweis": "2 Sätze. Warum jetzt anfragen? Was passiert danach?", "zeichenlimit": 200},
            {"slot_typ": "oeffnungszeiten", "slot_label": "Öffnungszeiten",
             "hinweis": "Mo–Fr 07:00–18:00, Sa 08:00–13:00 o.ä.", "zeichenlimit": 200},
        ],
        "media": [],
    },
}

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def _ensure_slots(sitemap_page_id: int, page_type: str, lead_id: int, db: Session):
    """Legt fehlende Slots für eine Seite an (idempotent). Pflichtseiten werden übersprungen."""
    if page_type == "pflicht" or page_type not in PAGE_SLOTS:
        return

    template = PAGE_SLOTS[page_type]

    # Bestehende slot_typs laden (sections)
    existing_sections = {
        row[0] for row in db.execute(
            __import__("sqlalchemy").text(
                "SELECT slot_typ FROM content_sections WHERE sitemap_page_id = :pid"
            ),
            {"pid": sitemap_page_id},
        )
    }
    for slot in template["sections"]:
        if slot["slot_typ"] not in existing_sections:
            db.add(ContentSection(
                sitemap_page_id=sitemap_page_id,
                lead_id=lead_id,
                slot_typ=slot["slot_typ"],
                slot_label=slot["slot_label"],
                hinweis=slot.get("hinweis"),
                zeichenlimit=slot.get("zeichenlimit"),
            ))

    # Bestehende slot_typs laden (media)
    existing_media = {
        row[0] for row in db.execute(
            __import__("sqlalchemy").text(
                "SELECT slot_typ FROM content_media WHERE sitemap_page_id = :pid"
            ),
            {"pid": sitemap_page_id},
        )
    }
    for slot in template["media"]:
        if slot["slot_typ"] not in existing_media:
            db.add(ContentMedia(
                sitemap_page_id=sitemap_page_id,
                lead_id=lead_id,
                slot_typ=slot["slot_typ"],
                slot_label=slot["slot_label"],
                hinweis=slot.get("hinweis"),
            ))

    db.commit()


def _serialize_section(s: ContentSection) -> dict:
    return {
        "id": s.id,
        "sitemap_page_id": s.sitemap_page_id,
        "lead_id": s.lead_id,
        "slot_typ": s.slot_typ,
        "slot_label": s.slot_label,
        "hinweis": s.hinweis,
        "inhalt_ki": s.inhalt_ki,
        "inhalt_kunde": s.inhalt_kunde,
        "inhalt_final": s.inhalt_final,
        "status": s.status,
        "zeichenlimit": s.zeichenlimit,
        "erstellt_am": s.erstellt_am.isoformat() if s.erstellt_am else None,
        "aktualisiert_am": s.aktualisiert_am.isoformat() if s.aktualisiert_am else None,
    }


def _serialize_media(m: ContentMedia) -> dict:
    return {
        "id": m.id,
        "sitemap_page_id": m.sitemap_page_id,
        "lead_id": m.lead_id,
        "slot_typ": m.slot_typ,
        "slot_label": m.slot_label,
        "hinweis": m.hinweis,
        "dateiname": m.dateiname,
        "dateityp": m.dateityp,
        "datei_base64": m.datei_base64,
        "dateigroesse_kb": m.dateigroesse_kb,
        "status": m.status,
        "erstellt_am": m.erstellt_am.isoformat() if m.erstellt_am else None,
    }


def _row_to_section_dict(r) -> dict:
    """Section-Dict aus raw SQL row (selbe Form wie _serialize_section)."""
    return {
        "id": r.id,
        "sitemap_page_id": r.sitemap_page_id,
        "lead_id": r.lead_id,
        "slot_typ": r.slot_typ,
        "slot_label": r.slot_label,
        "hinweis": r.hinweis,
        "inhalt_ki": r.inhalt_ki,
        "inhalt_kunde": r.inhalt_kunde,
        "inhalt_final": r.inhalt_final,
        "status": r.status,
        "zeichenlimit": r.zeichenlimit,
        "erstellt_am": r.erstellt_am.isoformat() if r.erstellt_am else None,
        "aktualisiert_am": r.aktualisiert_am.isoformat() if r.aktualisiert_am else None,
    }


def _row_to_media_lite_dict(r) -> dict:
    """
    Media-Dict aus raw SQL row — OHNE `datei_base64` (koennte MB gross sein).
    Wird in Listen-Endpoints verwendet, wo der Frontend-Code das Base64
    ohnehin nicht konsumiert (nur `dateiname` + `status` fuer Anzeige).
    Einzel-GETs liefern weiterhin den Full-Content via /media/{id}/file.
    """
    return {
        "id": r.id,
        "sitemap_page_id": r.sitemap_page_id,
        "lead_id": r.lead_id,
        "slot_typ": r.slot_typ,
        "slot_label": r.slot_label,
        "hinweis": r.hinweis,
        "dateiname": r.dateiname,
        "dateityp": r.dateityp,
        "datei_base64": None,  # absichtlich ausgelassen — siehe Docstring
        "dateigroesse_kb": r.dateigroesse_kb,
        "status": r.status,
        "erstellt_am": r.erstellt_am.isoformat() if r.erstellt_am else None,
    }


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class SectionUpdate(BaseModel):
    inhalt_kunde: Optional[str] = None
    inhalt_final: Optional[str] = None
    status: Optional[str] = None


class MediaStatusUpdate(BaseModel):
    status: Optional[str] = None


# ── Endpunkte ─────────────────────────────────────────────────────────────────

@router.get("/{lead_id}")
def get_content_for_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """
    Alle Seiten des Leads mit ihren Sections + Media, gruppiert nach sitemap_page_id.

    Perf-optimiert:
      - 3 Queries total (Pages, Sections, Media) statt 1 + 2N bei N Seiten
      - Raw SQL mit expliziter Spalten-Liste statt ORM-Full-Row
      - `datei_base64` wird NICHT geladen (koennte MB gross sein) — die
        Listen-Ansicht zeigt nur Metadaten, Einzel-GETs gehen ueber
        /media/{id}/file
    """
    from sqlalchemy import text
    from collections import defaultdict

    # 1) Pages
    pages = db.execute(
        text("""
            SELECT id, page_name, page_type, ist_pflichtseite
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY position
        """),
        {"lid": lead_id},
    ).fetchall()

    if not pages:
        return []

    # 2) Sections fuer ALLE Pages auf einmal (eine Query)
    section_rows = db.execute(
        text("""
            SELECT id, sitemap_page_id, lead_id, slot_typ, slot_label,
                   hinweis, inhalt_ki, inhalt_kunde, inhalt_final,
                   status, zeichenlimit, erstellt_am, aktualisiert_am
            FROM content_sections
            WHERE lead_id = :lid
        """),
        {"lid": lead_id},
    ).fetchall()

    # 3) Media fuer ALLE Pages auf einmal — OHNE datei_base64
    media_rows = db.execute(
        text("""
            SELECT id, sitemap_page_id, lead_id, slot_typ, slot_label,
                   hinweis, dateiname, dateityp, dateigroesse_kb,
                   status, erstellt_am
            FROM content_media
            WHERE lead_id = :lid
        """),
        {"lid": lead_id},
    ).fetchall()

    # Gruppierung nach sitemap_page_id
    sections_by_page = defaultdict(list)
    for s in section_rows:
        sections_by_page[s.sitemap_page_id].append(_row_to_section_dict(s))

    media_by_page = defaultdict(list)
    for m in media_rows:
        media_by_page[m.sitemap_page_id].append(_row_to_media_lite_dict(m))

    return [
        {
            "sitemap_page_id": page.id,
            "page_name": page.page_name,
            "page_type": page.page_type,
            "ist_pflichtseite": bool(page.ist_pflichtseite),
            "sections": sections_by_page.get(page.id, []),
            "media": media_by_page.get(page.id, []),
        }
        for page in pages
    ]


@router.get("/page/{sitemap_page_id}")
def get_page_content(
    sitemap_page_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """
    Slots fuer eine einzelne Seite laden (und ggf. auto-erstellen).

    Perf-optimiert: raw SQL mit expliziter Spalten-Liste fuer sections
    und media, `datei_base64` wird nicht mitgeladen (siehe
    _row_to_media_lite_dict).
    """
    from sqlalchemy import text

    page = db.execute(
        text("SELECT id, page_name, page_type, lead_id, ist_pflichtseite FROM sitemap_pages WHERE id = :pid"),
        {"pid": sitemap_page_id},
    ).fetchone()

    if not page:
        raise HTTPException(status_code=404, detail="Seite nicht gefunden")

    _ensure_slots(sitemap_page_id, page.page_type, page.lead_id, db)

    section_rows = db.execute(
        text("""
            SELECT id, sitemap_page_id, lead_id, slot_typ, slot_label,
                   hinweis, inhalt_ki, inhalt_kunde, inhalt_final,
                   status, zeichenlimit, erstellt_am, aktualisiert_am
            FROM content_sections
            WHERE sitemap_page_id = :pid
        """),
        {"pid": sitemap_page_id},
    ).fetchall()

    media_rows = db.execute(
        text("""
            SELECT id, sitemap_page_id, lead_id, slot_typ, slot_label,
                   hinweis, dateiname, dateityp, dateigroesse_kb,
                   status, erstellt_am
            FROM content_media
            WHERE sitemap_page_id = :pid
        """),
        {"pid": sitemap_page_id},
    ).fetchall()

    return {
        "sitemap_page_id": page.id,
        "page_name": page.page_name,
        "page_type": page.page_type,
        "lead_id": page.lead_id,
        "ist_pflichtseite": bool(page.ist_pflichtseite),
        "sections": [_row_to_section_dict(s) for s in section_rows],
        "media": [_row_to_media_lite_dict(m) for m in media_rows],
    }


@router.put("/section/{section_id}")
def update_section(
    section_id: int,
    body: SectionUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Inhalt oder Status eines Text-Slots aktualisieren."""
    section = db.query(ContentSection).filter_by(id=section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section nicht gefunden")

    if body.inhalt_kunde is not None:
        section.inhalt_kunde = body.inhalt_kunde
    if body.inhalt_final is not None:
        section.inhalt_final = body.inhalt_final
    if body.status is not None:
        section.status = body.status

    db.commit()
    db.refresh(section)
    return _serialize_section(section)


@router.put("/media/{media_id}")
def update_media_status(
    media_id: int,
    body: MediaStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Status eines Medien-Slots setzen."""
    media = db.query(ContentMedia).filter_by(id=media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Medien-Slot nicht gefunden")

    if body.status is not None:
        media.status = body.status

    db.commit()
    db.refresh(media)
    return _serialize_media(media)


@router.delete("/media/{media_id}")
def delete_media(
    media_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Medien-Datei löschen (Datei + Datenbankzeile)."""
    media = db.query(ContentMedia).filter_by(id=media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Medien-Slot nicht gefunden")

    db.delete(media)
    db.commit()
    return {"ok": True}


# ── KI-Generierung ────────────────────────────────────────────────────────────

def _build_ki_prompt(section: ContentSection, db: Session) -> str:
    """Baut den Prompt für die KI aus Slot + Seite + Lead + Briefing."""
    from sqlalchemy import text

    page = db.execute(
        text("SELECT page_name, ziel_keyword, zweck, lead_id FROM sitemap_pages WHERE id = :pid"),
        {"pid": section.sitemap_page_id},
    ).fetchone()
    if not page:
        raise HTTPException(status_code=404, detail="Sitemap-Seite nicht gefunden")

    lead = db.execute(
        text("SELECT company_name, trade, city FROM leads WHERE id = :lid"),
        {"lid": page.lead_id},
    ).fetchone()

    briefing = db.execute(
        text("SELECT gewerk, leistungen, usp, zielgruppe FROM briefings WHERE lead_id = :lid LIMIT 1"),
        {"lid": page.lead_id},
    ).fetchone()

    company   = lead.company_name if lead else "Unbekannt"
    trade     = (lead.trade if lead else "") or (briefing.gewerk if briefing else "") or ""
    city      = (lead.city if lead else "") or ""
    usp       = (briefing.usp if briefing else "") or ""
    leistungen = (briefing.leistungen if briefing else "") or ""
    zielgruppe = (briefing.zielgruppe if briefing else "") or ""
    keyword    = page.ziel_keyword or ""
    zweck      = page.zweck or ""
    limit_txt  = f"{section.zeichenlimit} Zeichen" if section.zeichenlimit else "keine Vorgabe"
    hinweis    = section.hinweis or ""

    return (
        f"Schreibe für [{section.slot_label}] der Seite [{page.page_name}]:\n"
        f"Betrieb: {company}, Gewerk: {trade}, Stadt: {city}\n"
        f"Keyword: {keyword}, Seitenzweck: {zweck}\n"
        f"USP: {usp}\n"
        f"Leistungen: {leistungen}\n"
        f"Zielgruppe: {zielgruppe}\n"
        f"Zeichenlimit: {limit_txt}\n"
        f"Hinweis: {hinweis}"
    )


async def _generate_one(section_id: int) -> dict:
    """KI-Entwurf fuer einen einzelnen Slot erstellen.

    Eigene Session-Verwaltung (2× SessionLocal) — der aeussere DB-Pool wird
    waehrend des blockierenden Claude-Calls NICHT gehalten. Das ist kritisch
    auf Render Basic mit kleinem Pool: bei 5 parallelen Requests wuerde
    sonst der Pool verhungern, waehrend jede Anfrage ~60s im Claude-Call
    haengt.

    Phase 1 (Read): Section + Prompt-Kontext aus DB holen
    Phase 2 (Extern): Claude-Call ohne DB-Connection
    Phase 3 (Write): Section in einer frischen Session aktualisieren
    """
    import anthropic

    # ── Phase 1: Read mit eigener Session, direkt wieder freigeben ────
    db_read = SessionLocal()
    try:
        section = db_read.query(ContentSection).filter_by(id=section_id).first()
        if not section:
            raise HTTPException(status_code=404, detail="Section nicht gefunden")
        prompt = _build_ki_prompt(section, db_read)
    finally:
        db_read.close()

    # ── Phase 2: Claude-Call OHNE DB-Connection ──────────────────────
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=(
            "Du bist ein Texter für Handwerkerbetriebe. Schreibe präzise, "
            "authentisch und lokal. Antworte NUR mit dem fertigen Text, ohne Erklärung."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    ki_text = message.content[0].text.strip()

    # ── Phase 3: Write in frischer Session ───────────────────────────
    db_write = SessionLocal()
    try:
        section = db_write.query(ContentSection).filter_by(id=section_id).first()
        if not section:
            # Section wurde zwischenzeitlich geloescht — kein Persist,
            # aber den KI-Text trotzdem zurueckgeben (Aufrufer kann
            # entscheiden was tun).
            return {"id": section_id, "inhalt_ki": ki_text, "status": "orphan"}
        section.inhalt_ki = ki_text
        section.status    = "ki_entwurf"
        db_write.commit()
        db_write.refresh(section)
        return {"id": section.id, "inhalt_ki": ki_text, "status": section.status}
    finally:
        db_write.close()


@router.post("/section/{section_id}/generate")
async def generate_section(
    section_id: int,
    user=Depends(require_any_auth),
):
    """KI-Textentwurf fuer einen einzelnen Slot generieren.

    Nutzt keinen `db`-Dependency mehr — `_generate_one` verwaltet seine
    Session selbst, damit der Pool waehrend des Claude-Calls nicht blockiert.
    """
    return await _generate_one(section_id)


@router.post("/page/{sitemap_page_id}/generate-all")
async def generate_all_sections(
    sitemap_page_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """KI-Entwurf fuer alle Text-Slots der Seite generieren (sequenziell).

    Holt die Section-IDs in einer kurzlebigen DB-Session, schliesst sie
    SOFORT, und loopt dann durch die IDs. _generate_one oeffnet pro
    Iteration zwei eigene Sessions — der aeussere Request-Pool haengt
    nicht fuer die ganze Zeit an einer einzigen Connection.
    """
    sections = db.query(ContentSection).filter_by(sitemap_page_id=sitemap_page_id).all()
    section_ids = [s.id for s in sections]
    db.close()  # Pool freigeben BEVOR der Claude-Loop startet

    generated, errors = 0, []
    for sid in section_ids:
        try:
            await _generate_one(sid)
            generated += 1
        except Exception as exc:
            errors.append({"section_id": sid, "error": str(exc)})
    return {"generated": generated, "errors": errors}


# ── Datei-Upload ──────────────────────────────────────────────────────────────

_ALLOWED_MIME = {
    "image/jpeg", "image/png", "image/webp", "image/svg+xml", "image/gif",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/media/{media_id}/upload")
async def upload_media(
    media_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_any_auth),
):
    """Bild-Upload für einen Medien-Slot (base64 in DB)."""
    media = db.query(ContentMedia).filter_by(id=media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Medien-Slot nicht gefunden")

    if file.content_type not in _ALLOWED_MIME:
        raise HTTPException(status_code=415, detail=f"Dateityp nicht erlaubt: {file.content_type}")

    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Datei zu groß (max. 10 MB)")

    media.datei_base64    = base64.b64encode(data).decode("ascii")
    media.dateiname       = file.filename
    media.dateityp        = file.content_type
    media.dateigroesse_kb = len(data) // 1024
    media.status          = "vom_kunden"
    db.commit()
    db.refresh(media)
    return {
        "id":              media.id,
        "dateiname":       media.dateiname,
        "dateityp":        media.dateityp,
        "dateigroesse_kb": media.dateigroesse_kb,
        "status":          media.status,
    }


@router.get("/media/{media_id}/file")
def get_media_file(
    media_id: int,
    db: Session = Depends(get_db),
):
    """Bild-Datei abrufen (base64 → Binary, kein Auth für Vorschau im Frontend)."""
    media = db.query(ContentMedia).filter_by(id=media_id).first()
    if not media or not media.datei_base64:
        raise HTTPException(status_code=404, detail="Keine Datei vorhanden")

    raw = base64.b64decode(media.datei_base64)
    return Response(
        content=raw,
        media_type=media.dateityp or "image/jpeg",
        headers={"Cache-Control": "max-age=3600"},
    )
