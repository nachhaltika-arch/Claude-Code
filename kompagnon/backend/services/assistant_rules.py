"""Das Regelwerk des Projekt-Assistenten — was eine gute Antwort ausmacht.

Entscheidung 3.3 aus `docs/projekt-assistent-anforderungen.md`: Wissensbasis
sind die Projektdaten plus ein gepflegtes Regelwerk. Keine Vektordatenbank, kein
Index — dafür explizite Maßstäbe, die man lesen, prüfen und ändern kann.

Die Beispiele stammen aus `docs/conversion-spec-shk.md` und der Nische aus
Phase 1 (Heizung, Sanitär, Elektrik). Sie sind bewusst konkret: „Wärmepumpe,
Bad-Sanierung, Notdienst" ist eine Antwort, „Wir bieten alles rund ums Wasser"
ist keine.

Zwei Dinge macht dieses Modul:

* Es liefert dem Prompt **je Feld** einen Maßstab statt einer allgemeinen Bitte
  um Qualität.
* Es prüft eine Antwort **ohne Modell** auf die Dinge, die man zählen kann —
  Länge, Floskeln, fehlende Konkretheit. Was gezählt werden kann, muss kein
  Modell kosten.
"""
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Worthülsen, die in fast jedem Handwerker-Briefing auftauchen und nichts
# aussagen. Die Liste ist bewusst kurz und belegbar — nicht jede Floskel der
# Welt, sondern die, die hier wirklich vorkommen.
FLOSKELN = (
    "alles rund um", "aus einer hand", "kompetent und zuverlässig",
    "qualität und service", "ihr partner", "seit jahren", "modernste technik",
    "höchste qualität", "zu ihrer vollsten zufriedenheit", "rundum-sorglos",
    "wir sind für sie da", "alles was das herz begehrt",
)


@dataclass(frozen=True)
class Feldregel:
    """Der Maßstab für ein Briefing-Feld."""

    feld: str
    frage: str                  # was das Feld eigentlich wissen will
    warum: str                  # wofür die Antwort später gebraucht wird
    mindestzeichen: int
    gut: str
    schlecht: str
    braucht_zahl: bool = False  # eine gute Antwort enthält eine Zahl/Menge
    # Antworten, die für sich genommen nichts aussagen. Länge hilft hier nicht:
    # „SHK" ist kurz und gut, „Handwerk" ist länger und leer. Verglichen wird
    # die **ganze** Antwort — in einem längeren Satz darf das Wort vorkommen.
    zu_allgemein: Tuple[str, ...] = ()


REGELN: Tuple[Feldregel, ...] = (
    Feldregel(
        feld="gewerk",
        frage="Welches Handwerk übt der Betrieb aus?",
        warum="bestimmt Vokabular, Beispiele und Referenzen auf der ganzen Seite",
        mindestzeichen=6,
        gut="Sanitär, Heizung, Klima — Schwerpunkt Wärmepumpe",
        schlecht="Handwerk",
        zu_allgemein=("handwerk", "verschiedenes", "diverses", "alles"),
    ),
    Feldregel(
        feld="leistungen",
        frage="Was genau wird angeboten — einzeln benannt?",
        warum="wird zu den Leistungsseiten und entscheidet über die Auffindbarkeit",
        mindestzeichen=40,
        gut="Wärmepumpen (Luft/Wasser), Bad-Sanierung barrierefrei, "
            "Heizungswartung, 24h-Notdienst bei Rohrbruch",
        schlecht="Alles rund ums Wasser",
        zu_allgemein=("alles rund ums wasser", "alles", "diverses"),
    ),
    Feldregel(
        feld="einzugsgebiet",
        frage="Welche Orte werden bedient?",
        warum="jeder genannte Ort wird zu einem lokalen Suchbegriff",
        mindestzeichen=15,
        gut="Koblenz, Andernach, Neuwied, Mayen — 50 km Umkreis",
        schlecht="Region",
        zu_allgemein=("region", "deutschland", "umgebung", "überall", "bundesweit"),
        braucht_zahl=False,
    ),
    Feldregel(
        feld="usp",
        frage="Was kann dieser Betrieb, was der Nachbarbetrieb nicht kann?",
        warum="trägt den Hero und entscheidet, ob jemand anruft",
        mindestzeichen=30,
        gut="Meisterbetrieb in dritter Generation, Notdienst in 90 Minuten, "
            "Förderantrag übernehmen wir komplett",
        schlecht="Qualität und Service",
        zu_allgemein=("qualität und service", "gute arbeit", "erfahrung"),
    ),
    Feldregel(
        feld="typischer_kunde",
        frage="Wer ruft an — Alter, Wohnsituation, Anlass?",
        warum="bestimmt Ansprache, Schriftgröße und Kontaktweg",
        mindestzeichen=20,
        gut="Hausbesitzer 55+, Einfamilienhaus Baujahr 1960–1990, "
            "Heizung defekt oder Förderung im Blick",
        schlecht="Privatkunden",
        zu_allgemein=("privatkunden", "jeder", "alle", "hausbesitzer"),
    ),
    Feldregel(
        feld="haeufige_anfrage",
        frage="Womit kommen die meisten Anrufer?",
        warum="wird zur ersten Frage im FAQ und oft zum Hauptthema der Startseite",
        mindestzeichen=20,
        gut="Was kostet eine Wärmepumpe im Altbau und wie viel Förderung gibt es?",
        schlecht="Verschiedenes",
        zu_allgemein=("verschiedenes", "alles mögliche", "unterschiedlich"),
    ),
    Feldregel(
        feld="hauptziel",
        frage="Was soll die Website erreichen — messbar?",
        warum="bestimmt, worauf jede Seite hinführt",
        mindestzeichen=15,
        gut="Mehr qualifizierte Anfragen für Wärmepumpen — Ziel 10 pro Monat",
        schlecht="Bekannter werden",
        zu_allgemein=("bekannter werden", "mehr umsatz", "präsenz zeigen"),
    ),
    Feldregel(
        feld="aktionen",
        frage="Was soll der Besucher konkret tun?",
        warum="wird zum primären Handlungsaufruf auf jeder Seite",
        mindestzeichen=10,
        gut="Anrufen oder Vor-Ort-Termin über das Formular anfragen",
        schlecht="Kontakt aufnehmen",
        zu_allgemein=("kontakt aufnehmen", "melden", "sich informieren"),
    ),
    Feldregel(
        feld="stil",
        frage="Wie soll die Seite wirken?",
        warum="bestimmt Farben, Schrift und Bildsprache im Style-Guide",
        mindestzeichen=10,
        gut="Bodenständig und aufgeräumt, kein Hochglanz — große Schrift für "
            "ältere Kunden",
        schlecht="Modern",
        zu_allgemein=("modern", "schön", "ansprechend", "seriös"),
    ),
)

NACH_FELD: Dict[str, Feldregel] = {r.feld: r for r in REGELN}

ZAHL = re.compile(r"\d")


@dataclass(frozen=True)
class Befund:
    """Das Ergebnis einer Prüfung ohne Modell."""

    feld: str
    brauchbar: bool
    hinweise: List[str]

    @property
    def als_text(self) -> str:
        return " ".join(self.hinweise)


def pruefe_antwort(feld: str, antwort: Optional[str]) -> Befund:
    """Was sich zählen lässt, prüft der Code — nicht das Modell.

    Absicht: Der Assistent soll nicht für jede leere Eingabe einen Aufruf
    kosten. Erst wenn eine Antwort formal brauchbar ist, lohnt sich die
    inhaltliche Bewertung durch das Modell.
    """
    regel = NACH_FELD.get(feld)
    text = (antwort or "").strip()

    if regel is None:
        # Unbekanntes Feld: nichts zu prüfen, aber auch nichts zu behaupten.
        return Befund(feld, bool(text), [] if text else ["Noch nichts eingetragen."])

    hinweise: List[str] = []
    if not text:
        return Befund(feld, False, [f"Noch nichts eingetragen. {regel.frage}"])

    if len(text) < regel.mindestzeichen:
        hinweise.append(
            f"Das ist noch sehr knapp. {regel.frage} "
            f"Zum Vergleich: „{regel.gut}“")

    tief = text.lower()
    if tief.strip(" .!") in regel.zu_allgemein:
        hinweise.append(
            f"„{text}“ trifft auf fast jeden Betrieb zu. {regel.frage} "
            f"Zum Vergleich: „{regel.gut}“")

    gefundene = [f for f in FLOSKELN if f in tief]
    if gefundene:
        hinweise.append(
            f"„{gefundene[0]}“ sagt über diesen Betrieb nichts, was nicht über "
            f"jeden anderen auch gilt. Was davon stimmt nur hier?")

    if regel.braucht_zahl and not ZAHL.search(text):
        hinweise.append("Eine Zahl macht es überprüfbar — Menge, Umkreis oder Zeit.")

    return Befund(feld, not hinweise, hinweise)


def regelwerk_fuer_prompt(felder: Optional[List[str]] = None) -> str:
    """Der Maßstab, wie ihn das Modell zu sehen bekommt."""
    ausgewaehlt = [NACH_FELD[f] for f in felder if f in NACH_FELD] if felder else REGELN
    if not ausgewaehlt:
        return ""
    zeilen = []
    for r in ausgewaehlt:
        zeilen.append(
            f"- **{r.feld}** — {r.frage} (wofür: {r.warum})\n"
            f"  gut:      {r.gut}\n"
            f"  schlecht: {r.schlecht}")
    return "\n".join(zeilen)
