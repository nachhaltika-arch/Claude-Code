# -*- coding: utf-8 -*-
"""Der Massnahmenplan — aus dem Befund gerechnet, nicht aus einer festen Liste.

**Der Anlass.** `pdf_kataloge.roadmap_massnahmen` speist sich aus vier
GEO-Pruefpunkten und drei fest verdrahteten Langfristsaetzen. Der Bericht misst
daneben 39 Kriterien auf 103 Punkte und leitet daraus **keine** Empfehlung ab.
Ein Betrieb mit 3 von 6 Punkten bei `rc_impressum` liest im Bericht keine Zeile
darueber, was die anderen drei kostet.

**Was hier geprueft wird.** Nicht, dass irgendein Text entsteht, sondern dass
jede Zeile des Plans an einer Messung haengt:

* Was voll ist, erzeugt keine Massnahme.
* Was **nicht erhoben** wurde, erzeugt keine Massnahme — eine Messluecke ist
  keine Handlungsanweisung an den Betrieb. Das ist dieselbe Regel wie in
  `score_category`, wo nicht Erhobenes aus Zaehler und Nenner faellt.
* Der Schritt kommt aus der Abstufung des Kriteriums, also aus derselben
  Quelle, aus der das Buch seine Tabellen zieht (BUCH-F1). Er wird nicht
  formuliert, sondern gelesen.
* Wo die Abstufung die offene Teilpruefung nicht eindeutig bestimmt, sagt der
  Plan das, statt sich auf eine zu verlegen.
"""
import pytest

from services.audit_criteria import Source, find_criterion
from services.audit_massnahmen import Massnahme, massnahmen, stufenziel


# ── Hilfen ────────────────────────────────────────────────────────────

def _voll(ausser=None):
    """Jedes Kriterium auf Maximum, gemessen — ausser den genannten.

    `ausser` ist eine Abbildung Schluessel → erreichte Punkte.
    """
    from services.audit_criteria import all_criteria
    ausser = ausser or {}
    items, sources = {}, {}
    for crit in all_criteria():
        items[crit.key] = ausser.get(crit.key, crit.max_points)
        sources[crit.key] = Source.MEASURED
    return items, sources


def _nach_schluessel(plan):
    return {m.key: m for m in plan}


# ── Was keine Massnahme ergibt ────────────────────────────────────────

def test_ein_volles_kriterium_erzeugt_keine_massnahme():
    items, sources = _voll()
    assert massnahmen(items, sources) == []


def test_ein_nicht_erhobenes_kriterium_erzeugt_keine_massnahme():
    """Eine Messluecke ist kein Auftrag an den Betrieb.

    `tp_lcp` steht auf 0 — aber nicht, weil die Seite langsam waere, sondern
    weil PageSpeed nicht geantwortet hat. Wer daraus „Ladezeit verbessern"
    macht, schickt den Betrieb wegen eines eigenen Ausfalls los.
    """
    items, sources = _voll(ausser={"tp_lcp": 0})
    sources["tp_lcp"] = Source.NOT_COLLECTED

    assert "tp_lcp" not in _nach_schluessel(massnahmen(items, sources))


def test_ein_nicht_anwendbares_kriterium_erzeugt_keine_massnahme():
    items, sources = _voll(ausser={"cv_angebot": 0})
    sources["cv_angebot"] = Source.NOT_APPLICABLE

    assert "cv_angebot" not in _nach_schluessel(massnahmen(items, sources))


# ── Woher der Schritt kommt ───────────────────────────────────────────

def test_bei_einer_schwelle_nennt_der_schritt_die_naechsthoehere_stufe():
    """`tp_lcp` gibt 4/2/0 Punkte. Bei 2 erreichten ist der naechste Schritt
    die 4-Punkte-Stufe — und ihr Wortlaut steht im Katalog, nicht hier."""
    items, sources = _voll(ausser={"tp_lcp": 2})

    m = _nach_schluessel(massnahmen(items, sources))["tp_lcp"]
    erwartet = find_criterion("tp_lcp").abstufung.stufen[0].bedingung

    assert m.schritt == erwartet
    assert m.herkunft == "abstufung"
    assert m.gewinn == 2


def test_der_schritt_ist_die_naechste_stufe_und_nicht_die_beste():
    """`cv_cta` gibt 3/2/0. Von 0 aus ist der naechste Schritt die 2er-Stufe.

    Der Plan soll den naechsten Schritt nennen, nicht den weitesten. Wer einem
    Betrieb mit null Handlungsangeboten sofort „drei oder mehr" vorhaelt,
    verliert ihn an der ersten Zeile.
    """
    items, sources = _voll(ausser={"cv_cta": 0})

    m = _nach_schluessel(massnahmen(items, sources))["cv_cta"]
    stufen = find_criterion("cv_cta").abstufung.stufen

    assert m.schritt == stufen[1].bedingung   # die 2-Punkte-Stufe
    assert m.naechste_punkte == 2
    assert m.gewinn == 3                      # bis zum Maximum bleiben 3


def test_bei_gleich_grossen_teilen_bleibt_die_luecke_mehrdeutig():
    """`cv_kontakt` summiert 1+1+1. Bei einem erreichten Punkt kommen drei
    Faelle in Frage — welcher Teil offen ist, sagt die Arithmetik nicht."""
    crit = find_criterion("cv_kontakt")
    assert [s.punkte for s in crit.abstufung.stufen] == [1, 1, 1], "Testannahme"

    items, sources = _voll(ausser={"cv_kontakt": 1})
    m = _nach_schluessel(massnahmen(items, sources))["cv_kontakt"]

    assert m.eindeutig is False
    assert m.herkunft == "teilpruefung"
    for stufe in crit.abstufung.stufen:
        assert stufe.bedingung in m.schritt


def test_bei_ungleichen_teilen_ist_die_luecke_eindeutig():
    """`se_ki_lesbar` summiert 2+1. Bei zwei erreichten Punkten steht fest,
    dass genau der 1-Punkt-Teil offen ist — und nur der wird genannt."""
    crit = find_criterion("se_ki_lesbar")
    assert [s.punkte for s in crit.abstufung.stufen] == [2, 1], "Testannahme"

    items, sources = _voll(ausser={"se_ki_lesbar": 2})
    m = _nach_schluessel(massnahmen(items, sources))["se_ki_lesbar"]

    assert m.eindeutig is True
    assert m.schritt == crit.abstufung.stufen[1].bedingung
    assert crit.abstufung.stufen[0].bedingung not in m.schritt


def test_bei_ungleichen_teilen_bestimmt_die_arithmetik_den_offenen_teil():
    """Sind die Teile verschieden gross, ist die offene Menge oft eindeutig.

    `si_ssl`-artige Faelle gibt es im Katalog mehrere; geprueft wird hier die
    Rechnung selbst an einem Kriterium mit ungleichen Teilwerten.
    """
    from services.audit_massnahmen import _offene_teile
    from services.audit_kriterium import Stufe

    stufen = (Stufe(3, None, "A"), Stufe(2, None, "B"), Stufe(1, None, "C"))

    offen, eindeutig = _offene_teile(stufen, erreicht=4)   # 3+1 erreicht
    assert eindeutig is True
    assert [s.bedingung for s in offen] == ["B"]

    offen, eindeutig = _offene_teile(stufen, erreicht=3)   # 3 oder 2+1
    assert eindeutig is False
    assert {s.bedingung for s in offen} == {"A", "B", "C"}


def test_ohne_abstufung_traegt_der_hinweis_den_schritt():
    """Zehn der 39 Kriterien haben keine Abstufung — ueberwiegend die
    KI-bewerteten. Sie fallen nicht aus dem Plan, sondern nennen das, was der
    Katalog als geprueft ausweist, und sagen woher."""
    crit = find_criterion("dg_typografie")
    assert not (crit.abstufung and crit.abstufung.stufen), "Testannahme"

    items, sources = _voll(ausser={"dg_typografie": 0})
    m = _nach_schluessel(massnahmen(items, sources))["dg_typografie"]

    assert m.schritt == crit.hint
    assert m.herkunft == "hinweis"


# ── Reihenfolge ───────────────────────────────────────────────────────

def test_deckelregeln_stehen_vor_allem_anderen():
    """Ein fehlendes Impressum deckelt die Auszeichnung auf „Nicht konform".

    Solange das steht, ist jede Punktjagd daneben — deshalb steht es oben,
    unabhaengig vom Punktgewinn.
    """
    items, sources = _voll(ausser={"rc_impressum": 0, "tp_lcp": 0})
    plan = massnahmen(items, sources, blocker_keys=["kein_impressum"])

    assert plan[0].key == "rc_impressum"
    assert plan[0].ist_blocker is True
    assert plan[1].ist_blocker is False


def test_ohne_deckel_ordnet_der_punktgewinn():
    items, sources = _voll(ausser={"cv_kontakt": 0, "se_links": 0, "tp_lcp": 2})
    plan = massnahmen(items, sources)

    assert [m.key for m in plan] == ["cv_kontakt", "tp_lcp", "se_links"]
    assert [m.gewinn for m in plan] == [3, 2, 1]


def test_der_plan_veraendert_die_uebergebenen_daten_nicht():
    items, sources = _voll(ausser={"tp_lcp": 0})
    vorher = dict(items)

    massnahmen(items, sources)

    assert items == vorher


# ── Das Stufenziel ────────────────────────────────────────────────────

def test_das_stufenziel_nennt_die_kleinste_menge_bis_zur_naechsten_stufe():
    """Der Verkaufssatz des Berichts: „Diese drei Dinge bringen Silber."

    Gerechnet wird gegen dieselbe Schwellentabelle, die die Auszeichnung
    vergibt — nicht gegen eine zweite Liste daneben.
    """
    items, sources = _voll(ausser={
        "cv_kontakt": 0, "cv_vertrauen": 0, "se_schema": 0,
        "se_lokal": 0, "tp_lcp": 0, "tp_mobile": 0,
    })

    ziel = stufenziel(items, sources)

    assert ziel["erreichbar"] is True
    assert ziel["fehlende_punkte"] > 0
    assert len(ziel["massnahmen"]) >= 1
    # Die genannten Massnahmen tragen zusammen mindestens die fehlenden Punkte.
    assert sum(m.schritt_gewinn for m in ziel["massnahmen"]) >= ziel["fehlende_punkte"]
    # Und es ist die kleinste solche Menge: eine weniger reicht nicht.
    assert sum(m.schritt_gewinn for m in ziel["massnahmen"][:-1]) < ziel["fehlende_punkte"]


def test_bei_voller_punktzahl_gibt_es_kein_stufenziel_mehr():
    items, sources = _voll()
    ziel = stufenziel(items, sources)

    assert ziel["naechste_stufe"] is None
    assert ziel["massnahmen"] == []


def test_ein_kritischer_deckel_macht_punkte_wirkungslos():
    """Ohne Impressum bleibt die Auszeichnung „Nicht konform", auch bei 100
    Punkten. Ein Stufenziel, das trotzdem Punkte einsammeln liesse, waere eine
    Zusage, die die Bewertung nicht einloest."""
    items, sources = _voll(ausser={"rc_impressum": 0})
    ziel = stufenziel(items, sources, blocker_keys=["kein_impressum"])

    assert ziel["deckel"] == "kein_impressum"
    assert ziel["erreichbar"] is False
    assert ziel["massnahmen"][0].key == "rc_impressum"


# ── Die Zuordnung der Deckelregeln ────────────────────────────────────

def test_jede_deckelregel_kennt_ihr_kriterium():
    """Eine Deckelregel ohne Kriterium waere im Plan stumm.

    Der Plan kann einen Deckel nur dann in eine Handlung uebersetzen, wenn er
    weiss, welches Kriterium ihn aufhebt. Wer eine Regel hinzufuegt, ohne das
    zu entscheiden, faellt hier auf — dieselbe Bauart wie
    `test_deckelregeln_erhoben.py`, das die Gegenrichtung haelt.
    """
    from services.audit_criteria import BLOCKER_LABELS, find_criterion
    from services.audit_massnahmen import BLOCKER_KRITERIUM

    assert set(BLOCKER_KRITERIUM) == set(BLOCKER_LABELS)
    for blocker, key in BLOCKER_KRITERIUM.items():
        assert find_criterion(key) is not None, f"{blocker} zeigt auf {key}"
