"""Stufe B: einen Bibliotheksblock für einen Kunden umschreiben.

Stufe A gibt jeder Kundenseite dieselben Blöcke — individuell werden nur Texte
und Farben. Zwei SHK-Betriebe in derselben Stadt bekämen sichtbar dieselbe
Seite. Hier entsteht der Unterschied: Der gewählte Block wird **im Aufbau**
variiert, passend zu Leistung, Einzugsgebiet und Betrieb.

Zwei Grenzen halten das zusammen, und beide stehen im Prompt wie im Prüfer:

* **Derselbe Block.** Die Variante trägt weiter `data-block="<slug>"` und
  bleibt damit im Editor auffindbar und austauschbar.
* **Dieselben Slots.** Weniger ist erlaubt, umbenennen nicht: `generate-copy`
  und der Slot-Editor lesen die Angaben des Bibliotheksblocks.

Der Rest ist der Weg aus Stufe A: Vertrag prüfen, Verstöße einmal ans Modell
zurück, die Reparatur nur übernehmen, wenn sie es besser macht.
"""
import logging

from services.block_contract import pruefe, slots_im_markup

logger = logging.getLogger(__name__)

# Dieses Markup landet auf einer Kundenseite — dieselbe Wahl wie beim
# Blockautor in Stufe A.
VARIANTEN_MODELL = "claude-opus-5"


class VariantenAbbruch(Exception):
    """Ein Grund, den Auftrag mit einer verständlichen Meldung zu beenden."""


def _betriebs_beschreibung(briefing) -> str:
    """Was den Betrieb von jedem anderen unterscheidet.

    Ohne konkrete Welt — Gewerk, Leistungen, Einzugsgebiet, USP — fällt jedes
    Modell in denselben Durchschnitt. Genau davor warnt § 8 des Konzepts.
    """
    if briefing is None:
        return "Kein Briefing hinterlegt — halte dich an den vorhandenen Block."

    felder = [
        ("Gewerk", getattr(briefing, "gewerk", None)),
        ("Leistungen", getattr(briefing, "leistungen", None)),
        ("Einzugsgebiet", getattr(briefing, "einzugsgebiet", None)),
        ("Alleinstellung", getattr(briefing, "usp", None)),
        ("Stil-Wunsch", getattr(briefing, "stil", None)),
        ("Sonstiges", getattr(briefing, "sonstige_hinweise", None)),
    ]
    zeilen = [f"- {name}: {wert.strip()}"
              for name, wert in felder if wert and str(wert).strip()]
    return "\n".join(zeilen) or "Briefing ist leer — halte dich an den vorhandenen Block."


def _slot_liste(slots) -> str:
    eintraege = [s for s in (slots or []) if isinstance(s, dict) and s.get("key")]
    if not eintraege:
        return "(keine)"
    return "\n".join(
        f'- {{{{{s["key"]}}}}} — {s.get("label") or s["key"]}' for s in eintraege)


def baue_prompt(*, slug: str, vorlage: str, slots, briefing,
                wunsch: str = "", seite: str = "") -> str:
    """Der Auftrag ans Modell. Getrennt gehalten, damit er lesbar bleibt."""
    seiten_zeile = f"\nDIESE SECTION STEHT AUF DER SEITE: {seite}\n" if seite else ""
    wunsch_zeile = f"\nWUNSCH FÜR DIESE VARIANTE:\n{wunsch.strip()}\n" if wunsch.strip() else ""

    return f"""Du bist Senior Web-Designer. Schreibe die folgende Section für
**diesen einen Betrieb** um — nicht neu erfinden, sondern gezielt variieren:
andere Anordnung, andere Betonung, passend zu dem, was der Betrieb tut.

DER BETRIEB:
{_betriebs_beschreibung(briefing)}
{seiten_zeile}{wunsch_zeile}
DIE VORLAGE (Bibliotheksblock "{slug}"):
{vorlage}

DIE SLOTS DIESES BLOCKS — Namen sind gesetzt:
{_slot_liste(slots)}

HARTE REGELN:
1. Das Wurzelelement traegt weiter `data-block="{slug}"`. Der Block bleibt
   derselbe, nur anders gebaut.
2. Nutze **nur** die oben genannten Slot-Namen. Weglassen ist erlaubt, wenn die
   Variante ohne sie auskommt — umbenennen oder erfinden nicht. Die Slot-Namen
   liest der Text-Generator aus der Bibliothek, nicht aus deinem Markup.
3. NUR neutrale Farbtoene: `gray`, `slate`, `zinc`, `neutral`, `stone`, dazu
   `white`, `black`, `transparent`. Keine bunte Klasse, kein eigener Farbwert,
   keine Farbe im `style`- oder SVG-Attribut. Die Marke kommt aus dem
   Style-Guide des Kunden und ersetzt die Graustufen.
4. Keine Ressource von einem fremden Server: kein `<script>`, `<iframe>`,
   `<link>`, `<object>`, `<embed>`, kein `src="https://…"`, kein `@import`.
   Ein `<a href="https://…">` zum Anklicken ist erlaubt.
5. KEIN `id`-Attribut — der Block kann zweimal auf einer Seite stehen. Fuer
   Barrierefreiheit `aria-label` direkt am Bereich statt `aria-labelledby`.
6. Kein `position: fixed`/`sticky`, hoechstens 12 Ebenen Verschachtelung.
7. Mobile-first responsive mit sm:/md:/lg:-Praefixen, semantisches HTML.

ANTWORTE AUSSCHLIESSLICH mit diesem JSON, kein Markdown-Wrapper:

{{
  "html_override": "<das vollstaendige Markup als String>",
  "begruendung": "<ein Satz: was ist anders und warum passt es zu diesem Betrieb>"
}}"""


def reparatur_auftrag(verstoesse) -> str:
    zeilen = "\n".join(f"- {v}" for v in verstoesse)
    return f"""Die Variante verletzt den Vertrag:

{zeilen}

Behebe genau diese Punkte, sonst bleibt alles wie es ist. Antworte erneut
AUSSCHLIESSLICH mit dem JSON im selben Format."""


def pruefe_variante(html: str, *, slug: str, slots) -> list:
    """Vertrag plus die zwei Grenzen, die nur für eine Variante gelten."""
    verstoesse = [{"regel": v.regel, "text": v.text}
                  for v in pruefe(html, slug=slug)]
    bekannt = {s.get("key") for s in (slots or []) if isinstance(s, dict)}
    for name in slots_im_markup(html or ""):
        if name not in bekannt:
            verstoesse.append({
                "regel": "B2",
                "text": f'Slot "{name}" steht nur in der Variante. Erlaubt sind '
                        f'nur die Slots des Bibliotheksblocks: '
                        f'{", ".join(sorted(k for k in bekannt if k)) or "(keine)"}.',
            })
    return verstoesse


def _text(verstoesse) -> str:
    return " | ".join(f"{v['regel']}: {v['text']}" for v in verstoesse)


def erzeuge_variante(*, ki_runde, client, slug: str, vorlage: str, slots,
                     briefing, wunsch: str = "", seite: str = "",
                     auftrag: str = "") -> dict:
    """Eine Variante, geprüft und höchstens einmal repariert.

    `ki_runde` wird hereingereicht statt importiert: Dieselbe Funktion versorgt
    schon den Blockautor (JSON-Nachbesserung inklusive), und der Test kann sie
    ersetzen, ohne dass ein Token fließt.
    """
    nachrichten = [{"role": "user", "content": baue_prompt(
        slug=slug, vorlage=vorlage, slots=slots, briefing=briefing,
        wunsch=wunsch, seite=seite)}]

    antwort, ergebnis = ki_runde(client, nachrichten)
    html = _html_aus(ergebnis)
    verstoesse = pruefe_variante(html, slug=slug, slots=slots)

    if verstoesse:
        logger.info("variante %s: %d Verstoss/Verstoesse, eine Reparaturrunde — %s",
                    auftrag or slug, len(verstoesse), _text(verstoesse))
        nachrichten.append({"role": "assistant", "content": antwort.content})
        nachrichten.append({"role": "user", "content": reparatur_auftrag(verstoesse)})

        _, repariert = ki_runde(client, nachrichten)
        html_neu = _html_aus(repariert)
        nachher = pruefe_variante(html_neu, slug=slug, slots=slots)
        # Nur uebernehmen, wenn die Reparatur es wirklich besser macht.
        if len(nachher) < len(verstoesse):
            ergebnis, html, verstoesse = repariert, html_neu, nachher
        if verstoesse:
            logger.warning("variante %s: nach Reparatur weiterhin unsauber — %s",
                           auftrag or slug, _text(verstoesse))

    return {
        "slug": slug,
        "html_override": html,
        "begruendung": str(ergebnis.get("begruendung") or "").strip(),
        "contract": {"konform": not verstoesse, "verstoesse": verstoesse},
    }


def _html_aus(ergebnis) -> str:
    if not isinstance(ergebnis, dict):
        raise VariantenAbbruch("Antwort ist kein Objekt.")
    html = ergebnis.get("html_override")
    if not isinstance(html, str) or len(html.strip()) < 50:
        raise VariantenAbbruch("html_override fehlt oder ist zu kurz.")
    return html.strip()
