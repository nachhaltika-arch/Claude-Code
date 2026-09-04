# -*- coding: utf-8 -*-
"""Aus dem Befund ein Massnahmenplan — gerechnet, nicht formuliert.

**Der Anlass (03.09.2026).** Der Bericht misst 39 Kriterien auf 103 Punkte und
empfahl daraus nichts: `pdf_kataloge.roadmap_massnahmen` zog seine Vorschlaege
aus vier GEO-Pruefpunkten und drei fest verdrahteten Langfristsaetzen, die in
jedem Bericht standen. Ein Betrieb mit 3 von 6 Punkten bei `rc_impressum` las
keine Zeile darueber, was die anderen drei kostet.

**Warum das jetzt geht und vorher nicht.** Bis zum 25.08.2026 steckten die
Punktabstufungen als Rechenanweisungen im Programmtext (`3 if perf >= 90 else
…`). Seit BUCH-F1 (L-111) stehen sie als **Daten** am Kriterium — mit einem
Satz in Fachsprache je Stufe, den schon das Buch abdruckt. Genau dieser Satz
ist die Massnahme. Er wird hier **gelesen, nicht formuliert**; damit koennen
Bericht, Buch und Bewertung nicht auseinanderlaufen.

**Vier Regeln, die den Plan ehrlich halten.**

1. **Nicht erhoben ist keine Massnahme.** Faellt PageSpeed aus, steht `tp_lcp`
   auf 0 — aber nicht, weil die Seite langsam waere. Wer daraus „Ladezeit
   verbessern" macht, schickt den Betrieb wegen eines eigenen Ausfalls los.
   Dieselbe Regel wie in `score_category`, wo Nichterhobenes aus Zaehler und
   Nenner faellt.
2. **Der naechste Schritt, nicht der weiteste.** `cv_cta` gibt 3/2/0. Wer einem
   Betrieb ohne Handlungsangebot sofort „drei oder mehr" vorhaelt, verliert ihn
   an der ersten Zeile. Genannt wird die naechsthoehere Stufe.
3. **Deckelregeln zuerst.** Ohne Impressum bleibt die Auszeichnung „Nicht
   konform", auch bei 100 Punkten. Solange das steht, ist jede Punktjagd
   daneben.
4. **Kein Aufwand, keine Dauer.** Beides ist nirgends gemessen. Eine Zahl wie
   „ca. 1 Tag" saehe im Bericht aus wie ein Befund und waere geraten — dieselbe
   Fehlerfamilie wie das PDF, das „Schreiner" druckte, weil im Text „holz"
   stand.

**Was der Plan bewusst nicht kann.** Bei einer `SUMME` aus gleich grossen
Teilen sagt die Arithmetik nicht, **welcher** Teil offen ist: `cv_kontakt`
summiert 1+1+1, bei einem erreichten Punkt kommen drei Faelle in Frage. Dann
nennt der Plan alle offenen Teile und setzt `eindeutig = False`, statt sich auf
einen zu verlegen. Bei ungleichen Teilen (`se_ki_lesbar`: 2+1) ist die Menge
eindeutig und wird auch so ausgewiesen.
"""
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Sequence, Tuple

from services.audit_criteria import (
    BLOCKER_LABELS,
    BLOCKING_CRITICAL,
    BLOCKING_MAJOR,
    CATALOGUE,
    LEVELS,
    Source,
    determine_level,
    score_all,
)
from services.audit_kriterium import Criterion, Stufe

__all__ = ["Massnahme", "BLOCKER_KRITERIUM", "massnahmen", "stufenziel"]


#: Welches Kriterium eine Deckelregel repariert.
#:
#: Die Deckelregeln (`detect_blockers`) tragen eigene Kennungen und kannten
#: bisher keinen Bezug zu einem Kriterium. Ohne diesen Bezug kann der Plan
#: nicht sagen, **was zu tun ist**, um den Deckel loszuwerden — er koennte den
#: Deckel nur melden.
#:
#: `test_jede_deckelregel_kennt_ihr_kriterium` haelt die Zuordnung
#: vollstaendig: Wer eine Deckelregel hinzufuegt, muss hier entscheiden,
#: welches Kriterium sie aufhebt. Sonst waere die neue Regel im Plan stumm.
BLOCKER_KRITERIUM: Dict[str, str] = {
    "kein_impressum": "rc_impressum",
    "keine_datenschutzerklaerung": "rc_datenschutz",
    "kein_gueltiges_tls": "si_ssl",
    # Beide Regeln greifen dieselbe Ursache ab — es fehlt ein wirksames
    # Einwilligungswerkzeug. `si_drittanbieter` misst die Folge, `rc_cookie`
    # die Ursache; repariert wird die Ursache.
    "tracking_ohne_consent": "rc_cookie",
    "cookies_ohne_consent": "rc_cookie",
}


@dataclass(frozen=True)
class Massnahme:
    """Eine Zeile des Plans. Jedes Feld haengt an einer Messung.

    `gewinn` ist der Abstand zum Maximum des Kriteriums, `schritt_gewinn` das,
    was der **genannte** Schritt einbringt. Beide koennen auseinanderfallen:
    `cv_cta` von 0 auf die naechste Stufe bringt 2, bis zum Maximum waeren es
    3. Der Bericht nennt den Schritt, das Stufenziel rechnet mit ihm.
    """

    key: str
    label: str
    kategorie: str
    erreicht: int
    maximum: int
    gewinn: int
    naechste_punkte: int
    schritt_gewinn: int
    schritt: str
    herkunft: str          # "abstufung" | "teilpruefung" | "hinweis"
    eindeutig: bool
    ist_blocker: bool


# ── Der naechste Schritt eines Kriteriums ─────────────────────────────

def _naechste_stufe(stufen: Sequence[Stufe], erreicht: int) -> Optional[Stufe]:
    """Die niedrigste Stufe oberhalb der erreichten Punktzahl.

    Die Stufen stehen im Katalog von der besten zur schlechtesten — bei
    `richtung="bis"` ebenso wie bei `"ab"`, weil die erste Zeile immer die
    hoechste Punktzahl traegt. Gesucht ist deshalb nicht die erste passende,
    sondern die **kleinste** oberhalb.
    """
    hoeher = [s for s in stufen if s.punkte > erreicht]
    return min(hoeher, key=lambda s: s.punkte) if hoeher else None


def _offene_teile(stufen: Sequence[Stufe], erreicht: int) -> Tuple[Tuple[Stufe, ...], bool]:
    """Welche Teilpruefungen einer `SUMME` offen sind — und ob das eindeutig ist.

    Gesucht sind alle Teilmengen, deren Punkte die erreichte Zahl ergeben. Ist
    es genau eine, steht die Restmenge fest. Sind es mehrere, ist offen, welche
    Teile fehlen; dann werden alle unerfuellbaren genannt und `eindeutig` ist
    falsch.
    """
    treffer = [
        set(idx)
        for groesse in range(len(stufen) + 1)
        for idx in combinations(range(len(stufen)), groesse)
        if sum(stufen[i].punkte for i in idx) == erreicht
    ]
    if len(treffer) == 1:
        offen = tuple(s for i, s in enumerate(stufen) if i not in treffer[0])
        return offen, True

    # Mehrdeutig: genannt wird jeder Teil, der in mindestens einer Lesart
    # offen ist. Ohne Treffer (eine Punktzahl, die keine Teilmenge ergibt)
    # gilt dasselbe — dann stimmt etwas an der Erhebung nicht, und der
    # vollstaendige Katalog ist die ehrlichere Auskunft.
    offen = tuple(
        s for i, s in enumerate(stufen)
        if not treffer or any(i not in t for t in treffer)
    )
    return offen, False


def _schritt(crit: Criterion, erreicht: int) -> Tuple[str, int, str, bool]:
    """Text, Punktzahl der Zielstufe, Herkunft und Eindeutigkeit."""
    abstufung = crit.abstufung
    if not (abstufung and abstufung.stufen):
        # Zehn der 39 Kriterien fuehren keine Abstufung, ueberwiegend die
        # KI-bewerteten. Sie fallen nicht aus dem Plan: Der Katalog sagt in
        # `hint`, was geprueft wird, und genau das ist hier die Auskunft.
        return crit.hint, crit.max_points, "hinweis", False

    if abstufung.art == "SUMME":
        offen, eindeutig = _offene_teile(abstufung.stufen, erreicht)
        text = " · ".join(s.bedingung for s in offen)
        ziel = erreicht + min((s.punkte for s in offen), default=0) if not eindeutig \
            else crit.max_points
        return text, ziel, "teilpruefung", eindeutig

    stufe = _naechste_stufe(abstufung.stufen, erreicht)
    if stufe is None:
        return crit.hint, crit.max_points, "hinweis", False
    return stufe.bedingung, stufe.punkte, "abstufung", True


# ── Der Plan ──────────────────────────────────────────────────────────

def _zaehlt(key: str, sources: Dict[str, object]) -> bool:
    quelle = sources.get(key, Source.NOT_COLLECTED)
    wert = getattr(quelle, "value", quelle)
    return wert not in (Source.NOT_COLLECTED.value, Source.NOT_APPLICABLE.value)


def massnahmen(
    items: Dict[str, int],
    sources: Dict[str, object],
    klasse: Optional[str] = None,
    blocker_keys: Sequence[str] = (),
) -> List[Massnahme]:
    """Der Plan: je offenem Kriterium eine Zeile, Deckelregeln zuerst.

    Die uebergebenen Abbildungen werden gelesen, nicht veraendert.
    """
    gedeckelt = {BLOCKER_KRITERIUM[b] for b in blocker_keys if b in BLOCKER_KRITERIUM}

    plan: List[Tuple[int, Massnahme]] = []
    rang = 0
    for kategorie in CATALOGUE:
        for crit in kategorie.criteria:
            rang += 1
            if crit.max_points <= 0 or not _zaehlt(crit.key, sources):
                continue
            erreicht = max(0, min(int(items.get(crit.key) or 0), crit.max_points))
            if erreicht >= crit.max_points:
                continue

            text, ziel, herkunft, eindeutig = _schritt(crit, erreicht)
            plan.append((rang, Massnahme(
                key=crit.key,
                label=crit.label,
                kategorie=kategorie.label,
                erreicht=erreicht,
                maximum=crit.max_points,
                gewinn=crit.max_points - erreicht,
                naechste_punkte=ziel,
                schritt_gewinn=max(0, ziel - erreicht),
                schritt=text,
                herkunft=herkunft,
                eindeutig=eindeutig,
                ist_blocker=crit.key in gedeckelt,
            )))

    plan.sort(key=lambda p: (not p[1].ist_blocker, -p[1].gewinn, p[0]))
    return [m for _, m in plan]


# ── Das Stufenziel ────────────────────────────────────────────────────

def _punkte_fuer_stufe(schwelle: int, moeglich: int) -> int:
    """Wie viele Punkte die Schwelle verlangt.

    Der Gesamtwert ist `round(erreicht / moeglich * 100)`. Gesucht ist die
    kleinste ganze Zahl, die nach dieser Rundung die Schwelle erreicht — nicht
    der ungerundete Anteil, sonst nennt der Bericht einen Punkt zu viel.
    """
    for punkte in range(0, moeglich + 1):
        if round(punkte / moeglich * 100) >= schwelle:
            return punkte
    return moeglich


def stufenziel(
    items: Dict[str, int],
    sources: Dict[str, object],
    klasse: Optional[str] = None,
    blocker_keys: Sequence[str] = (),
) -> dict:
    """Die kleinste Menge Massnahmen bis zur naechsten Auszeichnungsstufe.

    Das ist der Satz, den der Bericht bisher nicht sagen konnte: „Diese drei
    Dinge bringen Silber." Gerechnet wird gegen dieselbe Schwellentabelle, die
    die Auszeichnung vergibt (`LEVELS`), nicht gegen eine zweite Liste daneben.

    **Ein kritischer Deckel macht die Rechnung gegenstandslos.** Ohne Impressum
    bleibt es „Nicht konform", auch bei voller Punktzahl. Dann nennt die
    Ausgabe den Deckel und die Massnahme, die ihn aufhebt — und `erreichbar`
    ist falsch, damit der Bericht keine Stufe verspricht.
    """
    zusammenfassung = score_all(items, sources, klasse)
    erreicht = zusammenfassung["achieved_points"]
    moeglich = zusammenfassung["possible_points"]
    gesamt = zusammenfassung["total_score"]
    plan = massnahmen(items, sources, klasse, blocker_keys)

    aktuell = determine_level(gesamt, list(blocker_keys))
    kritisch = next((b for b in blocker_keys if b in BLOCKING_CRITICAL), None)
    major = next((b for b in blocker_keys if b in BLOCKING_MAJOR), None)
    deckel = kritisch or major

    if deckel:
        reparatur = [m for m in plan if m.ist_blocker]
        return {
            "aktuelle_stufe": aktuell,
            "naechste_stufe": None,
            "fehlende_punkte": 0,
            "deckel": deckel,
            "deckel_label": BLOCKER_LABELS.get(deckel, deckel),
            "erreichbar": False,
            "massnahmen": reparatur,
        }

    hoeher = [(schwelle, label) for schwelle, label in LEVELS if schwelle > gesamt]
    if not hoeher or not moeglich:
        return {
            "aktuelle_stufe": aktuell,
            "naechste_stufe": None,
            "fehlende_punkte": 0,
            "deckel": None,
            "deckel_label": None,
            "erreichbar": False,
            "massnahmen": [],
        }

    schwelle, label = min(hoeher, key=lambda h: h[0])
    fehlend = max(0, _punkte_fuer_stufe(schwelle, moeglich) - erreicht)

    gewaehlt: List[Massnahme] = []
    summe = 0
    for m in sorted(plan, key=lambda m: -m.schritt_gewinn):
        if summe >= fehlend:
            break
        if m.schritt_gewinn <= 0:
            continue
        gewaehlt.append(m)
        summe += m.schritt_gewinn

    return {
        "aktuelle_stufe": aktuell,
        "naechste_stufe": label,
        "fehlende_punkte": fehlend,
        "deckel": None,
        "deckel_label": None,
        "erreichbar": summe >= fehlend,
        "massnahmen": gewaehlt,
    }
