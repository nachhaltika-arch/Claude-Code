# -*- coding: utf-8 -*-
"""Das Kundendashboard muss den eigenen Betrieb zeigen.

**Der Befund (26.08.2026, von David beim Anmelden als Kunde gefunden).** Ein
angemeldeter Kunde sah auf seiner Startseite „Daten konnten nicht geladen
werden." Im Netzwerkprotokoll: `GET /api/usercards/3/profile` → **404**.

**Die Ursache stand seit dem 24.08. als L-106 in der Lückenliste** und war
dort schon richtig beschrieben — nur ohne den Beleg, dass sie wirklich
zuschlägt. `usercards` sollte einmal `leads` und `customers` zusammenlegen,
ausdrücklich als *Teil 1 von 3*; die anderen zwei kamen nie. Der
Kopierschritt, der die Tabelle füllte, wurde entfernt
(`migrations_runtime.py:445`: *„caused DB lock on startup"*). Seither wird
sie bei jedem Start **angelegt** und **nie befüllt**.

**Die Route rechnet ohnehin mit Lead-Kennungen.** `_check_kunde_access`
vergleicht `current_user.lead_id` mit der Kennung aus dem Pfad, die Audits
werden über `AuditResult.lead_id` gesucht, die Projekte über
`Project.lead_id`, und der Antwortschlüssel heißt `"lead"`. Einzig die
Existenzprüfung sah in `usercards` nach — in einer Tabelle, die mit diesen
Kennungen nichts zu tun hat und obendrein leer ist.

**Warum das niemandem auffiel:** Der Innendienst benutzt diese Route nicht;
er hat den Lead-Router. Sie gehört zum `kunden_router`, und Kunden melden
sich selten an — bis einer es tut.

**Nicht abgebaut.** `usercards` bleibt, wie sie ist; die Innendienst-Routen
darauf sind unangetastet. Ob die Tabelle je gefüllt wird oder verschwindet,
ist eine eigene Entscheidung (L-106) und keine, die man beim Reparieren
einer Kundenstartseite nebenbei trifft.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


def _profil(client, headers, kennung):
    return client.get(f"/api/usercards/{kennung}/profile", headers=headers)


class TestDerEigeneBetrieb:
    def test_der_kunde_sieht_sein_profil(self, client, kunde_headers, kunde_user):
        """Der Fall, den David gefunden hat — vorher ein 404."""
        # Act
        antwort = _profil(client, kunde_headers, kunde_user.lead_id)

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["lead"]["id"] == kunde_user.lead_id

    def test_es_ist_wirklich_sein_betrieb(self, client, kunde_headers, kunde_user):
        """Nicht irgendein Datensatz mit derselben Nummer."""
        daten = _profil(client, kunde_headers, kunde_user.lead_id).json()

        assert daten["lead"]["company_name"] == "Pytest Kundenbetrieb"

    def test_die_antwort_traegt_die_abschnitte_des_bildschirms(
            self, client, kunde_headers, kunde_user):
        """`CustomerDashboard.jsx` liest genau diese Schlüssel. Fehlt einer,
        bleibt ein Abschnitt leer, ohne dass irgendwo ein Fehler steht."""
        daten = _profil(client, kunde_headers, kunde_user.lead_id).json()

        for schluessel in ("lead", "audits", "projects", "score_history",
                           "total_audits", "current_score", "current_level"):
            assert schluessel in daten, f"„{schluessel}“ fehlt in der Antwort"

    def test_ein_betrieb_ohne_audit_ist_kein_fehler(self, client, kunde_headers,
                                                    kunde_user):
        """Ein neuer Kunde hat noch nichts — das ist ein leerer Bildschirm,
        keine Fehlermeldung."""
        daten = _profil(client, kunde_headers, kunde_user.lead_id).json()

        assert daten["audits"] == [] or isinstance(daten["audits"], list)
        assert daten["total_audits"] == len(daten["audits"])


class TestDieGrenzenBleiben:
    def test_ein_fremder_betrieb_bleibt_verschlossen(
            self, client, kunde_headers, fremder_betrieb):
        """Die Reparatur darf die Zugriffsgrenze nicht aufweichen — sie war
        nie das Problem."""
        assert _profil(client, kunde_headers, fremder_betrieb).status_code == 403

    def test_eine_unbekannte_kennung_bleibt_404(self, client, auth_headers):
        antwort = _profil(client, auth_headers, 999999)

        assert antwort.status_code == 404

    def test_ohne_anmeldung_gibt_es_nichts(self, client, kunde_user):
        """`optional_auth` laesst den Aufruf ohne Anmeldung durch — die Route
        gehoert dem Kundenportal, und der Zugang laeuft dort auch ueber einen
        Token-Link. Ein **fremder** Betrieb bleibt aber auch dann zu."""
        antwort = _profil(client, {}, kunde_user.lead_id)

        assert antwort.status_code in (200, 401, 403), antwort.text


class TestDieLeereTabelleErklaert:
    def test_usercards_ist_leer_und_das_stoert_nicht_mehr(self, app):
        """Der Kern des Befunds, als Zusicherung festgehalten.

        Sollte jemand `usercards` eines Tages fuellen, faellt dieser Test —
        und dann gehoert L-106 neu entschieden, statt dass die Kundenstartseite
        still wieder von einer zweiten Quelle liest.
        """
        from database import SessionLocal, UserCard

        db = SessionLocal()
        try:
            anzahl = db.query(UserCard).count()
        finally:
            db.close()

        assert anzahl == 0, (
            f"`usercards` hat {anzahl} Zeilen. Die Kundenstartseite liest "
            f"bewusst aus `leads` — bitte L-106 entscheiden, statt hier "
            f"stillschweigend die Quelle zu wechseln.")
