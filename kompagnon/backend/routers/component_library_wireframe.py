"""Der Online-Fertig-Editor: Wireframes, Varianten, Komposition (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/component_library.py` hatte
2.143 Zeilen und fuehrte **zwei** Router: `component_router` fuer die
Bausteinbibliothek und `wireframe_router` fuer die Seitenentwuerfe der
Kundenprojekte. Zwei Router auf zwei verschiedenen Praefixen in einer Datei —
gewachsen, nicht entworfen.

Der Wireframe-Teil bringt seine eigenen Modelle, seine drei Job-Speicher und
sechs Helfer mit, die sonst niemand braucht; nachgemessen vor dem Schnitt.
Geteilt bleibt nur `_nur_freigegebene` — die Frage, welche Bausteine ein
Projekt sehen darf — und die wird von hier geholt.

**Die Sperre bleibt, wo sie war:** `require_innendienst` am Router. Der
Seitenbau ist Innendienstarbeit; ein Kunde hat hier nichts zu suchen, auch
nicht bei seinem eigenen Projekt (L-87).
"""
import json
import os
import threading
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from routers.auth_router import require_any_auth, require_innendienst
from services.block_contract import als_text, pruefe, slots_im_markup
from services.block_variant import VariantenAbbruch, erzeuge_variante
from services.page_composer import KompositionsAbbruch, komponiere
import logging

from anthropic import Anthropic

from database import Briefing, ComponentLibrary, Project, SessionLocal, get_db
# Aus der Bausteinbibliothek geholt statt kopiert: `_nur_freigegebene`
# beantwortet, welche Bausteine ein Projekt sehen darf; die vier
# KI-Helfer bauen und lesen die Modellaufrufe. Alle fuenf werden auch
# drueben gebraucht — zwei Fassungen davon liefen heute schon zweimal
# auseinander (`_serialize`, `PHASEN`).
logger = logging.getLogger(__name__)

from routers.component_library import _Abbruch, _nur_freigegebene

# Die drei KI-Helfer sind mit dem KI-Teil gewandert (L-25, 22.08.2026) —
# Aufforderung bauen, Antwort lesen, Modellrunde fahren.
from routers.component_library_ki import (
    _build_prompt,
    _extract_text_from_response,
    _ki_runde,
)


# In-Memory Job-Store fuer den KI-Generator.
# { job_id: { "status": "running"|"done"|"error", "result": dict|None, "error": str|None } }
_wireframe_jobs: dict = {}


# Stufe B: ein Block, fuer einen Kunden umgeschrieben.
_variant_jobs: dict = {}


# Stufe C: die Abfolge einer ganzen Seite.
_compose_jobs: dict = {}


# Vorgabe am Router, nicht an der einzelnen Route. Bis zum 21.08.2026 trugen
# diese Routen nur `require_any_auth` und **keine Zeilenpruefung**: Sie holen
# das Projekt per `project_id` und antworten. Kunden haben Konten — ein
# angemeldeter Kunde kam damit an **jedes** Projekt (Naht `/api/projects`,
# `docs/module-karte.md`; dieselbe Bauart wie L-66).
#
# Alle Aufrufer haengen an `roles={{'admin', 'auditor'}}`, also am Innendienst.
# Die Sperre stand in der Oberflaeche statt am Endpunkt — und eine
# Oberflaechenpruefung ist keine Sperre.
wireframe_router = APIRouter(prefix="/api/projects", tags=["wireframe"],
                              dependencies=[Depends(require_innendienst)])


class WireframeBlock(BaseModel):
    slug: str
    order: int = 0
    slots: dict = {}
    # Stufe B: Markup, das nur für diesen Kunden gilt. Ist es gesetzt, zieht der
    # Renderer es dem Bibliotheks-Template vor. Der Block bleibt trotzdem
    # derselbe — `slug` zeigt weiter auf die Vorlage, aus der er entstanden ist,
    # und die Slot-Angaben kommen unverändert von dort.
    html_override: Optional[str] = None


class WireframePage(BaseModel):
    page_id: int
    page_name: Optional[str] = None
    blocks: list[WireframeBlock] = []


class WireframeData(BaseModel):
    """
    Persistent store fuer den Online-Fertig-Editor.
    pages              — vom KI-Wireframe-Generator oder manuellem Block-Tausch
    style_guide        — Tokens aus StyleGuideView (Farben/Typo/Buttons/Spacing)
    style_guide_approved — Gate fuer DesignView (Step E)
    """
    pages: list[WireframePage] = []
    style_guide: Optional[dict] = None
    style_guide_approved: Optional[bool] = False


class VarianteRequest(BaseModel):
    page_id: int
    slug:    str
    wunsch:  Optional[str] = ""


class KompositionRequest(BaseModel):
    page_id: int


def _pruefe_variante(db: Session, block) -> dict:
    """Der Vertragsbefund einer kundeneigenen Variante.

    Zwei Dinge zusaetzlich zum Vertrag:

    * Die Variante wird gegen den **Slug ihres Bibliotheksblocks** geprueft.
      Traegt sie eine fremde Markierung, findet der Editor den Block nicht
      wieder (Regel R2).
    * Sie darf die Slots **nicht umbenennen**. `generate-copy` und der
      Slot-Editor lesen die Angaben des Bibliotheksblocks; erfindet die Variante
      eigene Schluessel, fuellt sie niemand mehr. Weglassen ist erlaubt — eine
      kuerzere Fassung ist eine Gestaltungsentscheidung.
    """
    vorlage = (db.query(ComponentLibrary)
                 .filter(ComponentLibrary.slug == block.slug).first())
    slots = (vorlage.slots if vorlage else None) or []
    bekannt = {s.get("key") for s in slots if isinstance(s, dict)}

    verstoesse = [{"regel": v.regel, "text": v.text}
                  for v in pruefe(block.html_override, slug=block.slug)]

    if vorlage is None:
        verstoesse.append({
            "regel": "B1",
            "text": f"Zu '{block.slug}' gibt es keinen Bibliotheksblock — eine "
                    f"Variante braucht die Vorlage, aus der sie entstanden ist.",
        })
    else:
        for name in slots_im_markup(block.html_override):
            if name not in bekannt:
                verstoesse.append({
                    "regel": "B2",
                    "text": f'Slot "{name}" steht nur in der Variante. Die '
                            f"Slot-Angaben kommen vom Bibliotheksblock — "
                            f"generate-copy wuerde ihn nie fuellen.",
                })

    return {"konform": not verstoesse, "verstoesse": verstoesse}


def _seiten_name(wireframe_data, page_id: int) -> str:
    for seite in (wireframe_data or {}).get("pages", []):
        if seite.get("page_id") == page_id:
            return seite.get("page_name") or ""
    return ""


def _bloecke_der_seite(wireframe_data, page_id: int) -> list:
    for seite in (wireframe_data or {}).get("pages", []):
        if seite.get("page_id") == page_id:
            return sorted(seite.get("blocks", []), key=lambda b: b.get("order", 0))
    return []


def _run_wireframe_job(job_id: str, project_id: int, api_key: str) -> None:
    """Background-Thread — laedt DB-Daten, ruft Claude, speichert Resultat."""
    db = SessionLocal()
    try:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            _wireframe_jobs[job_id] = {"status": "error", "error": "Projekt verschwunden"}
            return

        briefing = db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()

        pages_rows = db.execute(text("""
            SELECT id, page_name
            FROM sitemap_pages
            WHERE lead_id = :lid
            ORDER BY parent_id NULLS FIRST, position, id
        """), {"lid": proj.lead_id}).fetchall()
        pages = [{"id": r[0], "page_name": r[1]} for r in pages_rows]
        if not pages:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "Keine Sitemap-Seiten — bitte zuerst Sitemap generieren.",
            }
            return

        # Nur Freigegebenes. Ein Entwurf darf nie auf einer Kundenseite landen.
        components_rows = _nur_freigegebene(db.query(ComponentLibrary)).all()
        if not components_rows:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "Komponenten-Bibliothek leer — Seed nicht gelaufen?",
            }
            return
        components = [{
            "slug":           r.slug,
            "category":       r.category,
            "name":           r.name,
            "ki_prompt_hint": r.ki_prompt_hint or "",
            "slots":          r.slots or [],
        } for r in components_rows]

        prompt = _build_prompt(briefing, pages, components)

        client = Anthropic(api_key=api_key)
        # max_tokens=32000 deckt grosse Sitemaps ab (~50 Seiten x 8 Bloecke).
        # Vorher 4000 → JSON wurde bei groesseren Wireframes mitten im String
        # abgeschnitten, json.loads kippte mit "Unterminated string". Anthropic
        # rechnet nur tatsaechlich generierte Tokens ab, daher kein Cost-Risiko.
        #
        # Streaming-Pflicht ab 2025: Die Anthropic-SDK weigert sich, non-streaming
        # Calls mit hoher max_tokens-Erwartung > ~10min zu starten und wirft
        # ValueError("Streaming is required..."). Daher hier ueber stream() —
        # final_message hat dieselbe Struktur wie ein gewoehnliches Response.
        with client.messages.stream(
            model="claude-sonnet-5", thinking={"type": "disabled"},
            max_tokens=32000,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            # Iterator konsumieren, damit der Akkumulator das final_message baut.
            for _ in stream.text_stream:
                pass
            response = stream.get_final_message()
        stop_reason = getattr(response, "stop_reason", None)
        raw_text = _extract_text_from_response(response)

        # Wenn das Modell wegen max_tokens gestoppt hat, ist der JSON-Output
        # garantiert truncated — klarer Fehler statt obskurem JSON-Parse-Error.
        if stop_reason == "max_tokens":
            logger.warning(
                f"wireframe job {job_id}: stop_reason=max_tokens, output truncated "
                f"({len(raw_text)} chars); pages={len(pages)}, components={len(components)}"
            )
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": (
                    "KI-Output wurde abgeschnitten (max_tokens erreicht). "
                    "Sitemap mit weniger Seiten erneut generieren oder Limit erhoehen."
                ),
            }
            return

        try:
            # strict=False wie im Block-Generator: rohe Steuerzeichen in
            # Zeichenketten sollen einen Auftrag nicht kosten. Eine zweite
            # Chance wie dort gibt es hier bewusst noch nicht — dafuer fehlt
            # der Beleg, und dieser Auftrag ist deutlich teurer zu wiederholen.
            wireframe = json.loads(raw_text, strict=False)
        except json.JSONDecodeError as exc:
            logger.warning(
                f"wireframe job {job_id}: JSON-Parsing fehlgeschlagen: {exc}; "
                f"stop_reason={stop_reason}; raw_len={len(raw_text)}; "
                f"raw[:300]={raw_text[:300]!r}"
            )
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": f"KI-Output kein valides JSON: {exc}",
            }
            return

        if not isinstance(wireframe, dict) or "pages" not in wireframe:
            _wireframe_jobs[job_id] = {
                "status": "error",
                "error": "KI-Output fehlt 'pages'",
            }
            return

        # Persistieren — frische Query, weil der Thread eine andere Session hat.
        # Style-Guide + Freigabe-Flag werden NICHT ueberschrieben — KI-Generator
        # bestimmt nur die pages-Struktur, alles andere bleibt erhalten.
        proj_for_write = db.query(Project).filter(Project.id == project_id).first()
        if proj_for_write is not None:
            existing = proj_for_write.wireframe_data or {}
            if not isinstance(existing, dict):
                existing = {}
            merged = {**existing, "pages": wireframe.get("pages") or []}
            proj_for_write.wireframe_data = merged
            db.commit()

        _wireframe_jobs[job_id] = {
            "status":     "done",
            "page_count": len(wireframe.get("pages") or []),
            "result":     wireframe,
        }
    except Exception as exc:
        logger.error(f"wireframe job {job_id} crashed: {exc}", exc_info=True)
        _wireframe_jobs[job_id] = {"status": "error", "error": str(exc)}
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()


def _run_variant_job(*, job_id, api_key, slug, vorlage, slots, briefing,
                     wunsch, seite) -> None:
    """Hintergrund-Thread: schreibt den Block um und prueft das Ergebnis."""
    try:
        client = Anthropic(api_key=api_key)
        ergebnis = erzeuge_variante(
            ki_runde=_ki_runde, client=client, slug=slug, vorlage=vorlage,
            slots=slots, briefing=briefing, wunsch=wunsch, seite=seite,
            auftrag=job_id,
        )
        _variant_jobs[job_id] = {"status": "done", "result": ergebnis}
    except (VariantenAbbruch, _Abbruch) as exc:
        _variant_jobs[job_id] = {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.error("variant job %s crashed: %s", job_id, exc, exc_info=True)
        _variant_jobs[job_id] = {"status": "error", "error": str(exc)}


def _run_compose_job(*, job_id, api_key, seite, zweck, ist_startseite, briefing,
                     bloecke, bestehend) -> None:
    """Hintergrund-Thread: schlaegt die Abfolge vor und prueft sie."""
    try:
        client = Anthropic(api_key=api_key)
        ergebnis = komponiere(
            ki_runde=_ki_runde, client=client, seite=seite, zweck=zweck,
            ist_startseite=ist_startseite, briefing=briefing, bloecke=bloecke,
            bestehend=bestehend, auftrag=job_id)
        # Namen dazu, damit das Frontend die Abfolge lesbar anzeigen kann.
        nach_slug = {b["slug"]: b for b in bloecke}
        for section in ergebnis["sections"]:
            eintrag = nach_slug.get(section["slug"]) or {}
            section["name"] = eintrag.get("name") or section["slug"]
            section["category"] = eintrag.get("category") or ""
        _compose_jobs[job_id] = {"status": "done", "result": ergebnis}
    except (KompositionsAbbruch, _Abbruch) as exc:
        _compose_jobs[job_id] = {"status": "error", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.error("compose job %s crashed: %s", job_id, exc, exc_info=True)
        _compose_jobs[job_id] = {"status": "error", "error": str(exc)}


@wireframe_router.get("/{project_id}/wireframe")
def get_wireframe(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_innendienst),
):
    """Gespeicherten Wireframe abrufen. Leere Struktur wenn noch nichts."""
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    return proj.wireframe_data or {"pages": []}


@wireframe_router.post("/{project_id}/wireframe")
def save_wireframe(
    project_id: int,
    data: WireframeData,
    db: Session = Depends(get_db),
    user=Depends(require_innendienst),
):
    """Manueller Save (Block-Tausch im UI, ohne KI).

    Kundeneigene Varianten (`html_override`) gehen durch dasselbe Tor wie die
    Bibliothek: Was den Vertrag verletzt, wird nicht gespeichert. Sonst waere
    er in einer Zeile zu umgehen — man schriebe den Block einfach nicht in die
    Bibliothek, sondern direkt beim Kunden.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")

    for seite in data.pages:
        for block in seite.blocks:
            if not (block.html_override or "").strip():
                continue
            befund = _pruefe_variante(db, block)
            if befund["verstoesse"]:
                raise HTTPException(422, {
                    "message": f"Die Variante von '{block.slug}' verletzt den "
                               f"Vertrag und wurde nicht gespeichert.",
                    "slug": block.slug,
                    "page_id": seite.page_id,
                    **befund,
                })

    # **Ein weggelassenes Feld loescht nichts (L-88).** `WireframeData` fuehrt
    # drei Felder, und wer nur `pages` schickt, bekam fuer die anderen die
    # Vorgaben — `None` und `False`. Genau das tat die Oberflaeche an fuenf
    # von sieben Speicherstellen: Ein Blocktausch loeschte den kompletten
    # Style-Guide samt der Freigabe, die das Tor zur DesignView ist.
    # Stillschweigend; beim naechsten Aufruf sah die Seite einfach anders aus.
    #
    # Die Oberflaeche ist repariert, aber die naechste Speicherstelle kommt
    # bestimmt — wer sie schreibt, denkt an `pages`; an einen Style-Guide, den
    # er nicht anfasst, denkt niemand. Deshalb steht die Sperre hier.
    #
    # `exclude_unset` unterscheidet **nicht geschickt** von **absichtlich
    # zurueckgenommen**: Wer `style_guide_approved: false` schickt, nimmt die
    # Freigabe zurueck, und das muss gehen — sonst waere sie unwiderruflich.
    geschickt = data.model_dump(exclude_unset=True)
    bisher = proj.wireframe_data if isinstance(proj.wireframe_data, dict) else {}

    zusammengefuehrt = {**bisher, **geschickt}
    # `pages` ist das eine Feld, das immer der Absender bestimmt: Eine leere
    # Seitenliste ist eine Aussage, kein Weglassen.
    zusammengefuehrt["pages"] = data.model_dump()["pages"]

    proj.wireframe_data = zusammengefuehrt
    db.commit()
    return {"status": "saved", "page_count": len(data.pages)}


# Polling-Endpoint fuer KI-Jobs unter /wireframe-jobs/ — eindeutiger Pfad,
# damit FastAPI nicht mit /{project_id}/wireframe kollidiert.
@wireframe_router.get("/wireframe-jobs/{job_id}")
def get_wireframe_job(job_id: str, user=Depends(require_innendienst)):
    """Polling fuer KI-Job. Cleanup nach erstem Read von done/error."""
    job = _wireframe_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        snapshot = dict(job)
        _wireframe_jobs.pop(job_id, None)
        return snapshot
    return job


@wireframe_router.post("/{project_id}/wireframe/generate")
def generate_wireframe(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_innendienst),
):
    """Startet KI-Wireframe-Generierung als Background-Job.

    Returnt sofort `{job_id, status: 'running'}` — Frontend pollt
    `GET /api/projects/wireframe-jobs/{job_id}` bis status=done|error.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(status_code=500, detail="anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY nicht konfiguriert")

    job_id = str(uuid.uuid4())
    _wireframe_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_wireframe_job,
        args=(job_id, project_id, api_key),
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


@wireframe_router.get("/wireframe-variant-jobs/{job_id}")
def get_variant_job(job_id: str, user=Depends(require_innendienst)):
    """Polling fuer den Varianten-Auftrag. Cleanup nach dem ersten Abholen."""
    job = _variant_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        return _variant_jobs.pop(job_id)
    return job


@wireframe_router.post("/{project_id}/wireframe/variant")
def generate_variant(
    project_id: int,
    body: VarianteRequest,
    db: Session = Depends(get_db),
    user=Depends(require_innendienst),
):
    """Startet das Umschreiben eines Blocks fuer diesen Kunden.

    Returnt sofort `{job_id, status: 'running'}` — das Frontend pollt
    `GET /api/projects/wireframe-variant-jobs/{job_id}`.

    Gespeichert wird hier nichts: Das Ergebnis geht zurueck ans Frontend, und
    erst der Save des Wireframes traegt es ein — durch dasselbe Tor wie jede
    andere Variante.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    vorlage = (db.query(ComponentLibrary)
                 .filter(ComponentLibrary.slug == body.slug).first())
    if not vorlage:
        raise HTTPException(404, f"Bibliotheksblock '{body.slug}' nicht gefunden")

    briefing = (db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()
                if proj.lead_id else None)
    seite = _seiten_name(proj.wireframe_data, body.page_id)

    job_id = str(uuid.uuid4())
    _variant_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_variant_job,
        kwargs={
            "job_id":   job_id,
            "api_key":  api_key,
            "slug":     body.slug,
            "vorlage":  vorlage.html_template or "",
            "slots":    vorlage.slots or [],
            "briefing": briefing,
            "wunsch":   body.wunsch or "",
            "seite":    seite,
        },
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}


@wireframe_router.get("/wireframe-compose-jobs/{job_id}")
def get_compose_job(job_id: str, user=Depends(require_innendienst)):
    """Polling fuer den Kompositions-Auftrag."""
    job = _compose_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden oder bereits abgeholt")
    if job["status"] in ("done", "error"):
        return _compose_jobs.pop(job_id)
    return job


@wireframe_router.post("/{project_id}/wireframe/compose")
def compose_page(
    project_id: int,
    body: KompositionRequest,
    db: Session = Depends(get_db),
    user=Depends(require_innendienst),
):
    """Schlaegt eine Abfolge fuer diese Seite vor.

    Gespeichert wird nichts: Das Ergebnis geht ans Frontend, dort wird es
    angesehen und uebernommen. Das Markup je Section schreibt danach Stufe B.
    """
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Projekt nicht gefunden")
    if not Anthropic:
        raise HTTPException(500, "anthropic-Library nicht installiert")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "ANTHROPIC_API_KEY nicht konfiguriert")

    # Nur freigegebene Bloecke — ein Entwurf hat auf einer Kundenseite nichts
    # verloren, und der Wireframe-Generator haelt es genauso.
    bloecke = [
        {"slug": r.slug, "category": r.category, "name": r.name,
         "ki_prompt_hint": r.ki_prompt_hint}
        for r in _nur_freigegebene(db.query(ComponentLibrary)).all()
    ]

    seite = db.execute(text("""
        SELECT page_name, zweck, position FROM sitemap_pages WHERE id = :pid
    """), {"pid": body.page_id}).fetchone()
    seiten_name = (seite[0] if seite else "") or _seiten_name(
        proj.wireframe_data, body.page_id) or "Seite"
    zweck = (seite[1] if seite else "") or ""
    ist_startseite = bool(seite and (seite[2] or 0) == 0)

    bestehend = [b.get("slug") for b in _bloecke_der_seite(proj.wireframe_data,
                                                           body.page_id)]

    briefing = (db.query(Briefing).filter(Briefing.lead_id == proj.lead_id).first()
                if proj.lead_id else None)

    job_id = str(uuid.uuid4())
    _compose_jobs[job_id] = {"status": "running"}

    threading.Thread(
        target=_run_compose_job,
        kwargs={
            "job_id": job_id, "api_key": api_key, "seite": seiten_name,
            "zweck": zweck, "ist_startseite": ist_startseite, "briefing": briefing,
            "bloecke": bloecke, "bestehend": bestehend,
        },
        daemon=True,
    ).start()

    return {"job_id": job_id, "status": "running"}
