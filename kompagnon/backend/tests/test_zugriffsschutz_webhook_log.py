"""Das Webhook-Protokoll ist kein öffentlicher Aushang.

Befund vom 19.08.2026, gefunden beim Durchzählen der Webhooks für den Umzug
nach Frankfurt: ``GET /api/webhooks/log`` antwortete produktiv mit **200 ohne
jede Anmeldung**. Die Route macht ``SELECT *`` auf ``webhook_log`` — also
``source``, ``email``, ``company``, ``created_at``. Das sind die Kontaktdaten
eingehender Leads aus Facebook, Google, LinkedIn, Telefon und Postkarte.

Aufgefallen ist es nur deshalb nicht, weil die Liste heute **leer** ist: Der
Schreibweg ist seit dem 16.08. hinter ``WEBHOOK_SECRET`` zu, und die Variable
ist produktiv nie gesetzt worden. Die Lücke wäre also genau in dem Moment
scharf geworden, in dem der erste Lead ankommt — beim Setzen der Variablen,
nicht beim Öffnen der Route. Ein leeres Ergebnis ist kein Beleg für
Dichtheit; siehe die Leadliste am 14.08. ([[test_zugriffsschutz_leads]]).

Zweiter Punkt derselben Route: ``limit`` war ungedeckelt. Ein einziger Aufruf
mit ``?limit=1000000`` hätte den ganzen Bestand gezogen.

Die fünf POST-Endpunkte daneben bleiben absichtlich ohne Anmeldung — sie
weisen sich per Geheimnis aus, weil Facebook und Netlify sich nicht anmelden
können. Der letzte Test hält diese Grenze fest.
"""
import pytest

GESCHLOSSEN = (401, 403)

LOG_PFAD = "/api/webhooks/log"

# Die Endpunkte, die ohne Anmeldung erreichbar bleiben müssen. Sie sind nicht
# offen, sondern per `X-Webhook-Secret` geschützt — geprüft in
# `test_webhook_signaturen.py`.
FREMDAUFRUF_ENDPUNKTE = ("facebook", "linkedin", "google", "postkarte", "telefon")


@pytest.fixture(scope="module", autouse=True)
def webhook_log_tabelle():
    """``webhook_log`` entsteht nur im Migrationsblock von ``main.py``.

    Es ist kein Modell, sondern rohes SQL — ``create_all`` legt es also nicht
    an, und ohne diese Vorbereitung antwortet die Route mit 500 statt mit dem
    Ergebnis. Eine 500 würde die Berechtigungsfrage genauso „bestehen" wie
    eine 200 und damit nichts belegen.
    """
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_log (
                id SERIAL PRIMARY KEY,
                source VARCHAR(50),
                email VARCHAR(255),
                company VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        db.commit()
    finally:
        db.close()


def test_ohne_anmeldung_gibt_es_das_protokoll_nicht(client):
    """Der produktiv gemessene Fall: 200 auf einen blanken GET."""
    # Act
    antwort = client.get(LOG_PFAD)

    # Assert
    assert antwort.status_code in GESCHLOSSEN, (
        f"{LOG_PFAD} -> {antwort.status_code}: Das Webhook-Protokoll enthält "
        "E-Mail-Adressen eingehender Leads und ist ohne Anmeldung lesbar."
    )


def test_mit_innendienst_anmeldung_geht_es(client, auth_headers):
    """Die Sperre darf die Anwendung nicht mitnehmen."""
    # Act
    antwort = client.get(LOG_PFAD, headers=auth_headers)

    # Assert
    assert antwort.status_code == 200, f"-> {antwort.status_code}: {antwort.text[:160]}"


def test_ein_angemeldeter_kunde_sieht_fremde_leads_nicht(client, kunde_headers):
    """Angemeldet heißt nicht berechtigt — dieselbe Richtung wie am 18.08."""
    # Act
    antwort = client.get(LOG_PFAD, headers=kunde_headers)

    # Assert
    assert antwort.status_code == 403, (
        f"-> {antwort.status_code}: Ein Kunde bekommt die Lead-Zugänge "
        "anderer Betriebe zu sehen."
    )


def test_die_menge_ist_gedeckelt(client, auth_headers):
    """Ohne Deckel zieht ein Aufruf den gesamten Bestand."""
    # Act
    antwort = client.get(LOG_PFAD, params={"limit": 1_000_000}, headers=auth_headers)

    # Assert — 422 von der Prüfung, nicht 200 mit allem
    assert antwort.status_code == 422, (
        f"-> {antwort.status_code}: `limit` nimmt jede Zahl entgegen."
    )


@pytest.mark.parametrize("grenzwert", [0, -1])
def test_unsinnige_mengen_werden_abgewiesen(client, auth_headers, grenzwert):
    # Act / Assert
    antwort = client.get(LOG_PFAD, params={"limit": grenzwert}, headers=auth_headers)

    assert antwort.status_code == 422, f"limit={grenzwert} -> {antwort.status_code}"


def test_die_route_traegt_die_sperre_selbst():
    """Damit sie nicht beim nächsten Umbau still wieder aufgeht.

    Geprüft wird am Router, nicht an ``app.routes``: Die hier installierte
    FastAPI-Version legt eingebundene Router als ``_IncludedRouter`` ab und
    flacht ihre Routen nicht auf — ``app.routes`` findet die Route also gar
    nicht, egal wie es um sie steht.

    Die Abhängigkeit hängt an *dieser* Route, nicht am Router: Der Router
    trägt die fünf Fremdaufruf-Endpunkte mit, die keine Anmeldung haben
    dürfen.
    """
    from routers.webhooks import router

    treffer = [r for r in router.routes if getattr(r, "path", "") == LOG_PFAD]

    assert treffer, f"{LOG_PFAD} existiert nicht mehr"
    assert treffer[0].dependencies, f"{LOG_PFAD} ohne Vorgabe-Anmeldung"


@pytest.mark.parametrize("pfad", FREMDAUFRUF_ENDPUNKTE)
def test_die_fremdaufrufe_bleiben_ohne_anmeldung_erreichbar(client, pfad):
    """403 wegen des fehlenden Geheimnisses — nicht 401 wegen der Anmeldung.

    Der Unterschied entscheidet, ob Facebook noch Leads liefern kann.
    """
    # Arrange / Act
    antwort = client.post(f"/api/webhooks/{pfad}", json={"beliebig": "inhalt"})

    # Assert
    assert antwort.status_code != 401, (
        f"{pfad}: verlangt jetzt eine Anmeldung — der Absender kann sich nicht "
        "anmelden, der Weg ist damit tot."
    )
