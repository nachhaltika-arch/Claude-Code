"""Ein Fehler, den niemand sieht, ist ein Fehler, der bleibt.

Lücke L-10: Produktiv gibt es keine Fehlerauskunft. Wie teuer das ist, hat
der 18.08.2026 an drei Stellen gezeigt:

- `POST /api/academy/modules/{id}/lessons` antwortete **seit jeher** mit 500.
  Niemand hat es gemerkt, weil die Oberfläche den Fehler verschluckte.
- Zwölf Spalten wurden zugewiesen und stillschweigend verworfen.
- Drei Routen gaben Daten an Rollen heraus, die sie nicht haben durften.

Nur der erste dieser drei wäre hier aufgetaucht — aber er wäre am ersten Tag
aufgetaucht statt nach Monaten.

**Bewusst im eigenen Haus.** Ein Dienst wie Sentry bekäme Ausschnitte aus
Kundendaten; das verlangt einen Auftragsverarbeitungsvertrag und einen Eintrag
in der Datenschutzerklärung. Die eigene Tabelle liegt in derselben Datenbank,
die die Erklärung ohnehin nennt.

**Zusammengefasst statt gesammelt.** Ein kaputter Endpunkt schreibt sonst
tausende gleiche Zeilen und macht die Liste unlesbar. Gleiche Fehler an
derselben Stelle zählen hoch, statt sich zu häufen.
"""
from datetime import datetime, timedelta

import pytest


@pytest.fixture(autouse=True)
def leere_tabelle(app):
    from database import Fehlerprotokoll, SessionLocal

    db = SessionLocal()
    try:
        db.query(Fehlerprotokoll).delete()
        db.commit()
    finally:
        db.close()


def _merken(**felder):
    from services import fehlerprotokoll

    vorgabe = dict(
        pfad="/api/academy/modules/1/lessons",
        methode="POST",
        art="TypeError",
        meldung="'checklist_items_json' is an invalid keyword argument",
        spur="Traceback...\n  File routers/academy.py, line 377",
        benutzer_id=None,
    )
    return fehlerprotokoll.merke_fehler(**{**vorgabe, **felder})


def test_ein_fehler_wird_festgehalten(app):
    from database import Fehlerprotokoll, SessionLocal

    _merken()

    db = SessionLocal()
    try:
        eintrag = db.query(Fehlerprotokoll).one()
        assert eintrag.pfad == "/api/academy/modules/1/lessons"
        assert eintrag.art == "TypeError"
        assert eintrag.anzahl == 1
    finally:
        db.close()


def test_derselbe_fehler_zaehlt_hoch_statt_sich_zu_haeufen(app):
    from database import Fehlerprotokoll, SessionLocal

    for _ in range(5):
        _merken()

    db = SessionLocal()
    try:
        eintrag = db.query(Fehlerprotokoll).one()
        assert eintrag.anzahl == 5
    finally:
        db.close()


def test_ein_anderer_pfad_ist_ein_anderer_eintrag(app):
    from database import Fehlerprotokoll, SessionLocal

    _merken()
    _merken(pfad="/api/leads/7")

    db = SessionLocal()
    try:
        assert db.query(Fehlerprotokoll).count() == 2
    finally:
        db.close()


def test_die_spur_wird_gekuerzt(app):
    """Ein Traceback kann Kundendaten enthalten — er wird nicht in Gaenze
    aufbewahrt."""
    from database import Fehlerprotokoll, SessionLocal
    from services.fehlerprotokoll import SPUR_MAX

    _merken(spur="x" * (SPUR_MAX + 500))

    db = SessionLocal()
    try:
        assert len(db.query(Fehlerprotokoll).one().spur) <= SPUR_MAX
    finally:
        db.close()


def test_das_protokoll_reisst_nichts_mit(app, monkeypatch):
    """Wenn das Festhalten scheitert, darf die Anfrage nicht daran sterben."""
    from services import fehlerprotokoll

    def kaputt(*_, **__):
        raise RuntimeError("Datenbank weg")

    monkeypatch.setattr(fehlerprotokoll, "SessionLocal", kaputt)

    # Kein Fehler nach aussen — der Aufruf gibt None zurueck.
    assert _merken() is None


def test_alte_eintraege_verschwinden(app):
    from database import Fehlerprotokoll, SessionLocal
    from services.fehlerprotokoll import AUFBEWAHRUNG_TAGE, alte_aufraeumen

    _merken()
    db = SessionLocal()
    try:
        eintrag = db.query(Fehlerprotokoll).one()
        eintrag.zuletzt = datetime.utcnow() - timedelta(days=AUFBEWAHRUNG_TAGE + 1)
        db.commit()
    finally:
        db.close()

    entfernt = alte_aufraeumen()

    db = SessionLocal()
    try:
        assert entfernt == 1
        assert db.query(Fehlerprotokoll).count() == 0
    finally:
        db.close()


def test_nur_der_innendienst_sieht_die_liste(client, kunde_headers):
    antwort = client.get("/api/fehler/", headers=kunde_headers, follow_redirects=True)

    assert antwort.status_code == 403


def test_der_innendienst_sieht_die_liste(client, auth_headers, app):
    _merken()

    antwort = client.get("/api/fehler/", headers=auth_headers, follow_redirects=True)

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["gesamt"] >= 1
    assert daten["eintraege"][0]["art"] == "TypeError"


# ── Der Weg von der Ausnahme zur Zeile ────────────────────────────────

def test_eine_unbehandelte_ausnahme_landet_im_protokoll(client, app):
    """Der ganze Weg, nicht nur der Dienst: Route wirft → Zeile steht da."""
    from database import Fehlerprotokoll, SessionLocal

    @app.get("/api/testroute-die-kracht")
    def _kracht():
        raise ValueError("absichtlich kaputt")

    try:
        client.get("/api/testroute-die-kracht")
    except ValueError:
        # Der TestClient reicht die Ausnahme durch, der Handler lief trotzdem.
        pass
    finally:
        # **Die Route wieder abhaengen (22.08.2026).** Sie blieb bisher fuer
        # den Rest des Laufs in der Anwendung stehen. Wer danach an der
        # geladenen App misst — `tools/schwacher-zugriffsschutz.py`, der
        # Bestandswaechter aus L-67 —, zaehlt sie mit und findet eine Route
        # ohne Anmeldepruefung, die es gar nicht gibt. Genau daran ist der
        # Waechter beim ersten Gesamtlauf gescheitert: 50 statt 49, und die
        # ueberzaehlige hiess `/api/testroute-die-kracht`.
        app.router.routes = [
            r for r in app.router.routes
            if getattr(r, "path", "") != "/api/testroute-die-kracht"
        ]

    db = SessionLocal()
    try:
        eintrag = (db.query(Fehlerprotokoll)
                     .filter(Fehlerprotokoll.art == "ValueError")
                     .first())
        assert eintrag is not None, "Die Ausnahme wurde nirgends festgehalten"
        assert "testroute-die-kracht" in eintrag.pfad
        assert eintrag.meldung == "absichtlich kaputt"
    finally:
        db.close()


def test_es_gibt_genau_einen_handler():
    """Es waren zwei mit demselben Namen — der zweite gewann stillschweigend."""
    from pathlib import Path

    quelle = Path(__file__).resolve().parents[1] / "main.py"
    inhalt = quelle.read_text(encoding="utf-8")

    assert inhalt.count("@app.exception_handler(Exception)") == 1


def test_die_liste_nennt_was_heute_passierte(client, auth_headers, app):
    """Eine Gesamtsumme sieht immer gleich schlimm aus."""
    _merken()

    daten = client.get("/api/fehler/", headers=auth_headers, follow_redirects=True).json()

    assert daten["letzte_24h"] == 1
