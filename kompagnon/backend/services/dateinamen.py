# -*- coding: utf-8 -*-
"""Dateinamen, die durch eine HTTP-Kopfzeile passen.

**Eine Stelle, nicht vier.** Drei Endpunkte bauten ihren Anhangsnamen aus
`company_name` zusammen — der Widget-Bericht, das Audit-PDF und das Angebot —
und alle drei schrieben den Rohnamen in die Kopfzeile. Der vierte nahm den
hochgeladenen Namen einer Datei. Vier gleiche Fehler an vier Orten sind ein
Fehler an einem Ort, der viermal abgeschrieben wurde.

Warum das nötig ist, steht ausführlich in `tests/test_anhang_dateiname.py`.
Kurz: Eine HTTP-Kopfzeile trägt nach RFC 7230 nur ASCII. RFC 6266 löst das
mit zwei Feldern nebeneinander — `filename` als Rückfall für alte Clients,
`filename*` mit dem echten Namen in UTF-8.
"""
from urllib.parse import quote

#: Deutsche Umlaute werden umschrieben statt weggeworfen: `Ingenieurbuero`
#: ist ein Name, `Ingenieurbro` ist ein Tippfehler. Die Umschreibung folgt
#: DIN 5007-2 — also der Schreibweise, die jeder Deutsche von Hand wählt,
#: wenn ihm die Umlaute fehlen.
UMSCHRIFT = {
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
}

#: Was eine Kopfzeile zerlegen würde: Anführungszeichen beenden die
#: Zeichenkette, der Rückstrich maskiert das nächste Zeichen, und ein
#: Zeilenumbruch beginnt eine **neue** Kopfzeile. `company_name` kommt aus
#: dem Scraper, also von einer fremden Seite — das hier ist keine Vorsorge
#: gegen Tippfehler, sondern gegen eine eingeschleuste Kopfzeile.
GEFAEHRLICH = '"\\\r\n\t\x00'

#: Ein leerer Dateiname ist kein Dateiname. Bleibt nach dem Aussieben nichts
#: übrig — ein Name ganz ohne lateinische Schrift —, muss der Rückfall
#: trotzdem etwas benennen.
ERSATZNAME = "Datei"


def ascii_rueckfall(name: str) -> str:
    """Der lesbare ASCII-Rest: umgeschrieben, entschärft, ausgesiebt."""
    umgeschrieben = "".join(UMSCHRIFT.get(z, z) for z in name)
    entschaerft = "".join(z for z in umgeschrieben if z not in GEFAEHRLICH)
    ascii_rein = "".join(z for z in entschaerft if ord(z) < 128)

    # Die Endung darf nicht mitverschwinden: Bleibt nur noch `.pdf` übrig,
    # soll die Datei `Datei.pdf` heissen und nicht `.pdf` — ein Name, der
    # unter Unix eine versteckte Datei ergibt.
    stamm, punkt, endung = ascii_rein.rpartition(".")
    if punkt and not stamm.strip():
        return f"{ERSATZNAME}.{endung}"
    return ascii_rein.strip() or ERSATZNAME


def anhang_kopfzeile(name: str) -> str:
    """Der vollständige Wert für ``Content-Disposition``.

    Beide Formen stehen nebeneinander, das ist so gewollt: Ein Client, der
    `filename*` nicht kennt, nimmt den Rückfall; jeder andere nimmt den
    echten Namen. Die Reihenfolge folgt RFC 6266 — erst der Rückfall.
    """
    echt = quote(name.replace("\r", "").replace("\n", ""), safe="", encoding="utf-8")
    return f'attachment; filename="{ascii_rueckfall(name)}"; filename*=UTF-8\'\'{echt}'
