"""Offener Mailversand, fremde Projektbilder, fremde Zustellprotokolle (L-67).

**Vierter Durchgang, 22.08.2026 — und der erste Fund ist der schwerste des
Tages.**

`POST /api/messages/send-email` nimmt `to`, `subject` und `html` entgegen und
**versendet**. Geprueft wurde nur, dass irgendwer angemeldet ist. Ein Kunde
konnte damit eine beliebige Mail an eine beliebige Adresse ueber die
Absenderinfrastruktur von KOMPAGNON schicken — der Eintrag im
Nachrichtenprotokoll traegt dabei `sender_role="admin"`. Das ist kein
Datenleck, sondern ein offenes Versandtor: Der Schaden faellt auf den Ruf der
Absenderdomain zurueck, und zwar dauerhaft.

Die Oberflaeche half nicht: Die Newsletter-Routen tragen `<PrivateRoute>`
**ohne** `roles` — auch dort kam jeder Angemeldete durch.

Dazu zwei weitere Bestaende:

* `GET /api/messages/{lead_id}` — die gesamte Korrespondenz mit einem
  fremden Betrieb lesen.
* `GET|POST /api/assets/project/{id}` — Bilder eines fremden Projekts sehen
  und hochladen.
* `GET /api/mail-events/lead/{lead_id}` — Zustellungsstoerungen eines fremden
  Betriebs samt Empfaengeradresse, Grund und Betreff.

**Warum hier je Route und nicht am Router.** `messages` fuehrt zwei
Kundenwege — `GET|POST /{lead_id}/kunde` — die **ohne Anmeldung** arbeiten
und den `customer_token` selbst pruefen. Eine Router-Sperre haette das
Kundenportal ausgesperrt. Bei `assets` und `mail_events` gibt es solche Wege
nicht; dort haengt die Sperre wie ueblich am Router.
"""
import pytest


GESPERRT = [
    ("post", "/api/messages/send-email",
     {"to": "fremd@example.com", "subject": "x", "html": "<p>x</p>"}),
    ("get",  "/api/messages/1", None),
    ("get",  "/api/assets/project/1", None),
    ("get",  "/api/mail-events/lead/1", None),
    # Kundennamen, Kunden-E-Mails, Umsaetze und Provisionen — ungefiltert.
    # Dieselbe Bauart wie `GET /api/invoices` aus PR #45.
    ("get",  "/api/affiliate-conversions", None),
]


def _ruf(client, methode, pfad, rumpf, headers=None):
    zusatz = {"json": rumpf} if rumpf is not None else {}
    if headers:
        zusatz["headers"] = headers
    return getattr(client, methode)(pfad, **zusatz)


class TestDerKundeKommtNichtHeran:
    @pytest.mark.parametrize("methode,pfad,rumpf", GESPERRT)
    def test_kein_kunde(self, client, kunde_headers, methode, pfad, rumpf):
        antwort = _ruf(client, methode, pfad, rumpf, kunde_headers)

        assert antwort.status_code == 403, (
            f"{methode.upper()} {pfad} → {antwort.status_code}")

    @pytest.mark.parametrize("methode,pfad,rumpf", GESPERRT)
    def test_ohne_anmeldung_erst_recht_nicht(self, client, methode, pfad, rumpf):
        antwort = _ruf(client, methode, pfad, rumpf)

        assert antwort.status_code in (401, 403)


class TestDasVersandtorIstZu:
    def test_der_kunde_versendet_keine_mail_ueber_uns(self, client, kunde_headers):
        """Der schwerste Fall: Es geht nicht um Einsicht, sondern um Versand
        unter fremdem Namen. Der Schaden faellt auf die Absenderdomain."""
        antwort = client.post("/api/messages/send-email",
                              json={"to": "irgendwer@example.com",
                                    "subject": "Guenstige Angebote",
                                    "html": "<p>…</p>"},
                              headers=kunde_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_und_bekommt_auch_kein_erfolg_zurueck(self, client, kunde_headers):
        """Die Route faengt intern jede Ausnahme und antwortet
        `{"success": false}` statt zu scheitern — eine Sperre, die als
        Fehlermeldung im Rumpf ankommt, waere keine."""
        antwort = client.post("/api/messages/send-email",
                              json={"to": "x@example.com", "subject": "x", "html": "x"},
                              headers=kunde_headers)

        assert "success" not in antwort.text or antwort.status_code == 403


class TestWasBewusstOffenBleibt:
    def test_der_versandstand_bleibt_fuer_alle_lesbar(self, client, kunde_headers):
        """**Eine Entscheidung, keine Luecke.** `GET /api/versand/status` gibt
        ein einzelnes Ja/Nein zurueck — ob der automatische Versand gerade
        erlaubt ist —, kein Kundendatum. Der `VersandProvider` umschliesst die
        **ganze** Oberflaeche, auch die Kundenseiten; eine Sperre haette dort
        bei jedem Laden einen 403 erzeugt. Das Schreiben ist admin-gesperrt.
        """
        antwort = client.get("/api/versand/status", headers=kunde_headers)

        assert antwort.status_code != 403, antwort.text[:200]


class TestDerKundenwegBleibtOffen:
    def test_der_token_weg_der_nachrichten_bleibt_ohne_anmeldung_erreichbar(self, client):
        """`GET /{lead_id}/kunde` prueft den `customer_token` selbst und
        arbeitet **ohne** Anmeldung — das Kundenportal haengt daran. Eine
        Router-Sperre haette es ausgesperrt."""
        antwort = client.get("/api/messages/1/kunde", params={"token": "falsch"})

        # 403 wegen falschem Token ist richtig; 401 hiesse, die Route
        # verlangt jetzt eine Anmeldung, und das waere der Fehler.
        assert antwort.status_code != 401, antwort.text[:200]


class TestDerInnendienstArbeitetWeiter:
    def test_der_admin_liest_die_nachrichten_eines_betriebs(self, client, auth_headers):
        antwort = client.get("/api/messages/1", headers=auth_headers)

        assert antwort.status_code != 403, antwort.text[:200]
