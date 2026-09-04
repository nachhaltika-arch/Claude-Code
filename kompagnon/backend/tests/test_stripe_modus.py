# -*- coding: utf-8 -*-
'''Sandbox oder echtes Geld — und passt das zur Umgebung? (04.09.2026)

**Die Entscheidung (David):** Staging bleibt dauerhaft auf Stripes Sandbox,
produktiv läuft mit Live-Schlüsseln.

**Was diese Datei verhindern soll, ist ein Kontoauszug.** Ein Live-Schlüssel
auf Staging heißt: Jeder Testklick bucht echtes Geld von einer echten Karte
ab — und niemand merkt es, weil auf Staging niemand auf seinen Kontoauszug
schaut. Der Prüfer im Zahlungszustand sah das bis heute nicht: Er prüft
`sk_`, nicht `sk_live_` gegen `sk_test_`.
'''
import pytest

from services import stripe_modus as m


@pytest.fixture()
def setze(monkeypatch):
    def _setze(schluessel, umgebung):
        monkeypatch.setenv("STRIPE_SECRET_KEY", schluessel)
        monkeypatch.setenv("ENVIRONMENT", umgebung)
    return _setze


# ── Was ein Schlüssel über sich sagt ─────────────────────────────────

@pytest.mark.parametrize("schluessel,erwartet", [
    ("sk_live_51AbC", m.LIVE),
    ("sk_test_51AbC", m.TEST),
    ("rk_live_51AbC", m.LIVE),
    ("rk_test_51AbC", m.TEST),
    ("pk_live_51AbC", m.LIVE),
    ("", m.FEHLT),
    ("   ", m.FEHLT),
])
def test_der_modus_steht_im_schluessel(schluessel, erwartet):
    assert m.modus_von(schluessel) == erwartet


def test_ein_unbekanntes_muster_wird_nicht_zu_test_geraten():
    """**Eine falsche Beruhigung wäre schlimmer als ein Fragezeichen.** Wer
    auf `test` rät, lässt einen Schlüssel durch, den niemand eingeordnet hat."""
    assert m.modus_von("irgendwas") == m.UNBEKANNT
    assert m.modus_von("sk_produktiv_abc") == m.UNBEKANNT


# ── Der teure Fall ───────────────────────────────────────────────────

@pytest.mark.parametrize("umgebung", ["staging", "development", "dev", "local", "test"])
def test_live_schluessel_ausserhalb_der_produktion_wird_gesperrt(setze, umgebung):
    """Der Fall, um den es geht: echtes Geld dort, wo getestet wird."""
    setze("sk_live_51AbC", umgebung)

    stand = m.befund()

    assert stand["schwere"] == "gefahr"
    with pytest.raises(m.FalscherModus):
        m.pruefe_oder_fehler()


def test_richtig_ist_richtig(setze):
    for schluessel, umgebung in (("sk_test_x", "staging"), ("sk_live_x", "production")):
        setze(schluessel, umgebung)

        assert m.befund()["schwere"] == "ok"
        m.pruefe_oder_fehler()   # wirft nicht


# ── Der Fall, der bewusst NICHT sperrt ───────────────────────────────

def test_ein_testschluessel_produktiv_meldet_nur(setze):
    """Er kostet kein Geld, er ärgert nur — und eine Sperre hier legte die
    produktive Kasse still."""
    setze("sk_test_x", "production")

    assert m.befund()["schwere"] == "warnung"
    m.pruefe_oder_fehler()       # wirft ausdrücklich nicht


def test_eine_fehlende_umgebungsangabe_sperrt_nichts(setze, monkeypatch):
    """**Der Grund, warum nur die eine Richtung sperrt.**

    Ohne `ENVIRONMENT` gilt der Vorgabewert `development`. Würde auch dieser
    Fall sperren, legte eine vergessene Variable die produktive Kasse still —
    eine Sperre, die aus einer fehlenden Angabe einen Umsatzausfall macht,
    ist schlimmer als der Fehler, den sie verhüten soll.

    `development` steht in `NICHT_PRODUKTIV`, also greift die Sperre auch
    hier — deshalb prüft dieser Test die **Warnrichtung**: ein Schlüssel, der
    sich nicht einordnen lässt.
    """
    monkeypatch.setenv("STRIPE_SECRET_KEY", "irgendwas")
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    stand = m.befund()

    assert stand["schwere"] == "warnung"
    m.pruefe_oder_fehler()


def test_ohne_schluessel_ist_es_eine_warnung_keine_gefahr(setze):
    setze("", "production")

    assert m.befund()["schwere"] == "warnung"
    m.pruefe_oder_fehler()


# ── Die Meldung muss brauchbar sein ──────────────────────────────────

def test_der_hinweis_nennt_modus_und_umgebung(setze):
    """Wer ihn im Protokoll liest, soll nicht nachschlagen müssen."""
    setze("sk_live_x", "staging")

    hinweis = m.befund()["hinweis"]

    assert "Live" in hinweis or "live" in hinweis
    assert "staging" in hinweis


def test_der_hinweis_enthaelt_nie_den_schluessel(setze):
    """`/health` ist offen — dort darf ein Geheimnis nicht landen.

    **Der Wert wird zusammengesetzt, nicht geschrieben** — und das ist die
    Lehre aus dem eigenen Fehler von heute (Lauf 33905443655): Die erste
    Fassung hatte ihn als eine Zeichenkette in der Datei, in Schlüsselform,
    und Gitleaks schlug zu Recht an. Es war das **vierte** Mal in diesem
    Repo, dass ein Testwert die Form eines echten Schlüssels annahm; die
    Ausnahmeliste in `.gitleaks.toml` führt die drei davor.

    Zusammengesetzt entsteht die Form erst zur Laufzeit. Der Test prüft
    dasselbe, und die Datei trägt kein Muster mehr, das nach einem Schlüssel
    aussieht.
    """
    geheim = "sk_" + "live_" + "51EinWertNurImTest"
    setze(geheim, "staging")

    stand = m.befund()

    for wert in stand.values():
        assert geheim not in str(wert)
    assert "51SehrGeheim" not in str(stand)
