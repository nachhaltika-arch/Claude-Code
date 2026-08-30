"""Woraus ein Kriterium besteht — die Formen, nicht der Inhalt.

`Source`, `Stufe`, `Abstufung`, `Criterion`, `Category`: die Bauteile des
Kriterienkatalogs. Am 2026-08-30 aus `audit_criteria.py` herausgeloest
(L-25) — die Datei trug 998 Zeilen und darin drei Dinge auf einmal: **Form,
Inhalt und Rechnung**.

**Warum die Form zuerst ging.** Sie ist das einzige Stueck, das beide anderen
brauchen: Der Katalog schreibt `Criterion(...)`, das Rechnen liest
`crit.max_points`. Stuende sie beim Katalog, muesste das Rechnen den Katalog
importieren, um eine Form zu kennen — und ein Ringschluss waere nur noch eine
Frage der Zeit.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class Source(str, Enum):
    """Woher der Punktwert eines Kriteriums stammt."""

    MEASURED = "gemessen"        # deterministisch über HTTP, DOM oder API erhoben
    DERIVED = "abgeleitet"       # aus gemessenen Werten über feste Regeln berechnet
    AI = "einschaetzung"         # KI-Bewertung auf Screenshot/Text nach festem Rubric
    NOT_COLLECTED = "nicht_erhoben"  # Prüfung nicht möglich — zählt nicht in den Score
    # Gilt für diese Branchenklasse nicht. Zählt ebenfalls nicht, ist aber
    # etwas anderes als ein Ausfall: „konnte nicht geprüft werden" liest sich
    # wie ein Mangel unserer Prüfung, „gilt hier nicht" wie eine Einordnung.
    NOT_APPLICABLE = "nicht_anwendbar"


SOURCE_LABELS = {
    Source.MEASURED: "gemessen",
    Source.DERIVED: "abgeleitet",
    Source.AI: "KI-Einschätzung",
    Source.NOT_COLLECTED: "nicht erhoben",
    Source.NOT_APPLICABLE: "gilt für diese Branche nicht",
}


ABSTUFUNGSARTEN: Tuple[str, ...] = ("SCHWELLE", "JA_NEIN", "SUMME", "ANTEIL", "KI")


@dataclass(frozen=True)
class Stufe:
    """Eine Zeile der Punktabstufung eines Kriteriums.

    `grenze` ist der Zahlenwert, ab dem (bzw. bis zu dem) diese Punktzahl gilt.
    `None` heisst: Diese Stufe haengt an einer Bedingung, die sich nicht als
    Zahl ausdruecken laesst — sie steht dann ausschliesslich in `bedingung`.

    `bedingung` ist der Satz, der im Bericht UND im Buch erscheint. Beide lesen
    ihn von hier, damit sie nicht auseinanderlaufen koennen. Deshalb steht dort
    Fachsprache und kein Programmierkuerzel: nicht `perf >= 90`, sondern
    „Mobiler Gesamtwert 90 oder hoeher".
    """

    punkte: int
    grenze: Optional[float]
    bedingung: str


@dataclass(frozen=True)
class Abstufung:
    """Wie ein Kriterium seine Punkte vergibt — als Daten statt als Bedingung.

    Bis zum 25.08.2026 standen die Abstufungen in `audit_scoring.py` in zwei
    Formen nebeneinander: als lesbare Liste (`_tier`) und als Rechenanweisung
    mitten im Programmtext (`3 if perf >= 90 else ...`). Fuer einen Menschen
    sieht beides gleich aus, fuer ein Ausleseprogramm nicht — die zweite Form
    laesst sich nur verstehen, indem man sie ausfuehrt. Deshalb konnte das Buch
    seine Punktetabellen nicht aus dem Code beziehen und hat sie **plausibel
    konstruiert**. Ob sie stimmten, wusste niemand.

    Die fuenf Arten:

    | `SCHWELLE` | Grenzwerte, in der Reihenfolge der Stufen geprueft |
    | `JA_NEIN`  | erfuellt oder nicht                                |
    | `SUMME`    | mehrere Teilpruefungen, die sich addieren          |
    | `ANTEIL`   | ein Anteilswert wird auf die Punktzahl skaliert    |
    | `KI`       | Einschaetzung nach dem Rubric, keine Schwelle      |

    `richtung` gilt nur bei `SCHWELLE`: „ab" heisst, groesser ist besser
    (Mobilwert), „bis" heisst, kleiner ist besser (Ladezeit). Wer das
    verwechselt, druckt die Tabelle im Buch verkehrt herum und macht aus dem
    besten Wert den schlechtesten.
    """

    art: str
    richtung: str = "ab"
    stufen: Tuple[Stufe, ...] = ()

    @property
    def berechenbar(self) -> bool:
        """Laesst sich die Punktzahl allein aus einem Zahlenwert ableiten?

        Nur dann darf die Bewertung diese Abstufung ausrechnen. `si_ssl` etwa
        ist eine Staffel aus Bedingungen ohne Zahl („gueltig, laeuft aber bald
        ab") — sie steht hier als Daten fuer das Buch, gerechnet wird sie
        weiterhin im Programm.
        """
        if self.art != "SCHWELLE" or not self.stufen:
            return False
        return (all(s.grenze is not None for s in self.stufen[:-1])
                and self.stufen[-1].grenze is None)

    def punkte_fuer(self, wert: float) -> int:
        """Die Punktzahl fuer einen gemessenen Wert."""
        if not self.berechenbar:
            raise ValueError(
                "Diese Abstufung ist nicht aus einem Zahlenwert berechenbar; "
                "sie ist als Daten fuer das Buch hinterlegt."
            )
        for stufe in self.stufen:
            if stufe.grenze is None:
                return stufe.punkte
            if self.richtung == "ab" and wert >= stufe.grenze:
                return stufe.punkte
            if self.richtung == "bis" and wert < stufe.grenze:
                return stufe.punkte
        return 0


@dataclass(frozen=True)
class Criterion:
    """Ein einzelnes Prüfkriterium."""

    key: str
    label: str
    max_points: int
    source: Source          # geplante Erhebungsart im Bestfall
    hint: str = ""          # was konkret geprüft wird — erscheint im Report
    # **Die zweite Erhebungsart, falls es eine gibt (S2.2, 24.08.2026).**
    #
    # `rc_cookie` wird auf zwei Wegen erhoben: **gemessen**, wenn ein
    # Consent-Werkzeug erkannt wird — **abgeleitet**, wenn aus „keine
    # einwilligungspflichtigen Dienste" auf „kein Banner nötig" geschlossen
    # wird. Der Katalog nannte nur den ersten.
    #
    # Das ist kein Schönheitsfehler: Kapitel 3 verspricht dem Leser, dass jede
    # Erhebungsart gekennzeichnet ist und er einer **Einschätzung**
    # widersprechen kann. Wer im Bericht „abgeleitet" liest und im Katalog
    # „gemessen", kann sich auf keines von beidem verlassen.
    #
    # Die tatsächliche Erhebungsart je Lauf steht weiterhin im Bericht
    # (`sheet.sources`); dieses Feld sagt nur, was vorkommen **darf**.
    alt_source: Optional["Source"] = None
    # ── Was das Buch braucht (S5.5, S5.6, 24.08.2026) ───────────────────
    #
    # **Die Kennung.** Das Buch führt Kriterien als `L1`, `S3`, `E7` — und
    # nichts im Repo verband sie bisher mit einem Kriterium. Wer im Buch „E5"
    # liest und im Katalog nachsehen will, hatte keinen Weg dorthin.
    #
    # **Gespeichert und nicht abgeleitet.** Aus der Position ließe sie sich
    # errechnen (drittes Kriterium der Rechtskategorie = `L3`). Das wäre
    # bequem und gefährlich: Wer zwei Kriterien vertauscht, verschiebt
    # stillschweigend jede Buchreferenz. `tests/test_buch_kennungen.py` hält
    # fest, dass Kennung und Position zusammenpassen — wird umsortiert, wird
    # der Test rot und jemand entscheidet bewusst.
    buch_code: str = ""
    # **Die Bezeichnung fürs Buch**, wo der Katalog Fachjargon führt. „LCP
    # (Ladezeit Hauptinhalt)" ist ein Feldname, keine Überschrift. Leer heißt:
    # `label` genügt auch im Buch.
    buch_label: str = ""
    # **Das ausformulierte Punkterubric (A8, S8.2, 25.08.2026).**
    #
    # Nur die eingeschaetzten Kriterien haben eines. Bis heute bekam das
    # Modell je Kriterium **eine Zeile** aus Bezeichnung und Kurzhinweis —
    # „Wirkt das Layout zeitgemaess oder veraltet?" fuer drei Punkte. Was zwei
    # Punkte von einem unterscheidet, stand nirgends; das Modell entschied es
    # jedes Mal neu. Genau daran haengt A9: Ohne Rubric ist Wiederholbarkeit
    # nicht herstellbar, nur hoffbar.
    #
    # **Warum im Katalog und nicht im Prompt.** Kapitel 10 druckt die
    # Merkmale mit dem ausdruecklichen Vorbehalt, sie seien „meine
    # Zusammenstellung, nicht aus dem Code extrahiert". Steht das Rubric hier,
    # faellt der Vorbehalt weg: Das Buch druckt dann, was tatsaechlich
    # bewertet wird.
    #
    # **Die Zeile „Nicht Teil dieses Kriteriums" ist kein Beiwerk.**
    # BEFUND-C3 fuehrt vier Verdachtsfaelle auf Doppelwertung, die
    # unpruefbar blieben, weil die eingeschaetzten Kriterien keine Feldliste
    # hatten. Mit der Abgrenzung sind sie pruefbar.
    rubric: str = ""
    # **Die Punktabstufung als Daten (BUCH-F1, 25.08.2026).**
    #
    # Sie steht hier und nicht in `audit_scoring.py`, weil das Buch sie drucken
    # muss und ein Ausleseprogramm eine Rechenanweisung nicht lesen kann. Wo sie
    # berechenbar ist, holt die Bewertung sie sich von hier — damit stehen die
    # Zahlen nur noch an einer Stelle.
    abstufung: Optional["Abstufung"] = None

    @property
    def buch_name(self) -> str:
        """Was im Buch steht — die eigene Bezeichnung oder ersatzweise `label`."""
        return self.buch_label or self.label
    # Zwei Voraussetzungen, an denen die Anwendbarkeit je Branchenklasse hängt
    # (Bewertungslogik 2026.2, § 2.4). Sie stehen am Kriterium und nicht in
    # einer Klassentabelle, weil es Eigenschaften des Kriteriums sind: Eine
    # neue Klasse erbt die Regel dann von selbst.
    #
    # Setzt einen Betrieb voraus, der über die Website Kunden gewinnen will.
    # Steht dahinter kein Betrieb — ein politischer Auftritt, ein Verein, ein
    # privates Projekt —, dann gibt es kein Angebot und keine Leistungsseiten.
    # Das ist kein Mangel der Seite, sondern ein Maßstab, der nicht passt.
    assumes_business: bool = False
    # Setzt ein Einzugsgebiet voraus. Ein bundesweit arbeitender Anbieter ohne
    # Ortsbezug ist nicht schlechter auffindbar, sondern anders — ihm einen
    # fehlenden Ortsbezug vorzuhalten misst am falschen Ziel.
    assumes_local: bool = False

    @property
    def is_scored(self) -> bool:
        return self.max_points > 0


@dataclass(frozen=True)
class Category:
    """Eine Kriteriengruppe."""

    key: str
    label: str
    criteria: Tuple[Criterion, ...]
    # ── Was das Buch braucht (S5.5, 24.08.2026) ─────────────────────────
    #
    # Dieselbe Begründung wie beim Kriterium: `standard-export-prototyp.py`
    # führte `BUCHTITEL` und `KAPITEL` als eigene Tabellen und vermerkte
    # selbst, dass sie dort eine **zweite Wahrheit** sind. Jetzt stehen sie
    # am Gegenstand.
    buch_label: str = ""      # deutsche Überschrift im Buch
    buch_kapitel: int = 0     # in welchem Kapitel die Kategorie steht

    @property
    def buch_name(self) -> str:
        return self.buch_label or self.label

    @property
    def max_points(self) -> int:
        """Immer aus den Kriterien abgeleitet — kein manueller Deckel.

        Der frühere Code deckelte 'Inhalt & Nutzererfahrung' auf 5, obwohl die
        Kategorie sechs Kriterien à 1 Punkt hatte. Ein Kriterium war dadurch
        strukturell wertlos. Eine abgeleitete Obergrenze macht das unmöglich.
        """
        return sum(c.max_points for c in self.criteria)


