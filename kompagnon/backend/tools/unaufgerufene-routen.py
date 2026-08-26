#!/usr/bin/env python3
"""Welche Route ruft niemand auf? (L-101)

    cd kompagnon/backend
    ./venv/bin/python tools/unaufgerufene-routen.py
    ./venv/bin/python tools/unaufgerufene-routen.py --alle   # auch die erklärten

**Warum es dieses Werkzeug gibt.** „Gebaut, nicht angeschlossen" ist in
diesem System eine eigene Fehlerfamilie, und sie wurde bisher jedes Mal von
Hand gefunden:

* **L-55** — ein Wächter, den niemand aufrief
* **L-79** — die seitenweise Freigabe ist erreichbar, nur ruft sie keiner
* **L-11** — ``_fernet_available()`` wurde nie gerufen und beim Aufräumen
  als überflüssig gelöscht; sie war nicht überflüssig, sondern nicht
  angeschlossen
* **24.08.2026** — ``POST /api/projects/{id}/time``: Die Margenrechnung hängt
  an diesen Stunden, und im ganzen Frontend ruft sie niemand ein

Viermal derselbe Fund. Eine Route, die niemand aufruft, ist kein Fehler —
aber sie ist eine **Frage**, und die soll nicht vom Zufall abhängen.

**Das Gegenstück** ist ``tests/test_frontend_adressen.py``: Es prüft, dass
jeder Aufruf des Frontends eine Route trifft. Beide lesen dieselbe Grundlage
(``tools/adressen.py``), damit sie nicht auseinanderdriften.

**Warum kein Test.** „Ruft niemand auf" ist oft genau richtig: Webhooks
kommen von außen, das Widget lebt auf fremden Seiten, Portalrouten hängen an
einem Einmal-Token, der Scheduler ruft intern. Ein Test wäre dauerhaft rot
oder bekäme eine Ausnahmeliste, die niemand pflegt. Dieses Werkzeug sortiert
stattdessen: Was von außen gerufen wird, steht unter „erklärt"; alles andere
ist eine offene Frage.
"""
import pathlib
import sys

# Wie die Nachbarwerkzeuge: Das Backend liegt eine Ebene hoeher, und von dort
# kommen `main` und `tools.adressen`.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools.adressen import (  # noqa: E402
    importe_je_modul,
    gerufene_adressen,
    normalisieren,
    trifft_ende,
    routen_mit_funktion,
    routen_mit_methode,
    weitere_aufrufer,
)

#: Adressen, die planmäßig nicht aus dem Frontend gerufen werden.
#: Jede Gruppe braucht einen Grund — sonst wird die Liste zum Ablagefach.
ERKLAERT = (
    ("/api/webhooks/", "Webhook — wird von aussen gerufen (Stripe, Brevo, Netlify)"),
    ("/api/widget/", "Widget — lebt eingebettet auf fremden Seiten"),
    ("/api/portal/", "Kundenportal — haengt am Einmal-Token aus der Mail"),
    ("/api/public/", "Oeffentlich — Landingpage und Freigabelinks"),
    # **Nicht ohne Zugang, nur mit einem anderen Aufrufer (24.08.2026).**
    # Am 24.08. stand `design-canvas` als „ganzes Merkmal ohne Oberflaeche" in
    # der Liste. Der Kopf des Routers sagt es anders: Ein Canvas entsteht in
    # **Claude Code** und wird als Artifact abgelegt; dieser Router liefert
    # die Dateien und nimmt sie bearbeitet zurueck. Der Aufrufer ist das
    # Werkzeug `DesignSync`, nicht der Browser — deshalb findet ihn kein
    # Suchlauf im Frontend, und deshalb ist er hier erklaert und kein Befund.
    ("/api/design-canvas/", "Design-Canvas — wird aus Claude Code gerufen (DesignSync), nicht aus dem Browser"),
    ("/api/health", "Betriebspruefung"),
    ("/health", "Betriebspruefung"),
    ("/docs", "FastAPIs eigene Oberflaeche"),
    ("/redoc", "FastAPIs eigene Oberflaeche"),
    ("/openapi.json", "FastAPIs eigenes Schema"),
)


#: Ein Aufrufer, den kein Suchlauf hier findet: Die WebSprint-Landingpage
#: liegt auf fremdem Apache und **nicht in diesem Repo** (L-20). Sie holt ihr
#: Gratis-Audit über `/api/audit/{id}` und `/api/audit/status/{id}` (L-52).
#: Solange das so ist, sieht jede Messung von hier aus diese Routen als
#: ungerufen — sie sind es nicht. Das ist kein Fehler des Werkzeugs, sondern
#: der Preis dafür, dass eine Verkaufsseite außerhalb der Quellversionierung
#: lebt.
AUSSERHALB_DES_REPOS = ("/api/audit/status/", "/api/audit/{audit_id}")


def _modul_des_handlers(main, methode: str, pfad: str) -> str:
    """In welchem Modul steht der Handler? — fuer den Selbstaufruf-Ausschluss."""
    def suchen(routen, praefix=""):
        for route in routen:
            eingebunden = getattr(route, "original_router", None)
            if eingebunden is not None:
                kontext = getattr(route, "include_context", None)
                gefunden = suchen(eingebunden.routes,
                                  praefix + (getattr(kontext, "prefix", "") or ""))
                if gefunden:
                    return gefunden
                continue
            if praefix + (getattr(route, "path", "") or "") != pfad:
                continue
            if methode not in (getattr(route, "methods", None) or ()):
                continue
            return getattr(getattr(route, "endpoint", None), "__module__", "")
        return ""

    return suchen(main.app.routes)


def _erklaerung(pfad: str):
    for anfang, grund in ERKLAERT:
        if pfad.startswith(anfang):
            return grund
    return None


def main(argv: list) -> int:
    alle = "--alle" in argv

    gerufen = gerufene_adressen()
    weitere = weitere_aufrufer()
    routen = routen_mit_methode()
    funktionen = routen_mit_funktion()
    importe = importe_je_modul()

    import main  # fuer endpoint.__module__

    def _intern(methode: str, pfad: str):
        """Ruft Backend-Code diesen Handler direkt auf, statt ueber HTTP?"""
        name = funktionen.get((methode, pfad))
        if not name:
            return None
        eigene = _modul_des_handlers(main, methode, pfad)
        fremde = {m for m in importe.get((eigene, name), set()) if m != eigene}
        return f"{name}() aus {', '.join(sorted(fremde))}" if fremde else None

    def _ueber_variable(adresse: str):
        """Trifft ein Aufruf diese Route nur ueber einen Platzhalter?

        **Warum das eine eigene Gruppe wird und kein stiller Abzug
        (26.08.2026).** `passt_auf` laesst `{}` auf **beiden** Seiten gelten.
        Der Knopf fuer die Mailstrecke baut die Aktion in den Pfad
        (`/api/leads/${leadId}/sequence/${action}`) und trifft damit
        `start`, `pause` und `stop` — richtig so. Ein Aufruf
        `/api/projects/${id}/${was}` traefe aber ebenso **jede**
        Projektroute mit zwei Abschnitten.

        Ein Werkzeug, das zu wenig meldet, ist schlimmer als eines, das zu
        viel meldet: Es sagt „alles angeschlossen", wo niemand nachgesehen
        hat. Deshalb wird der Treffer gezeigt, nicht verrechnet.

        **Und nur Aufrufe, die sonst nirgends landen, zaehlen hier.** Die
        erste Fassung nahm alle und meldete 57 Treffer, fast durchweg Unsinn:
        `/api/leads/befunde-nachtragen` „gerufen als `/api/leads/{}`" — der
        Platzhalter eines **anderen** Aufrufs, der laengst seine eigene Route
        trifft (`/api/leads/{lead_id}`). Wer schon exakt landet, wird nicht
        zusaetzlich anderen Routen gutgeschrieben. `/api/leads/{}/sequence/{}`
        dagegen trifft **keine** Route genau — also loest es sich zur Laufzeit
        in `start`, `pause` oder `stop` auf.
        """
        for gerufene in offene_aufrufe:
            if gerufene == adresse:
                continue
            # Einseitig, aus demselben Grund wie unten: symmetrisch traefe
            # `/{}/{}/editor` jede dreiteilige Route, die auf einen Parameter
            # endet — das Wort `editor` verschwaende im Platzhalter der Route.
            if trifft_ende(gerufene.strip("/").split("/"),
                            adresse.strip("/").split("/")):
                return gerufene

        # Eine Variable kann auch fuer **mehrere** Abschnitte stehen.
        # `GrapesEditor` ruft `${API_BASE_URL}${endpointBase}/${pageId}/editor`
        # auf, und `endpointBase` ist `/api/pages` oder `/api/kas/pages` — die
        # Adresse wird zu `/{}/{}/editor` und hat damit **weniger** Abschnitte
        # als die Route. Abschnittsweise verglichen passt sie auf keine, und
        # fuenf angeschlossene Routen standen als „ruft niemand auf" da.
        #
        # Erkennbar ist der Fall am Platzhalter an **erster** Stelle: Keine
        # echte Route beginnt mit einem Parameter, alle mit `api`. Verglichen
        # wird dann nur der Rest gegen das Ende der Route.
        #
        # **Nur wenn der Aufruf genau eine Route trifft.** `/{}/{}/editor`
        # passt auf **26** Routen — es sagt damit ueber keine einzelne etwas
        # aus. Sie trotzdem alle gutzuschreiben senkte die Zahl von 109 auf
        # 85 und war die Untermessung, die dieses Werkzeug gerade vermeiden
        # sollte. Mehrdeutige Aufrufe stehen unten als Hinweis; die Routen
        # bleiben in „Ruft niemand".
        eigene = adresse.strip("/").split("/")
        for gerufene in eindeutige_variablenaufrufe:
            rest = gerufene.strip("/").split("/")[1:]
            if len(rest) >= len(eigene) or not rest:
                continue
            if trifft_ende(rest, eigene[-len(rest):]):
                return gerufene
        return None

    #: Aufrufe, die auf keine Route genau passen — nur die duerfen ueber
    #: Platzhalter zugeordnet werden. Siehe `_ueber_variable`.
    alle_adressen = {normalisieren(p) for _, p in routen}
    # Eine Adresse, die **nur** aus Platzhaltern besteht (`/{}` aus
    # `apiCall(url)` in `AuthContext`), sagt ueber keine Route etwas aus und
    # traf sonst jede mit gleicher Abschnittszahl.
    offene_aufrufe = {g for g in gerufen
                      if g not in alle_adressen
                      and set(g.strip("/").split("/")) != {"{}"}}

    # Aufrufe, deren Anfang eine Variable ist (`${endpointBase}/...`). Sie
    # werden am **Ende** der Route verglichen — aber nur, wenn dabei genau
    # eine Route herauskommt. Siehe `_ueber_variable`.
    eindeutige_variablenaufrufe, mehrdeutige = [], []
    for gerufene in offene_aufrufe:
        teile = gerufene.strip("/").split("/")
        if not teile or teile[0] != "{}" or len(teile) < 2:
            continue
        rest = teile[1:]
        treffer = [p for _, p in routen
                   if len(normalisieren(p).strip("/").split("/")) > len(rest)
                   and trifft_ende(rest, normalisieren(p).strip("/")
                                    .split("/")[-len(rest):])]
        if len(set(treffer)) == 1:
            eindeutige_variablenaufrufe.append(gerufene)
        elif treffer:
            mehrdeutige.append((gerufene, len(set(treffer))))

    offen, intern, nur_rand, erklaert, ueber_variable = [], [], [], [], []
    for methode, pfad in routen:
        adresse = normalisieren(pfad)
        if adresse in gerufen:
            continue
        treffer = _ueber_variable(adresse)
        if treffer:
            ueber_variable.append((methode, pfad, treffer))
            continue
        grund = _erklaerung(pfad)
        if grund:
            erklaert.append((methode, pfad, grund))
            continue
        woher = _intern(methode, pfad)
        if woher:
            intern.append((methode, pfad, woher))
        elif adresse in weitere:
            nur_rand.append((methode, pfad, ", ".join(sorted(weitere[adresse]))))
        else:
            offen.append((methode, pfad, None))

    for liste in (offen, nur_rand, erklaert, ueber_variable):
        liste.sort(key=lambda e: (e[1], e[0]))

    print(f"Backend: {len(routen)} Endpunkte · Frontend ruft "
          f"{len(gerufen)} verschiedene Adressen, "
          f"Widget und E2E weitere {len(weitere)}")

    print(f"\nRuft niemand — {len(offen)}:")
    if not offen:
        print("  keine")
    for methode, pfad, _ in offen:
        print(f"  {methode:<7} {pfad}")

    if mehrdeutige:
        print("\nAufrufe, deren Anfang eine Variable ist und die auf mehrere")
        print("Routen passen — sie sagen ueber keine einzelne etwas aus:")
        for gerufene, anzahl in sorted(mehrdeutige):
            print(f"  {gerufene}  ({anzahl} moegliche Routen)")

    print(f"\nNur ueber eine Variable im Pfad getroffen — {len(ueber_variable)}:")
    print("  (Der Aufruf baut einen Abschnitt zur Laufzeit zusammen. Meist ist")
    print("   das genau richtig — aber ein Aufruf mit zwei Platzhaltern trifft")
    print("   auch Routen, die niemand meint. Von Hand beurteilen.)")
    if not ueber_variable:
        print("  keine")
    for methode, pfad, treffer in ueber_variable:
        print(f"  {methode:<7} {pfad}\n            gerufen als {treffer}")

    print(f"\nNicht ueber HTTP, aber aus Backend-Code gerufen — {len(intern)}:")
    if not intern:
        print("  keine")
    for methode, pfad, woher in intern:
        print(f"  {methode:<7} {pfad}\n            {woher}")

    print(f"\nNur von E2E oder Widget gerufen, nicht aus der "
          f"Oberflaeche — {len(nur_rand)}:")
    if not nur_rand:
        print("  keine")
    for methode, pfad, woher in nur_rand:
        print(f"  {methode:<7} {pfad}\n            {woher}")

    print(f"\nErklaert — {len(erklaert)} (mit --alle einzeln):")
    if alle:
        for methode, pfad, grund in erklaert:
            print(f"  {methode:<7} {pfad}\n            {grund}")
    else:
        gruende = {}
        for _, _, grund in erklaert:
            gruende[grund] = gruende.get(grund, 0) + 1
        for grund, anzahl in sorted(gruende.items(), key=lambda g: -g[1]):
            print(f"  {anzahl:>4}  {grund}")

    print("\nEine Route ohne Aufrufer ist kein Fehler — sie ist eine Frage: "
          "\nfehlt der Knopf, oder ist die Route ueberfluessig geworden?")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
