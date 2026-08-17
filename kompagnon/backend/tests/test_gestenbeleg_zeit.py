"""Der Bedienungsbeleg darf nicht durch bloßes Lesen der Seite zu haben sein.

Befund vom 17.08.2026. Die Hürde war gebaut, um Postfach-Scanner abzuwehren:
Das Feld `nachweis` ist im ausgelieferten HTML leer und wird erst bei
`pointerdown` gefüllt. Gegen ein blind abgeschicktes Formular wirkt das.

**Nur stand der Wert daneben.** Er hing als `data-nachweis` am Knopf — also im
selben HTML, das die Hürde schützen soll. Wer die Seite abruft, sie liest und
den Wert zurückschickt, kommt durch: ohne JavaScript, ohne Geste. Der Beleg
bewies „jemand hat die Seite geladen", nicht „jemand hat den Knopf gedrückt".

Beweisen lässt sich ein Mensch von hier aus nicht. Was sich einbauen lässt,
ist etwas, das man durch Lesen nicht bekommt: **Zeit**. Der Beleg trägt den
Zeitpunkt seiner Ausgabe, und die Bestätigung wird erst angenommen, wenn
zwischen Ausgabe und Absenden genug Zeit liegt — und nicht zu viel.

Ein Dienst, der Links abklappert, tut das in Millisekunden. Ein Mensch braucht
Sekunden. Wartet ein Dienst absichtlich zwei Sekunden, ist er von einem
Menschen ohnehin nicht mehr zu unterscheiden — dann hilft nur noch der
Nachweis, wer es war, und den gibt es seit heute auch.
"""
import time

import pytest

from services.widget_report import (
    BELEG_HOECHSTALTER_S,
    BELEG_MINDESTALTER_S,
    beleg_gueltig,
    gestenbeleg,
)


TOKEN = "pytest-token-fuer-den-beleg"


def test_ein_frischer_beleg_gilt_noch_nicht():
    """Genau das Loch: Seite abrufen, Wert lesen, sofort zurückschicken."""
    beleg = gestenbeleg(TOKEN)

    gueltig, grund = beleg_gueltig(TOKEN, beleg)

    assert gueltig is False
    assert grund == "zu_schnell"


def test_nach_der_wartezeit_gilt_er():
    beleg = gestenbeleg(TOKEN, zeitpunkt=time.time() - (BELEG_MINDESTALTER_S + 1))

    gueltig, grund = beleg_gueltig(TOKEN, beleg)

    assert gueltig is True
    assert grund == "ok"


def test_ein_alter_beleg_gilt_nicht_mehr():
    """Eine Seite von gestern soll sich nicht abschicken lassen."""
    beleg = gestenbeleg(TOKEN, zeitpunkt=time.time() - (BELEG_HOECHSTALTER_S + 60))

    gueltig, grund = beleg_gueltig(TOKEN, beleg)

    assert gueltig is False
    assert grund == "zu_alt"


def test_ein_erfundener_beleg_gilt_nicht():
    gueltig, grund = beleg_gueltig(TOKEN, "1755000000.deadbeef")

    assert gueltig is False
    assert grund == "falsch"


def test_der_beleg_eines_anderen_tokens_gilt_nicht():
    """Sonst genügt ein einziger gelesener Beleg für alle Bestätigungen."""
    fremd = gestenbeleg("ein-anderes-token",
                        zeitpunkt=time.time() - (BELEG_MINDESTALTER_S + 1))

    gueltig, grund = beleg_gueltig(TOKEN, fremd)

    assert gueltig is False
    assert grund == "falsch"


def test_ein_veraenderter_zeitpunkt_gilt_nicht():
    """Sonst schreibt sich der Abrufer die Wartezeit einfach selbst."""
    beleg = gestenbeleg(TOKEN)
    _, unterschrift = beleg.split(".", 1)
    gefaelscht = f"{time.time() - 999:.0f}.{unterschrift}"

    gueltig, grund = beleg_gueltig(TOKEN, gefaelscht)

    assert gueltig is False
    assert grund == "falsch"


@pytest.mark.parametrize("murks", ["", "keinpunkt", ".", "abc.def", "1755000000."])
def test_unsinn_wird_abgewiesen(murks):
    gueltig, _ = beleg_gueltig(TOKEN, murks)

    assert gueltig is False


def test_die_seite_liefert_einen_zeitgestempelten_beleg():
    """Verstecken hilft nicht — der Browser braucht den Wert ja auch.

    Ein Abrufer, der die Seite liest, bekommt den Beleg weiterhin. Er nützt
    ihm nur nichts, solange er ihn sofort zurückschickt. Genau das tun
    Postfach-Scanner: Sie klappern Links in Millisekunden ab.
    """
    from services.widget_report import aktionsseite

    beleg = gestenbeleg(TOKEN)
    seite = aktionsseite("Titel", "Text", "Knopf", "/ziel", nachweis=beleg)

    assert beleg in seite
    assert beleg_gueltig(TOKEN, beleg)[0] is False, "frisch ausgestellt, also noch nicht gültig"


def test_die_geste_wird_nur_bei_echten_ereignissen_uebernommen():
    """`isTrusted` ist false, wenn ein Skript das Ereignis erzeugt hat."""
    from services.widget_report import aktionsseite

    seite = aktionsseite("Titel", "Text", "Knopf", "/ziel", nachweis=gestenbeleg(TOKEN))

    assert "isTrusted" in seite
