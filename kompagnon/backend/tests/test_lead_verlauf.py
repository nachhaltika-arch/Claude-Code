"""Was zuletzt geschah, ohne vorher zu klicken (L-82).

**Der Befund.** Aus dem HubSpot-Audit vom 19.08.2026: Dort ist die
Datensatzseite dreispaltig, und was zuletzt geschah steht **immer** da. Bei
uns liegt es hinter Reitern — E-Mails im einen, Audits im anderen, Nachrichten
im dritten. Wer beim Anruf erst klicken muss, um zu sehen, was zuletzt geschah,
sieht es nicht.

**Warum das mehr ist als eine Anzeigefrage.** Es gibt bei uns keinen Verlauf,
den man anzeigen koennte — die Ereignisse liegen in fuenf Tabellen, und keine
Stelle fuehrt sie zusammen. Genau daran ist am 17.08. schon einmal etwas
gescheitert: `email_logs` und `communications` kennen einander nicht, und
deshalb wurde zweimal der falsche Absender beschuldigt.

**Die Dublette gehoert zusammengefuehrt, nicht verdoppelt.** Dieselbe Mail
kann in beiden Protokollen stehen. Ein Verlauf, der sie zweimal zeigt, ist
irrefuehrend; einer, der ein Protokoll weglaesst, ist unvollstaendig. Also:
ein Ereignis, beide Quellen benannt.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import text


HEUTE = datetime(2026, 8, 22, 10, 0, 0)


def _aufraeumen(db):
    """Kinder vor Eltern — sonst haelt der Fremdschluessel von `projects`
    den Betrieb fest, und der naechste Lauf findet einen halben Bestand vor."""
    kennungen = "(SELECT id FROM leads WHERE company_name LIKE 'L82 %')"
    db.execute(text(f"DELETE FROM communications WHERE project_id IN "
                    f"(SELECT id FROM projects WHERE lead_id IN {kennungen})"))
    db.execute(text(f"DELETE FROM projects WHERE lead_id IN {kennungen}"))
    db.execute(text(f"DELETE FROM audit_results WHERE lead_id IN {kennungen}"))
    db.execute(text(f"DELETE FROM email_logs WHERE lead_id IN {kennungen}"))
    db.execute(text("DELETE FROM leads WHERE company_name LIKE 'L82 %'"))
    db.commit()


@pytest.fixture
def betrieb(app):
    """Ein Betrieb mit Ereignissen aus vier Quellen — darunter eine Dublette."""
    from database import Lead, AuditResult, Project, SessionLocal

    db = SessionLocal()
    try:
        # `email_logs` entsteht erst beim Start in `migrations_runtime.py` und
        # gehoert keinem Modell — im Test gibt es sie also nicht von selbst.
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS email_logs (
                id SERIAL PRIMARY KEY, lead_id INTEGER, project_id INTEGER,
                recipient VARCHAR, subject VARCHAR, body TEXT,
                sent_at TIMESTAMP DEFAULT NOW(), status VARCHAR DEFAULT 'sent')"""))
        _aufraeumen(db)

        lead = Lead(company_name="L82 Betrieb", website_url="https://l82.example",
                    created_at=HEUTE - timedelta(days=10))
        db.add(lead)
        db.commit()
        db.refresh(lead)

        db.add(AuditResult(lead_id=lead.id, website_url="https://l82.example",
                           company_name="L82 Betrieb", total_score=72,
                           created_at=HEUTE - timedelta(days=9)))
        projekt = Project(lead_id=lead.id, created_at=HEUTE - timedelta(days=5))
        db.add(projekt)
        db.commit()
        db.refresh(projekt)

        # Dieselbe Mail in beiden Protokollen — der Fall vom 17.08.
        db.execute(text(
            "INSERT INTO email_logs (lead_id, subject, sent_at, status) "
            "VALUES (:l, 'Ihr Angebot', :z, 'sent')"),
            {"l": lead.id, "z": HEUTE - timedelta(days=3)})
        from database import Communication
        db.add(Communication(project_id=projekt.id, type="email", direction="outbound",
                             subject="Ihr Angebot", sent_at=HEUTE - timedelta(days=3)))
        db.commit()

        kennung = lead.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        _aufraeumen(db)
    finally:
        db.close()


def _verlauf(client, headers, kennung, **params):
    antwort = client.get(f"/api/leads/{kennung}/verlauf", headers=headers, params=params)
    assert antwort.status_code == 200, antwort.text[:300]
    return antwort.json()


class TestZugriff:
    def test_der_kunde_sieht_den_verlauf_eines_fremden_betriebs_nicht(
            self, client, kunde_headers, betrieb):
        antwort = client.get(f"/api/leads/{betrieb}/verlauf", headers=kunde_headers)

        assert antwort.status_code == 403

    def test_ohne_anmeldung_gar_nicht(self, client, betrieb):
        assert client.get(f"/api/leads/{betrieb}/verlauf").status_code in (401, 403)

    def test_ein_unbekannter_betrieb_ist_kein_leerer_verlauf(
            self, client, auth_headers):
        """Sonst sieht ein Tippfehler in der Kennung aus wie ein Betrieb,
        bei dem noch nichts geschehen ist."""
        antwort = client.get("/api/leads/99999999/verlauf", headers=auth_headers)

        assert antwort.status_code == 404


class TestZusammenfuehrung:
    def test_traegt_ereignisse_aus_mehreren_quellen(self, client, auth_headers, betrieb):
        daten = _verlauf(client, auth_headers, betrieb)

        arten = {e["art"] for e in daten["ereignisse"]}
        assert {"angelegt", "audit", "projekt", "email"} <= arten, arten

    def test_neuestes_zuerst(self, client, auth_headers, betrieb):
        """Beim Anruf zaehlt das Letzte, nicht das Erste."""
        daten = _verlauf(client, auth_headers, betrieb)

        zeiten = [e["zeitpunkt"] for e in daten["ereignisse"]]
        assert zeiten == sorted(zeiten, reverse=True)

    def test_das_anlegen_steht_immer_ganz_unten(self, client, auth_headers, betrieb):
        """Der Anker: Ab hier gibt es den Betrieb ueberhaupt."""
        daten = _verlauf(client, auth_headers, betrieb)

        assert daten["ereignisse"][-1]["art"] == "angelegt"

    def test_dieselbe_mail_aus_zwei_protokollen_ist_ein_ereignis(
            self, client, auth_headers, betrieb):
        """Der Fall vom 17.08.: `email_logs` und `communications` kennen
        einander nicht. Zweimal dieselbe Mail im Verlauf laedt dazu ein,
        zweimal denselben Schluss zu ziehen."""
        daten = _verlauf(client, auth_headers, betrieb)

        mails = [e for e in daten["ereignisse"] if e["art"] == "email"]
        assert len(mails) == 1, mails

    def test_und_nennt_beide_protokolle(self, client, auth_headers, betrieb):
        """Wer der Zahl nachgeht, muss wissen, wo er nachsehen kann."""
        daten = _verlauf(client, auth_headers, betrieb)

        mail = next(e for e in daten["ereignisse"] if e["art"] == "email")
        assert set(mail["quellen"]) == {"email_logs", "communications"}


class TestGrenzen:
    def test_die_laenge_ist_begrenzt(self, client, auth_headers, betrieb):
        daten = _verlauf(client, auth_headers, betrieb, limit=2)

        assert len(daten["ereignisse"]) == 2

    def test_eine_fehlende_tabelle_kippt_den_verlauf_nicht(
            self, client, auth_headers, betrieb, monkeypatch):
        """Auf einer frischen Datenbank fehlt `email_logs` — genau daran ist
        die CI am 22.08. schon einmal rot geworden."""
        from services import lead_verlauf

        monkeypatch.setattr(lead_verlauf, "tabelle_vorhanden",
                            lambda db, name: name != "email_logs")

        daten = _verlauf(client, auth_headers, betrieb)

        assert any(e["art"] == "audit" for e in daten["ereignisse"])
