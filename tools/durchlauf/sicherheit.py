# -*- coding: utf-8 -*-
"""Stufen, die nach still versagenden Schutzmechanismen suchen.

Die drei Klassen hier haben eines gemeinsam: **Nichts wird rot.** Ein
Waechter, der ohne Geheimnis durchlaesst, arbeitet aus Sicht der Protokolle
fehlerfrei; ein Schluessel in einer Adresse steht im Zugriffsprotokoll des
Empfaengers, nicht im eigenen; ein verschluckter Fehler in einem Schreibpfad
meldet Erfolg. Genau deshalb braucht es eine Messung — auffallen wuerden sie
sonst erst, wenn jemand sie ausnutzt.

    fail_open_waechter()   → L-47, L-136, L-139: ohne Geheimnis wird durchgelassen
    geheimnis_in_adresse() → L-98, L-103: Schluessel im Pfad statt im Kopf
    stiller_ausfall()      → L-36, L-141, L-48: Schreibpfad schluckt den Fehler
"""
from __future__ import annotations

import ast
import pathlib
import re

from .befund import Befund, WURZEL, kurz

BACKEND = WURZEL / "kompagnon" / "backend"

#: Namensteile, die einen Wert als Geheimnis kennzeichnen.
#:
#: **Die deutschen gehoeren dazu, und das war kein Detail.** Der erste Entwurf
#: kannte nur englische Woerter — in einem Repo, dessen Variablen `schluessel`
#: und `geheimnis` heissen, haette die Stufe **nie** etwas gefunden und
#: trotzdem jede Woche „null Befunde" gemeldet. Aufgefallen ist es nicht beim
#: Lesen, sondern in der Selbstprobe: Sie legte ein Beispiel mit
#: `schluessel` an, und die Stufe ging daran vorbei.
GEHEIM = ("secret", "key", "token", "password", "credential", "api_key",
          "geheim", "schluessel", "passwort", "kennwort", "zugangs")

#: Schreibende HTTP-Methoden — nur dort ist ein verschluckter Fehler ein Verlust.
SCHREIBT = ("post", "put", "patch", "delete")

#: Bereiche, in denen jede stille Stelle einzeln aufgefuehrt wird: Geld,
#: Konten, fremde Rueckrufe. Anderswo steht die Zahl, nicht die Liste.
HEIKEL = ("payments", "geo_payments", "shop", "webhooks", "stripe", "auth_router",
          "betriebszugaenge", "posteingang", "rechnungen", "retainer", "buch_versand")


def _dateien(*ordner: str) -> list[pathlib.Path]:
    treffer: list[pathlib.Path] = []
    for name in ordner:
        wurzel = BACKEND / name if name else BACKEND
        if not wurzel.exists():
            continue
        treffer += [p for p in wurzel.rglob("*.py")
                    if "venv" not in p.parts and "__pycache__" not in p.parts
                    and "tests" not in p.parts]
    return treffer


def _baum(datei: pathlib.Path):
    try:
        return ast.parse(datei.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


def _ist_geheim(name: str) -> bool:
    n = name.lower()
    return any(w in n for w in GEHEIM)


# ── L-47 / L-136: ohne Geheimnis wird durchgelassen ─────────────────────────

def fail_open_waechter() -> list[Befund]:
    """Pruefungen, die bei fehlendem Geheimnis **wahr** zurueckgeben.

    **Warum das die gefaehrlichste Zeile im Haus ist.** Eine Signaturpruefung,
    die ohne Schluessel `True` liefert, ist in der Entwicklung bequem und
    produktiv eine offene Tuer — und sie faellt nie auf, weil alles
    funktioniert. In L-42 griff aus demselben Grund der Vorgabewert
    `development`, und Demokonten wurden produktiv angelegt.

    Gesucht wird eine Funktion, die (a) ein Geheimnis aus der Umgebung liest
    und (b) einen Zweig hat, der bei leerem Geheimnis mit einem positiven
    Ergebnis endet — `return True`, oder ein `return` ohne Wert in einer
    Funktion, die sonst nur wahr/falsch liefert.
    """
    befunde = []
    for datei in _dateien(""):
        baum = _baum(datei)
        if baum is None:
            continue
        for knoten in ast.walk(baum):
            if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            quelle = ast.dump(knoten)
            liest_geheimnis = any(
                _ist_geheim(k.value)
                for k in ast.walk(knoten)
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            ) and "getenv" in quelle
            if not liest_geheimnis:
                continue
            for zweig in ast.walk(knoten):
                if not isinstance(zweig, ast.If):
                    continue
                pruefung = ast.dump(zweig.test)
                # `if not X` oder `if X is None` oder `if not X:` mit leerem Vergleich
                verneint = "UnaryOp" in pruefung and "Not" in pruefung
                ist_none = "Is(" in pruefung and "Constant(value=None)" in pruefung
                if not (verneint or ist_none):
                    continue
                for satz in zweig.body:
                    positiv = (isinstance(satz, ast.Return)
                               and isinstance(satz.value, ast.Constant)
                               and satz.value.value is True)
                    if not positiv:
                        continue
                    befunde.append(Befund(
                        kennung=f"fail-open/{datei.stem}.{knoten.name}",
                        ebene="schnittstelle",
                        titel=f"`{knoten.name}()` gibt ohne Geheimnis **wahr** zurueck",
                        beleg=f"{kurz(datei)}:{satz.lineno}",
                        einzelheiten=(
                            "Die Funktion liest ein Geheimnis aus der Umgebung und "
                            "laesst durch, wenn keines gesetzt ist. In der Entwicklung "
                            "ist das bequem, produktiv ist es eine offene Tuer — und "
                            "nichts wird rot: Aus Sicht der Protokolle arbeitet der "
                            "Waechter fehlerfrei. Zu entscheiden ist, ob die Bequemlichkeit "
                            "an `ENVIRONMENT != production` gebunden gehoert oder ganz weg."
                        ),
                        vorschlag="P0",
                        gegenstand=f"{datei.name}:{knoten.name}",
                    ))
                    break
    return befunde


# ── L-98 / L-103: Geheimnis in der Adresse ──────────────────────────────────

def geheimnis_in_adresse() -> list[Befund]:
    """Adressen, die einen Schluessel im Pfad oder in der Abfrage tragen.

    **Warum der Ort zaehlt.** Ein Schluessel im Kopf einer Anfrage steht in
    keinem Protokoll; einer in der Adresse steht im Zugriffsprotokoll des
    Empfaengers, in jedem Zwischenspeicher und in der Verlaufsanzeige. L-98
    fand sechs solche Stellen, zwei davon in f-Strings versteckt, wo eine
    Suche nach `params=` nichts findet.
    """
    befunde = []
    for datei in _dateien(""):
        baum = _baum(datei)
        if baum is None:
            continue
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.JoinedStr):
                continue
            fester_teil = "".join(
                t.value for t in knoten.values
                if isinstance(t, ast.Constant) and isinstance(t.value, str)
            )
            if "http" not in fester_teil:
                continue
            for teil in knoten.values:
                if not isinstance(teil, ast.FormattedValue):
                    continue
                name = ""
                ziel = teil.value
                if isinstance(ziel, ast.Name):
                    name = ziel.id
                elif isinstance(ziel, ast.Attribute):
                    name = ziel.attr
                elif isinstance(ziel, ast.Call):
                    for arg in ziel.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            name = arg.value
                if not name or not _ist_geheim(name):
                    continue
                befunde.append(Befund(
                    kennung=f"geheimnis-in-adresse/{datei.stem}:{knoten.lineno}",
                    ebene="schnittstelle",
                    titel=f"`{name}` wird in eine Adresse eingebaut ({datei.name}:{knoten.lineno})",
                    beleg=f"{kurz(datei)}:{knoten.lineno} — f-String mit "
                          f"'{fester_teil[:60]}'",
                    einzelheiten=(
                        "Ein Geheimnis in der Adresse landet im Zugriffsprotokoll des "
                        "Empfaengers, in Zwischenspeichern und in Verlaufsanzeigen — "
                        "Orte, die niemand rotiert. Gehoert in den Kopf der Anfrage "
                        "(`headers`) oder in den Rumpf. Wie L-98, wo zwei der sechs "
                        "Stellen ebenfalls in einem f-String standen."
                    ),
                    vorschlag="P1",
                    gegenstand=f"{datei.name}:{knoten.lineno}",
                ))
                break
    return befunde


# ── L-36 / L-141: der Schreibpfad schluckt den Fehler ───────────────────────

_NUR_PROTOKOLL = ("logger", "logging", "log", "print")


def _quittiert_erfolg(zweig) -> bool:
    """Endet der Abfangzweig mit einer Antwort, die wie Erfolg aussieht?

    `return {"ok": True}` und `return {"status": "error_logged"}` sind aus
    Sicht des Absenders dasselbe: HTTP 200. Bei einem Rueckruf von aussen
    heisst das **nicht wiederholen** — der Vorgang ist dann endgueltig weg.
    """
    for satz in zweig.body:
        if not isinstance(satz, ast.Return) or satz.value is None:
            continue
        if isinstance(satz.value, (ast.Dict, ast.Constant)):
            return True
    return False


def _hat_vorbelegung(funktion, zweig) -> bool:
    """Faengt eine Vorbelegung vor dem `try` den Fehlschlag auf?

    Das haeufigste unverdaechtige Muster im Repo: `scraped = {}` steht vor dem
    Versuch, im `try` wird ueberschrieben, und danach liest der Code
    `scraped.get(...)`. Der Zweig braucht dann selbst nichts zu tun — der
    Rueckfallwert steht schon da. `routers/audit.py:455` ist genau das.
    """
    versuch = None
    for k in ast.walk(funktion):
        if isinstance(k, ast.Try) and zweig in k.handlers:
            versuch = k
            break
    if versuch is None:
        return False
    im_versuch = {
        ziel.id
        for satz in ast.walk(versuch)
        if isinstance(satz, ast.Assign)
        for ziel in satz.targets
        if isinstance(ziel, ast.Name)
    }
    if not im_versuch:
        return False
    for satz in funktion.body:
        if satz is versuch:
            break
        if isinstance(satz, ast.Assign):
            for ziel in satz.targets:
                if isinstance(ziel, ast.Name) and ziel.id in im_versuch:
                    return True
    return False


def _erklaert(datei: pathlib.Path, zeile: int, umkreis: int = 3) -> bool:
    """Steht neben dem Abfangzweig eine Begruendung?

    Gesucht wird ein Kommentar in derselben Zeile oder in den drei Zeilen
    davor — auch `# noqa: BLE001`, mit dem das Repo bewusste Faelle
    kennzeichnet. Eine leere Zeile beendet die Suche nach oben: Ein Kommentar
    fuenf Zeilen hoeher gehoert zu etwas anderem.
    """
    try:
        zeilen = datei.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    i = zeile - 1
    if i < 0 or i >= len(zeilen):
        return False
    if "#" in zeilen[i]:
        return True
    for k in range(i - 1, max(-1, i - 1 - umkreis), -1):
        text = zeilen[k].strip()
        if not text:
            break
        if text.startswith("#"):
            return True
    return False


def stiller_ausfall() -> list[Befund]:
    """Schreibende Endpunkte, die jeden Fehler abfangen und trotzdem gelingen.

    **Warum nur die schreibenden.** Ein verschluckter Fehler beim Lesen kostet
    eine Anzeige; einer beim Schreiben kostet die Handlung, und der Aufrufer
    bekommt Erfolg gemeldet. L-36 und L-141 sind beide von dieser Art.

    **Drei Dinge machen einen Abfangzweig unverdaechtig, und alle drei kommen
    im Repo vor.** Er hebt den Fehler wieder an oder antwortet mit einem
    Statuscode — dann ist er behandelt. Er setzt eine Variable, die die
    Antwort danach auswertet (`versandt = False` in `auth_router.register`)
    — dann sagt die Antwort, was wirklich passiert ist. Oder er ist
    **erklaert**: ein Kommentar davor oder ein `noqa` daneben.

    Die dritte Bedingung ist keine Nachgiebigkeit, sondern der eigentliche
    Zweck der Stufe. Der erste Lauf meldete 49 Stellen; die ersten beiden,
    die ich nachgesehen habe, waren bewusst still und standen unter drei
    Zeilen Begruendung — „Die Registrierung an einem Mailserver-Schluckauf
    scheitern zu lassen waere schlimmer als eine ausbleibende
    Bestaetigungsmail". Eine Stufe, die solche Stellen meldet, bestraft die
    Sorgfalt. **Was uebrig bleibt, ist die Frage an die unerklaerten:
    absichtlich still, oder vergessen?** — und die Antwort gehoert als
    Kommentar in den Code, nicht in eine Liste.
    """
    befunde: list[Befund] = []
    fundstellen: list[tuple] = []
    for datei in sorted((BACKEND / "routers").rglob("*.py")):
        if "__pycache__" in datei.parts:
            continue
        baum = _baum(datei)
        if baum is None:
            continue
        for knoten in ast.walk(baum):
            if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            schreibt = any(
                isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and d.func.attr in SCHREIBT
                for d in knoten.decorator_list
            )
            if not schreibt:
                continue
            for zweig in ast.walk(knoten):
                if not isinstance(zweig, ast.ExceptHandler):
                    continue
                # Ein breiter Fang: `except Exception` oder `except:`
                breit = zweig.type is None or (
                    isinstance(zweig.type, ast.Name) and zweig.type.id == "Exception")
                if not breit:
                    continue
                rumpf = ast.dump(ast.Module(body=zweig.body, type_ignores=[]))
                hebt_an = "Raise(" in rumpf
                antwortet = "HTTPException" in rumpf or "status_code" in rumpf
                zuweisung = "Assign(" in rumpf or "AugAssign(" in rumpf
                protokolliert = any(w in rumpf for w in _NUR_PROTOKOLL)
                if hebt_an or antwortet or zuweisung:
                    continue
                if not protokolliert and rumpf.count("Pass()") == 0:
                    continue
                if _erklaert(datei, zweig.lineno):
                    continue
                if _hat_vorbelegung(knoten, zweig):
                    continue
                # **Rueckruf von aussen oder eigener Aufruf?** Die Antwort
                # entscheidet ueber die Schwere: Ein fremdes System liefert
                # bei 200 nie wieder; das eigene Frontend kann der Nutzer
                # noch einmal ausloesen.
                von_aussen = ("webhook" in datei.stem or "webhook" in knoten.name
                              or datei.stem in ("payments", "geo_payments"))
                # **P0 nur, wo Geld haengt.** Ein Anzeigenportal, dem man 200
                # antwortet, damit es den Rueckruf nicht abschaltet, kann eine
                # bewusste Entscheidung sein — dann fehlt nur die Begruendung
                # im Code. Bei einer Zahlung ist es keine: Was Stripe als
                # verarbeitet quittiert bekommt, kommt nie wieder.
                geld = datei.stem in ("payments", "geo_payments", "shop") or \
                    "stripe" in knoten.name or "payment" in knoten.name
                fundstellen.append(
                    (datei, knoten.name, zweig.lineno,
                     datei.stem in HEIKEL,
                     _quittiert_erfolg(zweig) and von_aussen,
                     _quittiert_erfolg(zweig),
                     _quittiert_erfolg(zweig) and von_aussen and geld))
                break

    # **Einzeln nur, wo es weh tut.** Vierunddreissig Zeilen in einem Bericht
    # sind eine Tapete; die Frage dahinter ist eine einzige. Getrennt wird
    # deshalb nach Bereich: Wo Geld, Konten oder fremde Rueckrufe im Spiel
    # sind, steht jede Stelle fuer sich — der Rest ist eine Entscheidung.
    for datei, funktion, zeile, heikel, rueckruf, quittiert, geld in fundstellen:
        if not (heikel or quittiert):
            continue
        befunde.append(Befund(
            kennung=f"stiller-ausfall/{datei.stem}.{funktion}",
            ebene="schnittstelle",
            titel=(f"`{funktion}()` antwortet im Fehlerfall mit Erfolg — der Absender "
                   f"wiederholt nicht" if rueckruf else
                   f"`{funktion}()` antwortet im Fehlerfall mit Erfolg" if quittiert else
                   f"`{funktion}()` faengt jeden Fehler ab und meldet trotzdem Erfolg"),
            beleg=f"{kurz(datei)}:{zeile}",
            einzelheiten=(
                ("**Der Abfangzweig endet mit einer Erfolgsantwort.** Bei einem "
                 "Rueckruf von aussen ist das folgenschwerer als ein verschlucktes "
                 "Protokoll: Stripe, Brevo und die Anzeigenportale werten 200 als "
                 "„verarbeitet\" und liefern **nie wieder**. Scheitert die "
                 "Verarbeitung, ist der Vorgang endgueltig weg — die Zahlung ist "
                 "gebucht, das Projekt entsteht nicht, und niemand erfaehrt es ausser "
                 "einer Protokollzeile. Der Absender darf nur dann 200 bekommen, wenn "
                 "der Vorgang **festgehalten** ist; alles andere gehoert mit 5xx "
                 "beantwortet, damit der Rueckruf wiederholt wird. "
                 + ("**Hier haengt Geld daran** — deshalb P0."
                    if geld else
                    "**Es kann Absicht sein**: Manche Anzeigenportale schalten einen "
                    "Rueckruf ab, der Fehler liefert. Dann ist die Antwort richtig und "
                    "es fehlt nur der Satz daneben, der das sagt — schreib ihn hin, "
                    "dann meldet der naechste Lauf die Stelle nicht mehr.")
                 if rueckruf else
                 "**Der Abfangzweig endet mit einer Erfolgsantwort an das eigene "
                 "Frontend.** Der Nutzer sieht, dass es geklappt hat; passiert ist "
                 "nichts. Kein Datenverlust wie beim Rueckruf von aussen — der "
                 "Vorgang laesst sich wiederholen —, aber niemand weiss, dass er es "
                 "muss. Die Antwort sollte sagen, was wirklich geschehen ist, wie es "
                 "`auth_router.register` mit `versandt` vormacht."
                 if quittiert else
                 "Ein schreibender Endpunkt in einem Bereich, in dem Geld, Konten "
                 "oder fremde Rueckrufe haengen — mit einem breiten Abfangzweig, der "
                 "nur protokolliert, keine Vorbelegung auffaengt und keinen Kommentar "
                 "traegt. Der Aufrufer bekommt Erfolg, die Handlung ist nicht passiert.")
                + " Familie L-36, L-141."
            ),
            vorschlag="P0" if geld else "P1",
            gegenstand=f"{datei.name}:{funktion}",
        ))
    rest = [f for f in fundstellen if not (f[3] or f[5])]
    if len(rest) >= 5:
        oben = " · ".join(
            f"{d.name}:{z} ({fn})" for d, fn, z, *_ in rest[:6])
        befunde.append(Befund(
            kennung="stiller-ausfall/sammel",
            ebene="schnittstelle",
            titel=(f"{len(rest)} schreibende Endpunkte schweigen unerklaert "
                   f"ueber Fehler"),
            beleg=oben,
            einzelheiten=(
                "Breiter Abfangzweig, nur ein Protokolleintrag, keine Vorbelegung, "
                "die ihn auffaengt, und kein Kommentar, der ihn begruendet. **Das ist "
                "keine Liste von Maengeln, sondern eine Liste von Fragen:** Bei jeder "
                "Stelle ist zu klaeren, ob das Schweigen Absicht ist. Ist es Absicht, "
                "gehoert der Grund als Kommentar daneben — dann verschwindet die Zeile "
                "beim naechsten Lauf von selbst. Ist es keine, gehoert der Fehler an "
                "den Aufrufer zurueck. Die Stufe zaehlt bewusst die **unerklaerten**: "
                "Wo eine Begruendung steht, meldet sie nichts."
            ),
            vorschlag="P2",
            gegenstand="unerklaert schweigende Schreibpfade",
        ))
    return befunde
