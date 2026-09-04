# -*- coding: utf-8 -*-
"""Findet der Durchlauf noch, was er finden soll?

**Wozu.** Elf der siebzehn Stufen melden heute null Befunde. Das kann zweierlei
heissen: Das System ist an dieser Stelle sauber — oder die Messung sieht
nichts mehr, weil sich eine Schreibweise geaendert hat, ein Regex nicht mehr
passt oder ein Ordner umgezogen ist. **Von aussen sind beide Faelle
ununterscheidbar**, und der zweite ist der gefaehrliche: Ein Durchlauf, der
blind geworden ist, meldet Ruhe.

Die Selbstprobe legt deshalb Beispieldateien an, die jeden gesuchten Fehler
**enthalten**, und laesst die Stufen darauf los. Findet eine Stufe ihr eigenes
Beispiel nicht, ist sie blind — und das gehoert in den Bericht, noch vor jedem
Sachbefund.

    python3 -m tools.durchlauf.selbstprobe      # einzeln aufrufbar
"""
from __future__ import annotations

import pathlib
import tempfile

from .befund import Befund

#: Je Stufe eine Beispieldatei, die genau den gesuchten Fehler enthaelt.
BEISPIELE = {
    "waechter.py": '''
import os


def signatur_gueltig(daten, signatur):
    geheimnis = os.getenv("WEBHOOK_SECRET", "")
    if not geheimnis:
        return True
    return signatur == geheimnis
''',
    "adresse.py": '''
import os


def abfragen(kunde):
    schluessel = os.getenv("PAGESPEED_API_KEY", "")
    ziel = f"https://example.test/api?key={schluessel}&kunde={kunde}"
    return ziel
''',
}

ROUTER_BEISPIEL = '''
from fastapi import APIRouter

router = APIRouter(prefix="/api/probe")


@router.post("/zahlung")
def webhook_probe(daten: dict):
    try:
        verarbeiten(daten)
    except Exception as fehler:
        logger.error("Fehler: %s", fehler)
        return {"ok": True}
    return {"ok": True}


@router.get("/doppelt")
def erste():
    return {}


@router.get("/doppelt")
def zweite():
    return {}
'''


def laufen() -> list[Befund]:
    """Legt die Beispiele an, misst darauf und meldet jede blinde Stufe."""
    from . import sicherheit, stufen

    befunde: list[Befund] = []
    with tempfile.TemporaryDirectory() as ordner:
        wurzel = pathlib.Path(ordner)
        (wurzel / "routers").mkdir()
        for name, inhalt in BEISPIELE.items():
            (wurzel / name).write_text(inhalt, encoding="utf-8")
        (wurzel / "routers" / "probe.py").write_text(ROUTER_BEISPIEL, encoding="utf-8")

        echt_sicherheit, echt_stufen = sicherheit.BACKEND, stufen.BACKEND
        try:
            sicherheit.BACKEND = wurzel
            stufen.BACKEND = wurzel
            proben = {
                "Waechter laesst ohne Geheimnis durch": sicherheit.fail_open_waechter,
                "Geheimnis in der Adresse": sicherheit.geheimnis_in_adresse,
                "Stiller Ausfall im Schreibpfad": sicherheit.stiller_ausfall,
                "Doppelte Routen": stufen.doppelte_routen,
            }
            for name, messen in proben.items():
                try:
                    treffer = messen()
                except Exception as fehler:              # noqa: BLE001
                    treffer = []
                    grund = f"{type(fehler).__name__}: {fehler}"
                else:
                    grund = "kein Treffer auf dem eigenen Beispiel"
                if treffer:
                    continue
                befunde.append(Befund(
                    kennung=f"selbstprobe/{name}",
                    ebene="konsistenz",
                    titel=f"Die Stufe „{name}“ findet ihr eigenes Beispiel nicht",
                    beleg=f"tools/durchlauf/selbstprobe.py — {grund}",
                    einzelheiten=(
                        "Die Selbstprobe legt eine Datei an, die genau diesen Fehler "
                        "enthaelt. Die Stufe hat ihn nicht gefunden. **Damit ist jede "
                        "Null dieser Stufe im Bericht wertlos** — sie kann Ruhe oder "
                        "Blindheit bedeuten. Zu pruefen, bevor irgendein Sachbefund "
                        "dieses Laufs verwendet wird."
                    ),
                    vorschlag="P0",
                    gegenstand=f"Stufe {name}",
                ))
        finally:
            sicherheit.BACKEND, stufen.BACKEND = echt_sicherheit, echt_stufen
    return befunde + _rollenprobe()


# ── Probe für die Rollenstufe ───────────────────────────────────────────────
#
# Die Stufe meldet heute null — richtig, denn gueltige Rollen, Rechtematrix
# und Oberflaeche stimmen ueberein. Ohne diese Probe waere diese Null nicht
# von einer kaputten Messung zu unterscheiden.

ROLLEN_QUELLE = (
    'ROLLEN = ("superadmin", "admin", "mitarbeiter", "kunde")\n'
    'ALTE_ROLLEN = {\n    "auditor": "mitarbeiter",\n}\n'
)

MATRIX_QUELLE = (
    'DEFAULT_PERMISSIONS = {\n'
    '    "superadmin": [],\n    "admin": [],\n'
    '    "mitarbeiter": [],\n    "kunde": [],\n}\n'
)

APP_BEISPIEL = (
    "<Routes>\n"
    "  <Route path=\"/app/probe\" element={<PrivateRoute roles={['auditor']}>"
    "<X /></PrivateRoute>} />\n"
    "</Routes>\n"
)


def _rollenprobe() -> list[Befund]:
    """Findet die Rollenstufe eine Rolle, die es nicht mehr gibt?"""
    from . import rollen

    befunde: list[Befund] = []
    with tempfile.TemporaryDirectory() as ordner:
        wurzel = pathlib.Path(ordner)
        (wurzel / "services").mkdir()
        (wurzel / "routers").mkdir()
        (wurzel / "services" / "rollen.py").write_text(ROLLEN_QUELLE, encoding="utf-8")
        (wurzel / "routers" / "admin_settings.py").write_text(
            MATRIX_QUELLE, encoding="utf-8")
        app = wurzel / "App.jsx"
        app.write_text(APP_BEISPIEL, encoding="utf-8")

        echt = (rollen.BACKEND, rollen.FRONTEND, rollen.QUELLE,
                rollen.MATRIX, rollen.APP_JSX)
        try:
            rollen.BACKEND = wurzel
            rollen.FRONTEND = wurzel
            rollen.QUELLE = wurzel / "services" / "rollen.py"
            rollen.MATRIX = wurzel / "routers" / "admin_settings.py"
            rollen.APP_JSX = app
            treffer, _notiz = rollen.rollen_drift()
        except Exception as fehler:                      # noqa: BLE001
            treffer, grund = [], f"{type(fehler).__name__}: {fehler}"
        else:
            grund = "kein Treffer auf dem eigenen Beispiel"
        finally:
            (rollen.BACKEND, rollen.FRONTEND, rollen.QUELLE,
             rollen.MATRIX, rollen.APP_JSX) = echt

        if not treffer:
            befunde.append(Befund(
                kennung="selbstprobe/Rollendrift",
                ebene="konsistenz",
                titel="Die Stufe „Rollendrift“ findet ihr eigenes Beispiel nicht",
                beleg=f"tools/durchlauf/selbstprobe.py — {grund}",
                einzelheiten=(
                    "Die Probe sperrt eine Route auf die abgeschaffte Rolle "
                    "`auditor`. Die Stufe hat das nicht gemeldet — ihre Null im "
                    "Bericht bedeutet damit nichts."
                ),
                vorschlag="P0",
                gegenstand="Stufe Rollendrift",
            ))
    return befunde


if __name__ == "__main__":
    ergebnis = laufen()
    if not ergebnis:
        print("Selbstprobe bestanden — alle geprueften Stufen finden ihr Beispiel.")
    for b in ergebnis:
        print(f"BLIND: {b.titel}\n       {b.beleg}")
