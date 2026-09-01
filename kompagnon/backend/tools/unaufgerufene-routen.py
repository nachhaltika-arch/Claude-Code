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

#: Adressen, die ein Suchlauf im Frontend planmaessig nicht findet — weil sie
#: von aussen gerufen werden oder weil der Aufrufer die Adresse zur Laufzeit
#: zusammensetzt. Jede Gruppe braucht einen Grund, und der Grund muss
#: **nachgemessen** sein: Am 01.09.2026 stand hier eine Ausnahme, deren
#: Begruendung nicht mehr zutraf (siehe `AUSSERHALB_DES_REPOS`). Sonst wird
#: die Liste zum Ablagefach, und ein Ablagefach gibt keinen Alarm.
ERKLAERT = (
    ("/api/webhooks/", "Webhook — wird von aussen gerufen (Stripe, Brevo, Netlify)"),
    # **Zwei weitere Rufe von aussen (26.08.2026).** Beide standen unter
    # „ruft niemand auf", obwohl sie taeglich gerufen werden — nur eben von
    # Brevo, nicht vom Browser. Sie weisen sich mit einem Geheimnis im Pfad
    # aus, weil Brevo seine Webhooks nicht signiert.
    ("/api/mail-events/", "Brevo meldet Zustellstoerungen — Geheimnis im Pfad"),
    ("/api/posteingang/", "Brevo liefert eingehende Kundenmails — Geheimnis im Pfad"),
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
    ("/api/ping", "Betriebspruefung"),
    ("/info", "Betriebspruefung — seit 15.08.2026 nur Wahrheitswerte"),
    ("/robots.txt", "Suchmaschinen"),
    ("/docs", "FastAPIs eigene Oberflaeche"),
    ("/redoc", "FastAPIs eigene Oberflaeche"),
    ("/openapi.json", "FastAPIs eigenes Schema"),
    # **Vier Stripe-Rueckrufe (01.09.2026).** Sie standen alle vier unter
    # „ruft niemand auf" — und das ist bei einem Webhook der Normalzustand.
    # `/api/webhooks/` deckte sie nicht, weil jede Kasse ihren Rueckruf im
    # eigenen Router traegt. Jeder weist sich mit einer Signatur aus; das
    # Geheimnis gehoert der jeweils eingetragenen Adresse (siehe den Kopf von
    # `routers/buch.py`).
    ("/api/payments/webhook", "Stripe meldet die Zahlung — Signatur im Kopf"),
    ("/api/shop/webhook", "Stripe meldet die Zahlung — Signatur im Kopf"),
    ("/api/book/webhook", "Stripe meldet die Zahlung — Signatur im Kopf"),
    ("/api/geo-payments/webhook", "Stripe meldet die Zahlung — Signatur im Kopf"),
    # **Drei Links, die in einer Mail stehen (01.09.2026).** Kein Bildschirm
    # ruft sie; der Kaeufer klickt sie im Postfach. Belegt an der Stelle, die
    # sie schreibt: `routers/shop.py:288` und `:304` bauen die beiden ersten
    # in die Bestellbestaetigung.
    ("/api/shop/download/", "Abruflink aus der Bestellbestaetigung"),
    ("/api/shop/orders/", "Auskunft und Rechnung — Link aus der Mail, Token im Pfad"),
    ("/api/files/portal/", "Kundenportal — haengt am Einmal-Token aus der Mail"),
    # **Die Basis ist eine Eigenschaft, kein fester Text (01.09.2026).** Das
    # Werkzeug meldete `/{}/{}/editor` als Aufruf, der auf zwei Routen passt
    # und ueber keine etwas sagt — und beide Routenpaare standen daneben als
    # „ruft niemand auf". Nachgesehen: `components/GrapesEditor.jsx` baut
    # `${endpointBase}/${pageId}/editor`, und `endpointBase` ist ein Parameter
    # mit der Vorgabe `/api/pages`; `pages/KasWebsite.jsx` uebergibt
    # `/api/kas/pages`. **Beide Paare werden also wirklich gerufen** — GET zum
    # Laden, POST zum Speichern. Kein Befund, sondern die Antwort auf die
    # Frage, die das Werkzeug selbst gestellt hat.
    ("/api/pages/{page_id}/editor", "GrapesEditor — Basis kommt als Eigenschaft"),
    ("/api/kas/pages/{page_id}/editor", "GrapesEditor auf der Agenturseite — Basis kommt als Eigenschaft"),
)


#: Aufrufer, die kein Suchlauf hier findet, weil sie ausserhalb des Repos
#: leben.
#:
#: **Am 01.09.2026 leer geworden — und das ist ein Befund, kein Aufraeumen.**
#: Hier standen `/api/audit/status/` und `/api/audit/{audit_id}` mit der
#: Begruendung, die WebSprint-Landingpage (L-20) hole ihr Gratis-Audit
#: darueber. **An der Live-Seite nachgemessen stimmt das nicht mehr:**
#: `https://websprint.kompagnon.eu` enthaelt keinen einzigen `/api/`-Aufruf.
#: Sie bettet stattdessen `kas.kompagnon.group/embed/audit-widget.html` als
#: iframe ein, und dieses Widget ruft ausschliesslich `/api/widget/*` — das
#: ist bereits als „Widget" erklaert. Die beiden Audit-Routen ruft unser
#: **eigenes** Frontend (`AuditTool.jsx`), sie tauchen also gar nicht mehr in
#: der Liste auf.
#:
#: **Eine Ausnahme, die ihren Grund ueberlebt hat, ist schlimmer als keine:**
#: Sie nimmt zwei Routen dauerhaft aus der Pruefung heraus, und niemand merkt
#: es, weil eine Ausnahme keinen Alarm gibt. Wer hier wieder einen Eintrag
#: setzt, misst vorher an der fremden Seite nach, statt sich auf die
#: Beschreibung zu verlassen.
AUSSERHALB_DES_REPOS = ()


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
