#!/usr/bin/env python3
"""Zaehlt die Trichterstufe 3 und 5 aus Render-Protokollzeilen.

Gedacht fuer `/kampagne`, Schritt 1: Die Zeilen kommen aus
`mcp__render__list_logs` (Dienst `srv-da30dg3bc2fs73fomi0g`) und werden hier
gezaehlt statt im Kopf — eigene Zaehlungen von Hand haben zu oft danebengelegen.

Eingabe auf stdin: entweder die ganze JSON-Antwort ({"logs": [...]}) oder eine
Liste von Log-Objekten oder JSON-Lines. Ausgabe: JSON mit den Zahlen.

    mcp-Antwort speichern, dann:
    ./scripts/kampagne-protokoll.py --eigene-ip 1.2.3.4 --eigene-ip 5.6.7.8 < lauf.json

Bewusst *keine* Bereinigung ohne Angabe: Ohne `--eigene-ip` ist
`aufrufe_bereinigt` nicht erhoben (null im Sinne von unbekannt), nicht 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

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

    return {
        "aufrufe_roh": len(stufe3),
        "ip_adressen": len({t[0] for t in treffer if t[0]}),
        "mobil": sum(1 for t in treffer if MOBIL_MUSTER.search(t[1] or "")),
        "bots": len(bots),
        "eigene_testaufrufe": len(eigene) if eigene_ips else None,
        "aufrufe_bereinigt": len(echte) if eigene_ips else None,
        "leads": len(stufe5),
        "lead_statuscodes": status5,
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
    argumente = parser.parse_args()

    try:
        eintraege = zeilen_lesen(sys.stdin.read())
    except (json.JSONDecodeError, TypeError) as fehler:
        print(f"Protokollzeilen nicht lesbar: {fehler}", file=sys.stderr)
        return 2

    if not eintraege:
        print("Keine Protokollzeilen auf stdin.", file=sys.stderr)
        return 2

    ergebnis = auswerten(eintraege, frozenset(argumente.eigene_ip))
    print(json.dumps(ergebnis, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
