"""Vorhandene Betriebe ergaenzen — Namen, Impressum, Ladezeit (L-25).

**Warum eigene Datei, 22.08.2026.** `routers/leads.py` hatte 2.575 Zeilen und
fuenfzig Funktionen. Sechs Routen, die alle dasselbe tun: einen Betrieb nehmen, der schon da
ist, und ein Feld nachtragen, das fehlt. Sie teilten mit dem Rest von
`leads.py` nichts ausser `logger`, dem Router und der Konstante
`NAMEN_JE_LAUF`, die mitgewandert ist.

Vor dem Schnitt nachgemessen: Der Rest braucht von hier **nichts**.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime
from database import Lead, Project, AuditResult, get_db, SessionLocal
from services import betriebsname, lead_quellen
from services.audit_pagespeed import (
    PSI_ENDPOINT,
    auth_headers as pagespeed_auth_headers,
)
import asyncio
import httpx
import json
from routers.auth_router import require_innendienst, require_admin, require_any_auth
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads-anreicherung"],
                   dependencies=[Depends(require_innendienst)])


#: Wie viele Betriebe ein Aufruf hoechstens anfasst. Jeder kostet einen
#: Seitenabruf samt KI-Auswertung — das soll man dosieren koennen.
NAMEN_JE_LAUF = 25


@router.post("/namen-nachtragen")
async def namen_nachtragen(
    anzahl: int = Query(NAMEN_JE_LAUF, ge=1, le=NAMEN_JE_LAUF,
                        description="Wie viele Betriebe dieser Lauf anfasst"),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Holt den echten Firmennamen für Betriebe, die wie ihre Domain heißen.

    Der Domainimport legt Betriebe mit der Domain als Namen an. Bis zum
    17.08.2026 verwarf der Impressum-Schritt den echten Namen wieder, weil das
    Feld als „gefüllt" galt. Behoben ist das — aber nur für künftige Läufe.
    Dieser Endpunkt holt nach, was in der Liste steht.

    Angefasst wird ausschließlich, wessen Name ein Platzhalter ist. Ein von
    Hand gepflegter Name bleibt, auch wenn das Impressum etwas anderes sagt.
    """
    from services.impressum_scraper import extract_contact_from_impressum

    kandidaten = [
        lead for lead in db.query(Lead).filter(Lead.website_url != "").all()
        if betriebsname.ist_platzhalter(lead.company_name, lead.website_url)
    ][:anzahl]

    geaendert, ohne_ergebnis = [], []
    for lead in kandidaten:
        try:
            ergebnis = await extract_contact_from_impressum(lead.website_url)
        except Exception as fehler:  # noqa: BLE001 — ein Betrieb darf den Lauf nicht kippen
            logger.warning(f"Impressum für {lead.website_url} nicht lesbar: {fehler}")
            ohne_ergebnis.append({"betrieb": lead.company_name, "grund": str(fehler)[:120]})
            continue

        # Der Abruf hat Sekunden gedauert. In der Zeit kann jemand über die
        # Oberfläche denselben Betrieb bearbeitet haben — genau das geschah am
        # 17.08.2026 bei „Frowein Haustechnik". Ohne dieses Nachlesen
        # entscheidet der Lauf auf dem Stand von vor dem Abruf.
        db.refresh(lead)

        # Drei Lagen, die vorher alle „kein brauchbarer Name im Impressum"
        # hießen — und damit dasselbe behaupteten wie ein echter Fehlschlag.
        # Deshalb stand ein Betrieb im Bericht als gescheitert, der längst
        # einen richtigen Namen trug.
        if not betriebsname.ist_platzhalter(lead.company_name, lead.website_url):
            ohne_ergebnis.append({
                "betrieb": lead.company_name,
                "grund": "hatte inzwischen schon einen richtigen Namen",
            })
            continue

        if not ergebnis.get("success"):
            ohne_ergebnis.append({
                "betrieb": lead.company_name,
                "grund": f"Impressum nicht lesbar: {ergebnis.get('error') or 'unbekannt'}"[:120],
            })
            continue

        gefunden = (ergebnis.get("data") or {}).get("company_name")
        echter_name = betriebsname.uebernehmen(lead.company_name, gefunden, lead.website_url)
        if not echter_name:
            ohne_ergebnis.append({
                "betrieb": lead.company_name,
                "grund": ("Impressum gelesen, aber kein Firmenname darin"
                          if not (gefunden or "").strip()
                          else f"gefundener Name taugt nicht: {gefunden[:60]!r}"),
            })
            continue

        geaendert.append({"id": lead.id, "vorher": lead.company_name, "nachher": echter_name})
        lead.company_name = echter_name
        # Nach jedem Betrieb schreiben, nicht am Ende. Je Betrieb fallen ein
        # Startseitenabruf, bis zu zwölf Kandidaten und ein KI-Aufruf an —
        # zusammen Sekunden. Reißt die Verbindung nach dem zwanzigsten ab,
        # sollen die ersten neunzehn Namen trotzdem stehen.
        db.commit()

    return {
        "geprueft": len(kandidaten),
        "geaendert": geaendert,
        "ohne_ergebnis": ohne_ergebnis,
        "grenze_erreicht": len(kandidaten) == anzahl,
    }


@router.post("/{lead_id}/extract-impressum")
async def extract_impressum(lead_id: int, db: Session = Depends(get_db)):
    """Extract contact data from a lead's website impressum using AI."""
    from services.impressum_scraper import extract_contact_from_impressum

    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    result = await extract_contact_from_impressum(lead.website_url)

    if not result['success']:
        raise HTTPException(status_code=422, detail=result['error'])

    # Nur leere Felder befüllen — vorhandene Daten NICHT überschreiben
    data = result['data']
    updated = {}

    # Der Firmenname nach eigener Regel — der Domainimport hat ihn mit der
    # Domain vorbelegt, und `not existing` hielte das für einen Wert.
    echter_name = betriebsname.uebernehmen(
        lead.company_name, data.get('company_name'), lead.website_url,
    )
    if echter_name:
        lead.company_name = echter_name
        updated['company_name'] = echter_name

    field_map = {
        'legal_form': lead.legal_form,
        'ceo_first_name': lead.ceo_first_name,
        'ceo_last_name': lead.ceo_last_name,
        'street': lead.street,
        'house_number': lead.house_number,
        'postal_code': lead.postal_code,
        'city': lead.city,
        'phone': lead.phone,
        'email': lead.email,
        'vat_id': lead.vat_id,
        'register_number': lead.register_number,
        'register_court': lead.register_court,
        'trade': lead.trade,
    }

    for field, existing in field_map.items():
        if field in data and not existing:
            setattr(lead, field, data[field])
            updated[field] = data[field]

    if updated:
        db.commit()

    return {
        'success': True,
        'extracted': data,
        'updated_fields': updated,
        'skipped_fields': [f for f in data if f not in updated],
    }


def _pagespeed_payload_lead(lead: Lead) -> dict:
    """Return stored PageSpeed values for a lead as a dict."""
    return {
        "mobile_score":  lead.pagespeed_mobile_score,
        "desktop_score": lead.pagespeed_desktop_score,
        "lcp_mobile":    lead.pagespeed_lcp_mobile,
        "cls_mobile":    lead.pagespeed_cls_mobile,
        "inp_mobile":    lead.pagespeed_inp_mobile,
        "fcp_mobile":    lead.pagespeed_fcp_mobile,
        "checked_at":    lead.pagespeed_checked_at.isoformat() if lead.pagespeed_checked_at else None,
    }


@router.get("/{lead_id}/pagespeed")
def get_lead_pagespeed(lead_id: int, db: Session = Depends(get_db)):
    """Return the last stored PageSpeed values for this lead without a new API call."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    return _pagespeed_payload_lead(lead)


@router.post("/{lead_id}/pagespeed")
async def run_lead_pagespeed(lead_id: int, db: Session = Depends(get_db)):
    """Call Google PageSpeed Insights (mobile + desktop), persist results on the lead."""
    from sqlalchemy import text as sa_text

    # Schnelle URL-Abfrage per Raw-SQL (vermeidet ORM-Spalten-Timeout)
    row = db.execute(sa_text("SELECT website_url FROM leads WHERE id = :lid"), {"lid": lead_id}).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    website_url = row[0]
    if not website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")

    # DB-Verbindung VOR dem externen PageSpeed-Call freigeben — der Call kann
    # bis zu 60s dauern und wuerde sonst eine Pool-Connection blockieren.
    # Persistiert wird unten ueber eine frische SessionLocal().
    db.close()

    # Schluessel als Kopfzeile, nicht in der URL — httpx protokolliert die
    # vollstaendige Anfrage-URL (L-98). Eine Stelle, vier Aufrufer.
    base = PSI_ENDPOINT
    params_base = {"url": website_url}
    kopf = pagespeed_auth_headers()

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            mobile_resp, desktop_resp = await asyncio.gather(
                client.get(base, params={**params_base, "strategy": "mobile"}, headers=kopf),
                client.get(base, params={**params_base, "strategy": "desktop"}, headers=kopf),
            )
    except Exception as e:
        logger.error(f"PageSpeed API request failed for {website_url}: {e}")
        raise HTTPException(status_code=502, detail=f"PageSpeed API nicht erreichbar: {str(e)[:100]}")

    # Log response status for debugging
    if mobile_resp.status_code != 200:
        logger.warning(f"PageSpeed mobile {mobile_resp.status_code} for {website_url}: {mobile_resp.text[:200]}")
    if desktop_resp.status_code != 200:
        logger.warning(f"PageSpeed desktop {desktop_resp.status_code} for {website_url}: {desktop_resp.text[:200]}")

    def _score(resp) -> int | None:
        try:
            data = resp.json()
            cat = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {})
            raw = cat.get("score")
            return round(raw * 100) if raw is not None else None
        except Exception:
            return None

    def _audit(resp, key) -> float | None:
        try:
            return resp.json()["lighthouseResult"]["audits"][key]["numericValue"]
        except Exception:
            return None

    mobile_score = _score(mobile_resp)
    desktop_score = _score(desktop_resp)
    logger.info(f"PageSpeed for {website_url}: mobile={mobile_score}, desktop={desktop_score}")

    if mobile_score is None and desktop_score is None:
        raise HTTPException(status_code=502, detail="PageSpeed konnte keine Scores ermitteln — Google API hat keine Ergebnisse geliefert")

    # Per Raw-SQL speichern (schnell, kein ORM-Overhead, kein Timeout) —
    # frische Session, da die urspruengliche vor dem PageSpeed-Call geschlossen wurde.
    db2 = SessionLocal()
    try:
        db2.execute(sa_text("""
            UPDATE leads SET
                pagespeed_mobile_score  = :mobile,
                pagespeed_desktop_score = :desktop,
                pagespeed_lcp_mobile    = :lcp,
                pagespeed_cls_mobile    = :cls,
                pagespeed_inp_mobile    = :inp,
                pagespeed_fcp_mobile    = :fcp,
                pagespeed_checked_at    = :checked
            WHERE id = :lid
        """), {
            "mobile": mobile_score,
            "desktop": desktop_score,
            "lcp": _audit(mobile_resp, "largest-contentful-paint"),
            "cls": _audit(mobile_resp, "cumulative-layout-shift"),
            "inp": _audit(mobile_resp, "interaction-to-next-paint"),
            "fcp": _audit(mobile_resp, "first-contentful-paint"),
            "checked": datetime.utcnow(),
            "lid": lead_id,
        })
        db2.commit()
    except Exception as e:
        db2.rollback()
        logger.error(f"PageSpeed save failed for lead {lead_id}: {e}")
        raise HTTPException(500, f"Speichern fehlgeschlagen: {str(e)[:100]}")
    finally:
        db2.close()

    return {
        "mobile_score": mobile_score,
        "desktop_score": desktop_score,
        "lcp_mobile": _audit(mobile_resp, "largest-contentful-paint"),
        "cls_mobile": _audit(mobile_resp, "cumulative-layout-shift"),
        "inp_mobile": _audit(mobile_resp, "interaction-to-next-paint"),
        "fcp_mobile": _audit(mobile_resp, "first-contentful-paint"),
        "checked_at": datetime.utcnow().isoformat(),
    }


@router.post("/{lead_id}/domain-check")
async def domain_check_lead(lead_id: int, db: Session = Depends(get_db), _=Depends(require_any_auth)):
    """Manueller Domain-Check für einen Lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(status_code=400, detail="Keine Website-URL hinterlegt")
    website_url = lead.website_url

    # DB-Verbindung vor externem Check freigeben
    db.close()

    from services.domain_checker import check_domain
    result = await check_domain(website_url)

    # Neue Session zum Speichern
    db2 = SessionLocal()
    try:
        lead = db2.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise HTTPException(status_code=404, detail="Lead nicht gefunden")
        lead.domain_reachable   = result["reachable"]
        lead.domain_status_code = result.get("status_code")
        lead.domain_checked_at  = datetime.utcnow()
        db2.commit()
        return {
            "reachable":    lead.domain_reachable,
            "status_code":  lead.domain_status_code,
            "checked_at":   lead.domain_checked_at.isoformat(),
            "website_url":  lead.website_url,
        }
    finally:
        db2.close()


# ── Dazugekommen am 23.08.2026 (L-25) ────────────────────────────────────
#
# Diese vier Routen standen in `leads.py` unter der Ueberschrift
# „IMPORT ENDPOINTS" — und keine davon importiert etwas. Die Ueberschrift war
# stehengeblieben, als die echten Import-Routen am 22.08. nach
# `leads_import.py` gingen; darunter sammelte sich, was thematisch hierher
# gehoert: Daten zu einem bekannten Betrieb nachtragen.
#
# Ein Wegweiser, der in die falsche Richtung zeigt, ist schlimmer als keiner.


# ===== IMPORT ENDPOINTS =====







@router.post("/{lead_id}/enrich")
async def enrich_single_lead(lead_id: int, db: Session = Depends(get_db)):
    """Manually trigger enrichment for a single lead."""
    from services.lead_enrichment import enrich_lead
    result = await enrich_lead(lead_id, db)
    return result


@router.get("/{lead_id}/latest-screenshot")
def get_latest_screenshot(lead_id: int, db: Session = Depends(get_db)):
    """Get the latest audit screenshot for a lead, saving it to the lead if found."""
    latest = (
        db.query(AuditResult)
        .filter(AuditResult.lead_id == lead_id, AuditResult.status == "completed", AuditResult.screenshot_base64 != "", AuditResult.screenshot_base64 != None)
        .order_by(AuditResult.created_at.desc())
        .first()
    )
    if not latest or not latest.screenshot_base64:
        return {"screenshot_url": None}
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead and not lead.website_screenshot:
        lead.website_screenshot = latest.screenshot_base64
        db.commit()
    return {
        "screenshot_url": f"data:image/jpeg;base64,{latest.screenshot_base64}",
        "audit_date": latest.created_at.strftime("%d.%m.%Y") if latest.created_at else "",
        "audit_score": latest.total_score,
    }


@router.post("/{lead_id}/screenshot")
async def create_screenshot(lead_id: int, db: Session = Depends(get_db)):
    """Capture website screenshot and return it immediately."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    if not lead.website_url:
        raise HTTPException(400, "Keine Website-URL hinterlegt")

    url = lead.website_url
    if not url.startswith("http"):
        url = "https://" + url

    try:
        from services.screenshot import capture_screenshot
        screenshot_b64 = await capture_screenshot(url)
        if screenshot_b64:
            lead.website_screenshot = screenshot_b64
            db.commit()
            return {"success": True, "screenshot_url": f"data:image/jpeg;base64,{screenshot_b64}"}
        else:
            raise HTTPException(500, "Screenshot konnte nicht erstellt werden")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Screenshot Fehler: {str(e)}")


@router.post("/befunde-nachtragen")
def befunde_nachtragen(
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """Holt SSL, Impressum und PageSpeed aus der alten Notizzeile in die Spalten.

    Seit dem 17.08.2026 stehen diese Befunde in eigenen Spalten. Für den
    Bestand hieß das: Spalten leer, Oberfläche sagt „nicht geprüft" — und
    darunter behauptet die alte Notiz „SSL: OK". Beides stimmt für sich,
    zusammen widersprechen sie sich auf einem Bildschirm.

    Übernommen wird nur, was noch leer ist: Was die neue Anreicherung
    geschrieben hat, ist jünger als die Notiz. Ein Zeitpunkt wird nicht
    erfunden — die Zeile trug keinen.
    """
    from services import anreicherungsnotiz

    betroffen = db.query(Lead).filter(
        Lead.notes.ilike(f"%{anreicherungsnotiz.MARKE}%")).all()

    bericht = []
    for lead in betroffen:
        befunde = anreicherungsnotiz.befunde_aus_notiz(lead.notes)
        uebernommen = []
        for feld, wert in befunde.items():
            if getattr(lead, feld, None) is None:
                setattr(lead, feld, wert)
                uebernommen.append(feld)

        lead.notes = anreicherungsnotiz.notiz_ohne_maschinenzeilen(lead.notes)
        bericht.append({
            "id": lead.id,
            "betrieb": lead.company_name,
            "uebernommen": uebernommen,
            "notiz_bleibt": bool(lead.notes),
        })

    if bericht:
        db.commit()

    return {"betroffen": len(betroffen), "betriebe": bericht}
