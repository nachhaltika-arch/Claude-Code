"""Rechnungen und Wartungsvertraege sind nicht fuer jeden Angemeldeten.

**Gefunden am 22.08.2026 beim Verdrahten der restlichen Rechte (L-05).**
`routers/retainer.py` haengt an `main.py:1969` und trug an **allen sieben**
Routen nur `get_current_user` — also jeden Angemeldeten, einschliesslich der
Rolle `kunde`. Was damit offenstand:

    GET  /api/invoices              SELECT * FROM invoices — ohne Filter,
                                    alle Rechnungen aller Kunden
    GET  /api/retainer              alle Wartungsvertraege, mit Name,
                                    E-Mail und Nettobetrag
    POST /api/invoices              Rechnungen **anlegen**
    PUT  /api/retainer/{id}         fremde Vertraege **aendern**
    GET  /api/invoices/{id}/pdf     fremde Rechnungen als PDF

Dieselbe Familie wie L-69 (dreizehn Projektrouten fuer jeden Angemeldeten)
und L-66. Der Unterschied: Hier stehen personenbezogene Daten **fremder**
Kunden nebst Betraegen, und zwei der Routen schreiben.

**Dass die Absicht eine andere war, steht daneben:** `GET /api/invoices/my`
filtert sauber nach `current_user.email`. Der Kundenweg war gebaut — die
Innendienst-Routen waren nur nie zugesperrt.

**Warum `verlangt_recht` und nicht `require_innendienst`:** Die Rechtematrix
gibt `view_billing` und `manage_billing` an **admin und superadmin**, nicht an
den Auditor. `require_innendienst` liesse ihn durch und wiche von der Vorgabe
ab; der Haken im Bildschirm „Rollen" bliebe eine Behauptung. So wird er
wirksam — zwei der zehn offenen Rechte aus L-05 weniger.

**Was das Kundenportal betrifft: nichts.** Gemessen vor der Aenderung:
`customer/MeineRechnungen.jsx` ruft ausschliesslich `/api/invoices/my` auf,
alles Uebrige kommt aus `RetainerDashboard.jsx` — dem Innendienst-Bildschirm.
"""
import pytest


#: Was der Innendienst darf und der Kunde nicht. Lesen und Schreiben getrennt,
#: weil sie an verschiedenen Rechten haengen.
NUR_INNENDIENST = [
    ("get",  "/api/retainer",            "view_billing"),
    ("get",  "/api/invoices",            "view_billing"),
    ("get",  "/api/invoices/999999/pdf", "view_billing"),
    ("post", "/api/retainer",            "manage_billing"),
    ("post", "/api/invoices",            "manage_billing"),
    ("put",  "/api/retainer/999999",     "manage_billing"),
]


@pytest.fixture(autouse=True)
def _tabellen(app):
    """Die Tabellen legt `_run_migrations` beim Start an — den laesst die
    Testeinrichtung aus."""
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS retainer_contracts (
                id SERIAL PRIMARY KEY, project_id INTEGER, lead_id INTEGER,
                package_name VARCHAR(120), price_net NUMERIC,
                customer_email VARCHAR(255), customer_name VARCHAR(255),
                start_date DATE, next_billing_date DATE, status VARCHAR(40),
                created_at TIMESTAMP DEFAULT NOW())"""))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS invoices (
                id SERIAL PRIMARY KEY, retainer_id INTEGER,
                invoice_number VARCHAR(40), customer_email VARCHAR(255),
                customer_name VARCHAR(255), amount_net NUMERIC,
                amount_gross NUMERIC, status VARCHAR(40),
                created_at TIMESTAMP DEFAULT NOW())"""))
        db.commit()
    finally:
        db.close()


def _ruf(client, methode, pfad, headers):
    return getattr(client, methode)(
        pfad, headers=headers, **({"json": {}} if methode in ("post", "put") else {}))


@pytest.mark.parametrize("methode,pfad,recht", NUR_INNENDIENST,
                         ids=[f"{m}-{p}" for m, p, _ in NUR_INNENDIENST])
def test_der_kunde_kommt_an_fremde_abrechnung_nicht_heran(
        client, kunde_headers, methode, pfad, recht):
    antwort = _ruf(client, methode, pfad, kunde_headers)

    assert antwort.status_code == 403, (
        f"{methode.upper()} {pfad} liess einen Kunden durch — {recht} greift nicht. "
        f"Antwort: {antwort.text[:160]}")


@pytest.mark.parametrize("methode,pfad,recht", NUR_INNENDIENST,
                         ids=[f"{m}-{p}" for m, p, _ in NUR_INNENDIENST])
def test_ohne_anmeldung_erst_recht_nicht(client, methode, pfad, recht):
    antwort = _ruf(client, methode, pfad, {})

    assert antwort.status_code in (401, 403), antwort.text[:160]


def test_der_admin_darf_die_liste_sehen(client, auth_headers):
    """Die Sperre darf dem Innendienst nichts wegnehmen."""
    antwort = client.get("/api/invoices", headers=auth_headers)

    assert antwort.status_code == 200, antwort.text[:200]


def test_der_kunde_sieht_weiterhin_seine_eigenen_rechnungen(client, kunde_headers):
    """`/my` ist der Kundenweg und bleibt offen — er filtert nach der
    eigenen E-Mail. Waere er mitgesperrt worden, haette die Reparatur das
    Kundenportal gebrochen."""
    antwort = client.get("/api/invoices/my", headers=kunde_headers)

    assert antwort.status_code == 200, antwort.text[:200]


def test_die_liste_zeigt_nur_die_eigenen(client, kunde_headers, kunde_user, app):
    """Sonst waere `/my` dasselbe Loch unter anderem Namen."""
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        # `invoice_number` ist eindeutig, und der Test laeuft oefter als
        # einmal — ohne dieses Aufraeumen scheitert er beim zweiten Lauf an
        # seiner eigenen Zeile von vorhin.
        db.execute(text("DELETE FROM invoices WHERE invoice_number LIKE 'KAS-TEST-%'"))
        db.execute(text(
            "INSERT INTO invoices (invoice_number, customer_email, amount_net) "
            "VALUES ('KAS-TEST-0001', 'fremder@example.com', 100)"))
        db.execute(text(
            "INSERT INTO invoices (invoice_number, customer_email, amount_net) "
            "VALUES ('KAS-TEST-0002', :eigen, 200)"), {"eigen": kunde_user.email})
        db.commit()
    finally:
        db.close()

    daten = client.get("/api/invoices/my", headers=kunde_headers).json()
    adressen = {z.get("customer_email") for z in daten}

    assert adressen <= {kunde_user.email}, f"fremde Rechnungen sichtbar: {adressen}"


def test_beide_rechte_gelten_als_durchgesetzt():
    """Sonst kennzeichnet der Bildschirm „Rollen" sie weiter als bloss
    beschreibend — und genau diese Luege ist L-05."""
    from services.rechte import DURCHGESETZTE_RECHTE

    assert {"view_billing", "manage_billing"} <= DURCHGESETZTE_RECHTE
