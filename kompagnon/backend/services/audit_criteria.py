"""
Kriterienkatalog für das Website-Audit — einzige Wahrheitsquelle.

Bis 2026-08-11 stand die Kriterienliste dreifach im Code: im KI-Prompt, in der
Fallback-Bewertung und im Frontend. Die drei Listen sind auseinandergelaufen.
Dieses Modul hält sie einmal; Scoring, Prompt und API-Antwort leiten sich daraus ab.

Der Gesamtscore wird immer auf 0–100 normiert, egal wie die Punkte im Katalog
verteilt sind. Damit gilt:

  * Gewichte lassen sich ändern, ohne dass sie in Summe exakt 100 ergeben müssen.
  * Nicht erhobene Kriterien fallen aus Zähler UND Nenner — es wird nie eine
    fehlende Messung als "0 Punkte" verkauft.

Gewichtung freigegeben am 2026-08-11 nach docs/audit-anforderungen-2026-08-11.md.

**Aufgeteilt am 2026-08-30 (L-25), nach Zustaendigkeit in drei Teile:**
`audit_kriterium.py` traegt die Formen, `audit_katalog.py` den Inhalt, und
diese Datei rechnet. Sie bleibt die Adresse, unter der 45 Fundstellen den
Katalog holen — die Namen werden hier weitergereicht, damit der Schnitt
niemanden zwingt, seinen Import zu aendern.
"""
from typing import Dict, List, Optional, Tuple

from services.audit_katalog import (
    BRONZE,
    CATALOGUE,
    INFRASTRUCTURE,
    LEVELS,
    NON_COMPLIANT,
)
from services.audit_kriterium import (
    ABSTUFUNGSARTEN,
    SOURCE_LABELS,
    Abstufung,
    Category,
    Criterion,
    Source,
    Stufe,
)

__all__ = [
    "ABSTUFUNGSARTEN", "Abstufung", "BRONZE", "BLOCKER_LABELS",
    "BLOCKING_CRITICAL", "BLOCKING_MAJOR", "CATALOGUE", "Category",
    "Criterion", "ERWARTETE_GESAMTPUNKTE", "INFRASTRUCTURE",
    "KLASSE_OHNE_BETRIEB", "KLASSE_OHNE_EINZUGSGEBIET", "LEVELS",
    "NICHT_ERHOBENE_BLOCKER", "NON_COMPLIANT", "SOURCE_LABELS", "Source",
    "Stufe", "TOTAL_POINTS", "ai_criteria", "all_criteria",
    "anwendbares_maximum", "category_of", "determine_level", "find_criterion",
    "ist_anwendbar", "item_keys", "score_all", "score_category",
]

# ═══════════════════════════════════════════════════════════════════
# Zugriffshilfen
# ═══════════════════════════════════════════════════════════════════

def all_criteria() -> List[Criterion]:
    """Alle bewerteten Kriterien über alle Kategorien."""
    return [c for cat in CATALOGUE for c in cat.criteria]


def item_keys() -> List[str]:
    """Schlüssel aller Kriterien inklusive Infrastruktur (für DB und API)."""
    return [c.key for c in all_criteria()] + [c.key for c in INFRASTRUCTURE]


def find_criterion(key: str) -> Optional[Criterion]:
    for c in list(all_criteria()) + list(INFRASTRUCTURE):
        if c.key == key:
            return c
    return None


def category_of(key: str) -> Optional[Category]:
    for cat in CATALOGUE:
        if any(c.key == key for c in cat.criteria):
            return cat
    return None


def ai_criteria() -> List[Criterion]:
    """Kriterien, die tatsächlich eine KI-Bewertung brauchen.

    Alles andere wird deterministisch erhoben und darf nicht an die KI gehen —
    sonst rät sie wieder Werte, die längst gemessen sind.
    """
    return [c for c in all_criteria() if c.source == Source.AI]


TOTAL_POINTS: int = sum(cat.max_points for cat in CATALOGUE)

#: Die Rohpunktsumme, die der Katalog **haben soll**.
#:
#: Sie stand bis zum 21.08.2026 als nackte `100` in der Pruefung — und
#: widersprach damit dem Kopf dieser Datei, der ausdruecklich sagt, dass die
#: Gewichte nicht auf 100 aufgehen muessen, weil normiert wird. Beides konnte
#: nicht stimmen. Jetzt steht die Zahl hier, mit einem Grund daneben: Der
#: Waechter faengt weiterhin jede **versehentliche** Verschiebung, aber eine
#: beabsichtigte wird sichtbar und muss hier eingetragen werden.
#:
#: 2026-08-11: 100 — Freigabe nach `docs/Audit/audit-anforderungen-2026-08-11.md`
#: 2026-08-21: 103 — `se_ki_lesbar` (3 P) ergaenzt, L-58 (a). Bewusst **ohne**
#:   anderswo Gewicht wegzunehmen: Welches Kriterium dafuer leichter wird, ist
#:   eine Produktentscheidung und gehoert David. Bis dahin wiegt jedes
#:   bestehende Kriterium rechnerisch 100/103 seines bisherigen Anteils.
#: 2026-08-24: entschieden — es wird **kein** Gewicht weggenommen. 103
#:   bleibt. Der angezeigte Score bleibt 0–100, weil normiert wird; 103
#:   ist die Rohpunktsumme des Katalogs. Der Buchuntertitel wird auf
#:   „39 Kriterien, 8 Kategorien, 103 Punkte" geaendert, und die
#:   Praxisfall-Kette in Kap. 2/5/6 auf 88 Rohpunkte nachgezogen — sonst
#:   faellt Fall A von Gold auf Silber (BUCH-M3).
#:
#:   Die Zeile darueber blieb bewusst stehen. Ein Verlauf, aus dem man
#:   Eintraege entfernt, ist keiner — und der offene Punkt war echt.
ERWARTETE_GESAMTPUNKTE: int = 103


# ═══════════════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════════════

# Klassen ohne Betrieb dahinter bzw. ohne Einzugsgebiet (§ 2.2 der
# Bewertungslogik 2026.2). Was daraus folgt, steht am Kriterium selbst.
KLASSE_OHNE_BETRIEB = frozenset({"K6"})
KLASSE_OHNE_EINZUGSGEBIET = frozenset({"K4", "K6"})


def ist_anwendbar(key: str, klasse: Optional[str]) -> bool:
    """Gilt dieses Kriterium für diese Branchenklasse?

    Ohne Klasse — und bei einer unbekannten — wird alles bewertet. Lieber
    vollständig messen als stillschweigend Kriterien verschlucken, deren
    Wegfall niemandem auffiele.
    """
    criterion = find_criterion(key)
    if criterion is None or not klasse:
        return True
    if criterion.assumes_business and klasse in KLASSE_OHNE_BETRIEB:
        return False
    if criterion.assumes_local and klasse in KLASSE_OHNE_EINZUGSGEBIET:
        return False
    return True


def anwendbares_maximum(klasse: Optional[str] = None) -> int:
    """Die erreichbaren Punkte dieser Klasse — gerechnet, nicht notiert.

    Die Bewertungslogik nennt in § 2.4 feste Maxima je Klasse. Die stimmen mit
    ihren eigenen Einzelwerten nicht überein (79 gegen 78 bei K6). Deshalb wird
    hier gezählt: Eine Zahl, die aus dem Katalog folgt, kann nicht veralten.
    """
    return sum(c.max_points for c in all_criteria() if ist_anwendbar(c.key, klasse))


def _collected(key: str, sources: Dict[str, Source]) -> bool:
    """Zählt dieses Kriterium in Zähler und Nenner?

    Nicht erhoben und nicht anwendbar fallen beide heraus — das eine, weil die
    Prüfung ausfiel, das andere, weil der Maßstab nicht passt. Getrennt gehalten
    werden sie nur in der Ausgabe, wo der Unterschied den Leser betrifft.
    """
    quelle = sources.get(key, Source.NOT_COLLECTED)
    return quelle not in (Source.NOT_COLLECTED, Source.NOT_APPLICABLE)


def _clamp(value, maximum: int) -> int:
    try:
        v = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, min(v, maximum))


def score_category(
    category: Category,
    items: Dict[str, int],
    sources: Dict[str, Source],
) -> dict:
    """Punkte einer Kategorie — nicht erhobene Kriterien fallen heraus."""
    achieved = 0
    possible = 0
    missing: List[str] = []

    for crit in category.criteria:
        if _collected(crit.key, sources):
            achieved += _clamp(items.get(crit.key, 0), crit.max_points)
            possible += crit.max_points
        else:
            missing.append(crit.key)

    return {
        "key": category.key,
        "label": category.label,
        "score": achieved,
        "max": possible,
        "nominal_max": category.max_points,
        "not_collected": missing,
        "percent": round(achieved / possible * 100) if possible else None,
    }


def score_all(
    items: Dict[str, int],
    sources: Dict[str, Source],
    klasse: Optional[str] = None,
) -> dict:
    """Gesamtauswertung: Kategorien, normierter Gesamtscore, Abdeckung.

    Der Gesamtscore ist der Anteil erreichter an erreichbaren Punkten,
    normiert auf 0–100. Nicht erhobene Kriterien reduzieren den Nenner,
    statt als Null durchzuschlagen.

    Die Abdeckung misst gegen das **anwendbare** Maximum der Branchenklasse,
    nicht gegen die vollen 100 Punkte. Sonst läse sich bei einer Seite ohne
    Betrieb eine Abdeckung von 78 %, als wäre ein Fünftel der Prüfung
    misslungen — dabei gilt es dort schlicht nicht.
    """
    categories = [score_category(cat, items, sources) for cat in CATALOGUE]

    achieved = sum(c["score"] for c in categories)
    possible = sum(c["max"] for c in categories)
    total = round(achieved / possible * 100) if possible else 0
    anwendbar = anwendbares_maximum(klasse)

    return {
        "categories": categories,
        "achieved_points": achieved,
        "possible_points": possible,
        "applicable_max": anwendbar,
        "total_score": total,
        "coverage": round(possible / anwendbar * 100) if anwendbar else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# K.-o.-Kriterien
# ═══════════════════════════════════════════════════════════════════

BLOCKING_CRITICAL = frozenset({
    "kein_impressum", "keine_datenschutzerklaerung", "kein_gueltiges_tls",
})
BLOCKING_MAJOR = frozenset({"tracking_ohne_consent", "cookies_ohne_consent"})

#: Deckelregeln, die der Katalog **nennt**, aber niemand **erhebt**.
#:
#: **Seit dem 26.08.2026 leer.** Hier stand `cookies_ohne_consent`: Die Regel
#: verlangt einen „Cookie-Vergleich vor/nach" der Einwilligung, und
#: `audit_collectors.detect_consent` liest ausschliesslich HTML — es erkennt
#: ein Consent-Werkzeug an seiner **Signatur**, nicht an seinem Verhalten. Ob
#: tatsaechlich Cookies gesetzt wurden, sah dabei niemand.
#:
#: Die Regel blieb damals trotzdem in `BLOCKING_MAJOR` stehen. Sie zu
#: entfernen, weil die Messung fehlt, hiesse den Massstab nach der
#: Erhebungslage zu richten — der Deckel gehoert in den Standard. Jetzt
#: erhebt sie der Browserlauf (`seitenbrowser`, `_cookies_vor_consent`): Er
#: klickt kein Banner an, also ist alles, was danach im Kontext steht, ohne
#: Zustimmung gesetzt.
#:
#: Die Menge bleibt bestehen, obwohl sie leer ist. Sie ist die Stelle, an der
#: die naechste ungemessene Regel eintraegt, wer sie einfuehrt — und
#: `tests/test_deckelregeln_erhoben.py` meldet jede stille Erweiterung.
NICHT_ERHOBENE_BLOCKER = frozenset()

BLOCKER_LABELS = {
    "kein_impressum": "Kein erreichbares Impressum (§ 5 DDG)",
    "keine_datenschutzerklaerung": "Keine erreichbare Datenschutzerklärung (Art. 13 DSGVO)",
    "kein_gueltiges_tls": "Kein gültiges TLS-Zertifikat",
    "tracking_ohne_consent": "Tracking oder externe Dienste ohne Einwilligung",
    "cookies_ohne_consent": "Cookies werden vor der Einwilligung gesetzt",
}


def _cap_at(level: str, ceiling: str) -> str:
    order = [lbl for _, lbl in LEVELS][::-1]  # schlechtestes zuerst
    return level if order.index(level) <= order.index(ceiling) else ceiling


def determine_level(total_score: int, blockers: Optional[List[str]] = None) -> str:
    """Level aus dem Score, gedeckelt durch K.-o.-Kriterien.

    Ohne Deckel könnte eine Website ohne Impressum rechnerisch 'Silber'
    erreichen. Ein Report, der Rechtsverstöße prämiert, ist als Verkaufs-
    unterlage nicht haltbar.
    """
    level = next(lbl for threshold, lbl in LEVELS if total_score >= threshold)
    if not blockers:
        return level

    if any(b in BLOCKING_CRITICAL for b in blockers):
        return NON_COMPLIANT
    if any(b in BLOCKING_MAJOR for b in blockers):
        return _cap_at(level, BRONZE)
    return level


# ═══════════════════════════════════════════════════════════════════
# Konsistenzprüfung beim Import
# ═══════════════════════════════════════════════════════════════════

def _pruefe_abstufung(crit: Criterion) -> None:
    """Die Abstufung muss zur Punktzahl des Kriteriums passen.

    Ohne diesen Waechter koennte das Buch eine Tabelle drucken, deren beste
    Zeile eine andere Punktzahl nennt als der Katalog — und niemand saehe es,
    bis das Buch gedruckt ist. Genau diese Art von Abweichung hat das Projekt
    schon einmal aufgehalten.
    """
    a = crit.abstufung
    if a is None:
        raise ValueError(f"{crit.key}: keine Abstufung hinterlegt (BUCH-F1)")
    if a.art not in ABSTUFUNGSARTEN:
        raise ValueError(f"{crit.key}: unbekannte Abstufungsart {a.art!r}")

    if a.art in ("ANTEIL", "KI"):
        # Bei beiden gibt es keine Stufentabelle: Der Anteil wird skaliert, die
        # Einschaetzung folgt dem Rubric. Wer hier Stufen eintraegt, erfindet
        # eine Tabelle, die die Bewertung nicht kennt.
        if a.stufen:
            raise ValueError(f"{crit.key}: {a.art} hat keine Stufentabelle")
        return

    if not a.stufen:
        raise ValueError(f"{crit.key}: {a.art} ohne Stufen")

    punkte = [s.punkte for s in a.stufen]
    if a.art == "SUMME":
        if sum(punkte) != crit.max_points:
            raise ValueError(
                f"{crit.key}: Teilpruefungen ergeben {sum(punkte)} statt "
                f"{crit.max_points} Punkte")
        return

    # SCHWELLE und JA_NEIN: eine Staffel von der vollen Punktzahl auf null.
    if max(punkte) != crit.max_points or min(punkte) != 0:
        raise ValueError(
            f"{crit.key}: Staffel laeuft von {max(punkte)} bis {min(punkte)}, "
            f"das Kriterium hat {crit.max_points} Punkte")
    if punkte != sorted(punkte, reverse=True):
        raise ValueError(f"{crit.key}: Stufen stehen nicht absteigend")
    if a.richtung not in ("ab", "bis"):
        raise ValueError(f"{crit.key}: unbekannte Richtung {a.richtung!r}")


def _validate() -> None:
    keys = item_keys()
    duplicates = {k for k in keys if keys.count(k) > 1}
    if duplicates:
        raise ValueError(f"Doppelte Kriterien-Schlüssel im Katalog: {sorted(duplicates)}")

    for crit in all_criteria():
        if crit.max_points <= 0:
            raise ValueError(f"Bewertetes Kriterium ohne Punkte: {crit.key}")
        _pruefe_abstufung(crit)

    if TOTAL_POINTS != ERWARTETE_GESAMTPUNKTE:
        raise ValueError(
            f"Katalog ergibt {TOTAL_POINTS} statt {ERWARTETE_GESAMTPUNKTE} Punkte — "
            "entweder ist eine Gewichtung verrutscht, oder die Aenderung war "
            "gewollt und gehoert in ERWARTETE_GESAMTPUNKTE, mit Datum und Grund."
        )


_validate()
