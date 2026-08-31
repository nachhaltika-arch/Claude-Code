"""`/health` sagt auch, ob die gekaufte Datei ausgeliefert werden kann.

**Der Anlass (31.08.2026, L-100).** Fuer Stripe gibt es diese Auskunft seit
dem 27.08.; sie hat damals eine Stunde Suchen erspart, weil ein Dashboard die
**Einstellung** zeigt und nicht den Zustand des Prozesses. Fuer die R2-Ablage
fehlte sie — und ohne sie laesst sich „ist der Shop lieferfaehig?" nur
beantworten, indem man etwas kauft und sieht, ob eine Datei kommt.

Der Eintrag L-100 behauptete ausserdem, Stripe sei „auf **keinem** der beiden
Dienste gesetzt". Am 31.08. an Staging gemessen: alle vier Werte gesetzt,
Praefixe richtig, `bereit: true`. Wer einen Eintrag liest statt zu messen,
haelt einen geloesten Blocker fuer offen — und einen offenen fuer geloest.

**Gemeldet werden Namen, nie Werte.** Welche Angabe fehlt, ist die Auskunft;
was darin steht, geht ueber eine offene Route nicht hinaus.
"""
import pytest

from routers import betriebszustand


@pytest.fixture()
def ohne_r2(monkeypatch):
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                 "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def mit_r2(monkeypatch):
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                 "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.setenv(name, "probe")


def test_ohne_zugangsdaten_nennt_die_auskunft_jede_fehlende(ohne_r2):
    zustand = betriebszustand._produktablage_zustand()

    assert zustand["bereit"] is False
    assert zustand["fehlt"] == ["R2_ACCESS_KEY_ID", "R2_ACCOUNT_ID",
                                "R2_BUCKET", "R2_SECRET_ACCESS_KEY"]


def test_mit_zugangsdaten_ist_sie_bereit(mit_r2):
    """Die positive Gegenprobe.

    Ohne sie waere der Test darueber auch dann gruen, wenn die Pruefung immer
    „nicht bereit" saegte — und dann waere die Auskunft wertlos.
    """
    zustand = betriebszustand._produktablage_zustand()

    assert zustand["bereit"] is True
    assert zustand["fehlt"] == []


def test_kein_wert_steht_in_der_auskunft(monkeypatch):
    """Die Namen sind die Auskunft, nicht der Inhalt."""
    geheim = "r2-" + "geheim" * 4
    for name in ("R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID",
                 "R2_SECRET_ACCESS_KEY", "R2_BUCKET"):
        monkeypatch.setenv(name, geheim)

    assert geheim not in repr(betriebszustand._produktablage_zustand())


def test_die_auskunft_haengt_wirklich_an_health(client):
    """Sonst ist sie gebaut und nicht angeschlossen — die Klasse, die dieser
    Bestand am haeufigsten getroffen hat."""
    antwort = client.get("/health")

    assert antwort.status_code == 200
    assert "produktablage" in antwort.json()


def test_ein_laufender_geheimniswechsel_ist_sichtbar(monkeypatch):
    """Der letzte Schritt eines Wechsels ist der, den man vergisst.

    Bleibt `BREVO_INBOUND_SECRET_ALT` stehen, gilt das alte — und damit das
    kompromittierte — Geheimnis weiter, und nichts sagt es. Deshalb steht es
    in `/health`.
    """
    monkeypatch.setenv("BREVO_INBOUND_SECRET", "eins-nur-im-test")
    monkeypatch.setenv("BREVO_INBOUND_SECRET_ALT", "zwei-nur-im-test")

    zustand = betriebszustand._posteingang_zustand()

    assert zustand["bereit"] is True
    assert zustand["wechsel_laeuft"] is True
    assert "BREVO_INBOUND_SECRET_ALT" in zustand["hinweis"]


def test_nach_dem_wechsel_ist_es_wieder_still(monkeypatch):
    """Die Gegenprobe — sonst stuende der Hinweis fuer immer da und niemand
    laese ihn mehr."""
    monkeypatch.setenv("BREVO_INBOUND_SECRET", "eins-nur-im-test")
    monkeypatch.delenv("BREVO_INBOUND_SECRET_ALT", raising=False)

    zustand = betriebszustand._posteingang_zustand()

    assert zustand["wechsel_laeuft"] is False
    assert zustand["hinweis"] == ""


def test_kein_geheimnis_steht_in_der_auskunft_zum_posteingang(monkeypatch):
    geheim = "posteingang-" + "geheim" * 3
    monkeypatch.setenv("BREVO_INBOUND_SECRET", geheim)
    monkeypatch.setenv("BREVO_INBOUND_SECRET_ALT", geheim)

    assert geheim not in repr(betriebszustand._posteingang_zustand())
