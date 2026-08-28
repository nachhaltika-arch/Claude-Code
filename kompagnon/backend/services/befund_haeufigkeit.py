"""Wie oft die zwanzig Befunde aus Kapitel 14 tatsächlich vorkommen (C7).

**Warum das der Publikationsblocker ist.** Das Buchkonzept sah für Kapitel 14
den Titel „Die zwanzig häufigsten Fehler" vor. Die Häufigkeit ist nie erhoben
worden — der Titel wäre eine Behauptung ohne Grundlage, und zwar auf einer
Kapitelüberschrift. Der Entwurf heißt deshalb „Zwanzig Befunde, die
wiederkehren". Erst wenn diese Auswertung vorliegt, darf der ursprüngliche
Titel zurück.

**Der Nenner ist je Befund ein anderer, und das ist der Kern.** Ein Kriterium,
das bei einer Prüfung ausfiel, darf nicht als „Befund liegt nicht vor" zählen.
Wer über alle Audits teilt, rechnet fehlende Messungen als bestandene — und
erzeugt genau die zu niedrigen Häufigkeiten, die im Druck stehen blieben. Der
Nenner ist deshalb: die Prüfungen, bei denen dieses Kriterium **erhoben**
wurde.

**Nicht alle zwanzig lassen sich ableiten.** Vier Befunde haben im Katalog
keine Entsprechung, die sie allein trägt — sie werden ausgewiesen, aber ohne
Zahl. Eine erfundene Zuordnung wäre schlimmer als eine Lücke: Sie sähe aus
wie eine Erhebung.
"""
from dataclasses import dataclass
from typing import Callable, Optional

from services.audit_criteria import Source, find_criterion


@dataclass(frozen=True)
class Befund:
    """Ein Befund aus Kapitel 14 und die Bedingung, unter der er vorliegt."""

    nummer: int
    titel: str
    #: Kriterium, aus dem sich der Befund ablesen lässt — None, wenn keines passt.
    kriterium: Optional[str]
    #: Liegt der Befund vor? Bekommt Punkte und Maximum des Kriteriums.
    trifft_zu: Optional[Callable[[int, int], bool]] = None
    #: Warum ohne Zahl, wenn `kriterium` fehlt — oder was die Zahl nicht abdeckt.
    vorbehalt: str = ""


def _null(punkte: int, _maximum: int) -> bool:
    """Der Befund liegt vor, wenn das Kriterium null Punkte bekam."""
    return punkte == 0


def _unvollstaendig(punkte: int, maximum: int) -> bool:
    """Der Befund liegt vor, sobald nicht die volle Punktzahl erreicht ist."""
    return punkte < maximum


BEFUNDE = (
    Befund(1, "Das Impressum ist verlinkt, aber nicht erreichbar",
           "rc_impressum", _null),
    Befund(2, "Die Datenschutzerklärung fehlt oder ist nicht erreichbar",
           "rc_datenschutz", _null),
    Befund(3, "Das Zertifikat ist abgelaufen", "si_ssl", _null),
    Befund(4, "Fremde Dienste laden, bevor eingewilligt wurde",
           "si_drittanbieter", _null),
    Befund(5, "Die Jahreszahl im Fußbereich ist veraltet", None,
           vorbehalt="Die Aktualität des Fußbereichs wird erhoben "
                     "(`freshness`), aber von keinem Kriterium allein "
                     "getragen — `ih_aktualitaet` mischt sie mit anderen "
                     "Anzeichen."),
    Befund(6, "Ein Verweis im Fußbereich führt ins Leere", "se_links", _null,
           vorbehalt="Gemessen werden defekte Verweise der ganzen Seite, "
                     "nicht nur die im Fußbereich."),
    Befund(7, "KI-Systeme sind ausgesperrt", "se_ki_lesbar",
           lambda p, m: p < 2,
           vorbehalt="Die Sperre wiegt 2 der 3 Punkte. Unter 2 Punkten ist "
                     "mindestens ein Crawler ausgesperrt."),
    Befund(8, "Es gibt keine Beschreibungsdatei für Maschinen",
           "se_ki_lesbar", lambda p, m: p in (0, 2),
           vorbehalt="`llms.txt` ist der dritte Punkt. 0 oder 2 Punkte "
                     "heisst: die Datei fehlt."),
    Befund(9, "Die Telefonnummer ist nicht anklickbar", "se_lokal",
           _unvollstaendig,
           vorbehalt="Der `tel:`-Verweis ist einer von drei Punkten. Die "
                     "Zahl nennt daher eine Obergrenze, nicht den Befund "
                     "allein."),
    Befund(10, "Es ist nicht gesagt, wann Sie antworten", None,
           vorbehalt="Die Antwortzusage wird nirgends eigens erhoben. "
                     "`cv_kontakt` bewertet die Kontaktwege insgesamt."),
    Befund(11, "Das Kopfbild ist unkomprimiert", "tp_bilder", _unvollstaendig,
           vorbehalt="Gemessen werden Format, Ladeverhalten und Groesse "
                     "aller Bilder, nicht nur des Kopfbilds."),
    Befund(12, "Die Alternativtexte der Bilder fehlen", "bf_alt", _null),
    Befund(13, "Schriftarten laden von einem fremden Server",
           "si_drittanbieter", _null,
           vorbehalt="Dasselbe Kriterium wie Befund 4. Getrennt zaehlbar "
                     "waere es nur ueber `third_parties.external_fonts`, das "
                     "nicht je Pruefung gespeichert wird."),
    Befund(14, "Steuerdatei oder Übersichtsdatei fehlen", "se_index",
           _unvollstaendig),
    Befund(15, "Es gibt keine strukturierten Daten", "se_schema", _null),
    Befund(16, "Die Nachweise sind da, aber nicht sichtbar", "cv_vertrauen",
           _unvollstaendig,
           vorbehalt="Eingeschaetzt, nicht gemessen — die Zahl haengt am "
                     "Rubric des Sprachmodells (siehe A8)."),
    Befund(17, "Alle Leistungen stehen auf einer Sammelseite",
           "ih_leistungsseiten", _null),
    Befund(18, "Es gibt keinen Preisrahmen und keine Kostenlogik",
           "cv_angebot", _unvollstaendig,
           vorbehalt="Eingeschaetzt, nicht gemessen. Fuer K2 ist die "
                     "Preisangabe berufsrechtlich heikel — dort ist der "
                     "Befund kein Mangel."),
    Befund(19, "Zwischen echten Fotos stehen gekaufte", "dg_bildqualitaet",
           _unvollstaendig, vorbehalt="Eingeschaetzt, nicht gemessen."),
    Befund(20, "Die Texte beschreiben den Betrieb statt das Anliegen",
           "ih_textqualitaet", _unvollstaendig,
           vorbehalt="Eingeschaetzt, nicht gemessen."),
)

#: Quellen, die weder Zähler noch Nenner speisen (§ 3.5 der Bewertungslogik).
AUSSER_WERTUNG = (Source.NOT_COLLECTED.value, Source.NOT_APPLICABLE.value)


def haeufigkeit(pruefungen: list) -> list:
    """Je Befund: wie oft er vorlag, bei wie vielen auswertbaren Prüfungen.

    `pruefungen` ist eine Liste aus ``(item_scores, item_sources)`` — beides
    die gespeicherten JSON-Felder einer Prüfung, bereits als ``dict``.
    """
    ergebnis = []
    for befund in BEFUNDE:
        if not befund.kriterium:
            ergebnis.append({
                "nummer": befund.nummer, "titel": befund.titel,
                "kriterium": None, "nenner": 0, "zaehler": 0, "anteil": None,
                "vorbehalt": befund.vorbehalt,
            })
            continue

        maximum = find_criterion(befund.kriterium).max_points
        nenner = zaehler = 0
        for punkte_je_kriterium, quellen in pruefungen:
            quelle = quellen.get(befund.kriterium)
            if quelle is None or quelle in AUSSER_WERTUNG:
                continue
            nenner += 1
            if befund.trifft_zu(int(punkte_je_kriterium.get(befund.kriterium, 0)),
                                maximum):
                zaehler += 1

        ergebnis.append({
            "nummer": befund.nummer, "titel": befund.titel,
            "kriterium": befund.kriterium, "nenner": nenner, "zaehler": zaehler,
            # Ohne Nenner keine Quote. Eine Null waere hier eine Aussage.
            "anteil": round(100 * zaehler / nenner) if nenner else None,
            "vorbehalt": befund.vorbehalt,
        })
    return ergebnis


# ── Grundgesamtheit: gezaehlt ist nicht auswertbar (L-126, 28.08.2026) ──────
#
# **Der Anlass.** Auf dem Produktivbestand standen 116 Zeilen auf `completed`,
# und die Auswertung darunter rechnete mit Nennern von 4 bis 8. Beides stimmte
# — es waren zwei verschiedene Dinge: 108 dieser Zeilen tragen **keine**
# Kriterien, es sind Huellen aus der Zeit vor der heutigen Erhebung (Maerz bis
# Juli 2026). Auswertbar sind acht, alle vom 16.08. bis 26.08.
#
# **Warum das kein Schoenheitsfehler ist.** Diese Zahlen gehen in den
# Methodenteil eines Buchs. Drei Angaben waren betroffen, alle aus derselben
# Ursache: die Grundgesamtheit, der Erhebungszeitraum und die Warnung vor
# gemischten Fassungen — deren „ohne Vermerk" kam allein von den Huellen.
#
# Die verworfenen Zeilen werden **benannt**. Eine Grundgesamtheit, die
# stillschweigend schrumpft, ist so wenig nachvollziehbar wie eine zu grosse.


def aufteilen(zeilen: list) -> tuple:
    """Trennt auswertbare Pruefungen von leeren Huellen.

    `zeilen` ist eine Liste aus ``(item_scores, item_sources, created_at,
    standard_version)``. Auswertbar ist, was ueberhaupt Kriterien traegt —
    ohne sie gibt es weder Zaehler noch Nenner.
    """
    auswertbar, verworfen = [], []
    for zeile in zeilen:
        (auswertbar if zeile[0] else verworfen).append(zeile)
    return auswertbar, verworfen


def kopfzeilen(auswertbar: list, verworfen: list) -> str:
    """Die Angaben, die Kapitel 14 verlangt — aus den auswertbaren Zeilen."""
    zeilen = [f"Grundgesamtheit: {len(auswertbar)} auswertbare Pruefungen"]

    if verworfen:
        zeilen.append(
            f"  ({len(verworfen)} weitere stehen auf „abgeschlossen\", tragen "
            f"aber keine Kriterien — sie zaehlen nicht mit.)")

    zeitpunkte = sorted(z[2] for z in auswertbar if z[2])
    if zeitpunkte:
        zeilen.append(f"Erhebungszeitraum: {zeitpunkte[0]:%d.%m.%Y} bis "
                      f"{zeitpunkte[-1]:%d.%m.%Y}")

    fassungen = sorted({(z[3] or "ohne Vermerk") for z in auswertbar})
    zeilen.append(f"Fassungen des Standards: {', '.join(fassungen) or '—'}")
    if len(fassungen) > 1:
        zeilen.append("  ⚠ Mehrere Fassungen. Die Kriterien haben sich "
                      "dazwischen geaendert; die Anteile mischen zwei "
                      "Massstaebe.")
    return "\n".join(zeilen)
