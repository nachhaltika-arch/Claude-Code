#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Zeigt das ausgelieferte Frontend auf das Backend — oder auf sich selbst? (L-145)

**Warum es das gibt.** Am 2026-08-28 stand `REACT_APP_API_URL` am Dienst
`kompagnon-frontend` auf `https://kas.kompagnon.group` — auf das Frontend
**selbst** statt auf das Backend. Jede API-Anfrage landete auf der Static
Site, bekam HTML statt JSON, und die Oberflaeche meldete
„Verbindungsfehler". Produktiv war 40 Minuten lang niemand anmeldbar.

**Warum nichts davon auffiel.** Der Rueckfall in `config.js` haelt den
richtigen Wert, aber die Variable war ja *gesetzt*, nur falsch — ein
Rueckfall greift bei Abwesenheit, nicht bei Unsinn. Und `/health` des
Backends war die ganze Zeit gruen (200 in 0,19 s), denn das Backend war nie
das Problem. Es gibt keine Stelle, an der ein Frontend meldet, dass es mit
niemandem spricht.

**Die Messung ist billig und braucht keine Zugangsdaten** — das Paket ist
oeffentlich abrufbar. Gelesen wird die API-Basis **ausdruecklich** aus dem
Modul, zu dem `config.js` uebersetzt wird, und dann verglichen.

**Zwei Irrwege, die beim Bau ausprobiert und verworfen wurden** — sie stehen
hier, weil beide ueberzeugend aussehen:

*Erstens: „das erwartete Backend muss im Paket vorkommen".* Zu schwach. Im
kaputten Paket vom 28.08. kam `api.kompagnon.group` vor — nur eben innerhalb
einer laengeren Adresse (`…/api/payments/create-checkout`) in einem
Anzeigetext. Eine Teilstring-Suche haette den Ausfall durchgewinkt.

*Zweitens: „die eigene Herkunft darf nicht im Paket vorkommen".* Falsch
positiv. Produktiv wird dasselbe Paket unter **zwei** Adressen ausgeliefert,
und `kompagnon-frontend.onrender.com` steht darin voellig zu Recht — in
Adresslisten der Anwendung. Die Regel haette bei jedem Lauf Alarm geschlagen.

**Wenn die Basis nicht bestimmbar ist, ist das ein Befund, kein Gruen.** Der
Minifizierer koennte die Form aendern; dann muss dieses Werkzeug sagen, dass
es nicht messen konnte, statt stillschweigend durchzulassen.

**Warum kein CI-Tor.** Ein Prueflauf, der bei jedem Push fremde Hosts abruft,
wird rot, wenn einer kurz nicht antwortet — und ein Tor, das aus fremden
Gruenden rot wird, wird abgeschaltet. Dieselbe Ueberlegung wie bei
`tools/blueprint_abgleich.py` (L-35). Was ohne Netz geht, haelt
`tests/test_api_basis.py` bei jedem Lauf fest.

Aufruf im Backend-Verzeichnis, nach einem Deploy oder wenn etwas komisch
aussieht:

    ./venv/bin/python tools/api_basis_pruefen.py
"""
import re
import sys
import urllib.error
import urllib.request

#: (Name, Herkunft des Frontends, erwartetes Backend)
UMGEBUNGEN = (
    ("produktiv",
     "https://kas.kompagnon.group",
     "https://api.kompagnon.group"),
    ("staging",
     "https://kompagnon-frontend-staging.onrender.com",
     "https://kompagnon-backend-staging.onrender.com"),
)

#: Produktiv liegt dasselbe Paket unter einer zweiten Adresse. Sie einzeln zu
#: pruefen brachte nichts — es ist derselbe Gegenstand. Geprueft wird
#: stattdessen, dass es **wirklich** derselbe ist; liefe sie auseinander,
#: waere die Messung oben nur noch fuer die halbe Produktion gueltig.
ZWEITNAME = ("https://kas.kompagnon.group",
             "https://kompagnon-frontend.onrender.com")

#: Webpack uebersetzt `config.js` zu einem Modul, das genau eine Zeichenkette
#: exportiert: `….d(t,{A:()=>r});const r="https://…"`. Die Buchstaben kommen
#: vom Minifizierer und koennen sich aendern — deshalb wird der Rueckverweis
#: mitgeprueft (`\1`) und ein Fehlschlag als Befund gemeldet, nicht als Gruen.
MUSTER = re.compile(
    r'\.d\([a-zA-Z_$]+,\{[a-zA-Z_$]+:\(\)=>([a-zA-Z_$]+)\}\);'
    r'const \1="(https?://[^"]*)"')


def basis_aus_paket(paket: str):
    """Die API-Basis, wie sie im ausgelieferten Paket steht — oder None."""
    treffer = MUSTER.findall(paket)
    ziele = {ziel for _, ziel in treffer}
    if len(ziele) != 1:
        return None
    return ziele.pop()


def pruefe_paket(paket: str, erwartetes_backend: str) -> list:
    """Die eigentliche Pruefung — ohne Netz, damit sie pruefbar ist.

    Gibt die Liste der Maengel zurueck; leer heisst in Ordnung. Bewusst als
    reine Funktion: Ein Waechter, den man nur gegen die Wirklichkeit laufen
    lassen kann, laesst sich nicht daraufhin pruefen, ob er anschlaegt.
    """
    basis = basis_aus_paket(paket)
    if basis is None:
        return ["die API-Basis liess sich im Paket nicht bestimmen — "
                "Muster pruefen, nicht als in Ordnung werten"]
    if basis != erwartetes_backend:
        return [f"die API-Basis ist {basis}, erwartet {erwartetes_backend}"]
    return []


def _hole(adresse: str) -> str:
    with urllib.request.urlopen(adresse, timeout=30) as antwort:
        return antwort.read().decode("utf-8", "replace")


def paketname(herkunft: str) -> str:
    """Die Startseite nennt das Paket; sein Name aendert sich mit jedem Bau."""
    treffer = re.search(r"static/js/main\.[a-z0-9]+\.js", _hole(herkunft + "/"))
    if not treffer:
        raise LookupError(f"{herkunft}: kein main.*.js in der Startseite")
    return treffer.group(0)


def main() -> int:
    fehler = 0

    for name, herkunft, backend in UMGEBUNGEN:
        try:
            paket = paketname(herkunft)
            inhalt = _hole(f"{herkunft}/{paket}")
        except (urllib.error.URLError, LookupError, OSError) as f:
            print(f"  ?  {name}: nicht erreichbar — {f}")
            fehler += 1
            continue

        maengel = pruefe_paket(inhalt, backend)
        if maengel:
            fehler += 1
            print(f"  ✗  {name} ({paket})")
            for m in maengel:
                print(f"       {m}")
        else:
            print(f"  ✓  {name} ({paket}) → {backend}")

    try:
        namen = {adresse: paketname(adresse) for adresse in ZWEITNAME}
        if len(set(namen.values())) == 1:
            print(f"  ✓  Zweitname liefert dasselbe Paket "
                  f"({next(iter(namen.values()))})")
        else:
            fehler += 1
            print("  ✗  Zweitname liefert ein **anderes** Paket:")
            for adresse, paket in namen.items():
                print(f"       {adresse} → {paket}")
    except (urllib.error.URLError, LookupError, OSError) as f:
        print(f"  ?  Zweitname nicht pruefbar — {f}")
        fehler += 1

    print()
    if fehler:
        print(f"{fehler} Befund(e). REACT_APP_API_URL am betroffenen Dienst "
              f"pruefen — der Wert wird beim **Bauen** gelesen, ein Neustart "
              f"genuegt nicht.")
    else:
        print("Alle Frontends sprechen mit ihrem Backend.")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
