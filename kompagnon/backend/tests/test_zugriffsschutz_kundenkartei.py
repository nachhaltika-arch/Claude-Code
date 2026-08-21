"""Ein angemeldeter Kunde sieht die Kundenkartei nicht — nur die eigene.

Befund vom 18.08.2026, am Testserver nachgestellt:

    GET /api/customers/   als Rolle `kunde`  → 200, vollstaendige Liste
    GET /api/usercards/   als Rolle `kunde`  → 200, vollstaendige Liste

Am 17.08. wurde genau das fuer den Lead- und den Projekt-Router geschlossen;
`usercards.py` blieb uebrig — und es faellt doppelt ins Gewicht, weil dieses
Modul zusaetzlich **Alias-Router** unter `/api/leads` und `/api/customers`
fuehrt, die auf dieselben Funktionen zeigen. Die Absicherung des einen
Routers war also nur einen Umweg entfernt.

Was der Kunde weiterhin braucht, ist genau eine Route: das eigene Profil,
das sein Dashboard laedt (`CustomerDashboard.jsx`). Die haengt jetzt an einem
eigenen Router mit Pruefung je Zeile — dieselbe Bauart wie beim Lead-Router.
"""
import pytest

GESPERRT_FUER_KUNDEN = (
    "/api/usercards/",
    "/api/customers/",
)


@pytest.mark.parametrize("pfad", GESPERRT_FUER_KUNDEN)
def test_ein_kunde_bekommt_die_liste_nicht(client, kunde_headers, pfad):
    antwort = client.get(pfad, headers=kunde_headers, follow_redirects=True)

    assert antwort.status_code == 403, f"{pfad} -> {antwort.status_code}"


@pytest.mark.parametrize("pfad", GESPERRT_FUER_KUNDEN)
def test_der_innendienst_kommt_weiterhin_dran(client, auth_headers, pfad):
    """Die Sperre darf die Anwendung nicht mitnehmen."""
    antwort = client.get(pfad, headers=auth_headers, follow_redirects=True)

    assert antwort.status_code == 200, f"{pfad} -> {antwort.status_code}"


@pytest.fixture()
def eigene_karte(kunde_user):
    """`usercards` ist eine eigene Tabelle — die Karte muss es geben.

    Das Kundendashboard ruft `/api/usercards/{lead_id}/profile`, setzt also
    voraus, dass Kartennummer und Betriebsnummer dieselben sind. Diese
    Kopplung ist nirgends festgehalten; hier wird sie nur nachgestellt.
    """
    from database import SessionLocal, UserCard

    db = SessionLocal()
    try:
        vorhanden = db.query(UserCard).filter(UserCard.id == kunde_user.lead_id).first()
        if not vorhanden:
            karte = UserCard(id=kunde_user.lead_id, company_name="Pytest Kundenbetrieb")
            db.add(karte)
            db.commit()
        return kunde_user.lead_id
    finally:
        db.close()


def test_der_kunde_sieht_sein_eigenes_profil(client, kunde_headers, eigene_karte):
    antwort = client.get(f"/api/usercards/{eigene_karte}/profile",
                         headers=kunde_headers)

    assert antwort.status_code == 200, antwort.text


def test_aber_kein_fremdes(client, kunde_headers, eigene_karte):
    fremd = eigene_karte + 999

    antwort = client.get(f"/api/usercards/{fremd}/profile", headers=kunde_headers)

    assert antwort.status_code == 403, antwort.text


def test_es_gibt_keine_alias_router_mehr():
    """Der Umweg ist weg — und das ist besser als ein gesicherter Umweg.

    Bis zum 21.08.2026 bot `usercards.py` dieselben Funktionen zusaetzlich
    unter `/api/leads` und `/api/customers` an. Beide Aliasse trugen zwar
    dieselbe Sperre, aber der `/api/customers`-Alias **ueberdeckte**
    `routers/customers.py`: Die Adresse lieferte UserCards statt Customers,
    und die strengere Sperre des Alias hat unbemerkt die Sicherheitsarbeit
    fuer den schwaecher gesicherten Router mitgemacht (Modulkarte,
    Nahtstelle `/api/customers`).

    Entfernt statt abgesichert. `tests/test_router_kollisionen.py` haelt die
    Adressen jetzt eindeutig.
    """
    from routers import usercards

    assert not hasattr(usercards, "leads_alias_router")
    assert not hasattr(usercards, "customers_alias_router")


def test_der_hauptrouter_traegt_die_sperre_selbst():
    from routers import usercards

    namen = [d.dependency.__name__ for d in usercards.router.dependencies]
    assert "require_innendienst" in namen, namen


def test_und_customers_py_ebenfalls():
    """Es trug nur `require_any_auth` — was nicht auffiel, weil die Route
    gar nicht dort ankam."""
    from routers import customers

    namen = [d.dependency.__name__ for d in customers.router.dependencies]
    assert "require_innendienst" in namen, namen
