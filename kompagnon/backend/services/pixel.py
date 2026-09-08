# -*- coding: utf-8 -*-
"""Die Facebook-Pixel-ID des Analyse-Widgets (Wunsch David, 08.09.2026).

**Nur die Nummer, nie der Schnipsel.** Der Meta Events Manager gibt ein
fertiges `<script>`-Stueck heraus, und genau das ist der wahrscheinlichste
Fehlgriff beim Einfuegen. Ein Widget, das den Schnipsel als Nummer an Facebook
weiterreicht, feuert nichts — und ein Pixel, der nicht feuert, meldet auch
nicht, dass er nicht feuert. Deshalb wird hier abgewiesen statt geschluckt.

**Leer heisst abgeschaltet**, und das ist der ausdrueckliche Weg zurueck: Wer
das Feld leert, laedt im Widget kein fremdes Skript mehr.
"""
import re

#: Meta vergibt 15- bis 16-stellige Nummern. Etwas Luft nach beiden Seiten,
#: damit eine kuenftige Laenge nicht als Fehler gilt — aber eng genug, dass
#: ein eingefuegter Schnipsel oder eine Telefonnummer auffaellt.
MUSTER = re.compile(r"^\d{10,20}$")

MELDUNG = ("Die Facebook-Pixel-ID besteht nur aus Ziffern (10 bis 20). "
           "Bitte nicht den ganzen Skript-Schnipsel einfuegen, sondern die "
           "Nummer aus dem Meta Events Manager.")


def geprueft(wert) -> str:
    """Die Pixel-ID, wie sie gespeichert werden darf.

    :raises ValueError: wenn etwas dasteht, das keine Pixel-ID ist.
    """
    gestutzt = (wert or "").strip()
    if not gestutzt:
        return ""
    if not MUSTER.match(gestutzt):
        raise ValueError(MELDUNG)
    return gestutzt
