# -*- coding: utf-8 -*-
"""Der Beleg je Kriterium — nennt der Bericht den Wert, der den Abzug ausloest?

**Der Anlass (L-151, 04.09.2026).** Ein Fremdleser hat den Bericht fuer seine
Seite durchgearbeitet und als durchgehende Kritik zurueckgemeldet: „haeufig
bleibt unklar, welcher konkrete Messwert oder welches konkrete Problem zu dem
Punktabzug gefuehrt hat." Bei `rc_cookie` stand 0 von 4 — welcher Dienst das
ausloest, stand nirgends. Er hat daraus geschlossen, die Pruefung sei kaputt.

**Was hier geprueft wird**, ist die ganze Kette: Der Beleg entsteht an der
Rechenstelle, wird gespeichert und steht im Bericht. Ein Beleg, der nur im
Bewertungslauf existiert, waere die sechste Wiederholung von „gebaut, nicht
angeschlossen".
"""
from services.audit_criteria import Source, find_criterion
from services.audit_scoring import score_audit, teile_beleg, zahl
from services.widget_report import _criteria_rows, _kategorien

from test_audit_scoring import _fakten


# ── Die Bausteine ─────────────────────────────────────────────────────

def test_zahlen_stehen_deutsch_und_ohne_nachkommanullen():
    assert zahl(3.4) == "3,4"
    assert zahl(90.0) == "90"
    assert zahl(0.02) == "0,02"
    assert zahl(120) == "120"


def test_der_teilbeleg_nennt_beide_seiten():
    """Nur die Maengel liest sich als Anklage, nur die Erfolge erklaert den
    Abzug nicht."""
    text = teile_beleg(((True, "sitemap.xml"), (False, "Canonical-Angabe")))

    assert "erfüllt: sitemap.xml" in text
    assert "offen: Canonical-Angabe" in text


# ── Der Beleg aus der Bewertung ───────────────────────────────────────

def test_eine_abstufung_belegt_mit_messwert_und_erreichter_stufe():
    """`tp_lcp` bei 3,4 s: Der Beleg nennt die Zahl **und** den Satz aus dem
    Katalog — nicht einen zweiten, hier formulierten."""
    fakten = _fakten()
    fakten["psi_mobile"] = {**fakten["psi_mobile"], "lcp_seconds": 3.4}

    beleg = score_audit(fakten)["belege"]["tp_lcp"]
    stufe = find_criterion("tp_lcp").abstufung.stufe_fuer(3.4)

    assert "3,4 s" in beleg
    assert stufe.bedingung in beleg


def test_ein_nicht_erhobenes_kriterium_hat_keinen_beleg():
    """Sonst stuende im Bericht eine Begruendung fuer einen Abzug, den es
    nicht gibt."""
    fakten = _fakten(psi_mobile={"collected": False})
    ergebnis = score_audit(fakten)

    assert ergebnis["sources"]["tp_lcp"] == Source.NOT_COLLECTED.value
    assert "tp_lcp" not in ergebnis["belege"]


def test_der_cookie_beleg_nennt_den_ausloesenden_dienst():
    """Der Fall aus dem Fremdlauf: kein Consent-Tool, aber ein Karteneinbau.

    Ohne den Dienstnamen liest sich „0 von 4" wie ein Messfehler — genau die
    Rueckfrage, die den Eintrag ausgeloest hat.
    """
    fakten = _fakten(
        consent={"collected": True, "cmp_detected": False},
        third_parties={"collected": True, "count": 1, "services": ["google_maps"],
                       "tracking_services": [], "external_fonts": False,
                       "maps_embedded": True},
    )
    ergebnis = score_audit(fakten)

    assert ergebnis["items"]["rc_cookie"] == 0
    assert "google_maps" in ergebnis["belege"]["rc_cookie"]


def test_ohne_einwilligungspflichtigen_dienst_sagt_der_beleg_genau_das():
    ergebnis = score_audit(_fakten(consent={"collected": True, "cmp_detected": False}))

    assert ergebnis["items"]["rc_cookie"] == 4
    assert "Kein einwilligungspflichtiger Dienst" in ergebnis["belege"]["rc_cookie"]


def test_eine_summe_belegt_die_offene_teilpruefung():
    fakten = _fakten()
    fakten["qa"] = {**fakten["qa"], "sitemap_xml": False}

    beleg = score_audit(fakten)["belege"]["se_index"]

    assert "offen: sitemap.xml" in beleg


def test_jedes_erhobene_kriterium_mit_eigener_messung_traegt_einen_beleg():
    """Der Waechter gegen ein halb angeschlossenes Merkmal.

    Die sechs KI-Kriterien bleiben aussen vor — ihre Begruendung schreibt das
    Modell, nicht die Bewertung.
    """
    ergebnis = score_audit(_fakten())
    ohne = [
        k for k, quelle in ergebnis["sources"].items()
        if quelle not in (Source.NOT_COLLECTED.value, Source.AI.value)
        and (find_criterion(k).max_points if find_criterion(k) else 0) > 0
        and not ergebnis["belege"].get(k)
    ]

    assert ohne == [], f"ohne Beleg: {ohne}"


# ── Der Weg in den Bericht ────────────────────────────────────────────

def test_der_bericht_zeigt_den_beleg():
    ergebnis = score_audit(_fakten(consent={"collected": True, "cmp_detected": False},
                                   third_parties={"collected": True, "count": 1,
                                                  "services": ["google_maps"],
                                                  "tracking_services": [],
                                                  "external_fonts": False}))
    kategorien = _kategorien(ergebnis["items"], ergebnis["sources"])
    html = _criteria_rows(kategorien, ergebnis["items"], ergebnis["sources"],
                          "", ergebnis["belege"])

    assert "google_maps" in html


def test_ohne_belege_bleibt_der_bericht_unveraendert():
    """Altbestand hat keine Belege. Dann faellt die Zeile weg — kein leeres
    Feld, das wie ein Fehler aussieht."""
    ergebnis = score_audit(_fakten())
    kategorien = _kategorien(ergebnis["items"], ergebnis["sources"])

    ohne = _criteria_rows(kategorien, ergebnis["items"], ergebnis["sources"], "", {})
    mit = _criteria_rows(kategorien, ergebnis["items"], ergebnis["sources"],
                         "", ergebnis["belege"])

    assert len(mit) > len(ohne)


def test_die_kategoriezeile_nennt_wie_viele_kriterien_geprueft_wurden():
    """„Barrierefreiheit 0/2" allein liest sich als Urteil ueber den Betrieb."""
    ergebnis = score_audit(_fakten(psi_mobile={"collected": False}))
    kategorien = _kategorien(ergebnis["items"], ergebnis["sources"])
    html = _criteria_rows(kategorien, ergebnis["items"], ergebnis["sources"], "", {})

    assert "von 5 geprüft" in html


def test_der_zusatz_erscheint_nur_wo_wirklich_etwas_fehlt():
    """Die Angabe ist ein Hinweis, kein Schmuck: Wo alle Kriterien erhoben
    sind, steht sie nicht — sonst gewoehnt sich das Auge daran und uebersieht
    sie dort, wo sie zaehlt.

    Geprueft wird die Regel, nicht ein Einzelfall: **jede** Angabe im Bericht
    muss eine echte Luecke nennen.
    """
    import re
    ergebnis = score_audit(_fakten(psi_mobile={"collected": False}))
    kategorien = _kategorien(ergebnis["items"], ergebnis["sources"])
    html = _criteria_rows(kategorien, ergebnis["items"], ergebnis["sources"], "", {})

    angaben = re.findall(r"(\d+) von (\d+) geprüft", html)
    assert angaben, "keine einzige Angabe im Bericht"
    for erhoben, gesamt in angaben:
        assert int(erhoben) < int(gesamt), f"{erhoben} von {gesamt} ist keine Lücke"

    # Recht & Compliance ist vollstaendig erhoben und traegt deshalb nichts.
    kopf = html[html.index("Recht &amp; Compliance"):][:400]
    assert "geprüft" not in kopf
