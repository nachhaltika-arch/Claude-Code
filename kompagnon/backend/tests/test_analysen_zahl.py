"""Die Zahl im Werbetext kommt aus der Datenbank (L-65).

**Der Befund.** Das eingebettete Widget sagt „Über 340 Handwerksbetriebe
analysiert" — auf **fremden Seiten**. Die Zahl stand fest im Quelltext,
waehrend die Anzahl durchgefuehrter Analysen in `audit_results` liegt und
sich abfragen liesse. Sie kann zutreffen; nachsehen kann es niemand, und mit
jedem Tag altert sie.

**Warum abgerundet.** „Über 347 analysiert" liest sich wie ein Zaehlerstand
und wird bei der naechsten Analyse falsch. Auf Zehner abgerundet ist die
Aussage **immer wahr**: Es sind mindestens so viele. Eine Werbeaussage, die
weniger behauptet als geschehen ist, kann nicht irrefuehren.

**Warum oeffentlich.** Das Widget laeuft ohne Anmeldung auf Kundenseiten.
Herausgegeben wird **eine** aggregierte Zahl — kein Betrieb, keine Domain,
kein Ergebnis. Beim Widget-Pentest am 12.08. war genau das der Befund: Der
Teaser gab jede Analyse aus.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def analysen(app):
    """Zwoelf Analysen — genug, um das Abrunden zu sehen."""
    from database import AuditResult, SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM audit_results WHERE company_name LIKE 'L65 %'"))
        db.commit()
        db.add_all([
            AuditResult(website_url=f"https://l65-{i}.example",
                        company_name=f"L65 Betrieb {i}", status="completed")
            for i in range(12)
        ])
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM audit_results WHERE company_name LIKE 'L65 %'"))
        db.commit()
    finally:
        db.close()


class TestOeffentlich:
    def test_ohne_anmeldung_erreichbar(self, client, analysen):
        """Das Widget laeuft auf fremden Seiten und ist nirgends angemeldet."""
        antwort = client.get("/api/audit/analysen/anzahl")

        assert antwort.status_code == 200, antwort.text[:200]

    def test_gibt_nur_die_zahl_heraus(self, client, analysen):
        """Beim Pentest am 12.08. gab der Teaser jede Analyse aus. Hier gibt
        es genau eine Zahl — kein Betrieb, keine Domain, kein Ergebnis."""
        daten = client.get("/api/audit/analysen/anzahl").json()

        assert set(daten) <= {"analysen", "anzeige"}
        assert "example" not in str(daten)


class TestEhrlichkeit:
    def test_rundet_ab_und_nicht_auf(self, client, analysen):
        """Aufrunden hiesse mehr behaupten, als geschehen ist."""
        daten = client.get("/api/audit/analysen/anzahl").json()

        assert daten["anzeige"] <= daten["analysen"]
        assert daten["anzeige"] % 10 == 0

    def test_unter_zehn_wird_nichts_behauptet(self, client, monkeypatch):
        """`0` als Anzeige heisst fuer die Oberflaeche: Satz weglassen.
        „Über 0 analysiert" waere schlechter als kein Satz.

        Gezaehlt wird hier ueber den Zaehler, **nicht** ueber ein `DELETE`
        auf `audit_results`: Ein Test, der den Bestand leert, macht den
        naechsten unzuverlaessig — und solche Wechselwirkungen zeigen sich
        erst im Gesamtlauf.
        """
        from routers import audit

        monkeypatch.setattr(audit, "analysen_zaehlen", lambda db: 7)

        daten = client.get("/api/audit/analysen/anzahl").json()

        assert daten["anzeige"] == 0
        assert daten["analysen"] == 7

    def test_eine_fehlende_tabelle_liefert_null_statt_eines_fehlers(
            self, client, monkeypatch):
        """Das Widget haengt auf einer fremden Seite. Faellt die Zahl aus,
        faellt der Satz weg — nicht das Widget."""
        from routers import audit

        def kaputt(*a, **k):
            raise RuntimeError("keine Tabelle")

        monkeypatch.setattr(audit, "analysen_zaehlen", kaputt)

        antwort = client.get("/api/audit/analysen/anzahl")

        assert antwort.status_code == 200
        assert antwort.json()["anzeige"] == 0
