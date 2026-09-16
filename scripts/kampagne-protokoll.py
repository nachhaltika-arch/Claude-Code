#!/usr/bin/env python3
"""Zaehlt die Trichterstufe 3 und 5 aus Render-Protokollzeilen.

Gedacht fuer `/kampagne`, Schritt 1: Die Zeilen kommen aus
`mcp__render__list_logs` (Dienst `srv-da30dg3bc2fs73fomi0g`) und werden hier
gezaehlt statt im Kopf — eigene Zaehlungen von Hand haben zu oft danebengelegen.

Eingabe: eine oder mehrere Dateien als Argument, sonst stdin. Je Datei
entweder die ganze JSON-Antwort ({"logs": [...]}), eine Liste von Log-Objekten
oder JSON-Lines. Ausgabe: JSON mit den Zahlen.

    ./scripts/kampagne-protokoll.py --eigene-ip 1.2.3.4 seite1.json seite2.json

Mehrere Dateien werden **ueber die Log-ID entdoppelt**. Das ist der Grund, warum
es sie gibt: Render liefert hoechstens 100 Zeilen je Abruf, und der bequemste
Weg zum ganzen Tag sind zwei Abrufe von beiden Enden (`forward` und `backward`),
die sich in der Mitte ueberlappen. Ohne Entdopplung waere jede Zeile der
Ueberlappung doppelt gezaehlt.

Bewusst *keine* Bereinigung ohne Angabe: Ohne `--eigene-ip` ist
`aufrufe_bereinigt` nicht erhoben (null im Sinne von unbekannt), nicht 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BOT_MUSTER = re.compile(
    r"bot|crawler|spider|slurp|headless|curl/|wget|python-requests|"
    r"facebookexternalhit|preview|monitor|uptime|pingdom|lighthouse",
    re.IGNORECASE,
)
MOBIL_MUSTER = re.compile(r"Mobile|Android|iPhone|iPad", re.IGNORECASE)
IP_MUSTER = re.compile(r'clientIP="([^"]+)"')
UA_MUSTER = re.compile(r'userAgent="([^"]*)"')


def zeilen_lesen(roh: str) -> list[dict]:
    """Nimmt die drei Formen entgegen, in denen die Protokollzeilen ankommen."""
    roh = roh.strip()
    if not roh:
        return []
    try:
        daten = json.loads(roh)
    except json.JSONDecodeError:
        return [json.loads(z) for z in roh.splitlines() if z.strip()]
    if isinstance(daten, dict):
        return list(daten.get("logs", []))
    return list(daten)


def merkmal(eintrag: dict, name: str) -> str | None:
    for label in eintrag.get("labels", []):
        if label.get("name") == name:
            return label.get("value")
    return None


def auswerten(eintraege: list[dict], eigene_ips: frozenset[str]) -> dict:
    stufe3 = [e for e in eintraege if merkmal(e, "path") == "/api/widget/config"]
    stufe5 = [
        e
        for e in eintraege
        if merkmal(e, "path") == "/api/widget/audit" and merkmal(e, "method") == "POST"
    ]

    treffer = [
        (
            (IP_MUSTER.search(e.get("message", "")) or [None, None])[1],
            (UA_MUSTER.search(e.get("message", "")) or [None, ""])[1],
        )
        for e in stufe3
    ]
    bots = [t for t in treffer if t[1] and BOT_MUSTER.search(t[1])]
    eigene = [t for t in treffer if t[0] in eigene_ips]
    echte = [t for t in treffer if t not in bots and t not in eigene]

    status5 = sorted({merkmal(e, "statusCode") for e in stufe5 if merkmal(e, "statusCode")})

    # Eine Eingabe ohne *jede* audit-Zeile sagt nicht "null Leads", sondern
    # "nicht abgefragt": Wer nur `path=/api/widget/config` abruft, bekommt hier
    # sonst eine 0 gemeldet, die keine Messung ist. Beim Bauen genau so
    # passiert (16.09.) — der eigene Bericht behauptete 0 Leads aus einer
    # Datei, in der Leads gar nicht vorkommen konnten.
    audit_abgefragt = any(merkmal(e, "path") == "/api/widget/audit" for e in eintraege)

    # Besucher statt Aufrufe: Ein Besucher laedt das Widget oft mehrfach, ein
    # Link-Klick ist aber ein Besucher. Die Quote Klick -> Aufruf vergleicht
    # sonst zwei verschiedene Groessen und wird groesser als 1.
    bot_ips = {t[0] for t in bots if t[0]}
    besucher_roh = {t[0] for t in treffer if t[0]}
    besucher_bereinigt = besucher_roh - bot_ips - set(eigene_ips)

    return {
        "aufrufe_roh": len(stufe3),
        "ip_adressen": len(besucher_roh),
        "besucher_bereinigt": len(besucher_bereinigt) if eigene_ips else None,
        "mobil": sum(1 for t in treffer if MOBIL_MUSTER.search(t[1] or "")),
        "bots": len(bots),
        "eigene_testaufrufe": len(eigene) if eigene_ips else None,
        "aufrufe_bereinigt": len(echte) if eigene_ips else None,
        "leads": len(stufe5) if audit_abgefragt else None,
        "lead_statuscodes": status5 if audit_abgefragt else None,
        "leads_hinweis": (
            None
            if audit_abgefragt
            else "keine /api/widget/audit-Zeile in der Eingabe — getrennt abfragen, "
            "das ist nicht erhoben und keine Null"
        ),
        "hinweis": (
            "ohne --eigene-ip ist die Bereinigung nicht erhoben (null), nicht 0"
            if not eigene_ips
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eigene-ip",
        action="append",
        default=[],
        help="eigene Test-IP, mehrfach angebbar; ohne sie bleibt die Bereinigung leer",
    )
    parser.add_argument(
        "dateien",
        nargs="*",
        help="Protokolldateien; ohne Angabe wird von stdin gelesen",
    )
    argumente = parser.parse_args()

    try:
        roh = [
            zeilen_lesen(Path(datei).read_text())
            for datei in argumente.dateien
        ] or [zeilen_lesen(sys.stdin.read())]
    except (json.JSONDecodeError, TypeError) as fehler:
        print(f"Protokollzeilen nicht lesbar: {fehler}", file=sys.stderr)
        return 2
    except OSError as fehler:
        print(f"Datei nicht lesbar: {fehler}", file=sys.stderr)
        return 2

    eintraege, gesehen, doppelt = [], set(), 0
    for seite in roh:
        for eintrag in seite:
            kennung = eintrag.get("id")
            if kennung is not None and kennung in gesehen:
                doppelt += 1
                continue
            if kennung is not None:
                gesehen.add(kennung)
            eintraege.append(eintrag)

    if not eintraege:
        print("Keine Protokollzeilen auf stdin.", file=sys.stderr)
        return 2

    ergebnis = auswerten(eintraege, frozenset(argumente.eigene_ip))
    ergebnis["seiten"] = len(roh)
    ergebnis["entdoppelt"] = doppelt
    print(json.dumps(ergebnis, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
