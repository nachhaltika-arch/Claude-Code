# -*- coding: utf-8 -*-
"""Die vorhandenen Einzelmessungen, als Stufen eingehaengt.

**Warum nicht neu bauen.** `unaufgerufene-routen.py` und
`schwacher-zugriffsschutz.py` messen an der **geladenen Anwendung** — sie
sehen damit, was eine Textmessung nie sieht: eine Sperre, die am Router
haengt statt am Funktionskopf, und einen Praefix, der erst bei der
Registrierung entsteht. Sie sind genauer als alles, was diese Stufen aus dem
Quelltext ableiten koennten. Der Durchlauf ruft sie deshalb auf, statt sie
nachzubauen.

**Der Preis ist eine Voraussetzung**: Sie brauchen die Umgebung des Backends.
Fehlt die, meldet der Durchlauf die Stufe als **nicht gemessen** — mit Grund.
Eine Zahl, die nicht erhoben wurde, darf nicht als Null erscheinen.
"""
from __future__ import annotations

import dataclasses
import pathlib
import re
import subprocess

from .befund import Befund, WURZEL

BACKEND = WURZEL / "kompagnon" / "backend"


def python_der_anwendung() -> pathlib.Path | None:
    """Der Interpreter, der die Backend-Abhaengigkeiten kennt — oder nichts."""
    for kandidat in (BACKEND / "venv" / "bin" / "python",
                     BACKEND / "venv" / "bin" / "python3",
                     BACKEND / ".venv" / "bin" / "python"):
        if kandidat.exists():
            return kandidat
    return None


@dataclasses.dataclass
class Werkzeug:
    """Ein vorhandenes Messskript und die Art, seine Ausgabe zu lesen."""

    name: str
    skript: str                  # relativ zur Repo-Wurzel
    arbeitsverzeichnis: str      # relativ zur Repo-Wurzel
    muster: str                  # Regex mit einer Gruppe: die Zahl
    schwelle: int
    titel: str
    ebene: str
    vorschlag: str
    einzelheiten: str
    kennung: str


WERKZEUGE = (
    Werkzeug(
        name="Routen ohne Aufrufer",
        skript="kompagnon/backend/tools/unaufgerufene-routen.py",
        arbeitsverzeichnis="kompagnon/backend",
        muster=r"Ruft niemand\s+—\s+(\d+)",
        schwelle=1,
        titel="{zahl} Endpunkte ruft niemand auf",
        ebene="schnittstelle",
        vorschlag="P2",
        einzelheiten=(
            "Ein ungerufener Endpunkt ist nicht ungefaehrlich, er ist **unbeobachtet**. "
            "Am 31.08.2026 lagen hinter zwei davon fremde Gespraeche offen, am 01.09. "
            "stand die Druckwarteschlange voller unbezahlter Bestellungen. Zu jedem "
            "gehoert eine Frage: fehlt der Knopf, oder ist die Route ueberfluessig "
            "geworden? Der Arbeitsstand steht in `docs/routen-ohne-aufrufer.md` (L-105); "
            "diese Zahl sagt nur, ob er noch stimmt."
        ),
        kennung="werkzeug/routen-ohne-aufrufer",
    ),
    Werkzeug(
        name="Routen ohne Anmeldung",
        skript="tools/schwacher-zugriffsschutz.py",
        arbeitsverzeichnis="kompagnon/backend",
        muster=r"ohne jede Anmeldepruefung:\s+(\d+)",
        schwelle=1,
        titel="{zahl} Routen unter /api/ antworten ohne jede Anmeldung",
        ebene="schnittstelle",
        vorschlag="P1",
        einzelheiten=(
            "Gemessen an der **geladenen** Anwendung, nicht an den Funktionskoepfen: "
            "Eine Sperre kann in der Signatur haengen oder am Router, und wer nur die "
            "Koepfe liest, sieht die halbe Wahrheit. Einige dieser Routen sind mit "
            "Absicht offen — Widget, Kundenportal-Token, Betriebsanzeigen. Die Zahl "
            "ist deshalb kein Mangel, sondern ein Stand: Sie darf nicht steigen, ohne "
            "dass jemand sagt warum. Familie L-51, L-67, L-69."
        ),
        kennung="werkzeug/routen-ohne-anmeldung",
    ),
    Werkzeug(
        name="Routen nur mit Anmeldung",
        skript="tools/schwacher-zugriffsschutz.py",
        arbeitsverzeichnis="kompagnon/backend",
        muster=r"nur angemeldet, ohne Rollenpruefung:\s+(\d+)",
        schwelle=1,
        titel="{zahl} Routen antworten jedem Angemeldeten, ohne Rollenpruefung",
        ebene="schnittstelle",
        vorschlag="P2",
        einzelheiten=(
            "Jeder Angemeldete heisst: auch die Rolle `kunde`. In L-05 gab genau das "
            "`GET /api/invoices` ohne Filter heraus — alle Rechnungen aller Kunden mit "
            "Namen, E-Mail und Betrag. Auch hier ist die Zahl ein Stand, kein Urteil; "
            "sie gehoert beobachtet, nicht auf null getrieben."
        ),
        kennung="werkzeug/routen-nur-angemeldet",
    ),
)


def einzelmessungen() -> tuple[list[Befund], str]:
    """Ruft die vorhandenen Werkzeuge auf und liest ihre Kennzahlen.

    Jede Zahl wird zu genau einem Befund — nicht zu einer Liste. Die Liste
    steht im Werkzeug selbst, und wer sie braucht, ruft es direkt auf; der
    Durchlauf sagt nur, ob sich der Stand bewegt hat.
    """
    interpreter = python_der_anwendung()
    if interpreter is None:
        return [], ("kein Interpreter mit den Backend-Abhaengigkeiten gefunden "
                    "(kompagnon/backend/venv) — nicht gemessen")

    befunde: list[Befund] = []
    gelaufen = fehlgeschlagen = 0
    for werkzeug in WERKZEUGE:
        skript = WURZEL / werkzeug.skript
        if not skript.exists():
            continue
        try:
            lauf = subprocess.run(
                [str(interpreter), str(skript)],
                cwd=WURZEL / werkzeug.arbeitsverzeichnis,
                capture_output=True, text=True, timeout=300)
        except (OSError, subprocess.SubprocessError):
            fehlgeschlagen += 1
            continue
        ausgabe = lauf.stdout + lauf.stderr
        treffer = re.search(werkzeug.muster, ausgabe)
        if not treffer:
            fehlgeschlagen += 1
            continue
        gelaufen += 1
        zahl = int(treffer.group(1))
        if zahl < werkzeug.schwelle:
            continue
        befunde.append(Befund(
            kennung=werkzeug.kennung,
            ebene=werkzeug.ebene,
            titel=werkzeug.titel.format(zahl=zahl),
            beleg=f"{werkzeug.skript} (aus {werkzeug.arbeitsverzeichnis}) → {zahl}",
            einzelheiten=werkzeug.einzelheiten,
            vorschlag=werkzeug.vorschlag,
            gegenstand=werkzeug.kennung.split("/")[-1],
        ))
    notiz = f"{gelaufen} von {len(WERKZEUGE)} Messungen gelaufen"
    if fehlgeschlagen:
        notiz += (f", {fehlgeschlagen} ohne verwertbare Ausgabe — "
                  "das Werkzeug von Hand aufrufen und nachsehen")
    return befunde, notiz

#: Messungen am **gerenderten** Bild. Sie brauchen ein laufendes Frontend
#: (`--basis`), deshalb Bedarf `dienst`. Der Durchlauf ruft sie nicht
#: automatisch auf — sie dauern Minuten und wollen eine Anmeldung; sie stehen
#: im Bericht unter „nicht gemessen", bis jemand sie fährt.
AM_BILD = (
    ("Schriftgrößen am gerenderten Text", "tools/schriftgroessen_messen.py",
     "misst gewichtet nach Zeichenmenge, Grenze 12 px wie Lighthouse — die "
     "belastbare Fassung der Lesbarkeitsfrage"),
    ("Kontrast und Fokusreihenfolge", "tools/bedienbarkeit_messen.py",
     "misst, was tatsächlich übereinanderliegt, statt Token-Paare zu rechnen; "
     "erkennt Text auf Bild und Verlauf aus den Bildpunkten"),
)


def am_bild_offen() -> tuple[list, str]:
    """Meldet die Messungen am gerenderten Bild als offen, nie als Null.

    **Warum als eigene Stufe und nicht als Fußnote.** Kontrast und
    Schriftgröße sind die zwei Fragen, die über Lesbarkeit entscheiden, und
    beide lassen sich am Quelltext nicht beantworten. Ein Bericht, der sie
    verschweigt, weil sie nicht gelaufen sind, liest sich sauberer als die
    Lage ist.
    """
    from .befund import Befund

    vorhanden = [(name, pfad, warum) for name, pfad, warum in AM_BILD
                 if (WURZEL / pfad).exists()]
    if not vorhanden:
        return [], "keines der Werkzeuge am gerenderten Bild gefunden"
    zeilen = " · ".join(f"{name} (`{pfad}`)" for name, pfad, _ in vorhanden)
    return [Befund(
        kennung="am-bild/nicht-gemessen",
        ebene="optik",
        titel=(f"{len(vorhanden)} Messungen am gerenderten Bild sind in diesem Lauf "
               f"nicht gefahren worden"),
        beleg=zeilen,
        einzelheiten=(
            "Kontrast und Schriftgröße entscheiden über Lesbarkeit, und beide lassen "
            "sich am Quelltext nicht beantworten — eine Farbe kann als Token bestehen "
            "und auf der Seite trotzdem auf dem falschen Grund landen. "
            + " ".join(f"**{name}**: {warum}." for name, _, warum in vorhanden)
            + " Beide brauchen ein laufendes Frontend und eine Anmeldung; sie dauern "
            "Minuten. **Dieser Eintrag verschwindet, sobald sie gelaufen sind** — er "
            "steht hier, damit ein Bericht ohne sie nicht sauberer aussieht als die "
            "Lage ist. Und seit dem 04.09. gilt: Beide gehören in **beiden** Themes "
            "gefahren, hell und dunkel zählen gleich."
        ),
        vorschlag="P2",
        gegenstand="Messungen am gerenderten Bild",
    )], f"{len(vorhanden)} Werkzeuge vorhanden, keines gelaufen"


def token_kontrast_tests() -> tuple[list, str]:
    """Lässt die vorhandenen Token-Kontrasttests laufen.

    `utils/tokenKontrast.test.js` prüft die als Kommentar notierten
    Kontrastzahlen, `tokenKontrastPaare.test.js` jedes Paar aus einer
    ausdrücklichen Liste — in **beiden** Tokensätzen. Das ist gründlicher als
    alles, was der Durchlauf nachbauen würde: Der Test kennt die Paare, die es
    wirklich gibt, statt ein Kreuzprodukt zu rechnen, das Fehlalarme erzeugt.
    """
    from .befund import Befund

    frontend = WURZEL / "kompagnon" / "frontend"
    if not (frontend / "node_modules").is_dir():
        return [], "kompagnon/frontend/node_modules fehlt — Tests nicht gelaufen"
    try:
        lauf = subprocess.run(
            ["npx", "--no-install", "react-scripts", "test",
             "--watchAll=false", "--testPathPattern=tokenKontrast"],
            cwd=frontend, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError) as fehler:
        return [], f"Testlauf nicht möglich: {type(fehler).__name__}"
    ausgabe = lauf.stdout + lauf.stderr
    if lauf.returncode == 0:
        treffer = re.search(r"Tests:\s+(\d+) passed", ausgabe)
        return [], (f"Token-Kontrast in beiden Themes bestanden"
                    + (f" ({treffer.group(1)} Prüfungen)" if treffer else ""))
    fehlzeilen = [z.strip() for z in ausgabe.splitlines()
                  if "✕" in z or "●" in z][:4]
    return [Befund(
        kennung="theme/token-kontrast-test",
        ebene="optik",
        titel="Die Token-Kontrasttests schlagen fehl",
        beleg=" · ".join(fehlzeilen) or "react-scripts test --testPathPattern=tokenKontrast",
        einzelheiten=(
            "`utils/tokenKontrastPaare.test.js` rechnet jedes wirklich benutzte "
            "Farbpaar in **beiden** Tokensätzen gegen WCAG AA. Ein Fehlschlag heißt: "
            "Irgendwo steht Text auf einem Grund, auf dem er nicht lesbar ist — im "
            "Hell- oder im Dunkelmodus. Am 28.08.2026 war es `--brand-primary-mid` mit "
            "2.18 auf `--surface`, an 78 Stellen als `color:` gesetzt."
        ),
        vorschlag="P1",
        gegenstand="Token-Kontrast",
    )], "Tests gelaufen, Fehlschlag"
