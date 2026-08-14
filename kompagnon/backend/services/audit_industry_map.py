"""Branchenklassen und die Zuordnung eines Freitextes auf eine Klasse.

Bewertungslogik „Homepage Standard 2026.2", § 2. Der Maßstab der
KI-Kriterien hängt an der Branche: Eine Steuerkanzlei ohne Preisrahmen ist
nicht schlechter als eine mit, sondern berufsrechtlich korrekt. Sie dafür
abzuwerten macht den Bericht als Akquiseinstrument unbrauchbar — derselbe
Effekt, den der Kandidatenauftritt am 14.08.2026 gezeigt hat.

**Das Modell erkennt, der Code entscheidet.** Das Modell meldet `branche` als
Freitext und `betriebsseite` als Ja/Nein; die Klasse fällt hier, nach fester
Tabelle. Der Grund ist die Wiederholbarkeit: Ein zweiter Modellaufruf könnte
dieselbe Website an zwei Tagen gegen zwei Maßstäbe laufen lassen, und ein
Standard, der das tut, ist keiner.

Was die Tabelle nicht kennt, wird vermerkt statt geraten — so wird sichtbar,
wo sie ergänzt gehört.
"""
import logging
from dataclasses import dataclass
from typing import Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Branchenklasse:
    """Eine der sechs Klassen aus § 2.2."""

    schluessel: str
    bezeichnung: str
    merkmal: str


KLASSEN = {
    "K1": Branchenklasse(
        "K1", "Lokaler Leistungsbetrieb",
        "Leistung wird beim Kunden oder vor Ort erbracht, mit Einzugsgebiet"),
    "K2": Branchenklasse(
        "K2", "Lokaler Beratungs- und Gesundheitsdienstleister",
        "Termin statt Auftrag, Qualifikation ist das Kaufargument, "
        "teils berufsrechtlich reglementiert"),
    "K3": Branchenklasse(
        "K3", "Lokaler Publikumsbetrieb",
        "Kunde kommt zum Anbieter, Öffnungszeiten und Sortiment entscheiden"),
    "K4": Branchenklasse(
        "K4", "Überregionaler Anbieter",
        "kein Einzugsgebiet, Leistung remote oder bundesweit"),
    "K5": Branchenklasse(
        "K5", "Onlineverkauf",
        "Vertragsschluss oder Zahlung findet auf der Website statt"),
    "K6": Branchenklasse(
        "K6", "Keine Betriebsseite",
        "kein Unternehmen, das über diese Seite Kunden gewinnt"),
}

# Reihenfolge ist die Entscheidungsreihenfolge: Was oben steht, gewinnt.
# K2 vor K1, weil „Steuerberatung für Handwerksbetriebe" eine Kanzlei ist und
# kein Handwerksbetrieb — das Stichwort der Zielgruppe darf die eigene Branche
# nicht überschreiben.
STICHWORTE: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("K6", (
        "verein", "partei", "kandidat", "kandidatur", "wahl", "blog",
        "stiftung", "kirche", "gemeinde", "behörde", "behoerde", "amt",
        "privatseite", "private seite", "privat", "hobby", "portfolio privat",
    )),
    ("K2", (
        "arzt", "ärzt", "aerzt", "praxis", "zahn", "physio", "heilpraktiker",
        "therapie", "psycholog", "hebamme", "tierarzt", "tierärzt",
        "anwalt", "anwält", "anwaelt", "kanzlei", "steuerberat", "notar",
        "wirtschaftsprüf", "wirtschaftspruef", "architekt", "ingenieurbüro",
        "ingenieurbuero", "sachverständ", "sachverstaend", "gutachter",
    )),
    ("K5", (
        "onlineshop", "online-shop", "webshop", "shop", "onlinehandel",
        "e-commerce", "ecommerce", "versandhandel", "versand",
    )),
    ("K3", (
        "restaurant", "gastronomie", "gasthaus", "gaststätte", "gaststaette",
        "café", "cafe", "bistro", "bäckerei", "baeckerei", "metzgerei",
        "hotel", "pension", "friseur", "frisör", "barbier", "kosmetik",
        "nagelstudio", "einzelhandel", "laden", "boutique", "fitness",
        "studio", "apotheke", "buchhandlung", "floristik", "blumen",
    )),
    ("K4", (
        "agentur", "beratung", "consulting", "unternehmensberat", "software",
        "it-dienstleist", "it-service", "edv", "coaching", "seminar",
        "personalvermittlung", "marketing", "webdesign", "b2b", "zulieferer",
    )),
    ("K1", (
        "heizung", "sanitär", "sanitaer", "shk", "klima", "lüftung",
        "lueftung", "elektro", "elektrik", "dach", "maler", "lackier",
        "zimmer", "tischler", "schreiner", "fliesen", "estrich", "putz",
        "stuck", "garten", "landschaftsbau", "kfz", "auto", "werkstatt",
        "schlosser", "metallbau", "bau", "handwerk", "montage", "reinigung",
        "gebäudereinigung", "gebaeudereinigung", "pflegedienst", "umzug",
        "schädlings", "schaedlings", "brunnen", "solar", "photovoltaik",
        "fenster", "türen", "tueren", "rollladen", "trockenbau", "gerüst",
        "geruest", "entsorgung", "schornstein", "kälte", "kaelte",
    )),
)

# Freitexte, für die keine Regel griff. Absichtlich im Speicher und nicht in
# der Datenbank: Die Liste dient dazu, die Tabelle zu ergänzen, nicht dazu,
# Verlauf zu führen.
nicht_zugeordnet: Set[str] = set()


@dataclass(frozen=True)
class Zuordnung:
    """Die Klasse und woher sie stammt — beides gehört in den Bericht."""

    klasse: str
    quelle: str  # "map" = Tabellentreffer, "rueckfall" = Regel aus § 2.3

    @property
    def bezeichnung(self) -> str:
        return KLASSEN[self.klasse].bezeichnung


def klasse_fuer_branche(branche: Optional[str], betriebsseite: bool) -> Zuordnung:
    """Bildet den erkannten Freitext auf genau eine Klasse ab.

    `betriebsseite=False` schlägt jedes Stichwort: Ein Blog über Dachdeckerei
    ist kein Dachdeckerbetrieb, und gegen dessen Maßstab gemessen entsteht
    genau der Bericht, den niemand ernst nimmt.
    """
    if not betriebsseite:
        return Zuordnung("K6", "map" if _trifft(branche, "K6") else "rueckfall")

    text = (branche or "").strip().lower()
    if text:
        for schluessel, stichworte in STICHWORTE:
            if any(wort in text for wort in stichworte):
                return Zuordnung(schluessel, "map")
        nicht_zugeordnet.add(text)
        logger.info(f"Branche ohne Zuordnung: {text!r} — als K1 bewertet")

    return Zuordnung("K1", "rueckfall")


def _trifft(branche: Optional[str], klasse: str) -> bool:
    text = (branche or "").strip().lower()
    if not text:
        return False
    for schluessel, stichworte in STICHWORTE:
        if schluessel == klasse:
            return any(wort in text for wort in stichworte)
    return False
