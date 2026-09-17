# -*- coding: utf-8 -*-
"""Die Brevo-Uebertragung schweigt nicht mehr, wenn sie nichts tut.

**Der Fund vom 17.09.2026.** `uebertrage_anfrage` brach bei fehlender
Listen-ID mit einem blanken `return` ab. Die Protokollzeile fuer diesen Fall
steht in `uebertrage` — also eine Ebene tiefer, die nie erreicht wurde. Das
Ergebnis war ein System, das bei fehlender Einrichtung **vollstaendig
schweigt**: kein Fehler, keine Warnung, kein Eintrag.

An den Render-Protokollen gemessen: Zwischen dem 03.09. und 13.09. haben
neun Adressen ihre E-Mail bestaetigt (`Widget-Adresse bestaetigt`), darunter
zwei echte Interessenten. Zu keiner einzigen steht eine Brevo-Zeile im
Protokoll — weder `in Liste ... eingetragen` noch `fehlgeschlagen`. Vierzehn
Tage lang sah „nicht eingerichtet" genauso aus wie „laeuft".

**Warum ein Test und nicht nur eine Zeile Code.** Eine Warnung, die jemand
beim naechsten Aufraeumen als „Rauschen" entfernt, ist wieder weg. Der Test
haelt fest, dass der Fall **ueberhaupt** eine Spur hinterlaesst — und
daneben, dass der eingerichtete Fall weiterhin durchkommt. Ohne die zweite
Zusicherung waere die erste auch dann gruen, wenn die Uebertragung nie
stattfindet (`waechter_ohne_wirkung`).
"""
import logging

from services import widget_crm


def test_ohne_listen_id_steht_eine_warnung_im_protokoll(caplog):
    with caplog.at_level(logging.WARNING, logger="services.widget_crm"):
        widget_crm.uebertrage_anfrage(12345, None, "adresse_bestaetigt")

    assert caplog.records, "Der Fall hinterlaesst keine Spur — genau der Fehler."
    text = caplog.text
    assert "BREVO_LIST_VERIFIED_ID" in text, (
        "Die Warnung nennt nicht, welche Variable fehlt — dann sucht der "
        "Leser im Code statt in der Umgebung.")
    assert "12345" in text and "adresse_bestaetigt" in text, (
        "Ohne Anfrage und Quelle laesst sich nicht sagen, wen es betraf.")


def test_mit_listen_id_wird_nicht_abgebrochen(monkeypatch, caplog):
    """Die positive Zusicherung daneben: Eingerichtet kommt sie durch.

    Geprueft wird an der Stelle, an der die Funktion die Datenbank oeffnet —
    weiter kommt sie hier nicht, und weiter muss sie auch nicht: Bewiesen ist
    damit, dass die Abzweigung von oben **nicht** genommen wurde.
    """
    erreicht = []

    def _sitzung():
        erreicht.append(True)
        raise RuntimeError("Abbruch nach der Abzweigung — Absicht des Tests.")

    monkeypatch.setattr("database.SessionLocal", _sitzung)

    with caplog.at_level(logging.WARNING, logger="services.widget_crm"):
        try:
            widget_crm.uebertrage_anfrage(12345, 7, "adresse_bestaetigt")
        except RuntimeError:
            pass

    assert erreicht, "Die Funktion kam nicht ueber die Abzweigung hinaus."
    assert "uebersprungen" not in caplog.text
