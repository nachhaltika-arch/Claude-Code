# -*- coding: utf-8 -*-
"""Zwei Tickets im selben Monat durften dieselbe Nummer bekommen.

**Gefunden am 08.09.2026 durch einen roten Lauf auf `main`** — derselbe Job
war auf der PR gruen. Die Meldung:

    duplicate key value violates unique constraint
    "support_tickets_ticket_number_key"
    DETAIL: Key (ticket_number)=(TKT-2609-2503) already exists.

**Das ist kein Testproblem.** `TKT-{Monat}-{4 Ziffern}` hat je Monat
**10.000** moegliche Nummern und keine Wiederholung bei Kollision. Nach dem
Geburtstagsparadoxon liegt die Wahrscheinlichkeit fuer mindestens eine
Doppelung bei 100 Tickets im Monat schon bei rund **39 Prozent**, bei 118
bei ueber der Haelfte. Was dann passiert, ist eine unbehandelte
`IntegrityError` — also ein **500 fuer den Kunden**, der gerade eine
Stoerung melden wollte.

Die Testreihe hat es zufaellig fruehzeitig getroffen: Sie legt in einem Lauf
gut zwei Dutzend Tickets an, und irgendwann faellt derselbe Vierstellige
zweimal. Ein Wuerfel, der selten daneben liegt, liegt trotzdem daneben.

**Zwei Dinge zusammen, nicht eines:** Die Nummer wird breiter (sechs
Ziffern), und bei einer Kollision wird eine neue gezogen. Die Breite macht
Kollisionen selten, die Wiederholung macht sie folgenlos. Nur das eine waere
Verlassen auf Glueck.
"""
import pytest
from sqlalchemy import text

from routers import tickets


class TestNummernform:

    def test_die_nummer_hat_die_erwartete_form(self):
        nr = tickets._gen_ticket_nr()
        assert nr.startswith("TKT-")
        monat, ziffern = nr[4:].split("-")
        assert len(monat) == 4 and monat.isdigit()
        assert len(ziffern) == 6 and ziffern.isdigit()

    def test_zwei_nummern_sind_praktisch_nie_gleich(self):
        """Eine Schranke, die den Nummernraum misst — nicht das Glueck.

        **Korrigiert am 17.09.2026.** Hier stand `== 200` mit dem Kommentar,
        eine Doppelung waere "schon auffaellig". Das stimmt nicht: Bei 200
        Ziehungen aus einer Million ist die erwartete Zahl der Doppelungen
        0,0199, und mindestens eine tritt mit **1,97 %** auf — nachgerechnet
        und an 2000 Wiederholungen gemessen (35 rot, 1,75 %). Der Test fiel
        also in etwa jedem 51. Lauf um und blockierte dabei den Deploy, weil
        er an allen Pruefjobs haengt. Am 17.09. traf es den Lauf 35231667026.

        Ein Test, der ohne Fehler im Gegenstand rot wird, ist schlimmer als
        keiner: Er kostet jedes Mal die Suche nach einer Ursache, die es
        nicht gibt, und gewoehnt daran, rote Laeufe zu wiederholen statt sie
        zu lesen.

        **Zwei Doppelungen sind erlaubt, drei nicht.** Das ist weiterhin eine
        echte Schranke — sie schlaegt an, sobald der Zufallsanteil kleiner
        wird (fuenf Stellen statt sechs: 18 % statt 0,0001 %) — und flattert
        rechnerisch in einem von 773.000 Laeufen.

        Dass eine Kollision im Betrieb **aufgeloest** wird, ist die eigentliche
        Zusicherung und steht unten in `TestKollisionWirdAufgeloest`.
        """
        ZIEHUNGEN, ERLAUBTE_DOPPELUNGEN = 200, 2

        nummern = {tickets._gen_ticket_nr() for _ in range(ZIEHUNGEN)}
        doppelt = ZIEHUNGEN - len(nummern)
        assert doppelt <= ERLAUBTE_DOPPELUNGEN, (
            f"{doppelt} Doppelungen bei {ZIEHUNGEN} Ziehungen — erwartet sind "
            f"0,02. Hat der Zufallsanteil an Stellen verloren?")


class TestKollisionWirdAufgeloest:

    def test_eine_belegte_nummer_fuehrt_nicht_zum_fehler(self, client, monkeypatch):
        """Die eigentliche Zusicherung.

        Die erste Ziehung liefert absichtlich eine Nummer, die schon
        vergeben ist. Frueher endete das mit 500; jetzt wird eine neue
        gezogen und das Ticket entsteht.
        """
        from database import SessionLocal

        belegt = "TKT-9999-000001"
        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO support_tickets (ticket_number, type, priority, "
                "status, title, description) VALUES (:nr, 'feedback', "
                "'medium', 'open', 'Platzhalter', 'belegt die Nummer')"
            ), {"nr": belegt})
            db.commit()
        finally:
            db.close()

        gezogen = [belegt, "TKT-9999-000002"]
        monkeypatch.setattr(tickets, "_gen_ticket_nr",
                            lambda: gezogen.pop(0) if gezogen else "TKT-9999-000003")

        antwort = client.post("/api/tickets/", json={
            "title": "Knopf reagiert nicht",
            "description": "Beim Speichern passiert nichts.",
        })

        assert antwort.status_code in (200, 201), antwort.text
        assert gezogen == [], "die zweite Nummer wurde nicht gezogen"

        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM support_tickets WHERE ticket_number "
                            "IN (:a, :b)"), {"a": belegt, "b": "TKT-9999-000002"})
            db.commit()
        finally:
            db.close()

    def test_endlos_wird_nicht_versucht(self, client, monkeypatch):
        """Die Gegenprobe: Die Wiederholung ist begrenzt.

        Zoege sie unbegrenzt, wuerde aus einem kaputten Nummernkreis eine
        haengende Anfrage — schlimmer als ein ehrlicher Fehler.
        """
        from database import SessionLocal

        belegt = "TKT-9999-000009"
        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO support_tickets (ticket_number, type, priority, "
                "status, title, description) VALUES (:nr, 'feedback', "
                "'medium', 'open', 'Platzhalter', 'belegt die Nummer')"
            ), {"nr": belegt})
            db.commit()
        finally:
            db.close()

        versuche = []

        def _immer_dieselbe():
            versuche.append(1)
            return belegt

        monkeypatch.setattr(tickets, "_gen_ticket_nr", _immer_dieselbe)

        antwort = client.post("/api/tickets/", json={
            "title": "Immer dieselbe Nummer",
            "description": "Sollte aufgeben, nicht haengen.",
        })

        assert antwort.status_code >= 400
        assert 1 <= len(versuche) <= tickets.NUMMER_VERSUCHE

        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM support_tickets WHERE ticket_number = :n"),
                       {"n": belegt})
            db.commit()
        finally:
            db.close()
