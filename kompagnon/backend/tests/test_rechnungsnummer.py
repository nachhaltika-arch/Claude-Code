# -*- coding: utf-8 -*-
"""Ein lückenloser, fortlaufender Nummernkreis (L-100, ORDERS_07).

**Format `KAS-YY-0000`, ein gemeinsamer Kreis** — Entscheidung David,
29.08.2026. Projekte und Shop ziehen aus derselben Quelle; zwei Systeme, die
unabhängig Nummern vergeben, erzeugen entweder Doppelungen oder Lücken.

**Der Mangel, den das behebt, ist älter als der Shop.** `routers/retainer.py`
vergab die Nummer als **`COUNT(*) + 1`** über die Tabelle `invoices`. Das ist
schlechter als das `MAX(...)+1`, vor dem ORDERS_07 warnt:

* Wird eine Rechnung gelöscht, sinkt die Zahl — die nächste Vergabe
  wiederholt eine bereits vergebene Nummer.
* Zwei gleichzeitige Aufrufe zählen dieselbe Menge und bekommen dieselbe
  Nummer.

`invoice_number` trägt eine UNIQUE-Bedingung, es gäbe also einen Serverfehler
statt einer stillen Doppelvergabe. Aber die GoBD verlangen lückenlos **und**
fortlaufend, und COUNT-basiert ist keines von beidem.

**Die Umstellung darf keine Nummer wiederholen.** Der Zähler wird beim ersten
Gebrauch eines Jahres aus dem Bestand aufgesetzt — auch aus dem alten Format
`KAS-2026-0001` mit vierstelligem Jahr. Ein Formatwechsel ist erklärbar; eine
zweite Rechnung mit derselben Nummer nicht.
"""
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def _leer(app):
    """Jede Prüfung startet mit leerem Kreis und leerer Rechnungstabelle."""
    from database import SessionLocal

    def raeumen():
        db = SessionLocal()
        try:
            db.execute(text("DELETE FROM invoice_counters"))
            db.execute(text("DELETE FROM invoices WHERE invoice_number LIKE 'KAS-%'"))
            db.commit()
        finally:
            db.close()

    raeumen()
    yield
    raeumen()


def _naechste(jahr=2026):
    from database import SessionLocal
    from services import rechnungsnummer

    db = SessionLocal()
    try:
        nummer = rechnungsnummer.naechste(db, jahr=jahr)
        db.commit()
        return nummer
    finally:
        db.close()


class TestFormat:
    def test_das_format_ist_kas_jj_vierstellig(self):
        # Act
        nummer = _naechste()

        # Assert
        assert nummer == "KAS-26-0001"

    def test_ein_anderes_jahr_hat_einen_eigenen_kreis(self):
        # Arrange
        _naechste(jahr=2026)

        # Act
        nummer = _naechste(jahr=2027)

        # Assert — jedes Jahr beginnt bei eins, das ist der uebliche Kreis.
        assert nummer == "KAS-27-0001"

    def test_die_vierte_stelle_waechst_mit(self):
        # Arrange
        from database import SessionLocal
        from services import rechnungsnummer

        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO invoice_counters (prefix, year, last_number) "
                "VALUES ('KAS', 2026, 9999) "
                "ON CONFLICT (prefix, year) DO UPDATE SET last_number = 9999"))
            db.commit()

            # Act
            nummer = rechnungsnummer.naechste(db, jahr=2026)
            db.commit()
        finally:
            db.close()

        # Assert — nicht abgeschnitten, sondern laenger.
        assert nummer == "KAS-26-10000"


class TestFortlaufend:
    def test_zwei_vergaben_geben_zwei_nummern(self):
        # Act
        erste, zweite = _naechste(), _naechste()

        # Assert
        assert (erste, zweite) == ("KAS-26-0001", "KAS-26-0002")

    def test_eine_geloeschte_rechnung_laesst_die_nummer_nicht_wiederkehren(self):
        """Der eigentliche Befund gegen `COUNT(*) + 1`."""
        # Arrange
        from database import SessionLocal

        erste = _naechste()
        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO invoices (invoice_number, amount_net) "
                "VALUES (:n, 100)"), {"n": erste})
            db.commit()
            db.execute(text("DELETE FROM invoices WHERE invoice_number = :n"),
                       {"n": erste})
            db.commit()
        finally:
            db.close()

        # Act
        zweite = _naechste()

        # Assert
        assert zweite != erste
        assert zweite == "KAS-26-0002"


class TestUmstellung:
    def test_der_zaehler_setzt_auf_dem_alten_format_auf(self):
        """`KAS-2026-0007` im Bestand heisst: die naechste ist die achte.

        Ohne dieses Aufsetzen begaenne der neue Kreis bei eins und vergaebe
        eine Nummer, die es schon gibt.
        """
        # Arrange
        from database import SessionLocal

        db = SessionLocal()
        try:
            for n in ("KAS-2026-0005", "KAS-2026-0007"):
                db.execute(text(
                    "INSERT INTO invoices (invoice_number, amount_net) "
                    "VALUES (:n, 100)"), {"n": n})
            db.commit()
        finally:
            db.close()

        # Act
        nummer = _naechste()

        # Assert
        assert nummer == "KAS-26-0008"

    def test_ein_fremdes_jahr_im_bestand_zaehlt_nicht_mit(self):
        # Arrange
        from database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO invoices (invoice_number, amount_net) "
                "VALUES ('KAS-2025-0042', 100)"))
            db.commit()
        finally:
            db.close()

        # Act
        nummer = _naechste(jahr=2026)

        # Assert
        assert nummer == "KAS-26-0001"

    def test_aufgesetzt_wird_nur_einmal_und_nicht_bei_jeder_vergabe(self):
        """Sonst zoege eine spaeter geloeschte Altrechnung den Zaehler zurueck."""
        # Arrange
        from database import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text(
                "INSERT INTO invoices (invoice_number, amount_net) "
                "VALUES ('KAS-2026-0005', 100)"))
            db.commit()
        finally:
            db.close()
        assert _naechste() == "KAS-26-0006"

        db = SessionLocal()
        try:
            db.execute(text(
                "DELETE FROM invoices WHERE invoice_number = 'KAS-2026-0005'"))
            db.commit()
        finally:
            db.close()

        # Act
        nummer = _naechste()

        # Assert
        assert nummer == "KAS-26-0007"


class TestGleichzeitig:
    def test_zehn_gleichzeitige_vergaben_geben_zehn_verschiedene_nummern(self):
        """Am Gegenstand gemessen, nicht am Sperrbefehl im Quelltext.

        `COUNT(*) + 1` und `MAX(...) + 1` bestehen diese Pruefung beide nicht:
        Zwei Aufrufe lesen denselben Stand, bevor einer schreibt.
        """
        # Arrange
        import threading

        from database import SessionLocal
        from services import rechnungsnummer

        ergebnisse = []
        sperre = threading.Lock()

        def hole():
            db = SessionLocal()
            try:
                nummer = rechnungsnummer.naechste(db, jahr=2026)
                db.commit()
                with sperre:
                    ergebnisse.append(nummer)
            except Exception as fehler:                  # noqa: BLE001
                with sperre:
                    ergebnisse.append(f"FEHLER: {fehler}")
            finally:
                db.close()

        faeden = [threading.Thread(target=hole) for _ in range(10)]

        # Act
        for f in faeden:
            f.start()
        for f in faeden:
            f.join()

        # Assert
        assert len(ergebnisse) == 10
        assert all(not str(e).startswith("FEHLER") for e in ergebnisse), ergebnisse
        assert len(set(ergebnisse)) == 10, f"Doppelte Nummer: {ergebnisse}"
        assert sorted(ergebnisse) == [f"KAS-26-{i:04d}" for i in range(1, 11)]


class TestAltbestand:
    """Der Projektpfad zieht aus demselben Kreis — sonst waeren es zwei."""

    def test_retainer_vergibt_aus_dem_gemeinsamen_kreis(self):
        # Arrange
        from database import SessionLocal
        from routers.retainer import _next_invoice_number

        db = SessionLocal()
        try:
            # Act
            erste = _next_invoice_number(db)
            db.commit()
            zweite = _next_invoice_number(db)
            db.commit()
        finally:
            db.close()

        # Assert — neues Format, fortlaufend, aus einer Quelle.
        jahr = __import__("datetime").date.today().year % 100
        assert erste == f"KAS-{jahr:02d}-0001"
        assert zweite == f"KAS-{jahr:02d}-0002"

    def test_shop_und_projekt_teilen_sich_die_nummern(self):
        """Der Kern der Entscheidung „ein gemeinsamer Kreis": Zwei Quellen
        erzeugen Doppelungen oder Luecken, eine nicht."""
        # Arrange
        from database import SessionLocal
        from routers.retainer import _next_invoice_number
        from services import rechnungsnummer

        jahr = __import__("datetime").date.today().year

        db = SessionLocal()
        try:
            # Act — abwechselnd aus beiden Wegen
            a = _next_invoice_number(db)
            db.commit()
            b = rechnungsnummer.naechste(db, jahr=jahr)
            db.commit()
            c = _next_invoice_number(db)
            db.commit()
        finally:
            db.close()

        # Assert
        assert len({a, b, c}) == 3
        assert [a, b, c] == [f"KAS-{jahr % 100:02d}-{i:04d}" for i in (1, 2, 3)]
