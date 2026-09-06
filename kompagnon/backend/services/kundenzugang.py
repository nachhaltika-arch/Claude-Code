# -*- coding: utf-8 -*-
"""Zwei Rechtestufen im Kundenkonto — ein Betrieb ist keine Person.

**Der Befund (L-160 Rang 4, K7 der Reibungskarte).** Ein Betrieb hatte genau
ein Konto. Wer einem Kollegen Zugang geben wollte, gab sein Kennwort weiter —
und damit auch den Blick auf Rechnungen und Zahlungsart. Die Routen zum
Anlegen von Konten gibt es laengst, aber sie verlangen `manage_users`, also
Innendienst: Jeder Zugang musste bei uns beantragt werden.

**Die zwei Stufen kommen aus dem Entwurf `kundenkonto-neu`** (David,
06.09.2026) und sind bewusst nur zwei. Drei waeren genauer und wuerden
seltener stimmen; die Frage, die ein Betrieb wirklich stellt, ist „darf der
ans Geld?".

**Warum ein leeres Feld `alles` bedeutet.** Jedes heutige Kundenkonto ist das
des Vertragsinhabers. Waere die Vorgabe `ansehen`, haette das Ausrollen jeden
Bestandskunden still auf die schwache Stufe gesetzt — dieselbe Ueberlegung wie
bei der Ausschlussliste der Sitzungen (L-172): Die Regel wirkt auf das, was
ausdruecklich gesetzt wurde, nicht auf den Bestand.

**Und warum die Sperre hier steht und nicht in den Routern.** Sie gilt an
mehreren Stellen — Zahlungen, Rechnungen, spaeter Vertragsunterlagen. Eine
Rechteregel, die an drei Orten steht, ist eine, die an zweien veraltet.
"""
from typing import Optional

#: Sieht alles ausser Rechnungen, Zahlungsart und Vertragsunterlagen.
ANSEHEN = "ansehen"

#: Zusaetzlich: freigeben, Aenderungen anfordern, Zugaenge verwalten.
ALLES = "alles"

STUFEN = (ANSEHEN, ALLES)

#: Was in der Oberflaeche daneben steht — die Erklaerung gehoert zur Stufe,
#: nicht in die Seite. Sonst haette der Bildschirm eine zweite Fassung.
BESCHREIBUNG = {
    ANSEHEN: ("Sieht den Projektstand, die Freigaben und die Berichte — "
              "aber keine Rechnungen, keine Zahlungsart und keine "
              "Vertragsunterlagen."),
    ALLES: ("Sieht alles und darf handeln: freigeben, Änderungen anfordern, "
            "Rechnungen einsehen und weitere Zugänge einrichten."),
}


def stufe_von(konto) -> str:
    """Die Stufe eines Kontos — `ALLES`, wenn keine eingetragen ist.

    **Ein leeres Feld ist kein Verdacht.** Der Bestand traegt nichts, und jedes
    Bestandskonto gehoert dem Vertragsinhaber.
    """
    wert = (getattr(konto, "kunde_recht", None) or "").strip().lower()
    return wert if wert in STUFEN else ALLES


def pruefe_stufe(wert: Optional[str]) -> str:
    """Eine Stufe aus einer Eingabe — mit klarer Absage statt stiller Vorgabe.

    **Kein Rueckfall auf `ALLES`.** Ein Tippfehler im Aufruf duerfte sonst
    versehentlich das starke Recht vergeben; hier ist die laute Absage die
    sichere.
    """
    kennung = (wert or "").strip().lower()
    if kennung not in STUFEN:
        raise ValueError(f"Unbekannte Rechtestufe: {wert!r}")
    return kennung


def darf_geld_sehen(stufe: str) -> bool:
    """Rechnungen, Zahlungsart, Vertragsunterlagen."""
    return stufe == ALLES


def darf_handeln(stufe: str) -> bool:
    """Freigeben und Aenderungen anfordern — alles, was den Vertrag beruehrt."""
    return stufe == ALLES


def darf_verwalten(stufe: str) -> bool:
    """Zugaenge einrichten, aendern, entfernen.

    Getrennt von `darf_handeln`, obwohl heute dieselbe Antwort: Die Frage
    „darf jemand andere hereinlassen" ist eine eigene, und sie wird als
    erste eine dritte Stufe brauchen.
    """
    return stufe == ALLES
