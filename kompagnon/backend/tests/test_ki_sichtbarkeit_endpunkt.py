"""Die KI-Sichtbarkeit muss erreichbar sein — sonst ist sie ungeprueft (L-68).

Zwei Endpunkte, und der erste ist der wichtigere fuer den Anfang: Er sagt,
**welche Systeme ueberhaupt angebunden sind**. Ohne ihn merkt niemand, dass ein
Schluessel in Render fehlt oder leer angelegt wurde — der Lauf meldet dann
brav „nicht erhoben", und das liest sich wie ein Ergebnis.
"""
import pytest
from sqlalchemy import text


SPALTEN_NACHZIEHEN = (
    "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit JSONB",
    "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_am TIMESTAMP",
)


@pytest.fixture(autouse=True)
def _spalten(app):
    """Die Spalten kommen beim Start aus `_run_migrations` — den laesst die
    Testeinrichtung bewusst aus."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        for sql in SPALTEN_NACHZIEHEN:
            db.execute(text(sql))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def projekt(app):
    from database import SessionLocal, Lead, Project

    db = SessionLocal()
    try:
        lead = Lead(company_name="Mustermann Heizung GmbH", trade="Heizung",
                    city="Kassel", website_url="https://mustermann-heizung.de")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        p = Project(lead_id=lead.id, company_name="Mustermann Heizung GmbH")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.id
    finally:
        db.close()


# ── Wer ist angebunden ───────────────────────────────────────────────

class TestAnbieterStand:
    def test_nennt_jedes_system_mit_seinem_schluesselnamen(self, client, auth_headers):
        antwort = client.get("/api/geo/ki-anbieter", headers=auth_headers)

        assert antwort.status_code == 200
        stand = {a["schluessel"]: a for a in antwort.json()["anbieter"]}
        # 25.08.2026: Google AI kam als viertes System dazu. Die Oberflaeche
        # muss **jedes** nennen — auch das nicht angebundene, sonst sieht ein
        # fehlender Schluessel aus wie ein System, das den Betrieb nicht kennt.
        assert set(stand) == {"chatgpt", "perplexity", "claude", "gemini"}
        assert stand["chatgpt"]["env_name"] == "OPENAI_API_KEY"
        assert stand["gemini"]["env_name"] == "GEMINI_API_KEY"
        assert "konfiguriert" in stand["claude"]

    def test_verraet_keine_schluesselwerte(self, client, auth_headers, monkeypatch):
        """`/info` hat am 15.08.2026 schon einmal Zugangsdaten preisgegeben."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-streng-geheim-123")

        roh = client.get("/api/geo/ki-anbieter", headers=auth_headers).text

        assert "sk-streng-geheim-123" not in roh

    def test_der_kunde_kommt_nicht_heran(self, client, kunde_headers):
        """Der Stand verraet die Betriebsausstattung — das ist Innendienst."""
        antwort = client.get("/api/geo/ki-anbieter", headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ohne_anmeldung_gar_nicht(self, client):
        assert client.get("/api/geo/ki-anbieter").status_code in (401, 403)


# ── Der Lauf ─────────────────────────────────────────────────────────

class TestLaufEndpunkt:
    def test_ohne_jeden_zugang_kommt_kein_falsches_ergebnis(
            self, client, auth_headers, projekt, monkeypatch):
        """Nicht 200 mit lauter Nullen — das waere eine Aussage ueber Systeme,
        die nie gefragt wurden."""
        from services import ki_anbieter

        for a in ki_anbieter.ANBIETER:
            monkeypatch.delenv(a.env_name, raising=False)

        antwort = client.post(f"/api/geo/{projekt}/ki-sichtbarkeit",
                              headers=auth_headers)

        assert antwort.status_code == 503
        assert "OPENAI_API_KEY" in antwort.text

    def test_ein_unbekanntes_projekt_ist_404(self, client, auth_headers, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        antwort = client.post("/api/geo/999999/ki-sichtbarkeit", headers=auth_headers)

        assert antwort.status_code == 404

    def test_der_kunde_darf_keinen_lauf_ausloesen(self, client, kunde_headers, projekt):
        """Jeder Lauf kostet Geld — das loest kein Kunde aus."""
        antwort = client.post(f"/api/geo/{projekt}/ki-sichtbarkeit",
                              headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ohne_ort_wird_nicht_geraten(self, client, auth_headers, app, monkeypatch):
        """Eine Frage nach einem erfundenen Ort misst den falschen Markt."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        from database import SessionLocal, Lead, Project

        db = SessionLocal()
        try:
            lead = Lead(company_name="Ohne Ort GmbH", trade="Heizung", city="")
            db.add(lead)
            db.commit()
            db.refresh(lead)
            p = Project(lead_id=lead.id, company_name="Ohne Ort GmbH")
            db.add(p)
            db.commit()
            db.refresh(p)
            projekt_id = p.id
        finally:
            db.close()

        antwort = client.post(f"/api/geo/{projekt_id}/ki-sichtbarkeit",
                              headers=auth_headers)

        assert antwort.status_code == 400
        assert "Ort" in antwort.text


# ── Der Verlauf (L-85) ───────────────────────────────────────────────

def test_der_verlauf_ist_lesbar_ohne_zu_messen(client, auth_headers, projekt):
    """Getrennt vom Lauf-Endpunkt, weil Lesen nichts kostet und Messen Geld.

    Ohne je gelaufen zu sein, ist der Verlauf leer — und **nicht** ein
    Fehler: „nie gemessen" ist eine gueltige Auskunft.
    """
    antwort = client.get(f"/api/geo/{projekt}/ki-sichtbarkeit/verlauf",
                         headers=auth_headers)

    assert antwort.status_code == 200
    assert antwort.json() == {"verlauf": [], "zuletzt": None}


def test_der_kunde_sieht_den_verlauf_nicht(client, kunde_headers, projekt):
    antwort = client.get(f"/api/geo/{projekt}/ki-sichtbarkeit/verlauf",
                         headers=kunde_headers)

    assert antwort.status_code == 403


def test_zwei_laeufe_stehen_nacheinander_im_verlauf(client, auth_headers, projekt, app):
    """Der eigentliche Befund von L-85, am Gegenstand geprueft: Der zweite
    Lauf **ersetzt** den ersten nicht."""
    from sqlalchemy import text
    from database import GeoAnalysis, SessionLocal
    from services.ki_sichtbarkeit import verlauf_fortschreiben

    befund = {"collected": True, "anbieter": {
        "chatgpt": {"collected": True, "genannt_bei": 1, "von": 3, "quote": 0.33}}}

    db = SessionLocal()
    try:
        db.execute(text(
            "ALTER TABLE geo_analyses ADD COLUMN IF NOT EXISTS ki_sichtbarkeit_verlauf JSONB"))
        db.commit()
        analyse = GeoAnalysis(project_id=projekt, status="pending")
        analyse.ki_sichtbarkeit_verlauf = verlauf_fortschreiben(
            verlauf_fortschreiben(None, befund, "2026-06-01T10:00:00"),
            befund, "2026-08-22T15:00:00")
        db.add(analyse)
        db.commit()
    finally:
        db.close()

    daten = client.get(f"/api/geo/{projekt}/ki-sichtbarkeit/verlauf",
                       headers=auth_headers).json()

    assert [e["am"] for e in daten["verlauf"]] == ["2026-06-01T10:00:00",
                                                   "2026-08-22T15:00:00"]
