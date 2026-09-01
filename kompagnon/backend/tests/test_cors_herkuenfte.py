# -*- coding: utf-8 -*-
"""Wer das Backend im Browser ansprechen darf (BUCH-09).

**Warum das eine Zusicherung braucht.** CORS ist der einzige Fehler in diesem
Bestand, der nirgends ein Protokoll erzeugt: Der Browser haelt die Anfrage an,
bevor sie ankommt. Im Render-Log steht nichts, in Stripe nichts, in der
Datenbank nichts. Ein Kaufknopf ohne Wirkung, und kein Alarm — nirgendwo.

**Was hier gemessen wird.** Dass die Liste aus einer Quelle kommt, dass die
Diagnose dieselbe Rechnung anstellt wie die Middleware, und dass die drei
stillen Fehlerformen aus BUCH-09 benannt statt verschluckt werden.

**Was nicht gemessen wird.** Ob der laufende Dienst die richtige Variable
gesetzt hat — das kann kein Test ohne Netz sagen, und dafuer gibt es
`scripts/check-cors.sh`. Ein Waechter, der so tut, als pruefe er die
Wirklichkeit, waere schlimmer als keiner.
"""
import pytest

import cors_herkuenfte

pytestmark = pytest.mark.usefixtures("app")


# ── Die Liste ────────────────────────────────────────────────────────

def test_die_vorgaben_gelten_auch_ohne_variable(monkeypatch):
    """Geht die Variable am Dienst verloren, laedt die Oberflaeche sonst und
    scheitert an jeder Anfrage — ohne dass irgendwo „CORS" stuende."""
    monkeypatch.delenv(cors_herkuenfte.UMGEBUNGSVARIABLE, raising=False)

    liste = cors_herkuenfte.herkuenfte()

    assert "https://kas.kompagnon.group" in liste
    assert "http://localhost:3000" in liste


def test_die_variable_ergaenzt_die_vorgaben_statt_sie_zu_ersetzen(monkeypatch):
    monkeypatch.setenv(cors_herkuenfte.UMGEBUNGSVARIABLE,
                       "https://buch.netlify.app, https://kas.kompagnon.group")

    liste = cors_herkuenfte.herkuenfte()

    assert liste[0] == "https://buch.netlify.app"
    assert liste.count("https://kas.kompagnon.group") == 1, "keine Dubletten"
    assert "https://websprint.kompagnon.eu" in liste


# ── Die drei stillen Fehlerformen ────────────────────────────────────

def test_ein_schraegstrich_am_ende_wird_benannt():
    funde = cors_herkuenfte.beanstandungen(["https://buch.example/"])
    assert len(funde) == 1
    assert "Schraegstrich" in funde[0]


def test_der_stern_neben_credentials_wird_benannt():
    funde = cors_herkuenfte.beanstandungen(["*"])
    assert len(funde) == 1
    assert "allow_credentials" in funde[0]


def test_unverschluesselt_wird_benannt_ausser_lokal():
    assert cors_herkuenfte.beanstandungen(["http://buch.example"])
    assert cors_herkuenfte.beanstandungen(["http://localhost:3000"]) == []


def test_eine_beanstandete_herkunft_bleibt_in_der_liste(monkeypatch):
    """**Nicht verwerfen.** Wer sie gesetzt hat, soll sie wiederfinden und den
    Grund danebenstehen sehen; still wegzuwerfen waere derselbe unsichtbare
    Fehler mit umgekehrtem Vorzeichen."""
    monkeypatch.setenv(cors_herkuenfte.UMGEBUNGSVARIABLE, "https://buch.example/")

    liste = cors_herkuenfte.herkuenfte()

    assert "https://buch.example/" in liste
    assert cors_herkuenfte.beanstandungen(liste)


def test_eine_saubere_liste_wird_nicht_beanstandet():
    """Die Gegenprobe — sonst waere „meldet Maengel" auch dann wahr, wenn es
    alles meldet."""
    assert cors_herkuenfte.beanstandungen(
        ["https://kas.kompagnon.group", "http://localhost:3000"]) == []


# ── Die Rechnung ─────────────────────────────────────────────────────

def test_jede_netlify_adresse_ist_erlaubt():
    """Absicht: Die erzeugten Kundenseiten liegen dort, jede unter eigener
    Subdomain. Sie einzeln zu pflegen hiesse, jede neue Kundenseite mit einem
    Deploy des Backends zu bezahlen."""
    assert cors_herkuenfte.ist_erlaubt("https://kunde-heizung.netlify.app", [])


def test_eine_fremde_adresse_ist_nicht_erlaubt():
    assert not cors_herkuenfte.ist_erlaubt("https://fremde.example", [])
    assert not cors_herkuenfte.ist_erlaubt("", [])


def test_das_netlify_muster_endet_am_ende():
    """`https://boese.example/x.netlify.app` ist keine Netlify-Adresse — und
    ein Ausdruck ohne Anker haette sie durchgelassen."""
    assert not cors_herkuenfte.ist_erlaubt(
        "https://boese.example/pfad.netlify.app", [])
    assert not cors_herkuenfte.ist_erlaubt(
        "https://kunde.netlify.app.boese.example", [])


# ── Die Diagnose ─────────────────────────────────────────────────────

def test_die_auskunft_nennt_die_herkunft_des_aufrufs(client, monkeypatch):
    monkeypatch.setenv(cors_herkuenfte.UMGEBUNGSVARIABLE, "https://buch.example")

    daten = client.get("/api/health/cors",
                       headers={"Origin": "https://buch.example"}).json()

    assert daten["request_origin"] == "https://buch.example"
    assert daten["origin_allowed"] is True
    assert "https://buch.example" in daten["allowed_origins"]


def test_die_auskunft_sagt_nein_wenn_die_herkunft_fehlt(client):
    daten = client.get("/api/health/cors",
                       headers={"Origin": "https://fremde.example"}).json()

    assert daten["origin_allowed"] is False
    assert daten["request_origin"] == "https://fremde.example"


def test_die_auskunft_braucht_keine_anmeldung(client):
    """Wer wissen will, ob eine **fremde** Landingpage das Backend erreicht,
    hat dort kein Token. Hinter der Anmeldung beantwortete der Endpunkt die
    Frage nicht, fuer die er gebaut ist."""
    assert client.get("/api/health/cors").status_code == 200


def test_die_auskunft_gibt_keine_geheimnisse_preis(client):
    """Am 15.08.2026 lagen Datenbank-Zugangsdaten auf einem Auskunftsendpunkt
    offen. Diese Zusicherung haelt fest, was hier stehen darf."""
    daten = client.get("/api/health/cors").json()

    assert set(daten) == {"allowed_origins", "request_origin", "origin_allowed",
                          "backend_version", "beanstandungen"}
    text = client.get("/api/health/cors").text.lower()
    for verraeterisch in ("password", "passwort", "secret", "postgres://",
                          "sk_live", "api_key"):
        assert verraeterisch not in text


def test_ein_fehlender_stand_wird_nicht_erfunden(monkeypatch):
    """Ein erfundener Stand ist schlimmer als ein zugegebener Unbekannter:
    Wer ihn liest, haelt seinen Deploy fuer draussen."""
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert cors_herkuenfte.fassung() == ""


# ── Middleware und Modul lesen dieselbe Liste ────────────────────────

def test_die_middleware_und_die_auskunft_haben_eine_quelle():
    """Zwei Leser, die ihre Liste je eigen zusammenbauen, sind zwei
    Wahrheiten — und die Diagnose waere falsch, wenn man sie braucht."""
    import main

    quelle = main.__dict__["cors_herkuenfte"]
    assert quelle is cors_herkuenfte

    mittel = [m for m in main.app.user_middleware
              if "CORSMiddleware" in str(m)]
    assert mittel, "keine CORS-Middleware registriert"
    erlaubte = mittel[0].kwargs["allow_origins"]
    assert erlaubte == main._cors_origins
    assert mittel[0].kwargs["allow_origin_regex"] == cors_herkuenfte.NETLIFY_MUSTER
    assert mittel[0].kwargs["allow_credentials"] is True
    assert "*" not in erlaubte, \
        "'*' neben allow_credentials=True wird vom Browser kommentarlos ignoriert"


def test_der_preflight_wird_nicht_von_der_anmeldung_abgefangen(client):
    """BUCH-09 Schritt 3: Eine Middleware vor CORS wuerde OPTIONS abfangen,
    und der Kauf schluege nur bei POST fehl — bei GET liefe er weiter."""
    antwort = client.options(
        "/api/book/checkout",
        headers={"Origin": "https://kas.kompagnon.group",
                 "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "content-type"})

    assert antwort.status_code == 200
    assert antwort.headers["access-control-allow-origin"] == \
        "https://kas.kompagnon.group"
