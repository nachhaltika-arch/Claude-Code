# -*- coding: utf-8 -*-
'''Die verbindliche Preisangabe eines Pakets — an einer Stelle gerechnet.

**Warum es diesen Dienst gibt (L-164).** Das Datenblatt WS-STA-01 stellt in
§ 4.1 eine Bedingung an das Produkt selbst, nicht an seine Beschreibung:

    „Der Preis darf niemals als '1.500 €' allein beworben werden. Wenn ein
    Abonnement zwingender Bestandteil ist, gehört der Gesamtpreis der
    Mindestlaufzeit in jede Preisangabe — in Anzeigen, auf der Preisseite,
    im Angebot, im Audit-Bericht."

Der Grund ist kein Geschmack: Eine Bewerbung mit dem Einmalpreis, bei der die
Abo-Pflicht erst im Kleingedruckten steht, ist das Vorenthalten einer
wesentlichen Information — angreifbar durch Mitbewerber und Wettbewerbsvereine.

**Warum gerechnet und nicht getippt.** Der Gesamtpreis des ersten Jahres ist
1.500 + 12 × 79 = 2.448 €. Stünde diese Zahl als Text in der Produktzeile,
wäre sie in dem Augenblick falsch, in dem jemand das Pflegeentgelt ändert —
und zwar falsch in einer Angabe, deren Richtigkeit rechtlich gefordert ist.
Sie wird deshalb aus zwei Quellen gebildet, die es schon gibt: dem Bau-
Nettopreis der Produktzeile und dem Abo-Preis aus `services.abo_stunden`.

**Warum im Backend und nicht in der Oberfläche.** § 4.1 verlangt die Angabe an
vier Orten. Ein Feld in der Antwort von `/api/products` erreicht alle vier;
eine Funktion im Shop erreicht den Shop.
'''
from typing import Optional

from services.abo_stunden import (
    PREIS_ABO_BAS_NETTO_CENT,
    PREIS_ABO_PRO_NETTO_CENT,
)

#: Die Abos, an die ein Paket gekoppelt sein kann — Kennung wie im Datenblatt.
#: Sie stehen **nicht** in `products`: Ihr Preis ist die Grundlage jeder
#: Abrechnung und liegt seit L-100 in `abo_stunden`. Eine zweite Zeile mit
#: demselben Betrag wäre genau die Bauart, die dieser Dienst vermeiden soll.
ABO_PREISE_NETTO_CENT = {
    "ABO-BAS": PREIS_ABO_BAS_NETTO_CENT,
    "ABO-PRO": PREIS_ABO_PRO_NETTO_CENT,
}


def _euro(cent: int) -> str:
    '''1500,00 € in deutscher Schreibweise — Punkt für Tausend, Komma für Cent.'''
    return f"{cent / 100:,.2f} €".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def abo_preis_netto_cent(abo: Optional[str]) -> int:
    '''Was das gekoppelte Abo monatlich netto kostet — 0, wenn keines gekoppelt ist.

    Eine **unbekannte** Kennung gibt ebenfalls 0 zurück statt zu scheitern:
    Diese Funktion beantwortet eine Anzeigefrage, und ein Tippfehler in einer
    Produktzeile darf den Katalog nicht unerreichbar machen. Dass die Kopplung
    dann nicht angezeigt wird, fällt beim ersten Blick auf die Seite auf —
    ein leerer Shop fällt später auf und sieht nach einem Ausfall aus.
    '''
    return ABO_PREISE_NETTO_CENT.get((abo or "").strip().upper(), 0)


def gesamtpreis_erstes_jahr_netto_cent(bau_netto_cent: int, abo: Optional[str],
                                       laufzeit_monate: int) -> int:
    '''Bauleistung plus Pflegeentgelt der Mindestlaufzeit, netto.'''
    monatlich = abo_preis_netto_cent(abo)
    monate = max(0, int(laufzeit_monate or 0))
    return int(bau_netto_cent) + monatlich * monate


def preisangabe(bau_netto_cent: int, abo: Optional[str],
                laufzeit_monate: int) -> str:
    '''Der Satz, der neben dem Preis stehen muss — leer, wenn kein Abo gekoppelt ist.

    Der Wortlaut folgt der „verbindlichen Darstellung" aus § 4.1 des
    Datenblatts. Er ist bewusst **nicht** frei konfigurierbar: Eine Vorgabe,
    die jeder überschreiben kann, ist keine.
    '''
    monatlich = abo_preis_netto_cent(abo)
    monate = max(0, int(laufzeit_monate or 0))
    if not monatlich or not monate:
        return ""
    gesamt = gesamtpreis_erstes_jahr_netto_cent(bau_netto_cent, abo, monate)
    return (f"{_euro(int(bau_netto_cent))} netto einmalig zzgl. "
            f"{_euro(monatlich)} netto monatlich, Mindestlaufzeit {monate} Monate. "
            f"Gesamtpreis erstes Jahr: {_euro(gesamt)} netto.")
