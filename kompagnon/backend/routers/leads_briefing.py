"""Die Bruecke vom Betrieb zu seinem Briefing (L-25).

Ein Endpunkt: Aus dem gecrawlten Inhalt der Kundenwebsite werden Vorschlaege
fuer den Briefing-Fragebogen gebaut. Am 2026-08-30 aus `leads.py`
herausgeloest — die Datei stand mit 805 Zeilen ueber der Grenze.

**Warum nicht nach `briefings.py`.** Die Adresse lautet
`/api/leads/{lead_id}/briefing-prefill`, und sie soll es bleiben: Das Frontend
ruft sie so, und eine Umbenennung waere eine Aenderung an der Schnittstelle,
die dieser Schnitt nicht rechtfertigt. Ein Modul unter `/api/briefings`, das
einen `/api/leads`-Pfad traegt, waere die schlechtere Ordnung — deshalb eine
eigene Datei mit eigenem Praefix statt eines Gastauftritts.
"""
import json
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from routers.auth_router import require_any_auth, require_innendienst

logger = logging.getLogger(__name__)

# **Die Sperre gehoert an den Router, nicht nur an die Funktion.** Genau das
# ist beim Umzug am 30.08.2026 zuerst schiefgegangen: In `leads.py` haengt
# `require_innendienst` am Router, die Funktion selbst traegt nur
# `require_any_auth`. Wer sie herausloest und den Router ohne Abhaengigkeit
# neu anlegt, macht aus „Innendienst" still „irgendwer ist angemeldet" — und
# ein Kunde haette die Briefing-Vorschlaege **jedes** Betriebs abrufen koennen.
#
# Gefunden hat es `test_zugriffsschutz_bestand`: 59 statt 58 schwach
# geschuetzte Routen. Beim Lesen faellt so etwas nicht auf, weil an der
# Funktion nichts fehlt.
router = APIRouter(prefix="/api/leads", tags=["leads-briefing"],
                   dependencies=[Depends(require_innendienst)])


@router.post("/{lead_id}/briefing-prefill")
async def briefing_prefill_from_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_any_auth),
):
    """Briefing-Vorschlaege aus gecrawltem Website-Content via lead_id."""
    rows = db.execute(
        text("""
            SELECT url, title, meta_description, h1, h2s, text_preview
            FROM website_content_cache
            WHERE customer_id = :lid
            ORDER BY scraped_at DESC LIMIT 20
        """),
        {"lid": lead_id},
    ).fetchall()

    if not rows:
        raise HTTPException(400, "Kein Website-Content vorhanden. Bitte zuerst Crawler ausfuehren.")

    all_h2s, page_names, pages_text = [], [], []
    for row in rows:
        url, title, meta, h1, h2s_json, preview = row
        try:
            all_h2s.extend(json.loads(h2s_json or '[]'))
        except Exception:
            pass
        try:
            path = urlparse(url).path.strip('/').split('/')[-1]
            if path and len(path) > 1:
                name = path.replace('-', ' ').replace('_', ' ').title()
                if name not in page_names:
                    page_names.append(name)
        except Exception:
            pass
        if preview:
            pages_text.append(f"URL: {url}\nH1: {h1 or title}\nVorschau: {preview[:300]}")

    return {
        "gewerk":        (all_h2s[0] if all_h2s else '')[:80],
        "leistungen":    ', '.join(set(all_h2s[:8])),
        "wunschseiten":  ', '.join(page_names[:8]),
        "einzugsgebiet": '',
        "usp":           '',
        "zielgruppe":    '',
        "source":        "heuristic",
    }


# ── Kaltakquise ──────────────────────────────────────────────────────────────
