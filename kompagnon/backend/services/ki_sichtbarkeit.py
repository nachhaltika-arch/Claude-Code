"""Nennt eine KI den Betrieb, wenn jemand nach seiner Leistung fragt? (L-58 b)

**Der Unterschied zu `se_ki_lesbar`.** Das Kriterium im Audit misst seit dem
21.08.2026 die **Lesbarkeit**: kein KI-Crawler ausgesperrt, `llms.txt`
vorhanden. Das ist die Voraussetzung. Ob ein Suchender, der eine KI fragt,
diesen Betrieb genannt bekommt, steht auf einem anderen Blatt — und genau das
misst dieser Dienst.

**Was gefragt wird.** Jedes angebundene System (`services/ki_anbieter.py`:
ChatGPT, Perplexity, Claude) bekommt dieselben Fragen, die ein Kunde stellt:
„Wer bietet Heizung in Kassel an?" Dann wird nachgesehen, ob der Betrieb in
der Antwort oder unter den herangezogenen Quellen auftaucht.

**Die Regel, die alles traegt — aus D1 (Audit, 11.08.2026).** Ein Anbieter
ohne Schluessel wird ausgewiesen, nicht geraten: Er steht mit
`collected: False` und seinem fehlenden Schluessel im Ergebnis und **ohne
jede Zahl**, die jemand als Null lesen koennte. „Perplexity: 0 von 5" bei
einem Betrieb, den wir dort nie gefragt haben, waere eine Behauptung, die ihn
Geld kostet.

**Die Fragen sind fest und nicht von einem Modell erzeugt.** Zwei Laeufe
sollen dasselbe messen — sonst ist der Vergleich zwischen gestern und heute
keiner, und genau der ist das Produkt.

**Warum das nichts am Score aendert.** Jeder Lauf kostet Geld. Ein kostenloses
Audit mit einer Kostenstelle je Aufruf ist ein anderes Produkt als eines ohne;
diese Entscheidung ist offen und gehoert David. Bis dahin haengt hier kein
Kriterium und kein Punkt.
"""
import logging
import re
from typing import List, Optional

from services.ki_anbieter import ANBIETER, konfigurierte_anbieter
from services.ki_wettbewerb import fuer_verlauf, mitbewerber_ermitteln

logger = logging.getLogger(__name__)

#: Was jeder Befund mitfuehrt. Ohne diesen Satz liest jemand ein
#: Claude-Ergebnis als Aussage ueber ChatGPT.
HINWEIS = ("Gemessen mit eingeschalteter Websuche, je System einzeln. "
           "Ein System ohne hinterlegten Zugang wird nicht gefragt und nicht "
           "gewertet — es erscheint als „nicht erhoben“, nie als Null.")

#: Hoechstens so viele Fragen je Lauf. Jede kostet.
MAX_FRAGEN = 5

#: Woerter, die in fast jedem Firmennamen stehen. Ein Treffer allein auf
#: „GmbH" wuerde jede zweite Antwort als Nennung zaehlen.
ALLERWELTSWOERTER = frozenset({
    "gmbh", "ug", "kg", "ohg", "ag", "co", "gbr", "e", "k", "mbh",
    "und", "sohn", "soehne", "söhne", "gebr", "gebrueder", "gebrüder",
    "meisterbetrieb", "fachbetrieb", "service", "gruppe", "team",
    "heizung", "sanitaer", "sanitär", "elektro", "elektrik", "bad", "haus",
})

#: Die Fragen, die ein Kunde stellt. Bewusst fest und nicht von einem Modell
#: erzeugt: Zwei Laeufe sollen dasselbe messen, sonst ist der Vergleich
#: zwischen gestern und heute keiner.
FRAGE_VORLAGEN = (
    "Wer bietet {gewerk} in {ort} an? Nenne konkrete Betriebe mit Namen.",
    "Ich suche einen zuverlässigen Betrieb für {gewerk} in {ort}. Welche gibt es?",
    "Welche Firmen für {gewerk} in {ort} und Umgebung werden empfohlen?",
    "{gewerk} {ort}: Welche Anbieter gibt es dort, mit Website?",
    "Ich brauche kurzfristig jemanden für {gewerk} in {ort}. Wen kann ich anrufen?",
)


def baue_fragen(gewerk: str, ort: str, max_fragen: int = MAX_FRAGEN) -> List[str]:
    """Die Fragen fuer einen Betrieb — oder keine.

    Ohne Gewerk oder ohne Ort wird **nicht** geraten: Eine Frage nach einem
    erfundenen Ort misst die Sichtbarkeit an einem Markt, in dem der Betrieb
    gar nicht arbeitet, und das Ergebnis waere schlechter als die Wahrheit.
    """
    gewerk = (gewerk or "").strip()
    ort = (ort or "").strip()
    if not gewerk or not ort:
        return []

    return [v.format(gewerk=gewerk, ort=ort) for v in FRAGE_VORLAGEN[:max_fragen]]


def _domain_kern(domain: str) -> str:
    """`https://www.beispiel.de/x` → `beispiel.de`."""
    roh = (domain or "").strip().lower()
    roh = re.sub(r"^https?://", "", roh)
    roh = roh.split("/")[0]
    return roh[4:] if roh.startswith("www.") else roh


def _namensteile(name: str) -> List[str]:
    """Die kennzeichnenden Woerter eines Firmennamens.

    „Mustermann Heizung GmbH" → `["mustermann"]`. Uebrig bleibt, was den
    Betrieb von seinen Nachbarn unterscheidet.
    """
    woerter = re.findall(r"[\wäöüß]+", (name or "").lower())
    return [w for w in woerter if len(w) > 3 and w not in ALLERWELTSWOERTER]


def ist_genannt(antwort: str, belege, domain: str, name: str) -> bool:
    """Kommt dieser Betrieb in Antwort oder Quellen vor?

    Zwei Wege, und der erste ist der harte: Steht die eigene Adresse unter den
    Quellen, hat die Suche sie wirklich herangezogen. Der zweite ist der
    Name im Text — eine Nennung ohne Link ist auch eine Nennung.
    """
    kern = _domain_kern(domain)
    text = (antwort or "").lower()

    if kern:
        for beleg in belege or []:
            if kern in _domain_kern(beleg):
                return True
        if kern in text:
            return True

    teile = _namensteile(name)
    return bool(teile) and all(t in text for t in teile)


def _fehlertext(fehler: Exception) -> str:
    """Ein Fehler muss sagen, welcher er war — auch wenn er selbst schweigt.

    **Gemessen am 31.08.2026:** `str(httpx.ReadTimeout())` ist die **leere**
    Zeichenkette. Im Bericht stand dann „✗ Fehler: " ohne Text — und ein
    Befund ohne Inhalt ist schlimmer als keiner, weil er nach einem aussieht.
    Perplexity braucht fuer eine Frage gemessene 15 bis 24 Sekunden; eine
    Zeitueberschreitung ist hier also der wahrscheinlichste Fall und
    ausgerechnet der stumme.

    Der Name der Ausnahme steht deshalb immer davor. Er ist die Angabe, die
    ohne Zutun stimmt.
    """
    art = type(fehler).__name__
    text = str(fehler).strip()
    return f"{art}: {text}"[:200] if text else art


async def _eine_frage(anbieter, frage: str, domain: str, name: str) -> dict:
    """Eine Frage an einen Anbieter. Wirft nie."""
    try:
        text, belege = await anbieter.frage_stellen(frage)
    except Exception as fehler:  # noqa: BLE001
        beschreibung = _fehlertext(fehler)
        logger.warning("KI-Sichtbarkeit %s: Frage gescheitert (%s)",
                       anbieter.schluessel, beschreibung)
        return {"frage": frage, "genannt": None, "fehler": beschreibung,
                "belege": []}

    return {
        "frage": frage,
        "genannt": ist_genannt(text, belege, domain, name),
        "belege": list(belege)[:5],
        "auszug": (text or "")[:400],
    }


async def _ein_anbieter(anbieter, fragen, domain, name) -> dict:
    """Alle Fragen an ein System — und was dabei herauskam."""
    ergebnisse = [await _eine_frage(anbieter, f, domain, name) for f in fragen]

    beantwortet = [e for e in ergebnisse if e["genannt"] is not None]
    genannt = [e for e in beantwortet if e["genannt"]]

    return {
        "collected": True,
        "anzeige": anbieter.anzeige,
        "modell": anbieter.modell,
        "fragen": ergebnisse,
        "von": len(fragen),
        "beantwortet": len(beantwortet),
        "genannt_bei": len(genannt),
        "fehler": len(ergebnisse) - len(beantwortet),
        "quote": round(len(genannt) / len(beantwortet), 2) if beantwortet else None,
    }


async def pruefe_ki_sichtbarkeit(
    name: str = "",
    domain: str = "",
    gewerk: str = "",
    ort: str = "",
    max_fragen: int = MAX_FRAGEN,
    anbieter: Optional[List] = None,
) -> dict:
    """Fragt jedes angebundene KI-System nach dem Betrieb. Wirft nie.

    Ein Ausfall darf nie wie ein schlechtes Ergebnis aussehen: „nicht erhoben"
    und „nicht gefunden" sind zwei verschiedene Nachrichten, und die zweite
    kostet den Betrieb Geld. Deshalb steht jeder nicht angebundene Anbieter
    mit `collected: False` und seinem fehlenden Schluessel im Ergebnis — und
    **ohne** Zahl, die jemand als Null lesen koennte.
    """
    fragen = baue_fragen(gewerk, ort, max_fragen)
    if not fragen:
        return {"collected": False, "hinweis": HINWEIS,
                "grund": "Gewerk oder Ort fehlt — ohne beides misst die Frage nichts"}

    gewaehlt = anbieter if anbieter is not None else konfigurierte_anbieter()

    befunde = {}
    for a in ANBIETER:
        if not any(g.schluessel == a.schluessel for g in gewaehlt):
            befunde[a.schluessel] = {
                "collected": False,
                "anzeige": a.anzeige,
                "grund": f"{a.env_name} nicht gesetzt — nicht gefragt, nicht gewertet",
            }
    for a in gewaehlt:
        befunde[a.schluessel] = await _ein_anbieter(a, fragen, domain, name)

    erhoben = [b for b in befunde.values() if b.get("collected")]
    if not erhoben:
        fehlend = ", ".join(a.env_name for a in ANBIETER)
        return {"collected": False, "hinweis": HINWEIS, "anbieter": befunde,
                "grund": f"Kein KI-Zugang konfiguriert. Erwartet: {fehlend}"}

    befund = {
        "collected": True,
        "hinweis": HINWEIS,
        "fragen_gestellt": len(fragen),
        "anbieter": befunde,
        "erhoben_bei": len(erhoben),
        "genannt_bei": sum(1 for b in erhoben if b.get("genannt_bei", 0) > 0),
    }
    # Wer wird stattdessen genannt (L-85, zweite Haelfte). Hier und nicht
    # beim Aufrufer: Sonst muesste jede Stelle, die misst, daran denken —
    # und die naechste vergisst es. Rein rechnerisch, kein weiterer Aufruf.
    befund["wettbewerb"] = mitbewerber_ermitteln(befund, domain)
    return befund


#: Wie viele Laeufe der Verlauf haelt. Ein Verlauf, der unbegrenzt waechst,
#: ist kein Verlauf, sondern ein Leck: Die Spalte wird bei jedem Lesen der
#: GEO-Analyse mitgeladen. Fuenfzig reichen fuer Jahre — der Lauf kostet
#: Geld und findet nicht taeglich statt.
VERLAUF_MAX = 50


def verlaufseintrag(befund: dict, am: str) -> dict:
    """Ein Lauf, auf das eingedampft, was ihn vergleichbar macht.

    **Was hineingeht:** je System die Trefferzahl und die drei haeufigsten
    Mitbewerber (nur Adresse und Zahl). **Was nicht:** die Antworttexte und
    die Belege. Die stehen im aktuellen Befund; im Verlauf
    machten sie die Spalte in einem Jahr unlesbar und beantworten die Frage
    nicht, die der Verlauf stellt — „mehr oder weniger als beim letzten Mal?"

    **Nicht erhobene Systeme stehen nicht mit Null darin.** Sonst zeigte die
    Kurve spaeter einen Einbruch, den es nie gab, nur weil ein Schluessel
    fehlte. Sie stehen unter `nicht_erhoben`, damit die Luecke sichtbar
    bleibt, statt als Ergebnis gelesen zu werden.
    """
    gemessen, offen = {}, []
    for schluessel, block in (befund.get("anbieter") or {}).items():
        if not block.get("collected"):
            offen.append(schluessel)
            continue
        gemessen[schluessel] = {
            "genannt_bei": block.get("genannt_bei", 0),
            "von": block.get("von", 0),
            "quote": block.get("quote"),
        }

    return {"am": am, "anbieter": gemessen, "nicht_erhoben": sorted(offen),
            "mitbewerber": fuer_verlauf(befund.get("wettbewerb"))}


def verlauf_fortschreiben(bestand, befund: dict, am: str) -> list:
    """Haengt einen Lauf an — und ersetzt ihn nicht.

    Das ist der ganze Befund von L-85: `ki_sichtbarkeit` hielt genau einen
    Stand, und der Wert der Messung entsteht erst aus dem Vergleich.

    Ein Lauf ohne jeden Zugang wird **nicht** vermerkt: Er hat nichts
    gemessen, und ein leerer Punkt in der Kurve laese sich nicht von einem
    schlechten Ergebnis unterscheiden.
    """
    # Die Spalte ist JSONB und kann alles enthalten, was einmal
    # hineingeschrieben wurde — auch etwas, das keine Liste ist.
    verlauf = list(bestand) if isinstance(bestand, list) else []

    if not befund.get("collected"):
        return verlauf

    verlauf.append(verlaufseintrag(befund, am))
    return verlauf[-VERLAUF_MAX:]
