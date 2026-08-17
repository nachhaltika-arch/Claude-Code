"""Maschinenbefunde gehören nicht in das Feld für deine Notizen.

UX-06. `enrich_lead` schrieb nach jedem Lauf eine Zeile

    [Auto-Enrichment] SSL: OK | Impressum: FEHLT | PageSpeed: 43/100 | Score: 65/100

**vor** das, was ein Mensch in `lead.notes` geschrieben hatte. Bei jedem Lauf
erneut. Das Feld für die eigenen Notizen füllte sich mit Maschinentext, und
die eigene Notiz rutschte nach unten.

Beim Anfassen kam heraus, warum es überhaupt dort stand: `pagespeed_score`
wurde berechnet und **nirgends gespeichert**. Die Notizzeile war der einzige
Ort, an dem SSL, Impressum und PageSpeed einen Lauf überlebten. Die Zeile
ersatzlos zu streichen hätte die Befunde vernichtet — deshalb zuerst die
Spalten, dann die Zeile.
"""
import pytest


@pytest.fixture
def betrieb_mit_notiz(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(
            company_name="Pytest Anreicherung",
            website_url="https://beispiel-anreicherung.de",
            notes="Chef ruft am liebsten dienstags zurück.",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def _lead(lead_id: int):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == lead_id).first()
    finally:
        db.close()


@pytest.fixture
def ohne_netz(monkeypatch):
    """Weder Scraper noch PageSpeed dürfen im Test wirklich hinausgehen."""
    async def falscher_scraper(url, *args, **kwargs):
        return {"has_impressum": True, "raw_html": "", "company_name": "",
                "phone": "", "email": "", "city": "", "trade": ""}

    monkeypatch.setattr("services.scraper.scrape_website", falscher_scraper)


def test_die_notiz_des_menschen_bleibt_unberuehrt(app, betrieb_mit_notiz, ohne_netz):
    import asyncio
    from database import SessionLocal
    from services.lead_enrichment import enrich_lead

    db = SessionLocal()
    try:
        asyncio.run(enrich_lead(betrieb_mit_notiz, db))
    finally:
        db.close()

    assert _lead(betrieb_mit_notiz).notes == "Chef ruft am liebsten dienstags zurück."


def test_die_befunde_stehen_in_eigenen_feldern(app, betrieb_mit_notiz, ohne_netz):
    import asyncio
    from database import SessionLocal
    from services.lead_enrichment import enrich_lead

    db = SessionLocal()
    try:
        asyncio.run(enrich_lead(betrieb_mit_notiz, db))
    finally:
        db.close()

    lead = _lead(betrieb_mit_notiz)
    assert lead.has_ssl is True, "https:// in der Adresse"
    assert lead.has_impressum is True
    assert lead.enriched_at is not None, "Ohne Zeitpunkt ist ein Befund nicht einzuordnen"


def test_ein_betrieb_ohne_notiz_bekommt_auch_keine(app, ohne_netz):
    import asyncio
    from database import SessionLocal, Lead
    from services.lead_enrichment import enrich_lead

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Ohne Notiz",
                    website_url="https://ohne-notiz.de")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        lead_id = lead.id
        asyncio.run(enrich_lead(lead_id, db))
    finally:
        db.close()

    assert not _lead(lead_id).notes


def test_der_pagespeed_wert_ueberlebt_den_lauf(app, betrieb_mit_notiz, ohne_netz, monkeypatch):
    """Vorher stand er nur in der Notizzeile — also nirgends."""
    import asyncio
    from database import SessionLocal
    from services import lead_enrichment

    async def falscher_pagespeed(url):
        return 43

    monkeypatch.setattr(lead_enrichment, "_pagespeed_mobil", falscher_pagespeed)

    db = SessionLocal()
    try:
        asyncio.run(lead_enrichment.enrich_lead(betrieb_mit_notiz, db))
    finally:
        db.close()

    assert _lead(betrieb_mit_notiz).pagespeed_mobile_score == 43
