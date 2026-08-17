"""Die alten Befunde stehen in der Notizzeile — sie gehoeren in die Spalten.

Seit heute schreibt die Anreicherung SSL, Impressum und PageSpeed in eigene
Spalten (UX-06). Fuer den Bestand hiess das: Die Spalten sind leer, die
Oberflaeche sagt ehrlich „nicht geprueft" — und zwei Zeilen darunter steht
weiterhin die alte Notiz `[Auto-Enrichment] SSL: OK | …`.

Beides stimmt fuer sich. Zusammen widersprechen sie sich auf einem Bildschirm.

Die Werte sind also da, nur im falschen Feld. Sie herueberzuholen ist besser,
als sie mit `scripts/notizen-bereinigen.sql` zu loeschen und auf den naechsten
Anreicherungslauf zu warten.

**Ein Zeitpunkt wird dabei nicht erfunden.** Die Notizzeile trug keinen, also
bleibt `enriched_at` leer, und die Oberflaeche sagt „Zeitpunkt unbekannt"
statt eines gefaelligen Datums.
"""
import pytest

from services.anreicherungsnotiz import befunde_aus_notiz, notiz_ohne_maschinenzeilen


ZEILE = "[Auto-Enrichment] SSL: OK | Impressum: FEHLT | PageSpeed: 43/100 | Score: 65/100"


# ── Die Zeile lesen ───────────────────────────────────────────────────

def test_die_zeile_wird_gelesen():
    assert befunde_aus_notiz(ZEILE) == {
        "has_ssl": True, "has_impressum": False, "pagespeed_mobile_score": 43,
    }


def test_auch_wenn_eine_eigene_notiz_davor_steht():
    text = f"Chef ruft dienstags zurück.\n{ZEILE}"

    assert befunde_aus_notiz(text)["has_ssl"] is True


def test_die_juengste_zeile_gewinnt():
    """Die Anreicherung stellte jede neue Zeile voran — oben steht die neueste."""
    neuer = "[Auto-Enrichment] SSL: OK | Impressum: OK | PageSpeed: 88/100 | Score: 90/100"
    alt = "[Auto-Enrichment] SSL: FEHLT | Impressum: FEHLT | PageSpeed: 12/100 | Score: 20/100"

    assert befunde_aus_notiz(f"{neuer}\n{alt}")["pagespeed_mobile_score"] == 88


def test_ohne_maschinenzeile_gibt_es_nichts_zu_holen():
    assert befunde_aus_notiz("Nur meine eigene Notiz.") == {}
    assert befunde_aus_notiz(None) == {}


def test_eine_halbe_zeile_liefert_nur_was_dasteht():
    assert befunde_aus_notiz("[Auto-Enrichment] SSL: OK") == {"has_ssl": True}


# ── Die Zeile entfernen ───────────────────────────────────────────────

def test_die_eigene_notiz_bleibt_erhalten():
    text = f"{ZEILE}\nChef ruft dienstags zurück."

    assert notiz_ohne_maschinenzeilen(text) == "Chef ruft dienstags zurück."


def test_bleibt_nichts_uebrig_wird_es_leer():
    """Ein leerer Kasten in der Oberfläche ist schlechter als gar keiner."""
    assert notiz_ohne_maschinenzeilen(ZEILE) is None


def test_eine_notiz_ohne_maschinentext_wird_nicht_angefasst():
    assert notiz_ohne_maschinenzeilen("Alles meins") == "Alles meins"


# ── Der Endpunkt ──────────────────────────────────────────────────────

@pytest.fixture
def betrieb_mit_alter_notiz(app):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = Lead(
            company_name="Pytest Altbefund",
            website_url="https://pytest-altbefund.de",
            notes=f"{ZEILE}\nChef ruft dienstags zurück.",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead.id
    finally:
        db.close()


def _lead(lead_id):
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == lead_id).first()
    finally:
        db.close()


def test_der_endpunkt_holt_die_werte_herueber(client, auth_headers, betrieb_mit_alter_notiz):
    antwort = client.post("/api/leads/befunde-nachtragen", headers=auth_headers)

    assert antwort.status_code == 200
    lead = _lead(betrieb_mit_alter_notiz)
    assert lead.has_ssl is True
    assert lead.has_impressum is False
    assert lead.pagespeed_mobile_score == 43


def test_der_endpunkt_raeumt_die_zeile_weg(client, auth_headers, betrieb_mit_alter_notiz):
    client.post("/api/leads/befunde-nachtragen", headers=auth_headers)

    assert _lead(betrieb_mit_alter_notiz).notes == "Chef ruft dienstags zurück."


def test_kein_zeitpunkt_wird_erfunden(client, auth_headers, betrieb_mit_alter_notiz):
    """Die Zeile trug keinen — also bleibt das Feld leer."""
    client.post("/api/leads/befunde-nachtragen", headers=auth_headers)

    assert _lead(betrieb_mit_alter_notiz).enriched_at is None


def test_ein_frischer_befund_wird_nicht_ueberschrieben(client, auth_headers,
                                                       betrieb_mit_alter_notiz):
    """Was die neue Anreicherung geschrieben hat, ist jünger als die Notiz."""
    from datetime import datetime
    from database import SessionLocal, Lead

    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == betrieb_mit_alter_notiz).first()
        lead.has_ssl = False
        lead.enriched_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

    client.post("/api/leads/befunde-nachtragen", headers=auth_headers)

    assert _lead(betrieb_mit_alter_notiz).has_ssl is False


def test_ein_kunde_darf_das_nicht(client, kunde_headers):
    antwort = client.post("/api/leads/befunde-nachtragen", headers=kunde_headers)

    assert antwort.status_code == 403
