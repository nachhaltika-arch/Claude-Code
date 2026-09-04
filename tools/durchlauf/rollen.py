# -*- coding: utf-8 -*-
"""Stufen, die die Rollen gegeneinanderhalten.

**Warum Rollen eine eigene Stufe verdienen.** Eine Rolle steht an drei
Stellen: in der Rechtematrix (`DEFAULT_PERMISSIONS`), in den Sperren der
Frontend-Routen (`roles={[…]}`) und als Zeichenkette im Backend-Code. Gehen
sie auseinander, entsteht kein Fehler, den jemand sieht — es entsteht eine
**stille Sperre oder eine stille Oeffnung**: Ein Nutzer sieht den Menuepunkt
nicht, obwohl er das Recht hat; oder er erreicht die Route, weil sein
Rollenname in keiner Liste steht, gegen die geprueft wird. L-05, L-55 und
L-133 gehoeren alle in diese Familie.

    rollen_drift()      → Rollenname an einer Stelle, an der anderen nicht
    route_ohne_sperre() → /app-Route ohne Rollenangabe, obwohl das Backend eine kennt
"""
from __future__ import annotations

import collections
import re

from .befund import Befund, WURZEL, kurz

BACKEND = WURZEL / "kompagnon" / "backend"
FRONTEND = WURZEL / "kompagnon" / "frontend" / "src"
MATRIX = BACKEND / "routers" / "admin_settings.py"
APP_JSX = FRONTEND / "App.jsx"

_MATRIX_ROLLE = re.compile(r'^\s{4}"(\w+)":\s*\[', re.M)
_ROLES_ATTRIBUT = re.compile(r"roles=\{\[([^\]]*)\]\}")
QUELLE = BACKEND / "services" / "rollen.py"

#: Zeichen, mit denen eine Kommentarzeile beginnt.
KOMMENTARZEICHEN = ("#", "*")


def _kanonisch() -> tuple[set[str], set[str]]:
    """Die gueltigen Rollen und die Altnamen — aus `services/rollen.py`.

    **Diese Datei ist die eine Stelle**, an der die Rollen stehen; sie wurde
    am 27.08.2026 genau deshalb angelegt, weil die Namen vorher an ueber
    siebzig Stellen standen. Eine Pruefung, die stattdessen den ganzen Code
    nach Zeichenketten absucht, misst etwas anderes: Der erste Entwurf meldete
    `auditor` und `nutzer` als Drift — beide stehen dort in `ALTE_ROLLEN`, der
    Uebersetzungstabelle, die den Drift **verhindert**, und `"nutzer"` in
    `assistant.py` ist ueberhaupt keine Benutzerrolle, sondern die Rolle einer
    Gespraechszeile. Zwei Fehlalarme aus einer zu breiten Suche.
    """
    if not QUELLE.exists():
        return set(), set()
    text = QUELLE.read_text(encoding="utf-8")
    gueltig = re.search(r"^ROLLEN\s*=\s*\(([^)]*)\)", text, re.M)
    alt = re.search(r"^ALTE_ROLLEN\s*=\s*\{(.*?)\}", text, re.M | re.S)
    return (
        set(re.findall(r'"(\w+)"', gueltig.group(1))) if gueltig else set(),
        set(re.findall(r'"(\w+)"\s*:', alt.group(1))) if alt else set(),
    )


def _matrix_rollen() -> set[str]:
    if not MATRIX.exists():
        return set()
    text = MATRIX.read_text(encoding="utf-8")
    treffer = re.search(r"DEFAULT_PERMISSIONS\s*=\s*\{(.*?)\n\}", text, re.S)
    return set(_MATRIX_ROLLE.findall(treffer.group(1))) if treffer else set()


def _frontend_rollen() -> dict[str, int]:
    if not APP_JSX.exists():
        return {}
    zaehler: collections.Counter = collections.Counter()
    for gruppe in _ROLES_ATTRIBUT.findall(APP_JSX.read_text(encoding="utf-8")):
        for rolle in re.findall(r"['\"](\w+)['\"]", gruppe):
            zaehler[rolle] += 1
    return dict(zaehler)


def _altnamen_im_umlauf(alt: set[str]) -> dict[str, list[str]]:
    """Wo stehen Altnamen noch — ausserhalb der Stellen, die sie kennen duerfen?

    `services/rollen.py`, `migrations_runtime` und die Tests duerfen sie
    kennen: Ein Bestand, der einen selbst gespeicherten Namen nicht mehr
    kennt, sperrt Menschen aus. Ueberall sonst ist ein Altname ein Rueckstand.
    """
    erlaubt = ("services/rollen.py", "migrations_runtime.py", "migrations.py",
               "tests/", "posteingang.py", "admin_settings.py")
    stellen: dict[str, list[str]] = collections.defaultdict(list)
    kandidaten = list(BACKEND.rglob("*.py")) + [
        p for p in FRONTEND.rglob("*.jsx") if "node_modules" not in p.parts]
    for datei in kandidaten:
        pfad = kurz(datei)
        if ("venv" in datei.parts or "__pycache__" in datei.parts
                or any(w in pfad for w in erlaubt)):
            continue
        # Der Assistent fuehrt eine eigene `rolle` je Gespraechszeile
        # ("nutzer" / "assistent"). Dieselben Woerter, andere Bedeutung —
        # und zwar in der ganzen Datei, nicht nur in der Zeile, die sie
        # erklaert.
        if "assistent" in pfad.lower() or "assistant" in pfad.lower():
            continue
        try:
            text = datei.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for name in alt:
            # Nur wo der Name **als Rolle** steht: neben `role`, `rolle`,
            # `roles=` oder einer Rechtepruefung. Eine Gespraechszeile mit
            # `rolle == "nutzer"` in `assistant.py` ist keine Benutzerrolle —
            # deshalb wird die Zeile mitgelesen, nicht nur das Wort.
            for zeile_nr, zeile in enumerate(text.splitlines(), 1):
                if f'"{name}"' not in zeile and f"'{name}'" not in zeile:
                    continue
                gestutzt = zeile.strip()
                # Ein Kommentar ist keine Anweisung. `component_library_
                # wireframe.py:73` erklaert in Prosa, woran die Aufrufer
                # haengen — der erste Lauf zaehlte den Satz als Rueckstand.
                if gestutzt[:1] in KOMMENTARZEICHEN or gestutzt[:2] == "//":
                    continue
                nahe = zeile.lower()
                if not any(w in nahe for w in ("role", "rolle")):
                    continue
                # **Nicht jede `rolle` ist eine Benutzerrolle.** Im Assistenten
                # heisst die Spalte der Gespraechszeile so und traegt die Werte
                # "nutzer" und "assistent". Derselbe String, eine voellig
                # andere Sache.
                if "assistent" in nahe or "assistant" in nahe:
                    continue
                stellen[name].append(f"{pfad}:{zeile_nr}")
    return dict(stellen)


def rollen_drift() -> tuple[list[Befund], str]:
    """Rollennamen, die nicht ueberall dieselben sind.

    Gemessen an den drei kanonischen Orten — `services/rollen.py` (die
    Wahrheit), `DEFAULT_PERMISSIONS` (die Rechte) und `App.jsx` (die Sperren
    der Oberflaeche) —, nicht an Zeichenketten im ganzen Baum.

    **Drei Richtungen, drei Folgen.** Eine Rolle, die die Oberflaeche kennt
    und die Wahrheit nicht, sperrt nach einem Namen, den niemand vergibt. Eine
    Rolle in der Wahrheit ohne Rechte in der Matrix bekommt bei jeder Pruefung
    eine leere Rechteliste. Und ein Altname ausserhalb der Stellen, die ihn
    kennen duerfen, ist ein Rueckstand der letzten Umbenennung — genau die
    Familie L-05, wo eine Sperre an einer Stelle korrigiert wurde und an den
    anderen nicht.
    """
    gueltig, alt = _kanonisch()
    if not gueltig:
        return [], "services/rollen.py nicht lesbar — nicht gemessen"
    matrix = _matrix_rollen()
    frontend = _frontend_rollen()
    rueckstaende = _altnamen_im_umlauf(alt)

    notiz = (f"gueltig: {', '.join(sorted(gueltig))} · Matrix: "
             f"{', '.join(sorted(matrix)) or '—'} · Oberflaeche: "
             f"{', '.join(sorted(frontend)) or '—'} · Altnamen: "
             f"{', '.join(sorted(alt)) or '—'}")

    befunde = []
    for rolle in sorted(set(frontend) - gueltig):
        befunde.append(Befund(
            kennung=f"rollendrift/oberflaeche/{rolle}",
            ebene="frontend",
            titel=(f"Die Oberflaeche sperrt {frontend[rolle]} Route(n) auf `{rolle}` — "
                   f"`services/rollen.py` kennt diese Rolle nicht"),
            beleg=f"kompagnon/frontend/src/App.jsx gegen services/rollen.py "
                  f"({', '.join(sorted(gueltig))})",
            einzelheiten=(
                "Die Route entscheidet nach einem Namen, den niemand mehr vergibt. "
                "Die Sperre trifft damit entweder nie zu (dann ist die Seite fuer alle "
                "zu) oder immer (dann fuer niemanden) — je nachdem, wie die Pruefung "
                "gebaut ist. Auffallen wuerde es erst, wenn sich jemand anmeldet."
            ),
            vorschlag="P1",
            gegenstand=rolle,
        ))
    for rolle in sorted(gueltig - matrix):
        befunde.append(Befund(
            kennung=f"rollendrift/matrix/{rolle}",
            ebene="schnittstelle",
            titel=f"Die Rolle `{rolle}` hat keinen Eintrag in der Rechtematrix",
            beleg=f"services/rollen.py fuehrt `{rolle}`; DEFAULT_PERMISSIONS in "
                  f"routers/admin_settings.py nicht",
            einzelheiten=(
                "Wer diese Rolle traegt, bekommt bei jeder rechtebasierten Pruefung "
                "eine **leere** Rechteliste. Nichts wird rot; der Nutzer sieht nur "
                "weniger, als er soll."
            ),
            vorschlag="P1",
            gegenstand=rolle,
        ))
    for name, stellen in sorted(rueckstaende.items()):
        befunde.append(Befund(
            kennung=f"rollendrift/altname/{name}",
            ebene="konsistenz",
            titel=(f"Der Altname `{name}` steht noch an {len(stellen)} Stelle(n) "
                   f"ausserhalb der Uebersetzung"),
            beleg=" · ".join(sorted(set(stellen))[:5]),
            einzelheiten=(
                "`services/rollen.py`, die Migrationen und die Testdaten duerfen "
                "Altnamen kennen — ein Bestand, der einen selbst gespeicherten Namen "
                "nicht mehr kennt, sperrt Menschen aus. Ueberall sonst ist ein Altname "
                "ein Rueckstand der Umbenennung: Er wird gegen einen Wert geprueft, "
                "den `rolle_normalisieren` laengst uebersetzt hat, und trifft nie zu."
            ),
            vorschlag="P2",
            gegenstand=name,
        ))
    return befunde, notiz


def route_ohne_sperre() -> tuple[list[Befund], str]:
    """Routen unter `/app`, die keine Rollenangabe tragen.

    Eine Route ohne `roles=` steht jedem Angemeldeten offen. Das ist bei den
    meisten richtig — Dashboard, eigenes Profil. Gemeldet wird deshalb nur,
    was nach Verwaltung aussieht: Adressen mit `admin`, `settings`, `users`,
    `roles`, `system`, `webhooks` oder `rechnungen` im Pfad.
    """
    if not APP_JSX.exists():
        return [], "App.jsx nicht gefunden"
    text = APP_JSX.read_text(encoding="utf-8")
    # **Ohne `rechnungen` und `billing`.** Der erste Lauf meldete
    # `/app/rechnungen` — dahinter steht `MeineRechnungen`, die Kundenansicht
    # der **eigenen** Rechnungen; der Endpunkt filtert nach der eigenen
    # Adresse. Ein Wort im Pfad sagt nichts darueber, wessen Daten die Seite
    # zeigt. Uebrig bleiben die Woerter, die nur in der Verwaltung vorkommen.
    verwaltung = ("admin", "settings", "users", "roles", "system",
                  "webhooks", "security")
    offen: list[str] = []
    geprueft = 0
    for zeile in text.splitlines():
        if "<Route" not in zeile or "path=" not in zeile:
            continue
        pfad = re.search(r'path="([^"]+)"', zeile)
        if not pfad:
            continue
        geprueft += 1
        if not any(w in pfad.group(1).lower() for w in verwaltung):
            continue
        if "roles=" in zeile or "PrivateRoute" not in zeile:
            continue
        offen.append(pfad.group(1))

    notiz = f"{geprueft} Routen in App.jsx geprueft"
    if not offen:
        return [], notiz
    return [Befund(
        kennung="rollen/verwaltungsroute-ohne-rolle",
        ebene="frontend",
        titel=(f"{len(offen)} Verwaltungsroute(n) ohne Rollenangabe: "
               f"{', '.join(offen[:6])}"),
        beleg=f"kompagnon/frontend/src/App.jsx — {', '.join(offen[:8])}",
        einzelheiten=(
            "Eine Route ohne `roles=` steht jedem Angemeldeten offen, auch der Rolle "
            "`kunde`. Bei Dashboard und Profil ist das richtig; bei einer Adresse mit "
            "`admin`, `settings` oder `rechnungen` im Namen ist es eine Frage. **Die "
            "Oberflaeche ist dabei nur die halbe Miete** — was wirklich zaehlt, ist "
            "die Sperre am Endpunkt; die misst `tools/schwacher-zugriffsschutz.py`. "
            "Eine ungesperrte Ansicht verraet aber schon durch ihr blosses Erscheinen, "
            "dass es sie gibt."
        ),
        vorschlag="P2",
        gegenstand="Verwaltungsrouten ohne Rollenangabe",
    )], notiz
