#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Meldet neue Aufträge aus der Trichter-Vorschau in die laufende Sitzung.

**Wozu.** Die Vorschau legt Beanstandungen in `.vorschau-auftraege.json` ab.
Bis jetzt musste jemand sagen „schau in die Aufträge" — der Auftrag lag
sonst da und wartete. Dieses Skript wird als Monitor gestartet: Jede Zeile,
die es ausgibt, wird in der Sitzung zu einer Meldung. Damit weckt ein
Klick in der Vorschau die Sitzung von selbst.

    Monitor(command="python3 scripts/auftraege-melden.py", persistent=True)

**Es schreibt nichts.** Ein Wächter, der in die Datei fasst, die er bewacht,
kann sie beschädigen — und dann ist die Woche Beanstandungen weg. Den
Zustand eines Auftrags ändert, wer ihn bearbeitet.

**Stille ist kein Erfolg.** Gemeldet wird auch, wenn die Ablage unlesbar
wird oder verschwindet. Ein Melder, der nur bei guten Nachrichten spricht,
sieht im Fehlerfall genauso aus wie einer, bei dem nichts los ist.
"""
from __future__ import annotations

import json
import os
import sys
import time

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABLAGE = os.environ.get("VORSCHAU_AUFTRAEGE") or os.path.join(
    WURZEL, ".vorschau-auftraege.json")

TAKT_SEKUNDEN = 3

#: Ein Auftrag gilt als offen, solange er weder angenommen noch erledigt ist.
OFFEN = "offen"


def sagen(text: str) -> None:
    """Eine Zeile = eine Meldung. Ohne `flush` bleibt sie im Puffer liegen."""
    print(text, flush=True)


def lesen():
    """(Einträge, Fehlertext). Genau eins von beiden ist gesetzt."""
    if not os.path.exists(ABLAGE):
        return [], None
    try:
        with open(ABLAGE, encoding="utf-8") as f:
            inhalt = f.read()
    except OSError as fehler:
        return None, f"Ablage nicht lesbar: {fehler}"
    if not inhalt.strip():
        return [], None
    try:
        return json.loads(inhalt).get("eintraege", []), None
    except json.JSONDecodeError as fehler:
        # Kann beim Schreiben auftreten. Die Vorschau schreibt zwar erst
        # daneben und benennt dann um, aber ein von Hand bearbeiteter
        # Zwischenstand ist möglich — deshalb kein Abbruch.
        return None, f"Ablage gerade nicht lesbar ({fehler})"


def beschreiben(eintrag: dict) -> str:
    ansicht = eintrag.get("ansicht") or "ohne Ansicht"
    stelle = (eintrag.get("auszug") or "").strip()
    regler = eintrag.get("regler") or {}
    zeilen = [f"AUFTRAG · {ansicht} · {eintrag.get('id')}",
              f"  {eintrag.get('text', '').strip()}"]
    if stelle:
        zeilen.append(f"  an der Stelle: {stelle[:110]}")
    if regler:
        zeilen.append("  Regler: " + ", ".join(f"{k}={v}" for k, v in regler.items()))
    return "\n".join(zeilen)


def main() -> int:
    gesehen = set()
    letzter_fehler = None

    # Beim Start wird der Rückstand **einmal** gemeldet, nicht verschwiegen:
    # Wer die Sitzung neu startet, soll wissen, was noch offen ist.
    eintraege, fehler = lesen()
    if fehler:
        sagen(f"MELDER · {fehler}")
        letzter_fehler = fehler
    else:
        offen = [e for e in eintraege if e.get("status") == OFFEN]
        gesehen = {e.get("id") for e in eintraege}
        if offen:
            sagen(f"MELDER · {len(offen)} Auftrag/Aufträge warten schon:")
            for e in offen:
                sagen(beschreiben(e))
        else:
            sagen("MELDER · bereit, keine offenen Aufträge.")

    while True:
        time.sleep(TAKT_SEKUNDEN)
        eintraege, fehler = lesen()

        if fehler:
            # Nicht bei jedem Takt wiederholen — sonst wird aus einem
            # Fehler ein Wasserfall und der Melder abgeschaltet.
            if fehler != letzter_fehler:
                sagen(f"MELDER · {fehler}")
                letzter_fehler = fehler
            continue
        letzter_fehler = None

        for eintrag in eintraege:
            kennung = eintrag.get("id")
            if kennung in gesehen:
                continue
            gesehen.add(kennung)
            if eintrag.get("status") == OFFEN:
                sagen(beschreiben(eintrag))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sagen("MELDER · beendet.")
