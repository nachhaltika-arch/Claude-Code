"""Slot-Angaben eines Blocks aus seinem Markup vervollstaendigen.

Vertragsregel R3 verlangt, dass jeder ``{{slot}}`` im Markup auch in den
Slot-Angaben steht — sonst fuellt ``generate-copy`` ihn nie, und der Block
zeigt beim Kunden eine geschweifte Klammer.

Der scharfe Lauf gegen die echte API (2026-08-13, zehn Bloecke) hat genau
einen Verstoss produziert, und der war zwoelfmal dieser: das Modell hatte die
Slots geschrieben, aber nicht aufgelistet. Es dafuer ein zweites Mal zu fragen
kostete 11k Eingabe- und 8k Ausgabe-Token — fuer eine Angabe, die im Markup
bereits steht. Also wird sie dort abgelesen statt erfragt.

Ergaenzt wird nur, was fehlt. Was das Modell selbst beschriftet hat, bleibt
unangetastet: eine abgeleitete Beschriftung ist immer schlechter als eine
gemeinte.
"""
from typing import List

from services.block_contract import slots_im_markup


def _beschriftung(key: str) -> str:
    """``product_1_spec_1`` wird zu ``Product 1 Spec 1`` — dieselbe Machart wie
    die Beschriftungen der bestehenden Bibliothek (``Schritt 1 Label``)."""
    return " ".join(teil.capitalize() for teil in key.split("_") if teil)


def ergaenze_fehlende_slots(html: str, slots) -> List:
    """Die Slot-Angaben, erweitert um jeden Slot, der nur im Markup steht.

    Reihenfolge: erst die vorhandenen Angaben, dann die fehlenden in der
    Reihenfolge ihres Auftretens im Markup. Die uebergebene Liste bleibt
    unveraendert.
    """
    vorhanden = list(slots or [])
    bekannt = {s.get("key") for s in vorhanden if isinstance(s, dict)}

    fehlend = [
        {
            "key":     name,
            "type":    "text",
            "label":   _beschriftung(name),
            # Als Vorgabewert die Beschriftung: im Wireframe ist der Platzhalter
            # sichtbar, statt dass an der Stelle eine Luecke klafft.
            "default": _beschriftung(name),
        }
        for name in slots_im_markup(html or "")
        if name not in bekannt
    ]
    return vorhanden + fehlend
