"""Wer wird **stattdessen** genannt? (L-85, zweite Hälfte)

Die erste Hälfte von L-85 ist seit dem 22.08.2026 zu: `ki_sichtbarkeit_verlauf`
sammelt die Läufe, statt sie zu überschreiben. Offen blieb der
Wettbewerbsvergleich — und der ist die eigentliche Auskunft. „Drei von fünf
Antworten nennen Sie nicht" ist eine Zahl. „Und stattdessen nennen sie diese
zwei Betriebe aus Ihrer Stadt" ist der Satz, für den ein Betrieb zahlt.

**Gezählt werden Quellen, nicht Prosa.** Steht eine Adresse unter den
herangezogenen Quellen, hat die Suche sie wirklich benutzt — dieselbe harte
Regel, mit der `ki_sichtbarkeit.ist_genannt` die eigene Nennung belegt. Aus
Fließtext Firmennamen zu erkennen wäre Raten, und ein falsch erkannter
„Mitbewerber" im Kundenbericht ist teurer als eine fehlende Zeile.

**Grundlage ist der Befund, nicht ein zweiter Lauf.** Gezählt wird, was im
Befund steht — also dieselben höchstens fünf Quellen je Antwort, die auch der
Bericht zeigt. Eine zweite Quelle für dieselbe Zahl ist der Fehler, der in
diesem Bestand am häufigsten weh getan hat.

**Ein Verzeichnis ist kein Mitbewerber.** `11880.com` steht unter fast jeder
Antwort. Es als Wettbewerber auszuweisen wäre die falsche Auskunft — und es
still wegzuwerfen die zweite: Dann ließe sich „nichts gefunden" nicht von
„alles gefiltert" unterscheiden. Beides steht deshalb im Befund, getrennt.

**Die Portalliste ist naturgemäß unvollständig**, und das ist bewusst die
ungefährlichere Richtung: Ein unbekanntes Portal taucht als Mitbewerber auf und
fällt beim Lesen auf. Andersherum — ein Mitbewerber, den eine zu breite Regel
verschluckt — fiele niemandem auf.
"""
import re
from typing import Iterable, List

#: Wie viele Mitbewerber der Verlauf je Lauf mitführt. Er soll die Frage
#: „dieselben wie beim letzten Mal?" beantworten, nicht den Befund doppeln —
#: die Quellen und Antworttexte bleiben draußen, wie bei den Trefferzahlen.
VERLAUF_MITBEWERBER = 3

#: Verzeichnisse, Portale, Netzwerke und Nachschlagewerke. Sie stehen unter
#: den Quellen, sind aber kein Betrieb, der dem Kunden den Auftrag wegnimmt.
#: Vergleich auf die Adresse **oder** eine ihrer Unterdomains.
VERZEICHNISSE = frozenset({
    # Branchen- und Handwerkerverzeichnisse
    "11880.com", "gelbeseiten.de", "dasoertliche.de", "dastelefonbuch.de",
    "meinestadt.de", "cylex.de", "cylex-branchenbuch.de", "wlw.de",
    "yelp.de", "yelp.com", "golocal.de", "branchenbuch.de", "hotfrog.de",
    "werkenntdenbesten.de", "kennstdueinen.de", "firmenwissen.de",
    "northdata.de", "unternehmensregister.de", "wer-zu-wem.de",
    # Auftragsvermittler
    "myhammer.de", "check24.de", "aroundhome.de", "blauarbeit.de",
    "daibau.de", "haus.de", "obi.de", "hornbach.de",
    "energieheld.de", "heizungsfinder.de", "wattfox.de", "selfio.de",
    # Karten, Netzwerke, Bewertungen
    "google.com", "google.de", "goo.gl", "bing.com", "apple.com",
    "facebook.com", "instagram.com", "linkedin.com", "xing.com",
    "youtube.com", "tiktok.com", "pinterest.de", "pinterest.com",
    "provenexpert.com", "trustpilot.com", "trustedshops.de", "kununu.com",
    # Nachschlagewerke, Kammern, Verbände, Behörden, Verbraucherportale
    "wikipedia.org", "wikidata.org",
    "handwerkskammer.de", "hwk-koblenz.de", "zvshk.de", "zdh.de",
    "innung.de", "bdh-koeln.de", "waermepumpe.de",
    "verbraucherzentrale.de", "co2online.de", "energie-fachberater.de",
    "kfw.de", "bafa.de", "bund.de", "test.de", "stiftung-warentest.de",
    # Presse und Portale, die in Antworten regelmäßig als Beleg auftauchen
    "ndr.de", "wdr.de", "zdf.de", "ard.de", "spiegel.de", "faz.net",
    "handelsblatt.com", "haustec.de", "ikz.de", "sbz-online.de",
})


def _domain(roh: str) -> str:
    """`https://www.beispiel.de/x?y` → `beispiel.de`.

    Bewusst dieselbe Zerlegung wie in `ki_sichtbarkeit._domain_kern`: Zwei
    Zählweisen für dieselbe Adresse gingen irgendwann auseinander, und dann
    wäre die eigene Domain hier plötzlich ein Mitbewerber.
    """
    wert = (roh or "").strip().lower()
    wert = re.sub(r"^[a-z]+://", "", wert)
    wert = re.split(r"[/?#]", wert, maxsplit=1)[0]
    wert = wert.split("@")[-1].split(":")[0]
    return wert[4:] if wert.startswith("www.") else wert


def ist_verzeichnis(domain: str) -> bool:
    """Portal, Verzeichnis oder Nachschlagewerk — kein Betrieb.

    Unterdomains zählen mit: `branchenbuch.meinestadt.de` ist dasselbe Portal
    wie `meinestadt.de`.
    """
    if not domain:
        return False
    return any(domain == v or domain.endswith("." + v) for v in VERZEICHNISSE)


def _domains_einer_antwort(belege: Iterable) -> List[str]:
    """Die Adressen einer Antwort, jede höchstens einmal.

    Zwei Unterseiten desselben Betriebs sind **eine** Nennung. Sie doppelt zu
    zählen bevorzugte Betriebe mit vielen verlinkten Unterseiten.
    """
    gesehen = []
    for beleg in belege or []:
        domain = _domain(beleg if isinstance(beleg, str) else str(beleg))
        if domain and domain not in gesehen:
            gesehen.append(domain)
    return gesehen


def mitbewerber_ermitteln(befund: dict, domain: str = "") -> dict:
    """Wer taucht in den Quellen auf, außer dem Betrieb selbst?

    Ein Lauf ohne Erhebung bekommt **keine** Liste — auch keine leere. Sie
    läse sich wie „kein Wettbewerb genannt" und wäre dieselbe Verwechslung von
    „nicht erhoben" mit „Null", gegen die dieser Dienst gebaut ist. Eine leere
    Liste gibt es nur, wenn wirklich gefragt und nichts Fremdes zitiert wurde.
    """
    if not befund.get("collected"):
        return {"collected": False,
                "grund": befund.get("grund", "Nicht erhoben — kein Vergleich")}

    eigene = _domain(domain)

    treffer = {}          # domain → {"genannt_bei": int, "systeme": set}
    verzeichnisse = {}
    nicht_erhoben = []
    ausgewertet = 0

    for schluessel, block in (befund.get("anbieter") or {}).items():
        if not block.get("collected"):
            nicht_erhoben.append(schluessel)
            continue

        for antwort in block.get("fragen") or []:
            # Eine gescheiterte Frage ist keine Antwort. Sie darf den Nenner
            # nicht füllen, sonst sieht ein halber Lauf aus wie ein ganzer.
            if antwort.get("genannt") is None:
                continue
            ausgewertet += 1

            for gefunden in _domains_einer_antwort(antwort.get("belege")):
                if eigene and (gefunden == eigene
                               or gefunden.endswith("." + eigene)):
                    continue
                ziel = verzeichnisse if ist_verzeichnis(gefunden) else treffer
                eintrag = ziel.setdefault(
                    gefunden, {"genannt_bei": 0, "systeme": set()})
                eintrag["genannt_bei"] += 1
                eintrag["systeme"].add(schluessel)

    return {
        "collected": True,
        "grundlage": "Quellen der ausgewerteten Antworten, je Antwort "
                     "höchstens fünf — keine Namen aus dem Fließtext",
        "antworten_ausgewertet": ausgewertet,
        "mitbewerber": _sortiert(treffer),
        "verzeichnisse": _sortiert(verzeichnisse),
        "nicht_erhoben": sorted(nicht_erhoben),
    }


def _sortiert(roh: dict) -> List[dict]:
    """Häufigster zuerst; bei Gleichstand der breiter gestreute, dann die
    Adresse — damit zwei Läufe über denselben Daten dieselbe Reihenfolge
    ergeben und ein Verlaufsvergleich nicht auf Zufall beruht."""
    return [
        {"domain": d, "genannt_bei": w["genannt_bei"],
         "systeme": sorted(w["systeme"])}
        for d, w in sorted(
            roh.items(),
            key=lambda p: (-p[1]["genannt_bei"], -len(p[1]["systeme"]), p[0]))
    ]


def fuer_verlauf(wettbewerb) -> List[dict]:
    """Die drei häufigsten Mitbewerber, auf Adresse und Zahl eingedampft.

    Ohne Verlauf wäre der Vergleich wieder eine Momentaufnahme — genau der
    Befund, der L-85 aufgemacht hat. Mitgeführt wird nur, was die Frage
    „dieselben wie beim letzten Mal?" beantwortet: kein System, keine Quelle,
    kein Text. Die stehen im aktuellen Befund.
    """
    if not isinstance(wettbewerb, dict) or not wettbewerb.get("collected"):
        return []
    return [{"domain": m["domain"], "genannt_bei": m["genannt_bei"]}
            for m in wettbewerb.get("mitbewerber", [])[:VERLAUF_MITBEWERBER]]
