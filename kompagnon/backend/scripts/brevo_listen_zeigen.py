#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zeigt die vorhandenen Brevo-Listen mit ihren Nummern. Ändert nichts.

    cd kompagnon/backend
    venv/bin/python -m scripts.brevo_listen_zeigen

Der Schlüssel kommt aus `BREVO_API_KEY` — aus der Umgebung oder aus der
lokalen `.env`. Er wird nicht ausgegeben.

**Warum es dieses Skript gibt.** `scripts/brevo_widget_listen.py` legt die
beiden Listen an, aber bei jedem Lauf neue — auch wenn der Name schon
dasteht. Wer nur die Nummern für `BREVO_LIST_VERIFIED_ID` und
`BREVO_LIST_OPTIN_ID` sucht, hätte damit zwei Listen zu viel und danach die
Frage, welche von beiden gilt. Also erst nachsehen, dann entscheiden.
"""
import sys

#: Die Namen, die `scripts/brevo_widget_listen.py` vergibt.
GESUCHT = {
    "KOMPAGNON Widget — Adresse bestätigt": "BREVO_LIST_VERIFIED_ID",
    "KOMPAGNON Widget — Marketing-Opt-in": "BREVO_LIST_OPTIN_ID",
}


def main() -> int:
    from services.brevo_service import BrevoError, BrevoService

    try:
        with BrevoService() as brevo:
            listen = brevo.listen()
    except BrevoError as fehler:
        print(f"Fehlgeschlagen: {fehler}", file=sys.stderr)
        return 1

    if not listen:
        print("Das Konto führt keine einzige Liste.")
        print("Dann legt `python -m scripts.brevo_widget_listen` sie an.")
        return 0

    print(f"{len(listen)} Liste(n) im Konto:\n")
    for eintrag in listen:
        name = eintrag.get("name", "")
        zeile = f"  {eintrag.get('id'):>6}  {name}"
        if name in GESUCHT:
            zeile += f"   ← {GESUCHT[name]}"
        print(zeile)

    gefunden = {e.get("name") for e in listen} & set(GESUCHT)
    fehlend = sorted(set(GESUCHT) - gefunden)
    print()
    if fehlend:
        # **Nicht stillschweigend übergehen.** Eine fehlende Liste sieht in
        # einer langen Aufzählung aus wie eine vorhandene, die man übersehen
        # hat — und das ist genau der Unterschied zwischen „Nummer eintragen"
        # und „erst anlegen".
        print("Noch nicht angelegt:")
        for name in fehlend:
            print(f"  · {name}  ({GESUCHT[name]})")
        print("\nAnlegen mit: venv/bin/python -m scripts.brevo_widget_listen")
    else:
        print("Beide Widget-Listen sind da — die Nummern oben gehören nach "
              "Render (Backend → Environment).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
