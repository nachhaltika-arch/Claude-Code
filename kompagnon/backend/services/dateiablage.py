"""Wo hochgeladene Dateien liegen — an einer Stelle beantwortet.

**Warum es das gibt.** Am 16.08.2026 fiel auf, dass Uploads auf dem
fluechtigen Dateisystem des Containers liegen: In den Blueprints stand kein
`disk:`, also ist bei jedem Deploy alles weg. Die eine Datei, die es gab, war
schon verloren.

Beim Beheben zeigte sich, dass **drei Schreibstellen drei Regeln folgten** —
eine las `UPLOAD_ROOT`, zwei hatten `uploads` fest verdrahtet. Ein
Datenträger, der nur ein Drittel der Dateien auffaengt, ist schlimmer als
keiner: Er sieht aus, als waere das Problem geloest.

Produktiv zeigt `UPLOAD_ROOT` auf den eingehaengten Datentraeger
(`/var/data/uploads`). Ohne die Variable bleibt es beim bisherigen relativen
`uploads` — lokal und in den Tests soll sich nichts aendern.
"""
import os
from pathlib import Path

#: Was gilt, wenn nichts gesetzt ist. Wie bisher, relativ zum Arbeitsverzeichnis.
VORGABE = Path("uploads")


def upload_wurzel() -> Path:
    """Das Wurzelverzeichnis für hochgeladene Dateien.

    Wird bei jedem Aufruf gelesen und nicht beim Import festgehalten — sonst
    haengt der Wert davon ab, in welcher Reihenfolge Module geladen wurden.
    """
    wert = (os.getenv("UPLOAD_ROOT") or "").strip()
    return Path(wert) if wert else VORGABE


def lead_verzeichnis(lead_id) -> Path:
    """Das Verzeichnis eines Betriebs unterhalb der Wurzel.

    Die Nummer muss eine Nummer sein. Ohne diese Pruefung schriebe ein
    gebasteltes `../../etc` irgendwohin — der Wert kommt aus der Adresszeile.
    """
    try:
        nummer = int(str(lead_id))
    except (TypeError, ValueError):
        raise ValueError(f"Keine gültige Betriebsnummer: {lead_id!r}")
    return upload_wurzel() / str(nummer)


def ablage_zustand() -> dict:
    """Liegt die Ablage auf einem eingehaengten Datentraeger — und laesst sie
    sich beschreiben?

    Warum die Frage von aussen beantwortbar sein muss: Ein Datentraeger, der
    nicht eingehaengt ist, faellt nicht auf. Der Dienst schreibt weiter, alles
    sieht richtig aus, und beim naechsten Deploy sind die Dateien weg. Genau
    das ist am 16.08.2026 passiert.

    `dauerhaft` erkennt einen eingehaengten Datentraeger daran, dass er ein
    eigenes Dateisystem ist: andere Geraetenummer als `/`. Auf einem Rechner
    ohne Datentraeger (lokal, Tests, CI) ist die Antwort deshalb `False` — und
    das ist richtig so, dort ueberlebt auch nichts einen Neustart.

    Bewusst knapp: Pfad und zwei Wahrheitswerte. Auf `/info` lagen hier einmal
    Zugangsdaten offen; eine Auskunft soll sagen, was noetig ist, nicht mehr.
    """
    wurzel = upload_wurzel()
    zustand = {"pfad": str(wurzel), "beschreibbar": False, "dauerhaft": False}

    try:
        wurzel.mkdir(parents=True, exist_ok=True)
        probe = wurzel / ".schreibprobe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        zustand["beschreibbar"] = True
    except Exception as fehler:
        zustand["grund"] = f"{type(fehler).__name__}: {fehler}"
        return zustand

    try:
        zustand["dauerhaft"] = os.stat(wurzel).st_dev != os.stat("/").st_dev
    except Exception as fehler:
        zustand["grund"] = f"{type(fehler).__name__}: {fehler}"

    return zustand
