"""Der Preis in der Bestätigungsmail muss der sein, der gilt.

Befund vom 19.08.2026 (L-29). `payments.py` trug eine feste Liste:

    PACKAGE_NAMES = {
        "starter":   "Starter (5 Seiten · 1.500 EUR)",
        "kompagnon": "KOMPAGNON (8 Seiten · 2.000 EUR)",
        "premium":   "Premium (12 Seiten · 2.800 EUR)",
    }

Sie wird an genau einer Stelle benutzt — im **Text der Kundenmail** nach dem
Kauf. Der Preis daneben stammt aus der `products`-Tabelle, die von Hand
gepflegt wird. Zwei Quellen für dieselbe Zahl, und die eine steht in einer
Mail, die der Kunde aufhebt.

Nachgemessen sind sie bereits auseinandergelaufen — im Frontend steht Premium
an zwei Stellen mit **2.500**, hier mit **2.800**, und Landing.jsx nennt
Kompagnon mit **3.500** statt 2.000. Welcher Preis der richtige ist, steht in
der Datenbank und ist eine Entscheidung von David; **dieser** Umbau nimmt nur
die Behauptung aus dem Quelltext heraus.

Der Name kommt jetzt aus derselben Zeile wie der Betrag. Ist das Produkt
unbekannt, steht dort die Kennung — und **kein erfundener Preis**.
"""
import pytest
from sqlalchemy import text

from database import SessionLocal


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture(autouse=True)
def produkte(db):
    """`products` entsteht nur im Migrationsblock — hier selbst anlegen."""
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            slug VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            price_brutto NUMERIC(10,2) NOT NULL DEFAULT 0
        )
    """))
    db.execute(text("DELETE FROM products WHERE slug LIKE 'probe-%'"))
    db.commit()
    yield

    # Ein Test loescht die Tabelle absichtlich.
    try:
        db.execute(text("DELETE FROM products WHERE slug LIKE 'probe-%'"))
        db.commit()
    except Exception:  # noqa: BLE001
        db.rollback()


def _anlegen(db, slug, name, preis):
    db.execute(
        text("INSERT INTO products (slug, name, price_brutto) "
             "VALUES (:s, :n, :p)"),
        {"s": slug, "n": name, "p": preis},
    )
    db.commit()


def test_name_und_preis_kommen_aus_derselben_zeile(db):
    # Arrange
    _anlegen(db, "probe-starter", "Starter", 1500)

    # Act
    from routers.payments import paketbezeichnung
    bezeichnung = paketbezeichnung(db, "probe-starter")

    # Assert
    assert "Starter" in bezeichnung
    assert "1.500" in bezeichnung or "1500" in bezeichnung


def test_ein_geaenderter_preis_steht_sofort_in_der_mail(db):
    """Der eigentliche Zweck: eine Quelle, kein Nachpflegen."""
    # Arrange
    _anlegen(db, "probe-premium", "Premium", 2500)
    from routers.payments import paketbezeichnung
    vorher = paketbezeichnung(db, "probe-premium")

    # Act
    db.execute(text("UPDATE products SET price_brutto = 2800 WHERE slug = :s"),
               {"s": "probe-premium"})
    db.commit()

    # Assert
    assert "2.500" in vorher or "2500" in vorher
    nachher = paketbezeichnung(db, "probe-premium")
    assert "2.800" in nachher or "2800" in nachher


def test_ein_unbekanntes_produkt_erfindet_keinen_preis(db):
    """Lieber die nackte Kennung als eine Zahl, die niemand verantwortet."""
    # Act
    from routers.payments import paketbezeichnung
    bezeichnung = paketbezeichnung(db, "gibt-es-nicht")

    # Assert
    assert bezeichnung == "gibt-es-nicht"
    assert "EUR" not in bezeichnung


def test_ohne_die_tabelle_faellt_nichts_um(db):
    """Der Endpunkt darf an einer fehlenden Tabelle nicht scheitern."""
    # Arrange
    db.execute(text("DROP TABLE IF EXISTS products"))
    db.commit()

    # Act
    from routers.payments import paketbezeichnung
    bezeichnung = paketbezeichnung(db, "probe-starter")

    # Assert
    assert bezeichnung == "probe-starter"


# ── Die feste Liste darf nicht zurückkommen ───────────────────────────

def test_die_feste_paketliste_ist_weg():
    """Die Liste war das Problem, nicht ihr Inhalt.

    Geprüft wird am Modul und nicht am Text: Die Docstring der Nachfolgerin
    zitiert die alten Zeilen bewusst — sie sollen nachlesbar bleiben, ohne
    wieder zu gelten. Ein Test, der jede Ziffer im Quelltext verbietet, würde
    genau diese Erinnerung austreiben.
    """
    from routers import payments

    assert not hasattr(payments, "PACKAGE_NAMES"), (
        "Die feste Paketliste ist zurück — damit auch die zweite Preisquelle."
    )
