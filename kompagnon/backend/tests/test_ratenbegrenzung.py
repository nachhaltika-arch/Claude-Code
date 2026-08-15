"""
Grenzen für die Endpunkte, die ohne Anmeldung Geld kosten.

L-04 der Soll-Ist-Analyse, benannt als „kein Rate-Limiting auf
`POST /api/leads/public`". Beim Nachsehen am 15.08.2026 zeigte sich, dass der
teurere Nachbar dasselbe Problem hat und niemand ihn genannt hatte:
**`POST /api/audit/start` ist ohne Anmeldung erreichbar** und löst je Aufruf
einen KI-Lauf, PageSpeed-Kontingent, einen Screenshot und einen
Mehrseiten-Crawl aus.

Das Widget hat seit dem 11.08. eigene Grenzen — aber es ruft die Funktion
intern auf. Wer den HTTP-Endpunkt direkt anspricht, umgeht sie vollständig.

Gezählt wird über das, was ohnehin gespeichert wird: Zeitpunkt und Zieladresse.
Keine neue Spalte, keine IP-Speicherung — für eine Grenze, die Kosten deckelt,
reicht „wie oft wurde diese Adresse zuletzt geprüft" und „wie viel läuft
insgesamt".
"""
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from database import AuditResult, Lead, SessionLocal
from services import ratenbegrenzung as rb


@pytest.fixture
def db(app):
    """`app` baut das Schema — ohne sie fehlen die Tabellen."""
    sitzung = SessionLocal()
    try:
        sitzung.query(AuditResult).delete()
        sitzung.query(Lead).filter(Lead.lead_source == "test_rate").delete()
        sitzung.commit()
        yield sitzung
    finally:
        sitzung.rollback()
        sitzung.close()


def _audits(db, anzahl, url="https://ziel.de/", alter_stunden=0):
    zeitpunkt = datetime.utcnow() - timedelta(hours=alter_stunden)
    for _ in range(anzahl):
        db.add(AuditResult(website_url=url, company_name="Ziel",
                           status="completed", created_at=zeitpunkt))
    db.commit()


# ── Grenze je Zieladresse ──────────────────────────────────────────

def test_die_erste_pruefung_einer_adresse_geht_durch(db):
    # Act & Assert — kein Fehler
    rb.pruefe_audit_grenzen(db, "https://ziel.de/")


def test_dieselbe_adresse_wird_nicht_beliebig_oft_geprueft(db):
    # Arrange
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG, url="https://ziel.de/")

    # Act & Assert
    with pytest.raises(HTTPException) as fehler:
        rb.pruefe_audit_grenzen(db, "https://ziel.de/")
    assert fehler.value.status_code == 429


def test_eine_andere_adresse_bleibt_frei(db):
    # Arrange — die eine ist ausgeschöpft
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG, url="https://ziel.de/")

    # Act & Assert — die andere nicht
    rb.pruefe_audit_grenzen(db, "https://andere.de/")


def test_gestrige_laeufe_zaehlen_nicht_mehr(db):
    # Arrange
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG, url="https://ziel.de/",
            alter_stunden=25)

    # Act & Assert
    rb.pruefe_audit_grenzen(db, "https://ziel.de/")


def test_die_adresse_wird_unabhaengig_von_schreibweise_gezaehlt(db):
    # Arrange — sonst umgeht ein angehängter Schrägstrich die Grenze
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG, url="https://ziel.de/")

    # Act & Assert
    with pytest.raises(HTTPException):
        rb.pruefe_audit_grenzen(db, "https://ZIEL.de")


# ── Gesamtgrenze ───────────────────────────────────────────────────

def test_die_gesamtlast_ist_gedeckelt(db):
    # Arrange — viele verschiedene Adressen, jede für sich unauffällig
    for i in range(rb.LIMIT_GESAMT_PRO_STUNDE):
        _audits(db, 1, url=f"https://ziel-{i}.de/")

    # Act & Assert
    with pytest.raises(HTTPException) as fehler:
        rb.pruefe_audit_grenzen(db, "https://noch-eine.de/")
    assert fehler.value.status_code == 429
    assert "Kontingent" in fehler.value.detail


# ── Wer angemeldet ist, wird nicht gedeckelt ───────────────────────

def test_angemeldete_arbeiten_ohne_grenze(db):
    # Arrange — das Tool selbst prüft Kundenseiten und darf nicht ausgesperrt
    # werden, nur weil dieselbe Adresse mehrfach geprüft wird
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG * 3, url="https://ziel.de/")

    # Act & Assert
    rb.pruefe_audit_grenzen(db, "https://ziel.de/", angemeldet=True)


# ── Die Lead-Anlage ────────────────────────────────────────────────

def test_die_lead_anlage_ist_ebenfalls_gedeckelt(db):
    # Arrange
    for i in range(rb.LIMIT_LEADS_PRO_STUNDE):
        db.add(Lead(website_url=f"https://neu-{i}.de", company_name=f"n{i}",
                    lead_source="test_rate", created_at=datetime.utcnow()))
    db.commit()

    # Act & Assert
    with pytest.raises(HTTPException) as fehler:
        rb.pruefe_lead_grenzen(db)
    assert fehler.value.status_code == 429


def test_die_lead_anlage_laeuft_normalerweise_durch(db):
    rb.pruefe_lead_grenzen(db)


# ── Am echten Endpunkt ─────────────────────────────────────────────

def test_der_audit_endpunkt_weist_die_vierte_anfrage_ab(client, db, monkeypatch):
    # Arrange — drei Läufe auf dieselbe Adresse liegen schon vor
    _audits(db, rb.LIMIT_JE_ADRESSE_PRO_TAG, url="https://viel-geprueft.de/")

    # Act
    antwort = client.post("/api/audit/start",
                          json={"website_url": "https://viel-geprueft.de/"})

    # Assert — kein Scrape, kein KI-Lauf, kein Datensatz
    assert antwort.status_code == 429


def test_der_endpunkt_laesst_eine_neue_adresse_durch(client, db, monkeypatch):
    # Arrange — der teure Teil wird nicht wirklich ausgeführt
    monkeypatch.setattr("routers.audit._run_audit_background", lambda audit_id: None)

    async def kein_scrape(url):
        return {}

    monkeypatch.setattr("services.scraper.scrape_website", kein_scrape)

    # Act
    antwort = client.post("/api/audit/start",
                          json={"website_url": "https://ganz-neu.de/"})

    # Assert
    assert antwort.status_code == 200, antwort.text


def test_das_widget_umgeht_die_grenze_bewusst(db):
    # Arrange — das Widget prüft eigene, feinere Grenzen und ruft die Funktion
    # dann direkt auf. Abhängigkeiten laufen dabei nicht mit; sonst würden
    # beide Zählungen gegeneinander arbeiten.
    import inspect

    from routers.audit import start_audit

    # Act
    unterschrift = inspect.signature(start_audit)

    # Assert — die Grenze hängt als Abhängigkeit, nicht im Rumpf
    assert "_grenzen" in unterschrift.parameters
