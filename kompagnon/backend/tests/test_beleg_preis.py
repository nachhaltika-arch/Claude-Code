"""Die Auftragsbestaetigung nannte den Preis aus einer festen Liste (L-29).

**Der Befund, gefunden am 22.08.2026 beim Nachzaehlen.** L-29 galt als
erledigt: `PACKAGE_NAMES` weg, `projekt_festpreis` an der Produktzeile, ein
Waechter ueber dem Frontend-Baum. Der Waechter prueft aber nur die
**Schreibweise** „1.500 €" in `.jsx` — rohe Zahlen im Backend sieht er nicht.
Ueber alle Python-Dateien gezaehlt stand in
`services/auftragsbestaetigung_pdf.py` eine **dritte** feste Preisliste.

**Warum diese die schlimmste war.** Sie steht im Dokument, das der Kunde als
Beleg bekommt. Der tatsaechlich gezahlte Betrag wurde als `amount_eur`
uebergeben — und **nirgends benutzt**; jede Zahl im PDF kam aus der Liste.
Zwei Folgen:

* Ein Preis, der in `products` geaendert wird, steht im Beleg weiter alt da.
* Ein unbekanntes Paket bekam `PAKETE["kompagnon"]` — **falscher Paketname,
  2.000 EUR, falsch ausgewiesene Umsatzsteuer**, egal was gezahlt wurde.

Dieselbe Bauart wie der `.get(package_id, 2000.0)` aus L-29, nur in einem
Dokument mit Belegcharakter.

**Die Reihenfolge ist dieselbe wie bei `projekt_festpreis`:** Produktzeile,
sonst der gezahlte Betrag, sonst **nichts**. Ein Beleg mit erfundenen Zahlen
ist schlechter als kein Beleg.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def produkte(app):
    from database import SessionLocal

    db = SessionLocal()
    try:
        # `products` entsteht nur im Migrationsblock, und ein anderer Test legt
        # sie verkuerzt an (nur vier Spalten). Was hier gebraucht wird, wird
        # darum nachgeruestet — sonst haengt der Lauf an der Reihenfolge.
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                price_brutto NUMERIC(10,2) NOT NULL DEFAULT 0)"""))
        for spalte in ("price_netto NUMERIC(10,2) DEFAULT 0",
                       "tax_rate NUMERIC(5,2) DEFAULT 19.0",
                       "features JSONB DEFAULT '[]'",
                       "delivery_days INTEGER DEFAULT 14",
                       "status VARCHAR(50) DEFAULT 'draft'"):
            db.execute(text(f"ALTER TABLE products ADD COLUMN IF NOT EXISTS {spalte}"))
        db.commit()

        db.execute(text("DELETE FROM products WHERE slug LIKE 'l29-%'"))
        db.execute(text(
            "INSERT INTO products (slug, name, price_brutto, price_netto, tax_rate, status) "
            "VALUES ('l29-test', 'Test-Paket', 1900.00, 1596.64, 19, 'live')"))
        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM products WHERE slug LIKE 'l29-%'"))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db():
    from database import SessionLocal

    sitzung = SessionLocal()
    yield sitzung
    sitzung.close()


class TestAusDerProduktzeile:
    def test_der_beleg_nimmt_den_preis_aus_der_zeile_die_abrechnet(self, db, produkte):
        from services.paket_beleg import paket_fuer_beleg

        paket = paket_fuer_beleg(db, "l29-test", bezahlt=1900.0)

        assert paket["brutto"] == 1900.0
        assert paket["name"] == "Test-Paket"

    def test_und_die_umsatzsteuer_stimmt_dazu(self, db, produkte):
        """Ein Beleg mit falsch ausgewiesener Steuer ist nicht nur ungenau."""
        from services.paket_beleg import paket_fuer_beleg

        paket = paket_fuer_beleg(db, "l29-test", bezahlt=1900.0)

        assert paket["netto"] == pytest.approx(1596.64, abs=0.01)
        assert paket["mwst"] == pytest.approx(1900.00 - 1596.64, abs=0.01)


class TestOhneProduktzeile:
    def test_ein_unbekanntes_paket_nimmt_den_gezahlten_betrag(self, db, produkte):
        """Vorher stand hier `PAKETE["kompagnon"]` — 2.000 EUR und ein
        Paketname, den der Kunde nie bestellt hat."""
        from services.paket_beleg import paket_fuer_beleg

        paket = paket_fuer_beleg(db, "gibtesnicht", bezahlt=2500.0)

        assert paket["brutto"] == 2500.0
        assert "2.000" not in str(paket["brutto"])
        assert "KOMPAGNON" not in paket["name"]

    def test_und_rechnet_die_steuer_aus_dem_gezahlten_betrag_zurueck(self, db, produkte):
        from services.paket_beleg import paket_fuer_beleg

        paket = paket_fuer_beleg(db, "gibtesnicht", bezahlt=2380.0)

        assert paket["netto"] == pytest.approx(2000.0, abs=0.01)
        assert paket["mwst"] == pytest.approx(380.0, abs=0.01)

    def test_ohne_produkt_und_ohne_zahlung_wird_nichts_erfunden(self, db, produkte):
        """Lieber kein Beleg als einer mit erfundenen Zahlen."""
        from services.paket_beleg import paket_fuer_beleg

        with pytest.raises(ValueError):
            paket_fuer_beleg(db, "gibtesnicht", bezahlt=0)

    def test_eine_fehlende_tabelle_faellt_auf_das_gezahlte_zurueck(self, db, monkeypatch):
        from services import paket_beleg

        def kaputt(*a, **k):
            raise RuntimeError("keine Tabelle")

        monkeypatch.setattr(db, "execute", kaputt)

        paket = paket_beleg.paket_fuer_beleg(db, "l29-test", bezahlt=1500.0)

        assert paket["brutto"] == 1500.0


class TestKeineZweitePreisliste:
    def test_die_feste_paketliste_im_beleg_ist_weg(self):
        """Die Liste war das Problem, nicht ihr Inhalt — wie bei
        `PACKAGE_NAMES`."""
        from services import auftragsbestaetigung_pdf

        assert not hasattr(auftragsbestaetigung_pdf, "PAKETE"), (
            "Die feste Preisliste im Beleg ist zurueck.")

    def test_das_pdf_bekommt_das_paket_uebergeben_und_holt_es_nicht_selbst(self):
        """Damit die Darstellung keine zweite Quelle aufmachen kann."""
        import inspect
        from services.auftragsbestaetigung_pdf import generate_auftragsbestaetigung

        felder = inspect.signature(generate_auftragsbestaetigung).parameters
        assert "paket" in felder, felder.keys()


class TestUeberAlleDateien:
    def test_keine_feste_paketpreisliste_mehr_im_backend(self):
        """**Der Waechter, der gefehlt hat.**

        Der vorhandene prueft `payments` als Modul und den Frontend-Baum auf
        die Schreibweise „1.500 €". Eine feste Liste in Python-Zahlen sah
        keiner von beiden — genau deshalb ueberlebte die dritte Liste ein
        Jahr lang in einem Rechtsdokument.

        Gesucht wird das **Muster**, nicht die einzelne Zahl: drei oder mehr
        Paketbetraege in derselben Datei ausserhalb der Produktvorlage.
        """
        import ast
        import pathlib

        BETRAEGE = {1500, 2000, 2500, 2800, 3500,
                    1500.0, 2000.0, 2500.0, 2800.0, 3500.0,
                    1260.50, 1680.67, 2352.94}
        # Die Vorlage, aus der `products` beim ersten Start gefuellt wird —
        # sie **ist** die Quelle und darf die Zahlen tragen.
        AUSNAHMEN = {"main.py", "migrations_runtime.py"}

        wurzel = pathlib.Path(__file__).resolve().parent.parent
        fund = {}

        for datei in wurzel.rglob("*.py"):
            teile = set(datei.parts)
            if teile & {"venv", ".venv", "__pycache__", "tests"}:
                continue
            if datei.name in AUSNAHMEN:
                continue
            try:
                baum = ast.parse(datei.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            treffer = [k.value for k in ast.walk(baum)
                       if isinstance(k, ast.Constant)
                       and isinstance(k.value, (int, float))
                       and not isinstance(k.value, bool)
                       and k.value in BETRAEGE]
            if len(set(treffer)) >= 3:
                fund[str(datei.relative_to(wurzel))] = sorted(set(treffer))

        assert fund == {}, f"Feste Paketpreise gefunden: {fund}"
