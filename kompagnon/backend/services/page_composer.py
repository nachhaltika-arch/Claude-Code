"""Stufe C: die Seite komponieren statt Blöcke aneinanderreihen.

Der Wireframe-Generator sucht passende Blöcke heraus. Was er nicht tut: eine
Seite **bauen** — Reihenfolge, Rhythmus, Übergänge, keine Wiederholung, und die
Pflicht-Sections aus `docs/conversion-spec-shk.md` vollständig.

**Warum zwei Phasen.** Eine ganze Seite in einem Aufruf zu erzeugen hieße acht
Sections Markup in einer Antwort — lang, teuer und beim kleinsten Formfehler
ganz verloren. Deshalb macht diese Datei nur den ersten Schritt: die
**Abfolge**. Wenige hundert Zeichen Antwort, dafür die Entscheidung, auf die es
ankommt. Das Markup je Section schreibt danach Stufe B — ein Aufruf pro
Section, bereits erprobt, einzeln prüfbar und einzeln zu wiederholen.

Die Bibliothek bleibt dabei der Anker: Jede Section nennt einen vorhandenen
Block. Das ist keine Einschränkung der Gestaltung — Stufe B baut ihn ohnehin
um — sondern das, was Slots, Editor und Textgenerator zusammenhält.
"""
import logging

logger = logging.getLogger(__name__)

# Komposition ist Auswahl und Reihenfolge, nicht Markup — dafür reicht das
# schnellere Modell. Das Markup je Section schreibt Stufe B auf Opus.
KOMPOSITIONS_MODELL = "claude-sonnet-4-6"

# Aus `docs/conversion-spec-shk.md`, Abschnitt 3. Für die Startseite gelten
# alle; für Unterseiten ist die Liste eine Empfehlung, keine Pflicht.
PFLICHT_SECTIONS = [
    ("Hero", "Klares Versprechen, sichtbarer CTA, ein Trust-Element"),
    ("Problem", "Die Schmerzen, die der Kunde jetzt hat"),
    ("Angebot", "Leistungen mit Wert je Position, Gesamtwert, Anker"),
    ("Ablauf", "4–6 nummerierte Schritte mit Zeitangabe"),
    ("Vertrauen", "Innung, Hersteller, Zertifikate, Bewertungen"),
    ("Referenzen", "3–5 echte Fälle mit Ort und Zahlen"),
    ("Garantie", "Die Zusagen, die das Risiko beim Kunden senken"),
    ("Fragen", "8–12 echte Einwände entkräften"),
    ("Dringlichkeit", "Echte Stichtage — Förderstand, freie Termine"),
    ("Abschluss-CTA", "Primärer CTA wiederholt, Telefon sichtbar"),
]


class KompositionsAbbruch(Exception):
    """Ein Grund, den Auftrag mit einer verständlichen Meldung zu beenden."""


def _bibliotheks_liste(bloecke) -> str:
    """Die Bibliothek, wie das Modell sie zu sehen bekommt: knapp und sortiert."""
    zeilen = []
    for b in sorted(bloecke, key=lambda x: (x.get("category") or "", x.get("slug") or "")):
        hinweis = (b.get("ki_prompt_hint") or "").strip()
        zeilen.append(f'- {b["slug"]} [{b.get("category") or "?"}] '
                      f'{b.get("name") or ""}{" — " + hinweis if hinweis else ""}')
    return "\n".join(zeilen)


def _pflicht_liste(ist_startseite: bool) -> str:
    kopf = ("PFLICHT-SECTIONS (alle, in sinnvoller Reihenfolge):"
            if ist_startseite else
            "SECTIONS, die auf so einer Seite üblich sind (Auswahl nach Zweck):")
    zeilen = "\n".join(f"- {name}: {inhalt}" for name, inhalt in PFLICHT_SECTIONS)
    return f"{kopf}\n{zeilen}"


def _betrieb(briefing) -> str:
    if briefing is None:
        return "Kein Briefing hinterlegt."
    felder = [
        ("Gewerk", getattr(briefing, "gewerk", None)),
        ("Leistungen", getattr(briefing, "leistungen", None)),
        ("Einzugsgebiet", getattr(briefing, "einzugsgebiet", None)),
        ("Alleinstellung", getattr(briefing, "usp", None)),
        ("Stil-Wunsch", getattr(briefing, "stil", None)),
        ("Sonstiges", getattr(briefing, "sonstige_hinweise", None)),
    ]
    zeilen = [f"- {name}: {str(wert).strip()}"
              for name, wert in felder if wert and str(wert).strip()]
    return "\n".join(zeilen) or "Briefing ist leer."


def baue_prompt(*, seite: str, zweck: str, ist_startseite: bool, briefing,
                bloecke, bestehend=None) -> str:
    """Der Auftrag: eine Abfolge, kein Markup."""
    bisher = ""
    if bestehend:
        bisher = ("\nDIE SEITE HAT HEUTE DIESE ABFOLGE — verbessere sie, statt "
                  "sie blind zu ersetzen:\n"
                  + "\n".join(f"- {s}" for s in bestehend) + "\n")

    return f"""Du komponierst eine Seite für einen Handwerksbetrieb. Nicht
Blöcke aneinanderreihen, sondern eine Seite bauen: Reihenfolge, Rhythmus,
Übergänge — und nichts doppelt.

DIE SEITE: {seite}{f" — {zweck}" if zweck else ""}

DER BETRIEB:
{_betrieb(briefing)}
{bisher}
{_pflicht_liste(ist_startseite)}

VERFÜGBARE BLÖCKE (nur diese slugs sind erlaubt):
{_bibliotheks_liste(bloecke)}

REGELN:
1. Jede Section nennt genau einen `slug` aus der Liste oben. Erfinde keinen.
2. Nie zweimal denselben Block hintereinander — das ist keine Seite, das ist
   eine Wiederholung.
3. Rhythmus: Nach zwei inhaltsschweren Sections darf eine leichte kommen. Ein
   CTA gehört alle paar Sections, aber nie zwei direkt hintereinander.
4. Der `auftrag` je Section ist **ein Satz** an den Gestalter: was diese
   Section für diesen Betrieb leisten soll. Kein Markup, keine Textvorschläge.
5. So viele Sections wie die Seite braucht — auf einer Startseite selten unter
   sechs, selten über zwölf.

ANTWORTE AUSSCHLIESSLICH mit diesem JSON, kein Markdown-Wrapper:

{{
  "aufbau": "<ein Satz: welchen Bogen die Seite schlägt>",
  "sections": [
    {{"slug": "<slug aus der Liste>",
      "rolle": "<Hero | Problem | Angebot | …>",
      "auftrag": "<ein Satz an den Gestalter>"}}
  ]
}}"""


def reparatur_auftrag(verstoesse) -> str:
    zeilen = "\n".join(f"- {v['text']}" for v in verstoesse)
    return f"""Die Abfolge passt so nicht:

{zeilen}

Sende die vollständige Abfolge erneut, diesmal ohne diese Punkte. Antworte
AUSSCHLIESSLICH mit dem JSON im selben Format."""


def pruefe_komposition(sections, erlaubte_slugs) -> list:
    """Was an einer Abfolge falsch sein kann, bevor ein Zeichen Markup entsteht."""
    verstoesse = []
    if not sections:
        return [{"regel": "C0", "text": "Die Abfolge ist leer."}]

    for i, section in enumerate(sections):
        slug = (section or {}).get("slug")
        if not slug or slug not in erlaubte_slugs:
            verstoesse.append({
                "regel": "C1",
                "text": f'Section {i + 1}: "{slug}" steht nicht in der Bibliothek. '
                        f"Erlaubt sind nur vorhandene Blöcke.",
            })
        if i > 0 and slug and slug == (sections[i - 1] or {}).get("slug"):
            verstoesse.append({
                "regel": "C2",
                "text": f'Section {i + 1}: "{slug}" steht zweimal hintereinander.',
            })
    return verstoesse


def komponiere(*, ki_runde, client, seite: str, zweck: str, ist_startseite: bool,
               briefing, bloecke, bestehend=None, auftrag: str = "") -> dict:
    """Eine Abfolge, geprüft und höchstens einmal nachgebessert."""
    erlaubt = {b.get("slug") for b in bloecke if b.get("slug")}
    if not erlaubt:
        raise KompositionsAbbruch(
            "Keine freigegebenen Bibliotheksblöcke — ohne sie gibt es nichts zu "
            "komponieren.")

    nachrichten = [{"role": "user", "content": baue_prompt(
        seite=seite, zweck=zweck, ist_startseite=ist_startseite, briefing=briefing,
        bloecke=bloecke, bestehend=bestehend)}]

    antwort, ergebnis = ki_runde(client, nachrichten)
    sections = _sections_aus(ergebnis)
    verstoesse = pruefe_komposition(sections, erlaubt)

    if verstoesse:
        logger.info("komposition %s: %d Punkt(e), eine Nachbesserung — %s",
                    auftrag or seite, len(verstoesse),
                    " | ".join(v["text"] for v in verstoesse))
        nachrichten.append({"role": "assistant", "content": antwort.content})
        nachrichten.append({"role": "user", "content": reparatur_auftrag(verstoesse)})

        _, zweiter = ki_runde(client, nachrichten)
        sections_neu = _sections_aus(zweiter)
        nachher = pruefe_komposition(sections_neu, erlaubt)
        if len(nachher) < len(verstoesse):
            ergebnis, sections, verstoesse = zweiter, sections_neu, nachher

    return {
        "aufbau": str(ergebnis.get("aufbau") or "").strip(),
        "sections": [{
            "slug":    s.get("slug"),
            "rolle":   str(s.get("rolle") or "").strip(),
            "auftrag": str(s.get("auftrag") or "").strip(),
        } for s in sections],
        "contract": {"konform": not verstoesse, "verstoesse": verstoesse},
    }


def _sections_aus(ergebnis) -> list:
    if not isinstance(ergebnis, dict):
        raise KompositionsAbbruch("Antwort ist kein Objekt.")
    sections = ergebnis.get("sections")
    if not isinstance(sections, list) or not sections:
        raise KompositionsAbbruch("Die Antwort enthält keine Sections.")
    return [s for s in sections if isinstance(s, dict)]
