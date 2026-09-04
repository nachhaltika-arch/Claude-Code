#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wie viele begonnene Briefings werden eingereicht? (L-14, Erfolgskriterium 4.3)

    cd kompagnon/backend
    ./venv/bin/python ../../tools/briefing-abschlussquote.py

**Warum es diese Zahl braucht.** Der Projekt-Assistent (Ausbau 1) ist gebaut,
und § 4.3 der Anforderungen nennt als Erfolgskriterium die **Abschlussquote
des Briefings**. Gemessen wurde sie nie. Ohne Ausgangswert lässt sich später
kein Vorher/Nachher zeigen — man hat dann eine Zahl und nichts, woran sie
hängt.

**Der Vergleich läuft innerhalb desselben Zeitraums, nicht davor/danach**
(Entscheidung 01.09.2026). Ein Vorher/Nachher über die Zeit vergleicht auch
alles andere mit, was sich zwischendurch geändert hat — andere Kunden, andere
Gewerke, ein umgebautes Formular. Verglichen werden deshalb **Betriebe mit
Assistenten-Gespräch gegen Betriebe ohne**. Die Verbindung dafür gibt es
bereits: `assistant_conversations.lead_id` und `briefings.lead_id` zeigen auf
denselben Betrieb — es musste nichts dafür gebaut werden.

**Was diese Zahl nicht ist: ein Beweis.** Wer den Assistenten benutzt, hat
sich dafür entschieden; das ist eine Auswahl und kein Zufall. Die Zahl zeigt
einen Unterschied, keine Ursache. Sie so zu lesen, als belege sie Wirkung,
wäre dieselbe Sorte Fehler wie eine Restzahl auf einer Annahme.

**Sie läuft gegen die eingestellte Datenbank.** Lokal sind zu wenige Zeilen
für eine Aussage — die Zahl, auf die es ankommt, entsteht am Produktivbestand,
und der ist von hier aus nicht erreichbar (siehe L-53). Das Werkzeug sagt
selbst, wenn die Grundgesamtheit zu klein ist, statt eine Quote aus drei
Zeilen zu melden.
"""
import pathlib
import sys

WURZEL = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "kompagnon" / "backend"))

#: Unterhalb dieser Zahl wird keine Quote ausgewiesen. Eine Prozentzahl aus
#: vier Zeilen springt bei jeder einzelnen um 25 Punkte — sie sieht aus wie
#: eine Messung und ist eine Zufallszahl.
MINDESTMENGE = 10

#: Ein Briefing gilt als abgeschlossen, sobald es eingereicht ist.
#: `routers/briefings.py` kennt genau zwei Werte: `entwurf` und `eingereicht`.
EINGEREICHT = "eingereicht"


def _quote(fertig: int, gesamt: int):
    return None if gesamt == 0 else round(100.0 * fertig / gesamt, 1)


def _zeile(name: str, fertig: int, gesamt: int) -> str:
    q = _quote(fertig, gesamt)
    if gesamt < MINDESTMENGE:
        return (f"  {name:<28}{fertig:>4} von {gesamt:<5} "
                f"— zu wenige für eine Quote (unter {MINDESTMENGE})")
    return f"  {name:<28}{fertig:>4} von {gesamt:<5} = {q:>5} %"


def main() -> int:
    from database import SessionLocal
    from modelle_assistent import AssistantConversation
    from modelle_briefing import Briefing

    db = SessionLocal()
    try:
        briefings = db.query(Briefing).all()
        mit_gespraech = {
            k for (k,) in db.query(AssistantConversation.lead_id)
                            .filter(AssistantConversation.lead_id.isnot(None))
                            .distinct().all()
        }
    finally:
        db.close()

    gesamt = len(briefings)
    fertig = sum(1 for b in briefings if (b.status or "") == EINGEREICHT)

    mit = [b for b in briefings if b.lead_id in mit_gespraech]
    ohne = [b for b in briefings if b.lead_id not in mit_gespraech]

    print("Abschlussquote des Briefings (L-14, Erfolgskriterium 4.3)\n")
    print(_zeile("insgesamt", fertig, gesamt))
    print(_zeile("mit Assistenten-Gespräch",
                 sum(1 for b in mit if (b.status or "") == EINGEREICHT), len(mit)))
    print(_zeile("ohne Assistenten-Gespräch",
                 sum(1 for b in ohne if (b.status or "") == EINGEREICHT), len(ohne)))

    if gesamt < MINDESTMENGE:
        print(f"\nDie Grundgesamtheit ist {gesamt}. Das ist keine Messung, "
              f"sondern eine Stichprobe — die Zahl, auf die es ankommt, "
              f"entsteht am Produktivbestand.")
    print("\nEin Unterschied ist kein Beweis: Wer den Assistenten benutzt, hat "
          "sich dafür entschieden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
