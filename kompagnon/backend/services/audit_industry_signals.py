"""Woran eine Klasse erkennbar ist — die messbare Seite von `PROFILE`.

`audit_industry_profiles` sagt in Prosa, wogegen eine Branchenklasse gemessen
wird; das Modell liest das. Hier stehen dieselben Erwartungen als Stichworte,
damit auch die **gemessenen** Kriterien den Maßstab der Klasse anlegen. Ohne
das war der Bericht seit dem 14.08.2026 in der richtigen Sprache geschrieben
und weiter falsch gerechnet: Ein Ingenieurbüro verlor Punkte bei
„Eigene Leistungsseiten", weil die Suche nach `wärmepumpe`, `wallbox` und
`sanitär` lief, und bei „Vertrauenssignale", weil sie `meisterbetrieb`,
`innung` und `handwerkskammer` erwartete. Beides kann ein Ingenieurbüro nicht
haben — abgewertet wurde es dafür trotzdem.

**Die Erhebung sammelt, die Bewertung entscheidet.** Die Klasse steht erst
fest, wenn das Modell die Seite gesehen hat — also nach der Erhebung. Die
Collector suchen deshalb nach `alle_begriffe()`, dem Verband aller Klassen, und
merken sich, welche Begriffe getroffen haben. Welcher Treffer zählt, entscheidet
`audit_scoring` später mit `begriffe(gruppe, klasse)`.

Die Basisbegriffe gelten in jeder Klasse. Was klassenspezifisch dazukommt, ist
bewusst knapp gehalten: Jeder Begriff, der zu weit greift, macht denselben
Fehler wie die Gewerkeschätzung im Scraper — „installation" traf dort jede
zweite deutsche Seite.
"""
from typing import Dict, Tuple

# ── Eigene Leistungsseiten (I1) ────────────────────────────────────────
# Basis: wie eine Navigation Leistungen benennt, unabhängig von der Branche.
BASIS_LEISTUNGSSEITEN: Tuple[str, ...] = (
    "leistung", "service", "angebot", "produkte", "lösungen", "loesungen",
    "portfolio", "was-wir", "was wir",
)

LEISTUNGSSEITEN: Dict[str, Tuple[str, ...]] = {
    "K1": ("wärmepumpe", "waermepumpe", "wallbox", "heizung", "sanitär",
           "sanitaer", "bad", "elektro", "photovoltaik", "solar", "klima",
           "lüftung", "lueftung", "notdienst", "wartung", "dach", "fenster",
           "garten", "reinigung", "montage", "reparatur", "sanierung"),
    "K2": ("fachgebiet", "rechtsgebiet", "behandlung", "therapie", "gutachten",
           "beratung", "mandat", "sprechstunde", "diagnostik", "planung",
           "prüfung", "pruefung", "zertifizierung", "bilanz", "bericht",
           "schwerpunkt"),
    "K3": ("sortiment", "speisekarte", "karte", "menü", "menue", "reservierung",
           "öffnungszeiten", "oeffnungszeiten", "zimmer", "kurse", "anwendungen"),
    "K4": ("modul", "plattform", "consulting", "workshop", "schulung",
           "fallstudie", "case", "referenzen", "branchen", "software"),
    "K5": ("shop", "kategorie", "kollektion", "sortiment", "versand",
           "bestellen", "marken"),
    # K6 fehlt bewusst: Ohne Betrieb gilt das Kriterium nicht (assumes_business).
}

# ── Vertrauenssignale (C4), Untergruppe Zertifikate ────────────────────
# Die übrigen vier Untergruppen — Bewertungen, Referenzen, Team, Garantie —
# sind klassenunabhängig und stehen weiter in `audit_collectors.TRUST_PATTERNS`.
# Nur der Nachweis der Befähigung heißt in jeder Branche anders.
BASIS_ZERTIFIKATE: Tuple[str, ...] = (
    "zertifiziert", "zertifikat", "ausgezeichnet", "geprüft", "geprueft",
    "mitglied",
)

ZERTIFIKATE: Dict[str, Tuple[str, ...]] = {
    "K1": ("meisterbetrieb", "meisterbrief", "innung", "handwerkskammer",
           "fachbetrieb", "sachkundenachweis", "tüv", "tuev"),
    "K2": ("kammer", "approbation", "zugelassen", "akkreditiert", "fachanwalt",
           "fachärzt", "faechaerzt", "fachaerzt", "öffentlich bestellt",
           "oeffentlich bestellt", "vereidigt", "sachverständig",
           "sachverstaendig"),
    "K3": ("auszeichnung", "siegel", "hygiene", "mitgliedschaft", "haube",
           "stern"),
    "K4": ("iso 9001", "iso 27001", "iso 14001", "certified", "akkreditiert",
           "partnerstatus", "referenzkunden"),
    "K5": ("trusted shops", "käufersiegel", "kaeufersiegel", "gütesiegel",
           "guetesiegel", "ehi", "sicheres einkaufen"),
}

# ── Primär-CTA (C2) ────────────────────────────────────────────────────
BASIS_CTA: Tuple[str, ...] = (
    "termin", "angebot", "anfrage", "beratung", "kontakt", "rückruf",
    "rueckruf", "jetzt", "kostenlos", "unverbindlich", "anfordern",
    "vereinbaren",
)

CTA: Dict[str, Tuple[str, ...]] = {
    "K1": ("notdienst", "vor ort", "besichtigung"),
    "K2": ("erstgespräch", "erstgespraech", "sprechstunde", "termin buchen"),
    "K3": ("reservieren", "reservierung", "tisch", "buchen", "anfahrt"),
    "K4": ("demo", "whitepaper", "erstgespräch", "erstgespraech", "case study"),
    "K5": ("warenkorb", "kaufen", "bestellen", "shoppen"),
}

_GRUPPEN: Dict[str, Tuple[Tuple[str, ...], Dict[str, Tuple[str, ...]]]] = {
    "leistungsseiten": (BASIS_LEISTUNGSSEITEN, LEISTUNGSSEITEN),
    "zertifikate": (BASIS_ZERTIFIKATE, ZERTIFIKATE),
    "cta": (BASIS_CTA, CTA),
}


def begriffe(gruppe: str, klasse: str) -> Tuple[str, ...]:
    """Was in dieser Klasse zählt — Basis plus das Eigene der Klasse.

    Ohne Klasse (Altbestand, fehlgeschlagene Erkennung) gilt der Verband aller
    Klassen: Lieber großzügig zählen als einem Betrieb etwas abziehen, das wir
    nur deshalb nicht suchen, weil wir ihn nicht einordnen konnten.
    """
    basis, je_klasse = _GRUPPEN[gruppe]
    if not klasse:
        return alle_begriffe(gruppe)
    return basis + je_klasse.get(klasse, ())


def alle_begriffe(gruppe: str) -> Tuple[str, ...]:
    """Der Verband aller Klassen — wonach die Erhebung sucht."""
    basis, je_klasse = _GRUPPEN[gruppe]
    gesehen = list(basis)
    for begriffe_der_klasse in je_klasse.values():
        gesehen.extend(b for b in begriffe_der_klasse if b not in gesehen)
    return tuple(gesehen)


def treffer(text: str, gruppe: str) -> Tuple[str, ...]:
    """Welche Begriffe dieser Gruppe im Text vorkommen — in Kleinschreibung."""
    unten = (text or "").lower()
    return tuple(b for b in alle_begriffe(gruppe) if b in unten)


def zaehlt_in_klasse(gefunden, gruppe: str, klasse: str) -> bool:
    """Ist mindestens ein gefundener Begriff für diese Klasse einschlägig?"""
    gueltig = set(begriffe(gruppe, klasse))
    return any(b in gueltig for b in gefunden or ())
