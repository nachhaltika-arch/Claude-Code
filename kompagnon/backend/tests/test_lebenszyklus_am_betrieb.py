"""Die Phase steht am Betrieb — und bleibt am Status hängen.

Zweiter Teil des Lifecycle-Umbaus vom 19.08.2026. Der erste
(`test_lebenszyklus.py`) prüft die Zuordnung als reine Rechnung; hier geht es
um das, was daraus in der Datenbank und an den Endpunkten wird.

Drei Dinge müssen gelten, und das dritte ist das eigentliche Ziel:

1. Die Phase folgt dem Status **von selbst**. Sie von Hand mitzupflegen wäre
   ein zweites Feld zum Vergessen — und ein Feld, das manchmal stimmt, ist
   schlechter als keines.
2. Bestandsdaten bekommen ihre Phase nachgetragen, sonst ist sie für alles
   Vorhandene leer.
3. **„Ist das ein Kunde?" ist eine Frage mit einer Antwort.** Vorher zählten
   zwei Stellen `status == "won"` und übersahen `customer` — den der
   Bildschirm anbietet und den `PATCH` klaglos schreibt.
"""
import pytest

from database import SessionLocal, Lead
from services.lebenszyklus import AUSGESCHIEDEN, IM_GESPRAECH, KUNDE, INTERESSENT


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture
def betrieb(db):
    b = Lead(company_name="Lebenszyklusprobe Betrieb", status="new")
    db.add(b)
    db.commit()
    db.refresh(b)
    yield b
    db.delete(b)
    db.commit()


# ── 1. Die Phase folgt dem Status ─────────────────────────────────────

def test_beim_anlegen_steht_die_phase_da(betrieb):
    assert betrieb.lifecycle_phase == INTERESSENT


@pytest.mark.parametrize("status,phase", [
    ("contacted", IM_GESPRAECH),
    ("won", KUNDE),
    ("customer", KUNDE),
    ("lost", AUSGESCHIEDEN),
])
def test_der_status_zieht_die_phase_mit(db, betrieb, status, phase):
    """Von selbst — niemand soll zwei Felder pflegen müssen."""
    # Act
    betrieb.status = status
    db.commit()
    db.refresh(betrieb)

    # Assert
    assert betrieb.lifecycle_phase == phase


def test_ein_unbekannter_status_laesst_die_phase_leer(db, betrieb):
    """Er soll auffallen, nicht in eine Phase gedrängt werden."""
    # Act
    betrieb.status = "irgendwas_neues"
    db.commit()
    db.refresh(betrieb)

    # Assert
    assert betrieb.lifecycle_phase is None


def test_auch_ueber_den_endpunkt(client, auth_headers, db, betrieb):
    """Der Weg, den die Oberfläche nimmt: `PATCH` mit einem Statuswert."""
    # Act
    antwort = client.patch(f"/api/leads/{betrieb.id}",
                           json={"status": "won"}, headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, antwort.text
    db.expire_all()
    assert db.query(Lead).filter(Lead.id == betrieb.id).first().lifecycle_phase == KUNDE


# ── 2. Bestandsdaten ──────────────────────────────────────────────────

def test_der_nachtrag_fuellt_leere_phasen(db, betrieb):
    """Ohne ihn bliebe die Phase für alles Vorhandene leer."""
    from sqlalchemy import text

    from services.lebenszyklus_nachtrag import phasen_nachtragen

    # Arrange — am Modell vorbei auf NULL, wie eine Bestandszeile
    db.execute(text("UPDATE leads SET status = 'won', lifecycle_phase = NULL "
                    "WHERE id = :i"), {"i": betrieb.id})
    db.commit()

    # Act
    bericht = phasen_nachtragen(db)

    # Assert
    db.expire_all()
    assert db.query(Lead).filter(Lead.id == betrieb.id).first().lifecycle_phase == KUNDE
    assert bericht["gefuellt"] >= 1


def test_der_nachtrag_laesst_unbekanntes_leer(db, betrieb):
    from sqlalchemy import text

    from services.lebenszyklus_nachtrag import phasen_nachtragen

    # Arrange
    db.execute(text("UPDATE leads SET status = 'krummer_wert', "
                    "lifecycle_phase = NULL WHERE id = :i"), {"i": betrieb.id})
    db.commit()

    # Act
    bericht = phasen_nachtragen(db)

    # Assert
    db.expire_all()
    assert db.query(Lead).filter(Lead.id == betrieb.id).first().lifecycle_phase is None
    assert bericht["ohne_zuordnung"] >= 1


# ── 3. Die Kennzahl, die vorher danebenlag ────────────────────────────

def test_ein_von_hand_gesetzter_kunde_zaehlt_mit(client, auth_headers, db, betrieb):
    """Der Fehler, um den es bei dem ganzen Umbau geht.

    `automations.py` zählte `status == "won"`. Ein Betrieb, den jemand im
    Bildschirm auf „Kunde" gesetzt hat, fehlte in der Kennzahl — und niemand
    merkt eine Zahl, die um eins zu klein ist.
    """
    # Arrange
    vorher = client.get("/api/dashboard/kpis", headers=auth_headers).json()["leads_won"]
    betrieb.status = "customer"
    db.commit()

    # Act
    nachher = client.get("/api/dashboard/kpis", headers=auth_headers).json()["leads_won"]

    # Assert
    assert nachher == vorher + 1, (
        "Ein Betrieb mit Status „customer\" zählt nicht als Kunde."
    )


# ── Die Phase kommt auch heraus ───────────────────────────────────────

def test_die_liste_nennt_die_phase(client, auth_headers, betrieb):
    """Sonst könnte die Oberfläche nicht danach filtern."""
    # Act
    antwort = client.get("/api/leads/", headers=auth_headers)

    # Assert
    assert antwort.status_code == 200
    meiner = [b for b in antwort.json() if b["id"] == betrieb.id]
    assert meiner, "Der Betrieb fehlt in der Liste"
    assert meiner[0]["lifecycle_phase"] == INTERESSENT
