"""Was aus einer Zahlung wird — der Pfad, auf dem Geld zu Daten wird.

L-09 nannte „Zahlungen" als ungetestet. `_handle_successful_payment` legt aus
einer abgeschlossenen Stripe-Sitzung **Lead, Benutzerkonto und Projekt** an,
verschickt eine Willkommensmail mit einem temporaeren Passwort und startet
eine Mailstrecke. Bis zum 21.08.2026 pruefte das nichts.

Der wichtigste Fall ist nicht der Normalfall, sondern die **Wiederholung**:
Stripe sendet einen Webhook bei Zeitueberschreitung mehrfach. Ohne Wache
entstuenden aus einer Zahlung zwei Kunden, zwei Konten und zwei Projekte —
und der zweite Kunde bekaeme eine zweite Willkommensmail mit einem zweiten
Passwort.

Die Nebenwirkungen sind hier ausgeschaltet: Der Test prueft, was in der
Datenbank landet, nicht ob eine Mail hinausgeht.
"""
import pytest
from sqlalchemy import text

from database import Lead, Project, SessionLocal, User


SITZUNG = "cs_test_l09_probe"
EMAIL = "probe-l09@kompagnon.local"


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture(autouse=True)
def aufraeumen(db):
    def weg():
        # Von innen nach aussen: An einem Projekt haengen Checklisten mit
        # Fremdschluessel. Der erste Entwurf loeschte das Projekt zuerst und
        # bekam eine `ForeignKeyViolation` — dieselbe Form wie L-56, nur im
        # Test. Siehe `test_projekt_loeschen.py` fuer die Frage, ob der
        # Loeschweg der Anwendung dasselbe Problem hat.
        db.execute(text("DELETE FROM users WHERE email = :e"), {"e": EMAIL})
        db.execute(text(
            "DELETE FROM project_checklists WHERE project_id IN ("
            "  SELECT p.id FROM projects p JOIN leads l ON l.id = p.lead_id"
            "  WHERE l.notes LIKE :m)"), {"m": f"%{SITZUNG}%"})
        db.execute(text(
            "DELETE FROM projects WHERE lead_id IN "
            "(SELECT id FROM leads WHERE notes LIKE :m)"), {"m": f"%{SITZUNG}%"})
        db.execute(text("DELETE FROM leads WHERE notes LIKE :m"), {"m": f"%{SITZUNG}%"})
        db.commit()

    weg()
    yield
    weg()


@pytest.fixture(autouse=True)
def ohne_nebenwirkungen(monkeypatch):
    """Mailstrecke, PDF und Scraper laufen im Hintergrund — hier nicht.

    Sie gehoeren zum Ablauf, aber nicht zu dieser Frage. Ein Test, der sie
    mitlaufen laesst, misst ihre Verfuegbarkeit statt der eigenen Zusage.
    """
    import threading

    class KeinFaden:
        def __init__(self, *a, **k):
            pass

        def start(self):
            pass

    monkeypatch.setattr(threading, "Thread", KeinFaden)


def _sitzung(betrag: float = 2000.0, paket: str = "kompagnon", email: str = EMAIL) -> dict:
    return {
        "id": SITZUNG,
        "amount_total": int(betrag * 100),
        "customer_email": email,
        "metadata": {
            "package": paket,
            "company_name": "Probe L09 GmbH",
            "customer_name": "Anna Beispiel",
            "customer_email": email,
            "website_url": "https://probe-l09.example",
            "phone": "+49 261 1234",
        },
    }


def _verarbeiten(db, sitzung):
    from routers.payments import _handle_successful_payment

    _handle_successful_payment(sitzung, db)


class TestNormalfall:
    def test_aus_einer_zahlung_werden_lead_benutzer_und_projekt(self, db):
        # Act
        _verarbeiten(db, _sitzung())

        # Assert
        lead = db.query(Lead).filter(Lead.notes.like(f"%{SITZUNG}%")).first()
        assert lead is not None, "Kein Betrieb angelegt"
        assert lead.company_name == "Probe L09 GmbH"
        assert lead.lead_source == "stripe_checkout"

        assert db.query(User).filter(User.email == EMAIL).count() == 1
        assert db.query(Project).filter(Project.lead_id == lead.id).count() == 1

    def test_der_projektpreis_ist_der_gezahlte_betrag(self, db):
        """Nicht der aus einer Liste — auf dieser Zahl rechnet die Marge
        (L-29)."""
        # Act
        _verarbeiten(db, _sitzung(betrag=2500.0, paket="gibt-es-nicht"))

        # Assert
        lead = db.query(Lead).filter(Lead.notes.like(f"%{SITZUNG}%")).first()
        projekt = db.query(Project).filter(Project.lead_id == lead.id).first()
        assert projekt.fixed_price == 2500.0


class TestWiederholung:
    """Stripe sendet bei Zeitueberschreitung erneut. Ohne Wache entstuenden
    aus einer Zahlung zwei Kunden."""

    def test_dieselbe_sitzung_zweimal_legt_nur_einmal_an(self, db):
        # Act
        _verarbeiten(db, _sitzung())
        _verarbeiten(db, _sitzung())

        # Assert
        leads = db.query(Lead).filter(Lead.notes.like(f"%{SITZUNG}%")).all()
        assert len(leads) == 1, f"{len(leads)} Betriebe aus einer Zahlung"
        assert db.query(User).filter(User.email == EMAIL).count() == 1
        assert db.query(Project).filter(Project.lead_id == leads[0].id).count() == 1

    def test_die_sitzungskennung_bleibt_auffindbar(self, db):
        """Die Wache haengt an der Kennung in `notes`. Verschwindet sie, ist
        die Wiederholung wieder offen — deshalb steht sie hier als Zusage."""
        # Act
        _verarbeiten(db, _sitzung())

        # Assert
        lead = db.query(Lead).filter(Lead.notes.like(f"%{SITZUNG}%")).first()
        assert SITZUNG in (lead.notes or "")


class TestOhneAngaben:
    def test_ohne_e_mail_entsteht_ein_betrieb_aber_kein_konto(self, db):
        """Ein Konto ohne Adresse waere eines, an das niemand herankommt."""
        # Act
        _verarbeiten(db, _sitzung(email=""))

        # Assert
        lead = db.query(Lead).filter(Lead.notes.like(f"%{SITZUNG}%")).first()
        assert lead is not None
        assert db.query(User).filter(User.email == "").count() == 0
