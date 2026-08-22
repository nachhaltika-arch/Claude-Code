#!/usr/bin/env python3
"""Ein echter Lauf gegen die angebundenen KI-Systeme — zum Nachsehen.

**Wozu.** Die Anfrageformen fuer ChatGPT und Perplexity stammen aus der
Herstellerdoku; ihre **Antwortformen** waren am 22.08.2026 nicht am lebenden
Dienst nachgestellt, weil kein Schluessel vorlag. `lies_openai_antwort` und
`lies_perplexity_antwort` sind deshalb tolerant gebaut: Sie liefern lieber
nichts als Unsinn. Genau das macht diesen Probelauf noetig — ein leeres
Ergebnis bei erfolgreichem Aufruf heisst, der Leser passt nicht.

**Aufruf** (der Schluessel bleibt in der Zeile, nicht in einer Datei):

    cd kompagnon/backend
    OPENAI_API_KEY=sk-... ./venv/bin/python tools/ki_sichtbarkeit_probe.py \\
        --name "Mustermann Heizung GmbH" \\
        --domain mustermann-heizung.de \\
        --gewerk Heizung --ort Kassel

Ohne Argumente laeuft ein Beispielbetrieb. Jede Frage kostet Geld, deshalb
ist die Voreinstellung **eine** Frage.

**Worauf zu achten ist.** Kommt der Aufruf durch, steht aber weder ein Auszug
noch ein Beleg da, dann hat der Dienst geantwortet und der Leser hat nichts
gefunden. Das ist der Fall, den dieses Werkzeug sichtbar machen soll — die
Rohantwort steht dann mit `--roh` daneben.
"""
import argparse
import asyncio
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from services.ki_anbieter import ANBIETER, anbieter_stand  # noqa: E402
from services.ki_sichtbarkeit import baue_fragen, pruefe_ki_sichtbarkeit  # noqa: E402


def _stand_zeigen() -> int:
    """Wer ist angebunden? Gibt die Zahl der angebundenen Systeme zurueck."""
    print("Angebundene Systeme")
    print("─" * 62)
    angebunden = 0
    for a in anbieter_stand():
        zeichen = "✓" if a["konfiguriert"] else "·"
        zustand = "angebunden" if a["konfiguriert"] else f"{a['env_name']} fehlt"
        print(f"  {zeichen} {a['anzeige']:12} {a['modell']:22} {zustand}")
        angebunden += bool(a["konfiguriert"])
    print()
    return angebunden


async def _lauf(args) -> int:
    angebunden = _stand_zeigen()
    if not angebunden:
        fehlend = ", ".join(a.env_name for a in ANBIETER)
        print(f"Kein System angebunden. Setze einen dieser Schluessel: {fehlend}")
        return 2

    fragen = baue_fragen(args.gewerk, args.ort, args.fragen)
    print(f"Gefragt wird ({len(fragen)} {'Frage' if len(fragen) == 1 else 'Fragen'}):")
    for f in fragen:
        print(f"  · {f}")
    print()

    befund = await pruefe_ki_sichtbarkeit(
        name=args.name, domain=args.domain, gewerk=args.gewerk,
        ort=args.ort, max_fragen=args.fragen,
    )

    if not befund.get("collected"):
        print(f"Nichts erhoben: {befund.get('grund')}")
        return 2

    leer = 0
    for schluessel, block in befund["anbieter"].items():
        print("─" * 62)
        if not block.get("collected"):
            print(f"{block.get('anzeige', schluessel)}: {block.get('grund')}")
            continue

        print(f"{block['anzeige']} ({block['modell']}) — "
              f"genannt bei {block['genannt_bei']} von {block['beantwortet']}, "
              f"{block['fehler']} Fehler")

        for eintrag in block["fragen"]:
            if eintrag["genannt"] is None:
                print(f"  ✗ Fehler: {eintrag.get('fehler', '')[:120]}")
                continue

            zeichen = "✓" if eintrag["genannt"] else "·"
            print(f"  {zeichen} {eintrag['frage'][:58]}")

            auszug = (eintrag.get("auszug") or "").strip()
            belege = eintrag.get("belege") or []
            if not auszug and not belege:
                leer += 1
                print("      ⚠ leer — der Dienst hat geantwortet, der Leser fand "
                      "nichts. Antwortform pruefen.")
            else:
                if auszug:
                    print(f"      Auszug: {auszug[:150]}")
                if belege:
                    print(f"      Belege: {', '.join(belege[:3])}")

    print("─" * 62)
    if leer:
        print(f"⚠ {leer} Antwort(en) blieben leer. Das ist der Fall, fuer den es "
              f"dieses Werkzeug gibt — mit --roh die Rohantwort ansehen.")
        return 1

    print("Alle Antworten wurden gelesen. Die Leser passen zur echten Form.")
    return 0


async def _roh(args) -> int:
    """Die unveraenderte Antwort eines Systems — wenn der Leser nichts fand."""
    from services import ki_anbieter

    frage = (baue_fragen(args.gewerk, args.ort, 1) or ["Wer bietet Heizung an?"])[0]

    for a in ki_anbieter.konfigurierte_anbieter():
        print("─" * 62)
        print(f"{a.anzeige}: {frage}")
        try:
            text, belege = await a.frage_stellen(frage)
            print(json.dumps({"text": text[:1200], "belege": belege},
                             ensure_ascii=False, indent=2))
        except Exception as fehler:  # noqa: BLE001
            print(f"  Fehler: {fehler}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="Mustermann Heizung GmbH")
    p.add_argument("--domain", default="mustermann-heizung.de")
    p.add_argument("--gewerk", default="Heizung")
    p.add_argument("--ort", default="Kassel")
    p.add_argument("--fragen", type=int, default=1,
                   help="Jede Frage kostet Geld (Voreinstellung: 1)")
    p.add_argument("--roh", action="store_true",
                   help="Die unveraenderte Antwort zeigen, statt sie zu lesen")
    args = p.parse_args()

    return asyncio.run(_roh(args) if args.roh else _lauf(args))


if __name__ == "__main__":
    raise SystemExit(main())
