# -*- coding: utf-8 -*-
"""Welche AGB-Fassung ein Käufer akzeptiert hat (L-100, ORDERS_05).

**Der Punkt, den ORDERS_05 „den Punkt, den fast alle vergessen" nennt.**
Ändern sich die AGB, muss nachweisbar bleiben, **welche Fassung** der Käufer
akzeptiert hat. Ohne diese Angabe ist die Zustimmung im Streitfall wertlos —
sie belegt dann nur, dass jemand irgendwann irgendetwas angehakt hat.

**Hier steht kein Rechtstext, und das ist Absicht.** ORDERS_05 sagt es
wörtlich: *„Erfinde keine Rechtstexte — auch keine Platzhalter, die aussehen
wie echte Texte."* Nachgesehen am 29.08.2026: Im Frontend gibt es
`Impressum.jsx` und `Datenschutz.jsx`, **keine AGB und keine
Widerrufsbelehrung**. Beide müssen von der Kanzlei kommen, bevor der Shop
öffentlich erreichbar ist.

Was dieses Modul kennt, ist deshalb nur die **Kennung** der Fassung — ein
Datum wie `2026-09-01`, gesetzt über `AGB_FASSUNG`, sobald die Texte
vorliegen. Der Wortlaut liegt im Frontend, nicht hier.

**Warum eine Umgebungsvariable und kein Wert im Quelltext.** Die Fassung
wechselt mit den Texten, nicht mit einem Deploy — und Staging soll eine
Fassung prüfen können, die produktiv noch nicht gilt.

**Warum die Abwesenheit ein Riegel ist und kein leeres Feld.** Ein Feld, das
NULL sein darf, wird NULL sein. Solange keine Fassung hinterlegt ist, entsteht
gar keine Bestellung — damit setzt der Code durch, was die Übersicht bisher
nur in Prosa sagt: **vor ORDERS_05 geht nichts live.**
"""
import os
from typing import Optional


def fassung() -> Optional[str]:
    """Die geltende AGB-Fassung — oder `None`, wenn keine hinterlegt ist.

    Bei jedem Aufruf gelesen und nicht beim Import: Ein Modulwert wird beim
    ersten Import eingefroren, und wer die Variable nachträgt, müsste den
    Dienst neu starten, ohne zu wissen warum.

    Leerraum gilt als nicht hinterlegt. Sonst stünde in einer Bestellung eine
    Fassung namens `" "`, und der Riegel wäre offen, ohne dass es auffiele.
    """
    return (os.getenv("AGB_FASSUNG", "").strip() or None)


def verlangen() -> str:
    """Die Fassung — oder ein Abbruch mit einer Meldung, die den Grund nennt.

    503 und nicht 400: Das ist ein Einrichtungszustand, kein Fehler des
    Käufers. Und die Meldung nennt **die AGB**, nicht „nicht eingerichtet" —
    sonst sucht jemand einen Stripe-Schlüssel, der längst da ist.
    """
    from fastapi import HTTPException

    gueltig = fassung()
    if not gueltig:
        raise HTTPException(
            503,
            "Der Verkauf ist noch nicht eingerichtet: Es ist keine "
            "AGB-Fassung hinterlegt (AGB_FASSUNG). Ohne sie liesse sich "
            "spaeter nicht nachweisen, welchen Bedingungen zugestimmt wurde.")
    return gueltig
