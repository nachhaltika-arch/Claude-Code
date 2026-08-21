"""Die Kundenliste antwortete mit 500, sobald ein Termin fehlte.

Gefunden am 21.08.2026 beim Auftrennen der Nahtstelle `/api/customers`
(`docs/module-karte.md`). Drei Router beanspruchten diese Adresse; der zuerst
eingebundene gewann, und `routers/customers.py` war damit **unerreichbar**.

Als der ueberdeckende Alias entfernt wurde, antwortete die Route zum ersten
Mal — und zwar mit **500**:

    {'type': 'datetime_type', 'loc': ('response', 0, 'next_touchpoint_date'),
     'msg': 'Input should be a valid datetime', 'input': None}

Ursache: `next_touchpoint_date: datetime = None`. In Pydantic v2 heisst das
**nicht** „darf None sein" — es ist ein Pflichtfeld vom Typ `datetime` mit
einer Vorgabe, die den eigenen Typ verletzt. Beim Serialisieren einer echten
`NULL`-Spalte schlaegt die Antwortpruefung zu. Vier Felder waren so deklariert,
in `CustomerUpdate` sechs weitere.

**Der Lehrsatz ist nicht Pydantic.** Eine tote Route ist nicht nur ungenutzt,
sie ist **ungeprueft** — und wer die Ueberdeckung entfernt, schaltet einen
Fehler scharf, den nie jemand gesehen hat. Dieselbe Familie wie L-53
(`NULL > 0` als `TypeError`).
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


@pytest.fixture
def kunde_ohne_termin(db):
    """Der Normalfall: eine Kundenzeile, bei der noch nichts geplant ist.

    `customers.project_id` ist ein Fremdschluessel — es braucht also ein
    echtes Projekt und dafuer einen echten Betrieb.
    """
    from database import Lead, Project

    db.execute(text("DELETE FROM customers WHERE notes = 'probe-kundenliste'"))
    db.commit()

    lead = Lead(company_name="Probe Kundenliste", status="won")
    db.add(lead)
    db.flush()
    projekt = Project(lead_id=lead.id, status="phase_1")
    db.add(projekt)
    db.commit()

    zeile = db.execute(text(
        "INSERT INTO customers (project_id, upsell_status, recurring_revenue, "
        "notes, created_at) VALUES (:p, 'offen', 0, 'probe-kundenliste', NOW()) "
        "RETURNING id"
    ), {"p": projekt.id}).fetchone()
    db.commit()

    yield zeile[0]

    db.execute(text("DELETE FROM customers WHERE notes = 'probe-kundenliste'"))
    db.execute(text("DELETE FROM projects WHERE id = :p"), {"p": projekt.id})
    db.execute(text("DELETE FROM leads WHERE id = :l"), {"l": lead.id})
    db.commit()


def test_die_liste_kommt_auch_ohne_termin_durch(client, auth_headers, kunde_ohne_termin):
    # Act
    antwort = client.get("/api/customers/", headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, antwort.text[:400]
    assert any(k["id"] == kunde_ohne_termin for k in antwort.json())


def test_ein_fehlender_termin_bleibt_leer_statt_erfunden(client, auth_headers, kunde_ohne_termin):
    """`None` heisst „noch nichts geplant". Ein Vorgabedatum waere ein Termin,
    den niemand vereinbart hat."""
    # Act
    eintrag = next(k for k in client.get("/api/customers/", headers=auth_headers).json()
                   if k["id"] == kunde_ohne_termin)

    # Assert
    assert eintrag["next_touchpoint_date"] is None
    assert eintrag["next_touchpoint_type"] is None


def test_kein_antwortfeld_verspricht_einen_typ_und_liefert_none():
    """Der Waechter auf die Bauart, nicht auf die vier Stellen.

    `x: datetime = None` faellt erst zur Laufzeit auf, und nur dann, wenn die
    Spalte wirklich leer ist. Genau deshalb lag es vier Monate lang still.
    """
    import inspect
    import re
    import typing

    from routers import customers

    verdaechtig = []
    for name, obj in vars(customers).items():
        if not (inspect.isclass(obj) and hasattr(obj, "model_fields")):
            continue
        for feld, info in obj.model_fields.items():
            if info.default is None and info.is_required() is False:
                # Vorgabe None ist nur zulaessig, wenn der Typ None erlaubt.
                erlaubt = type(None) in typing.get_args(info.annotation)
                if not erlaubt and info.annotation is not type(None):
                    verdaechtig.append(f"{name}.{feld}: {info.annotation}")

    assert verdaechtig == [], (
        "Diese Felder haben die Vorgabe None, erlauben None aber nicht — "
        f"sie antworten 500, sobald die Spalte leer ist: {verdaechtig}"
    )
