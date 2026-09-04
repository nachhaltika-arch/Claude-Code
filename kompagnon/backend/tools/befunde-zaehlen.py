#!/usr/bin/env python3
"""C7 — wie oft die zwanzig Befunde aus Kapitel 14 vorkommen.

**Der Publikationsblocker.** Kapitel 14 darf „Die zwanzig haeufigsten Fehler"
erst heissen, wenn die Haeufigkeit erhoben ist. Ohne diese Auswertung waere
der Titel eine Behauptung auf einer Kapitelueberschrift.

**Was ausgegeben wird — und was ausdruecklich dazugehoert.** Kapitel 14
verlangt Grundgesamtheit **und** Erhebungszeitraum. Eine Prozentzahl ohne
beides ist im Druck wertlos: Niemand kann sie einordnen, und ein Jahr spaeter
weiss niemand mehr, worauf sie sich bezog.

**Der Nenner ist je Befund ein anderer.** Wer durch alle Pruefungen teilt,
zaehlt ausgefallene Messungen als bestanden. Warum das falsch ist, steht in
`services/befund_haeufigkeit`.

    python3 tools/befunde-zaehlen.py            # alle abgeschlossenen Pruefungen
    python3 tools/befunde-zaehlen.py --ab 2026-08-01
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.befund_haeufigkeit import (  # noqa: E402
    aufteilen, haeufigkeit, kopfzeilen,
)

# Unter dieser Zahl ist ein Anteil keine Erhebung, sondern eine Anekdote.
# Der Wert ist eine Konvention dieses Werkzeugs, keine Regel des Standards —
# deshalb wird er benannt und nicht versteckt.
MINDESTZAHL = 20


def _json(wert) -> dict:
    if isinstance(wert, dict):
        return wert
    try:
        geladen = json.loads(wert or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return geladen if isinstance(geladen, dict) else {}


def _pruefungen(ab: str = "") -> tuple:
    from database import AuditResult, SessionLocal

    db = SessionLocal()
    try:
        abfrage = db.query(AuditResult).filter(AuditResult.status == "completed")
        if ab:
            abfrage = abfrage.filter(AuditResult.created_at >= ab)
        zeilen = [(_json(z.item_scores), _json(z.item_sources),
                   z.created_at, z.standard_version) for z in abfrage.all()]
        return aufteilen(zeilen)
    finally:
        db.close()


def main() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("--ab", default="", help="nur Pruefungen ab diesem Datum")
    argumente = zerleger.parse_args()

    auswertbar, verworfen = _pruefungen(argumente.ab)

    print(kopfzeilen(auswertbar, verworfen))
    print()

    # `haeufigkeit` bekommt weiterhin nur die beiden JSON-Felder.
    daten = [(z[0], z[1]) for z in auswertbar]

    if not daten:
        print("Keine **auswertbare** Pruefung — nichts zu rechnen. Zeilen auf "
              "„abgeschlossen\" ohne Kriterien zaehlen nicht mit; sie sahen "
              "bis zum 28.08.2026 wie eine Grundgesamtheit aus.")
        return 1

    for e in haeufigkeit(daten):
        if e["anteil"] is None:
            # Zwei verschiedene Gruende, die nicht vermengt werden duerfen:
            # kein Kriterium (dann steht der Vorbehalt dafuer) oder kein
            # Nenner (dann fehlt die Messung, und der Vorbehalt gilt trotzdem).
            grund = ("kein Kriterium traegt ihn allein" if not e["kriterium"]
                     else "keine auswertbare Pruefung")
            print(f"{e['nummer']:2}. {e['titel']}\n      — ohne Zahl: {grund}")
            if e["vorbehalt"]:
                print(f"      Vorbehalt: {e['vorbehalt']}")
            continue
        marke = "  " if e["nenner"] >= MINDESTZAHL else " !"
        print(f"{e['nummer']:2}.{marke}{e['anteil']:3} %  "
              f"({e['zaehler']} von {e['nenner']})  {e['titel']}")
        if e["vorbehalt"]:
            print(f"      Vorbehalt: {e['vorbehalt']}")

    print(f"\n„!\" heisst: weniger als {MINDESTZAHL} auswertbare Pruefungen. "
          "Solche Zeilen gehoeren nicht als Prozentzahl in ein Buch.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
