"""Die Herkunft aus der Anzeige geht beim Absenden verloren (L-86).

**Gefunden am 22.08.2026** beim Nachpruefen der Haken des Mai-Audits (L-38).
Dort stand „UTM-Tracking ✅". Die Spalten gibt es, und `routers/kampagne.py`
fuellt sie — aber der **Hauptweg** tut es nicht: `POST /api/leads/public`,
das Formular auf der Landingpage und im eingebetteten Widget, uebernahm
`website_url`, `email` und `lead_source`, und sonst nichts.

**Was das kostet.** Wer ueber eine Anzeige mit `?utm_source=google` kommt und
das Formular ausfuellt, verliert seine Herkunft im Moment des Absendens. Die
Kanalauswertung aus L-84 kann eine bezahlte Anzeige darum nicht als Kanal
ausweisen — die Frage „welcher Kanal bringt Kunden" bleibt fuer genau die
Kanaele unbeantwortet, die Geld kosten.

**Warum begrenzt entgegengenommen.** Die Felder kommen von aussen, ohne
Anmeldung, aus einem Widget auf fremden Seiten. Sie werden gekuerzt und roh
gespeichert — nie ausgewertet, nie in HTML gesetzt.
"""
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def _ohne_ratengrenze(app):
    """**Die Ratengrenze zaehlt alle Leads der letzten Stunde.**

    Einzeln liefen diese Tests durch, im Gesamtlauf nicht: Bis sie an der
    Reihe sind, haben andere Tests das Stundenkontingent aufgebraucht, und
    `POST /api/leads/public` antwortet 429. Geprueft wird hier die Uebernahme
    der Herkunft, nicht die Grenze — die hat ihren eigenen Test
    (`test_ratenbegrenzung.py`).
    """
    from services.ratenbegrenzung import lead_grenzen

    app.dependency_overrides[lead_grenzen] = lambda: None
    yield
    app.dependency_overrides.pop(lead_grenzen, None)


@pytest.fixture(autouse=True)
def _aufraeumen(app):
    from database import SessionLocal

    def weg():
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM leads WHERE website_url LIKE '%l86-%'"))
            db.commit()
        finally:
            db.close()

    weg()
    yield
    weg()


def _anlegen(client, **felder):
    daten = {"website_url": "https://l86-betrieb.example",
             "email": "l86@example.com", **felder}
    antwort = client.post("/api/leads/public", json=daten)
    assert antwort.status_code in (200, 201), antwort.text[:200]
    return antwort.json()["id"]


def _lead(kennung):
    from database import Lead, SessionLocal

    db = SessionLocal()
    try:
        return db.query(Lead).filter(Lead.id == kennung).first()
    finally:
        db.close()


class TestHerkunft:
    def test_die_herkunft_aus_der_anzeige_wird_behalten(self, client):
        kennung = _anlegen(client, utm_source="google", utm_medium="cpc",
                           utm_campaign="waermepumpe-nord")

        lead = _lead(kennung)
        assert lead.utm_source == "google"
        assert lead.utm_medium == "cpc"
        assert lead.utm_campaign == "waermepumpe-nord"

    def test_ohne_angabe_bleibt_es_leer_und_wird_nicht_geraten(self, client):
        """Eine erfundene Herkunft waere schlimmer als eine fehlende — auf ihr
        wuerde die Kanalauswertung rechnen."""
        kennung = _anlegen(client)

        lead = _lead(kennung)
        assert not lead.utm_source

    def test_der_bestehende_weg_bleibt_unveraendert(self, client):
        """Der Aufruf ohne UTM ist der haeufigste und darf sich nicht aendern."""
        kennung = _anlegen(client, lead_source="embed_audit")

        assert _lead(kennung).lead_source == "embed_audit"


class TestGrenzen:
    def test_uebermaessig_lange_werte_werden_gekuerzt(self, client):
        """Die Felder kommen ohne Anmeldung aus einem Widget auf fremden
        Seiten. Die Spalte fasst 200 Zeichen; ein laengerer Wert soll die
        Anlage nicht scheitern lassen."""
        kennung = _anlegen(client, utm_source="x" * 500)

        lead = _lead(kennung)
        assert lead.utm_source is not None
        assert len(lead.utm_source) <= 200

    def test_was_keine_zeichenkette_ist_wird_nicht_uebernommen(self, client):
        """`data` ist ein rohes `dict` — es steht nichts dazwischen."""
        kennung = _anlegen(client, utm_source={"boese": True}, utm_medium=["x"])

        lead = _lead(kennung)
        assert not lead.utm_source
        assert not lead.utm_medium
