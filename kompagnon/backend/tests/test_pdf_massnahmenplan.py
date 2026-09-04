# -*- coding: utf-8 -*-
"""Steht der gerechnete Massnahmenplan wirklich im Bericht?

**Warum dieser Test neben `test_pdf_unveraendert` noetig ist.** Dessen
Grundlage ist eine Website mit **voller** Punktzahl. Sie durchlaeuft im neuen
Massnahmenteil genau einen Zweig — „kein offener Punkt" — und laesst den
eigentlichen ungeprueft. Ein Waechter, der nur den leeren Fall sieht, ist
gruen und blind.

Hier wird deshalb ein Bericht mit **echten Luecken** gebaut und im fertigen
Flowable-Bestand nachgesehen, ob die gerechneten Zeilen dort ankommen.
"""
import json
from datetime import datetime

from pdf_inhalt import inhalt_von
from services.audit_criteria import CATALOGUE, Source, all_criteria, find_criterion
from services.pdf_generator import generate_audit_report

AUDITDATUM = datetime(2026, 1, 15)

#: Die Luecken dieses Berichts — je Kriterium die erreichten Punkte.
LUECKEN = {
    "cv_kontakt": 1,      # SUMME 1+1+1 — bei einem Punkt mehrdeutig
    "tp_lcp": 2,          # SCHWELLE 4/2/0, naechster Schritt ist die 4er-Stufe
    "se_links": 0,        # JA_NEIN 1/0
    "se_ki_lesbar": 2,    # SUMME 2+1, eindeutig
}


def _bericht(luecken=None, nicht_erhoben=(), blocker=()) -> list:
    luecken = dict(luecken or {})
    items, sources = {}, {}
    for crit in all_criteria():
        items[crit.key] = luecken.get(crit.key, crit.max_points)
        sources[crit.key] = (Source.NOT_COLLECTED.value if crit.key in nicht_erhoben
                             else Source.MEASURED.value)

    erreicht = sum(items[c.key] for c in all_criteria() if c.key not in nicht_erhoben)
    moeglich = sum(c.max_points for c in all_criteria() if c.key not in nicht_erhoben)
    gesamt = round(erreicht / moeglich * 100)

    daten = {
        "total_score": gesamt, "level": "Homepage Standard Gold", "coverage": 100,
        "company_name": "Muster GmbH", "website_url": "https://muster.de",
        "trade": "Heizung", "city": "Bochum", "created_at": AUDITDATUM,
        "ai_summary": "Solide Website mit Luecken.",
        "top_issues": json.dumps(["Ladezeit"]),
        "recommendations": json.dumps(["Bilder verkleinern"]),
        "item_scores": json.dumps(items),
        "item_sources": json.dumps(sources),
        "category_scores": json.dumps([
            {"key": c.key, "label": c.label, "score": c.max_points,
             "max": c.max_points, "nominal_max": c.max_points, "not_collected": []}
            for c in CATALOGUE
        ]),
        "blockers": json.dumps(list(blocker)),
    }
    return inhalt_von(generate_audit_report, daten)


def test_der_bericht_nennt_ein_kriterium_mit_seinem_schritt_und_punkten():
    """Die Zeile traegt drei Dinge: Kriterium, was zu tun ist, was es bringt."""
    inhalt = " ".join(_bericht(LUECKEN))
    crit = find_criterion("tp_lcp")

    assert crit.label in inhalt
    assert crit.abstufung.stufen[0].bedingung in inhalt
    assert "+2 Punkte" in inhalt


def test_der_bericht_nennt_die_naechste_auszeichnungsstufe():
    inhalt = " ".join(_bericht(LUECKEN))

    assert "Homepage Standard Platin" in inhalt
    assert "es fehlen" in inhalt


def test_eine_mehrdeutige_teilpruefung_wird_als_solche_ausgewiesen():
    inhalt = " ".join(_bericht(LUECKEN))

    assert "eine der genannten Teilprüfungen" in inhalt


def test_ein_nicht_erhobenes_kriterium_steht_nicht_im_plan():
    """Faellt PageSpeed aus, ist `tp_lcp` nicht gemessen — und darf im Plan
    nicht auftauchen. Sonst schickt der Bericht den Betrieb wegen eines
    eigenen Ausfalls los."""
    inhalt = " ".join(_bericht({"tp_lcp": 0}, nicht_erhoben=("tp_lcp",)))
    bedingung = find_criterion("tp_lcp").abstufung.stufen[0].bedingung

    assert bedingung not in inhalt


def test_ein_deckel_steht_ueber_den_punkten():
    """Ohne Impressum bleibt die Auszeichnung unten — der Bericht sagt das,
    statt eine Stufe zu versprechen, die die Bewertung nicht vergibt."""
    inhalt = " ".join(_bericht({"rc_impressum": 0}, blocker=("kein_impressum",)))

    assert "Kein erreichbares Impressum" in inhalt.replace(" ", " ")
    assert "hebt den Deckel auf" in inhalt
