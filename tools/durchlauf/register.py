# -*- coding: utf-8 -*-
"""Das Stufenregister — was gemessen wird und was es dafuer braucht.

**Warum ein Register und keine Liste von Funktionen.** Die Stufen haben
verschiedene Voraussetzungen: Die meisten lesen nur den Quelltext, zwei
brauchen die geladene Anwendung, eine den laufenden Dienst. Ein Durchlauf,
der das nicht unterscheidet, meldet eine nicht erhobene Zahl als Null — und
eine Null, die niemand gemessen hat, ist die gefaehrlichste Zahl im Bericht.

Jede Stufe nennt deshalb ihren **Bedarf**:

    quelltext   — liest Dateien, laeuft ueberall, Sekunden
    anwendung   — braucht die Backend-Umgebung (venv mit den Abhaengigkeiten)
    dienst      — braucht einen erreichbaren Dienst und einen Browser

Der Dirigent fuehrt aus, was moeglich ist, und schreibt fuer den Rest in den
Bericht, **warum** er nichts sagen kann.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Callable

from . import bauwerk, daten, sicherheit, stufen, werkzeuge


@dataclasses.dataclass(frozen=True)
class Stufe:
    name: str
    messen: Callable
    bedarf: str          # quelltext · anwendung · dienst
    findet: str          # eine Zeile: welche Fehlerklasse, mit Vorbild


REGISTER: tuple[Stufe, ...] = (
    # ── Ebene 1: Datenbank ──────────────────────────────────────────────
    Stufe("Felder ohne Leser", stufen.felder_ohne_leser, "quelltext",
          "gespeichert, angezeigt, nie gelesen — L-05, L-55"),
    Stufe("Modell ohne Migration", daten.spalten_ohne_migration, "quelltext",
          "Commit aendert das Modell und ruehrt keine Migration an — L-86, L-93"),
    Stufe("SQL nennt unbekannte Tabelle", daten.sql_nennt_unbekannte_tabelle, "quelltext",
          "rohes SQL auf einer Tabelle, die kein Modell fuehrt"),

    # ── Ebene 2: Schnittstelle ──────────────────────────────────────────
    Stufe("Doppelte Routen", stufen.doppelte_routen, "quelltext",
          "zwei Verfahren auf einer Adresse — L-76"),
    Stufe("Waechter laesst ohne Geheimnis durch", sicherheit.fail_open_waechter, "quelltext",
          "Pruefung gibt ohne Schluessel wahr zurueck — L-47, L-136"),
    Stufe("Geheimnis in der Adresse", sicherheit.geheimnis_in_adresse, "quelltext",
          "Schluessel im Pfad statt im Kopf — L-98, L-103"),
    Stufe("Stiller Ausfall im Schreibpfad", sicherheit.stiller_ausfall, "quelltext",
          "Fehler geschluckt, Erfolg gemeldet — L-36, L-141"),
    Stufe("Routen ohne Aufrufer / ohne Anmeldung", werkzeuge.einzelmessungen, "anwendung",
          "an der geladenen Anwendung gemessen — L-105, L-51, L-67"),

    # ── Ebene 3: Frontend ───────────────────────────────────────────────
    Stufe("Seiten ohne Weg", stufen.seiten_ohne_route, "quelltext",
          "weder Route noch Aufrufer"),
    Stufe("Bedienelement ohne Wirkung", bauwerk.bedienelement_ohne_wirkung, "quelltext",
          "Knopf ohne Handler und ohne Formularrolle — L-79"),

    # ── Optik ───────────────────────────────────────────────────────────
    Stufe("Farben ausserhalb der Vorgabe", stufen.farben_ausserhalb, "quelltext",
          "Markenfarben ohne Palette, Beinahe-Toene daneben — L-17, L-32, L-158"),

    # ── Konsistenz und Bauwerk ──────────────────────────────────────────
    Stufe("Namensdrift Umgebung", stufen.namensdrift_umgebung, "quelltext",
          "ein Schluessel unter zwei Namen — L-43"),
    Stufe("Umgebung ohne Blueprint", stufen.umgebung_ohne_blueprint, "quelltext",
          "Variable gelesen, in keinem Blueprint — L-42, L-156, L-157"),
    Stufe("Import ohne Eintrag", bauwerk.import_ohne_eintrag, "quelltext",
          "der naechste Neuaufbau scheitert — L-57"),
    Stufe("Prueftor mit Luecke", bauwerk.pruefto_mit_luecke, "quelltext",
          "das Tor prueft weniger, als es verspricht — L-78"),
    Stufe("Termine fremder Dienste", bauwerk.termine_fremder_dienste, "quelltext",
          "angekuendigte Abschaltung laeuft ab — L-81"),
    Stufe("Dateien ueber der Grenze", stufen.zu_grosse_dateien, "quelltext",
          "ueber der doppelten 800-Zeilen-Grenze — L-25"),
)


def ausfuehren(stufe: Stufe) -> tuple[list, str]:
    """Ruft eine Stufe auf; sie darf Befunde oder (Befunde, Notiz) liefern.

    Die Notiz traegt die Grundgesamtheit — „3 der letzten 60 Commits haben ein
    Modell geaendert". Ohne sie waere eine Null nicht zu deuten: sauber, oder
    nichts gesehen?
    """
    ergebnis = stufe.messen()
    if isinstance(ergebnis, tuple):
        return list(ergebnis[0]), str(ergebnis[1])
    return list(ergebnis), ""
