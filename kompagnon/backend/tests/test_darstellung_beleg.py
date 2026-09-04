# -*- coding: utf-8 -*-
"""Der Beleg erreicht auch die Oberfläche (L-151, Nachtrag vom 04.09.2026).

**Aufgefallen beim Vergleichslauf.** Nach dem Umbau trugen der HTML-Bericht
und das PDF den Beleg — die **API-Antwort** nicht. Genau die liest aber das
Werkzeug, also der Innendienst. Ein Merkmal, das zwei von drei Ausgaben
erreicht, ist nicht fertig; das ist dieselbe Klasse wie „gebaut, nicht
angeschlossen", nur eine Ebene hoeher.
"""
from services.audit_criteria import Source, all_criteria
from routers.audit_darstellung import _catalogue_payload


def _quellen(ausser=()):
    return {c.key: (Source.NOT_COLLECTED.value if c.key in ausser
                    else Source.MEASURED.value) for c in all_criteria()}


def test_der_beleg_steht_am_kriterium():
    nutzlast = _catalogue_payload(
        {"rc_cookie": 0}, _quellen(),
        {"rc_cookie": "Gefunden: google_maps · kein Consent-Tool erkannt"})

    kriterium = next(c for kat in nutzlast for c in kat["criteria"]
                     if c["key"] == "rc_cookie")
    assert "google_maps" in kriterium["beleg"]


def test_ohne_beleg_bleibt_das_feld_leer_statt_zu_fehlen():
    """Altbestand hat keine Belege. Ein fehlendes Feld waere fuer die
    Oberflaeche ein Fehler, ein leeres ist eine Auskunft."""
    nutzlast = _catalogue_payload({}, _quellen())

    assert all(c["beleg"] == "" for kat in nutzlast for c in kat["criteria"])


def test_die_kategorie_nennt_wie_viele_kriterien_erhoben_wurden():
    """„0 von 2" allein liest sich als Urteil ueber den Betrieb."""
    ohne_lighthouse = ("bf_lighthouse", "bf_kontrast", "bf_tastatur", "bf_semantik")
    nutzlast = _catalogue_payload({}, _quellen(ausser=ohne_lighthouse))

    bf = next(k for k in nutzlast if k["key"] == "barrierefreiheit")
    assert bf["erhoben"] == 1
    assert bf["kriterien"] == 5
    assert bf["max"] == 2, "nicht Erhobenes faellt aus dem Nenner"


# ── „Gilt für diese Branche nicht" ist kein Mangel (04.09.2026) ────────

def test_ein_nicht_anwendbares_kriterium_faellt_aus_der_wertung():
    """Am laufenden Bericht gefunden.

    `neovendo.de` ist Klasse K4 (ueberregionaler Anbieter); `se_lokal` gilt
    dort nicht. Der Bericht zeigte trotzdem **0 von 3** — und daneben den
    Beleg „erfuellt: Telefonnummer als Link, Karte…". Die Punktzahl
    widersprach ihrer eigenen Begruendung.

    Die Bewertung rechnete die ganze Zeit richtig (`score_category` nimmt
    beide Quellen heraus); falsch war allein die Darstellung.
    """
    quellen = _quellen()
    quellen["se_lokal"] = Source.NOT_APPLICABLE.value
    nutzlast = _catalogue_payload({"se_lokal": 0}, quellen,
                                  {"se_lokal": "erfüllt: Telefonnummer als Link"})

    seo = next(k for k in nutzlast if k["key"] == "seo")
    lokal = next(c for c in seo["criteria"] if c["key"] == "se_lokal")

    assert lokal["collected"] is False, "zaehlt nicht als erhoben"
    assert lokal["anwendbar"] is False, "und der Grund ist ein anderer"
    assert seo["erhoben"] == 6, "sechs von sieben SEO-Kriterien zaehlen"
    assert seo["max"] == 15, "der Nenner sinkt um die drei Punkte"


def test_nicht_erhoben_und_nicht_anwendbar_bleiben_unterscheidbar():
    """Beide fallen aus der Wertung, aber der Leser betrifft der Unterschied:
    das eine ist unser Ausfall, das andere seine Branche."""
    quellen = _quellen(ausser=("tp_lcp",))
    quellen["se_lokal"] = Source.NOT_APPLICABLE.value
    nutzlast = _catalogue_payload({}, quellen)

    alle = {c["key"]: c for k in nutzlast for c in k["criteria"]}
    assert alle["tp_lcp"]["anwendbar"] is True
    assert alle["se_lokal"]["anwendbar"] is False
