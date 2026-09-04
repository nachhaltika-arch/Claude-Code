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
