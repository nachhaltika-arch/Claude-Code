"""Die beiden Adressen, unter denen dieses System von aussen erreichbar ist.

Sie standen bisher an vier Stellen mit je eigenem Rückfallwert. Drei davon
trugen die Produktiv-Adresse fest im Code — was auf Staging bedeutete, dass
Links und Bild-Adressen stillschweigend ins Produktivsystem zeigten. Der
Fehler fällt nicht auf, weil nichts scheitert: Die Adresse ist gültig, nur
kennt der Server dort die Daten nicht, auf die sie sich bezieht.

Deshalb liegen beide Adressen jetzt an genau einer Stelle. Wer sie braucht,
importiert sie hier — nicht mit einer eigenen ``os.getenv``-Zeile.

Beide lesen die Umgebung bei **jedem Aufruf**, nicht beim Import. Das ist
Absicht: Der Startvorgang setzt Variablen nach, und Tests setzen sie um.
"""
import os
from typing import Optional

# Rückfallwerte, wenn die Umgebung schweigt. Sie sind der letzte Ausweg, nicht
# die Konfiguration.
#
# Die API-Adresse ist seit dem 16.08. eine Domain, die uns gehört. Vorher stand
# hier `claude-code-znq2.onrender.com` — eine Adresse, die Render vergeben hat
# und die beim Umzug nach Frankfurt verschwindet. Genau deshalb ist die Domain
# der erste Schritt des Umzugs und nicht der letzte.
#
# Auf Render greift dieser Wert nie: Dort steht `API_BASE_URL` (produktiv seit
# dem 16.08.) oder `RENDER_EXTERNAL_URL`, das Render je Dienst selbst setzt.
FALLBACK_API_BASE_URL = "https://api.kompagnon.group"
FALLBACK_PUBLIC_BASE_URL = "https://kas.kompagnon.group"


def _erste_gesetzte(*kandidaten: Optional[str]) -> str:
    """Der erste Kandidat mit Inhalt, ohne Schrägstrich am Ende."""
    for wert in kandidaten:
        if wert and wert.strip():
            return wert.strip().rstrip("/")
    return ""


def public_base_url() -> str:
    """Die Adresse der React-Anwendung — alles, was ein Mensch im Browser öffnet."""
    return _erste_gesetzte(
        os.getenv("PUBLIC_BASE_URL"),
        os.getenv("FRONTEND_URL"),
        FALLBACK_PUBLIC_BASE_URL,
    )


def api_base_url() -> str:
    """Die Adresse, unter der dieser Server von aussen erreichbar ist.

    Sie steht im Berichtslink — dem einzigen Weg zum Bericht. Hier war als
    Rückfall die Produktiv-Adresse fest eingetragen, und ``API_BASE_URL`` ist
    im Staging-Blueprint nie deklariert worden. Also lief der Audit auf
    Staging, das Token lag in der Staging-Datenbank, und die E-Mail schickte
    den Empfänger zum Produktiv-Server, der das Token nicht kennt: „Not
    Found", bei jeder einzelnen Anfrage.

    Render setzt ``RENDER_EXTERNAL_URL`` für jeden Dienst selbst. Damit
    stimmt die Adresse in jeder Umgebung, ohne dass jemand eine Variable
    setzen muss — und ein vergessener Eintrag zeigt nicht mehr stillschweigend
    ins falsche System.

    **Nicht für Aufrufe dieses Servers an sich selbst.** Dafür ist
    ``RENDER_INTERNAL_HOSTNAME`` der richtige Weg; der Umweg über das
    öffentliche Netz kostet bei einem Backend in Oregon Sekunden (L-34).
    """
    return _erste_gesetzte(
        os.getenv("API_BASE_URL"),
        os.getenv("RENDER_EXTERNAL_URL"),
        FALLBACK_API_BASE_URL,
    )
