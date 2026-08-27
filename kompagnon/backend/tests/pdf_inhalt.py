"""Den Textinhalt eines PDF-Berichts abgreifen, bevor er PDF wird (L-25).

**Warum es das gibt.** `generate_audit_report` hat **576 Zeilen** — zwei
Drittel von `pdf_generator.py`. Der Eintrag L-25 haelt fest, warum die
Funktion trotzdem nicht zerlegt wurde: Die dreissig vorhandenen Tests pruefen
Bausteine („wird erzeugt", Matrixlogik), aber **ob das PDF danach noch gleich
aussieht, sagt keiner** — und der Bericht geht an Kunden. Ohne Gegenprobe
waere jeder Schnitt ein Blindflug.

**Warum nicht das fertige PDF gelesen wird.** Dafuer braeuchte es `pypdf`
oder `pdfplumber`; beides ist nicht installiert, und eine Abhaengigkeit nur
fuer einen Test ist der falsche Preis. `reportlab` bekommt seinen Inhalt als
Liste von *Flowables* — `Paragraph`, `Table`, `Spacer` —, und die traegt den
Text bereits. Abgegriffen wird an `SimpleDocTemplate.build`, also genau dort,
wo der Bericht fertig ist und das Zeichnen beginnt.

**Das ist nicht nur billiger, sondern schaerfer:** Die Flowable-Folge haelt
auch die **Reihenfolge** fest. Ein Schnitt, der zwei Abschnitte vertauscht,
erzeugt ein gueltiges PDF mit demselben Wortbestand — und faellt hier auf.
"""
import contextlib

from reportlab.platypus import SimpleDocTemplate


def _text_eines(flowable) -> list:
    """Der lesbare Inhalt eines Flowables — leere Elemente ergeben nichts."""
    text = getattr(flowable, "text", None)
    if isinstance(text, str) and text.strip():
        return [text.strip()]

    # Tabellen tragen ihre Zellen; eine Zelle kann selbst ein Paragraph sein.
    zellen = getattr(flowable, "_cellvalues", None)
    if zellen:
        raus = []
        for zeile in zellen:
            for zelle in zeile:
                raus.extend(_text_eines(zelle))
        return raus

    # Verschachtelte Behaelter (KeepTogether und Verwandte).
    inhalt = getattr(flowable, "_content", None) or getattr(flowable, "_flowables", None)
    if inhalt:
        raus = []
        for teil in inhalt:
            raus.extend(_text_eines(teil))
        return raus

    if isinstance(flowable, str) and flowable.strip():
        return [flowable.strip()]
    return []


@contextlib.contextmanager
def mitgeschriebener_inhalt(sammler: list):
    """Faengt die Flowable-Folge ab, die an `doc.build` geht.

    Das PDF wird trotzdem erzeugt — der Test soll denselben Weg gehen wie der
    Betrieb, nicht einen kuerzeren.
    """
    echtes_build = SimpleDocTemplate.build

    def mitschreibend(self, story, *args, **kwargs):
        for flowable in story:
            sammler.extend(_text_eines(flowable))
        return echtes_build(self, story, *args, **kwargs)

    SimpleDocTemplate.build = mitschreibend
    try:
        yield sammler
    finally:
        SimpleDocTemplate.build = echtes_build


def inhalt_von(erzeuger, *args, **kwargs) -> list:
    """Ruft den Erzeuger auf und liefert seinen Textinhalt der Reihe nach."""
    sammler = []
    with mitgeschriebener_inhalt(sammler):
        erzeuger(*args, **kwargs)
    return sammler
