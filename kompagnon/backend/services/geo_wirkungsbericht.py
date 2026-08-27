# -*- coding: utf-8 -*-
"""Der Wirkungsbericht nach 60 Tagen (GEO-01, Position 7).

**Warum er lange nicht gebaut werden konnte.** Das Produktdatenblatt führte
ihn seit Mai mit dem Vermerk „braucht eine Messmethode, die es noch nicht
gibt". Seit dem 25.08.2026 gibt es sie: die Nennungsmessung mit ihrem Verlauf.

**Was er vergleicht.** Den Stand bei der Auslieferung mit dem Stand heute — in
zwei Größen, die verschiedene Fragen beantworten:

    GEO-Wert       Ist die Seite für Maschinen lesbar? (unser Werk)
    Nennungen      Nennen die Systeme den Betrieb?    (nicht unser Werk)

**Die zweite Zeile ist die ehrliche.** Wir stellen die Voraussetzungen her;
ob ein Assistent den Betrieb nennt, entscheidet dessen Anbieter. Ein Bericht,
der beides in eine Zahl presst, verkauft eine Wirkung, die niemand zusichern
kann.

**Ohne Vergleichspunkt gibt es keinen Bericht.** Wer erst seit zwei Wochen
dabei ist, bekommt keine Hochrechnung, sondern die Auskunft, dass es noch zu
früh ist. Eine Wirkung aus zwei Messpunkten zu behaupten wäre dieselbe Sorte
Zahl, die dieses Projekt seinen Kunden nicht zumutet.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

#: Nach wie vielen Tagen der Bericht fällig ist. Aus dem Leistungsverzeichnis.
FRIST_TAGE = 60

#: Wie viel Spielraum vor der Frist genügt, um schon zu berichten. Ein Bericht
#: am 58. Tag ist derselbe wie am 60.; einer am 30. wäre eine andere Aussage.
VORLAUF_TAGE = 3


def _zeitpunkt(wert) -> Optional[datetime]:
    if isinstance(wert, datetime):
        return wert
    if isinstance(wert, str) and wert:
        try:
            return datetime.fromisoformat(wert.replace("Z", ""))
        except ValueError:
            return None
    return None


def _erster_und_letzter(eintraege: list, feld: str) -> tuple:
    """Der erste und der letzte auswertbare Wert einer Verlaufsliste."""
    werte = [(e, e.get(feld)) for e in eintraege or [] if e.get(feld) is not None]
    if len(werte) < 2:
        return None, None
    return werte[0], werte[-1]


def _nennungen_summe(eintrag: dict) -> Optional[int]:
    """Wie oft der Betrieb in diesem Lauf genannt wurde — über alle Systeme.

    **Nur über die tatsächlich erhobenen.** Ein System ohne Schlüssel steht
    nicht mit Null darin; sonst zeigte der Vergleich einen Einbruch, den es
    nie gab.
    """
    anbieter = (eintrag or {}).get("anbieter") or {}
    if not anbieter:
        return None
    return sum(int(w.get("genannt_bei") or 0) for w in anbieter.values())


def baue_wirkungsbericht(analyse, heute: Optional[datetime] = None) -> dict:
    """Der Vergleich — oder die Auskunft, warum es ihn noch nicht gibt."""
    heute = heute or datetime.utcnow()
    seit = _zeitpunkt(getattr(analyse, "auslieferung_am", None))
    if seit is None:
        return {"faellig": False,
                "grund": "Es gibt keine ausgelieferte Fassung, auf die sich ein "
                         "Vergleich beziehen könnte"}

    tage = (heute - seit).days
    if tage < FRIST_TAGE - VORLAUF_TAGE:
        return {"faellig": False, "tage_seit_auslieferung": tage,
                "grund": f"Erst {tage} von {FRIST_TAGE} Tagen vergangen — für eine "
                         f"Aussage über die Wirkung zu früh"}

    bericht = {"faellig": True, "tage_seit_auslieferung": tage,
               "ausgeliefert_am": seit.isoformat(timespec="seconds")}

    # ── Lesbarkeit: unser Werk ───────────────────────────────────────
    erster, letzter = _erster_und_letzter(
        getattr(analyse, "monitoring_history", None) or [], "score")
    if erster and letzter and erster is not letzter:
        vorher, heute_wert = erster[1], letzter[1]
        bericht["geo_wert"] = {"vorher": vorher, "heute": heute_wert,
                               "veraenderung": heute_wert - vorher}
    else:
        # Ein einzelner Messpunkt ist keine Entwicklung.
        bericht["geo_wert"] = None

    # ── Nennungen: nicht unser Werk ──────────────────────────────────
    verlauf = getattr(analyse, "ki_sichtbarkeit_verlauf", None) or []
    summen = [(e, _nennungen_summe(e)) for e in verlauf]
    summen = [(e, s) for e, s in summen if s is not None]
    if len(summen) >= 2:
        (erst_e, erst_s), (letzt_e, letzt_s) = summen[0], summen[-1]
        bericht["nennungen"] = {
            "vorher": erst_s, "heute": letzt_s, "veraenderung": letzt_s - erst_s,
            "erste_messung": erst_e.get("am"), "letzte_messung": letzt_e.get("am"),
            "laeufe": len(summen),
        }
    else:
        # **Ein Messpunkt ist kein Verlauf.** Lieber die Lücke benennen als
        # eine Veränderung gegen nichts zu rechnen.
        bericht["nennungen"] = None
        bericht["nennungen_grund"] = (
            "Es liegen noch nicht genug Messungen vor, um eine Entwicklung zu "
            "zeigen")

    bericht["auslieferung_erreichbar"] = (
        (getattr(analyse, "auslieferung", None) or {}).get("vollstaendig"))
    return bericht


def klartext(bericht: dict) -> str:
    """Zwei bis drei Sätze für den Innendienst."""
    if not bericht.get("faellig"):
        return bericht.get("grund", "Noch nicht fällig")

    teile = [f"{bericht['tage_seit_auslieferung']} Tage seit der Auslieferung."]
    wert = bericht.get("geo_wert")
    if wert:
        richtung = "gestiegen" if wert["veraenderung"] > 0 else (
            "gefallen" if wert["veraenderung"] < 0 else "unverändert")
        teile.append(f"Lesbarkeit {richtung}: {wert['vorher']} auf {wert['heute']}.")
    nennung = bericht.get("nennungen")
    if nennung:
        teile.append(f"Nennungen über {nennung['laeufe']} Messungen: "
                     f"{nennung['vorher']} auf {nennung['heute']}.")
    else:
        teile.append(bericht.get("nennungen_grund", ""))
    return " ".join(t for t in teile if t)
