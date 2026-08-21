"""Ein fremdes Audit liest man nicht, indem man hochzählt.

Befund vom 19.08.2026 (L-52). `GET /api/audit/{id}` und
`/api/audit/status/{id}` sind ohne Anmeldung erreichbar — und das aus einem
guten Grund: Die öffentliche Landingpage startet ein Gratis-Audit und holt
das Ergebnis danach genau dort ab. Der Interessent hat kein Konto und soll
keines brauchen.

Der Preis dafür war, dass die Kennung eine fortlaufende Zahl ist. Wer sie
hochzählt, liest die Audits fremder Betriebe: Firmenname, Adresse, Bewertung
und die vollständige Befundliste.

Das Widget macht es seit jeher richtig vor — es liefert seinen Bericht unter
`/api/widget/report/{token}`. Dasselbe hier: Das Audit bekommt beim Anlegen
ein Geheimnis, `/start` gibt es zurück, und wer nicht angemeldet ist, braucht
es zum Lesen.

**Was dabei nicht passieren darf**, hält der zweite Teil fest: Die
Landingpage muss weiter funktionieren, und der Innendienst darf seine Audits
weiterhin ohne Token öffnen — sonst wäre die Leadliste unbenutzbar.
"""
import pytest

from database import SessionLocal, AuditResult


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def audit(db):
    """Ein fertiges Audit, wie es nach einem Lauf dasteht."""
    a = AuditResult(
        website_url="https://beispiel.invalid",
        company_name="Fremdbetrieb GmbH",
        status="completed",
        total_score=62,
        level="Homepage Standard Bronze",
        public_token="probetoken1234567890",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    yield a
    db.delete(a)
    db.commit()


# ── Was nicht mehr gehen darf ─────────────────────────────────────────

def test_ohne_token_und_ohne_anmeldung_kein_audit(client, audit):
    """Der Kern von L-52."""
    # Act
    antwort = client.get(f"/api/audit/{audit.id}")

    # Assert — 404, nicht 403: Ob es das Audit gibt, geht Fremde nichts an
    assert antwort.status_code == 404, (
        f"-> {antwort.status_code}: Ein fremdes Audit ist durch Hochzählen lesbar."
    )


def test_ein_falsches_token_reicht_nicht(client, audit):
    # Act
    antwort = client.get(f"/api/audit/{audit.id}", params={"token": "danebengeraten"})

    # Assert
    assert antwort.status_code == 404


def test_auch_der_zwischenstand_ist_geschuetzt(client, audit):
    """Sonst verrät der Statusweg, was der Hauptweg verschweigt."""
    # Act
    antwort = client.get(f"/api/audit/status/{audit.id}")

    # Assert
    assert antwort.status_code == 404


# ── Was weiter gehen muss ─────────────────────────────────────────────

def test_mit_dem_richtigen_token_geht_es(client, audit):
    """Der Weg der Landingpage: starten, Token behalten, abholen."""
    # Act
    antwort = client.get(f"/api/audit/{audit.id}",
                         params={"token": audit.public_token})

    # Assert
    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["total_score"] == 62


def test_der_innendienst_braucht_kein_token(client, auth_headers, audit):
    """Sonst wäre jedes Audit in der Leadliste unlesbar."""
    # Act
    antwort = client.get(f"/api/audit/{audit.id}", headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, antwort.text


def test_der_start_gibt_das_token_heraus(app):
    """Ohne diese Rückgabe könnte die Landingpage ihr eigenes Audit nicht lesen.

    Geprüft an der Quelle statt über einen echten Lauf: `POST /start` stösst
    einen Audit-Lauf an, der ins Netz greift.
    """
    import inspect

    from routers import audit as audit_router

    quelle = inspect.getsource(audit_router.start_audit)

    assert "public_token" in quelle, (
        "Der Start legt kein Geheimnis an oder gibt es nicht zurück — dann "
        "kommt der Interessent nicht an sein eigenes Ergebnis."
    )


def test_ein_altes_audit_ohne_token_bleibt_verschlossen(client, db):
    """Bestandsdaten haben kein Geheimnis — und bekommen keins geraten.

    Sie sind nur ueber eine Anmeldung erreichbar. Das ist richtig so: Ein
    Audit von gestern holt niemand mehr ueber die Landingpage ab.
    """
    # Arrange
    alt = AuditResult(website_url="https://alt.invalid", company_name="Alt GmbH",
                      status="completed", total_score=40)
    db.add(alt)
    db.commit()

    try:
        # Act / Assert
        assert client.get(f"/api/audit/{alt.id}").status_code == 404
        assert client.get(f"/api/audit/{alt.id}",
                          params={"token": ""}).status_code == 404
    finally:
        db.delete(alt)
        db.commit()
