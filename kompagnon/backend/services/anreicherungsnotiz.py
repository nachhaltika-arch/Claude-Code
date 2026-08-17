"""Die alte Befundzeile aus `leads.notes` lesen und entfernen.

Bis zum 17.08.2026 schrieb `enrich_lead` nach jedem Lauf

    [Auto-Enrichment] SSL: OK | Impressum: FEHLT | PageSpeed: 43/100 | Score: 65/100

vor die Notiz eines Menschen. Seither stehen diese Befunde in eigenen Spalten.
Fuer den Bestand hiess das: Spalten leer, Oberflaeche sagt ehrlich „nicht
geprueft" — und zwei Zeilen darunter behauptet die alte Notiz „SSL: OK".
Beides stimmt fuer sich, zusammen widersprechen sie sich.

Die Werte sind also da, nur im falschen Feld. Herueberholen ist besser als
loeschen: `scripts/notizen-bereinigen.sql` wuerde sie verwerfen und auf den
naechsten Anreicherungslauf warten lassen.

**Ein Zeitpunkt wird nicht erfunden.** Die Zeile trug keinen. `enriched_at`
bleibt deshalb leer, und die Oberflaeche sagt „Zeitpunkt unbekannt" statt
eines gefaelligen Datums.
"""
import re

MARKE = "[Auto-Enrichment]"

_ZEILE = re.compile(r"^\[Auto-Enrichment\].*$", re.MULTILINE)
_SSL = re.compile(r"SSL:\s*(OK|FEHLT)", re.IGNORECASE)
_IMPRESSUM = re.compile(r"Impressum:\s*(OK|FEHLT)", re.IGNORECASE)
_PAGESPEED = re.compile(r"PageSpeed:\s*(\d+)\s*/\s*100", re.IGNORECASE)


def befunde_aus_notiz(notiz) -> dict:
    """Liest SSL, Impressum und PageSpeed aus der juengsten Befundzeile.

    Die Anreicherung stellte jede neue Zeile voran — die oberste ist also die
    neueste. Fehlt ein Wert in der Zeile, fehlt er auch im Ergebnis; erfunden
    wird nichts.
    """
    if not notiz or MARKE not in notiz:
        return {}

    treffer = _ZEILE.search(notiz)
    if not treffer:
        return {}
    zeile = treffer.group(0)

    befunde = {}
    if (ssl := _SSL.search(zeile)):
        befunde["has_ssl"] = ssl.group(1).upper() == "OK"
    if (imp := _IMPRESSUM.search(zeile)):
        befunde["has_impressum"] = imp.group(1).upper() == "OK"
    if (ps := _PAGESPEED.search(zeile)):
        befunde["pagespeed_mobile_score"] = int(ps.group(1))
    return befunde


def notiz_ohne_maschinenzeilen(notiz):
    """Die Notiz ohne jede `[Auto-Enrichment]`-Zeile.

    Gibt ``None`` zurueck, wenn nichts uebrig bleibt — ein leerer Kasten in
    der Oberflaeche ist schlechter als gar keiner.
    """
    if not notiz:
        return None
    rest = _ZEILE.sub("", notiz).strip("\n").strip()
    return rest or None
