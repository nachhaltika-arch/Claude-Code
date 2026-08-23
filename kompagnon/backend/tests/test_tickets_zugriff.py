"""Alle Support-Tickets waren ohne Anmeldung lesbar (L-51 → L-90).

**Der Befund, 22.08.2026.** `GET /api/tickets/` fuehrte
`SELECT * FROM support_tickets … LIMIT 100` aus — **ohne jede
Anmeldepruefung**. Die Zeilen tragen Name, E-Mail-Adresse, Beschreibung,
Seiten-URL, Browser-Angaben und `screenshot_base64`. `GET /{ticket_id}` gab
dasselbe einzeln heraus, durchzaehlbar.

`PATCH /{ticket_id}` daneben traegt `require_innendienst` — jemand hat die
Datei gesehen und die **Leserouten uebersehen**. Genau die Bauart, die L-51
am 19.08. an elf Routern behoben hat.

**Warum die Zaehlung es nicht gefangen hat.** `test_zugriffsschutz_werkzeug.py`
prueft eine **von Hand gepflegte Liste** von Pfaden; `GET /api/tickets/` steht
dort nicht. Eine solche Liste waechst nicht mit dem Code mit — der Bestand
offener Routen stieg seit dem 19.08. von 42 auf 51, ohne dass etwas rot
wurde. Deshalb zaehlt `test_zugriffsschutz_bestand.py` jetzt beide Klassen
am **gesamten** Routenbaum.

**Was offen bleibt und warum.** `POST /api/tickets/` legt ein Ticket an und
wird aus dem `FeedbackButton` gerufen, der ueberall haengt. Ein Rueckmeldeweg,
der eine Anmeldung verlangt, verliert die Rueckmeldungen, auf die es
ankommt. `GET /my` deckt den Kundenfall ab und filtert auf die eigene
Adresse.
"""
import pytest


# `support_tickets` entsteht nur im Migrationsblock, nicht aus einem
# SQLAlchemy-Modell. Hier stand dafuer bis zum 23.08.2026 eine eigene
# Fixture mit der **wortgetreu abgeschriebenen** CREATE-Anweisung.
#
# Sie ist entfallen: Die Testdatenbank faehrt seither in `conftest.py`
# denselben Migrationsblock wie der Produktivstart. Die Kopie hier hat
# nichts kaputtgemacht — sie hat etwas **verdeckt**. Der naechste Test,
# der dieselbe Tabelle brauchte, fiel in der CI um, waehrend lokal alles
# gruen war, und die Ursache sah aus wie sein Fehler.


LESEN = [
    ("get", "/api/tickets/"),
    ("get", "/api/tickets/1"),
]


class TestOhneAnmeldungNichts:
    @pytest.mark.parametrize("methode,pfad", LESEN)
    def test_kein_zugriff_ohne_anmeldung(self, client, methode, pfad):
        """Die Zeilen tragen Namen, Adressen, Beschreibungen und
        Bildschirmfotos."""
        antwort = getattr(client, methode)(pfad)

        assert antwort.status_code in (401, 403), (
            f"{methode.upper()} {pfad} → {antwort.status_code}")

    @pytest.mark.parametrize("methode,pfad", LESEN)
    def test_und_auch_kein_kunde(self, client, kunde_headers, methode, pfad):
        """Ein Kunde sieht seine eigenen Tickets ueber `/my` — nicht die der
        anderen."""
        antwort = getattr(client, methode)(pfad, headers=kunde_headers)

        assert antwort.status_code == 403, (
            f"{methode.upper()} {pfad} → {antwort.status_code}")


class TestWasOffenBleibt:
    def test_ein_ticket_laesst_sich_ohne_anmeldung_anlegen(self, client):
        """Der `FeedbackButton` haengt ueberall. Ein Rueckmeldeweg, der eine
        Anmeldung verlangt, verliert die Rueckmeldungen, auf die es ankommt.
        """
        antwort = client.post("/api/tickets/", json={
            "type": "bug", "title": "L90 Probe",
            "description": "Testeintrag", "user_email": "l90@example.com",
        })

        assert antwort.status_code not in (401, 403), antwort.text[:200]

    def test_der_kunde_sieht_seine_eigenen(self, client, kunde_headers):
        antwort = client.get("/api/tickets/my", headers=kunde_headers)

        assert antwort.status_code == 200, antwort.text[:200]


class TestDerInnendienstArbeitetWeiter:
    def test_der_admin_sieht_die_liste(self, client, auth_headers):
        antwort = client.get("/api/tickets/", headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]
