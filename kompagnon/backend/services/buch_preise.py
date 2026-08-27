# -*- coding: utf-8 -*-
"""Preise und Bestellnummern des Buchs (BUCH-05).

**Eine Stelle für die Preise.** Am 24.08.2026 stand der Paketpreis an fünf
Stellen im System, und beim Nachzählen waren es vierzehn (L-29). Dieser Fehler
wird hier nicht wiederholt: Wer einen Buchpreis sucht, findet ihn hier — und
nur hier.

**Sieben Prozent, nicht neunzehn.** Bücher stehen in Anlage 2 UStG; das E-Book
ist dem gedruckten Buch seit Dezember 2019 gleichgestellt, und die Versandkosten
folgen dem Steuersatz der Hauptleistung. Der Produkteditor des Bestandssystems
stellt 19 % voreingestellt ein — für dieses Produkt wäre das falsch (BUCH-12).

**Die Fassung des Standards kommt aus dem Katalog.** `BUCH-05` sah dafür eine
Datei `shared/homepage-standard.json` vor; die gibt es nicht, und sie wäre eine
zweite Wahrheit neben `audit_scoring.STANDARD_VERSION`. Das Buch druckt den
Katalog — also nennt es dieselbe Fassung, die die Bewertung nennt.
"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from services.audit_scoring import STANDARD_VERSION

BUCH_FASSUNG = STANDARD_VERSION
STEUERSATZ = Decimal("7.00")

#: Was verkauft wird. Beträge in Cent — siehe `modelle_buch`.
VARIANTEN = {
    "pdf": {
        "brutto_cents": 3900,
        "versand_cents": 0,
        "bezeichnung": "Der Homepage Standard — PDF-Ausgabe",
    },
    "print": {
        "brutto_cents": 4900,
        "versand_cents": 495,
        "bezeichnung": "Der Homepage Standard — gedruckte Ausgabe",
    },
    "bundle": {
        "brutto_cents": 5900,
        "versand_cents": 495,
        "bezeichnung": "Der Homepage Standard — gedruckt und als PDF",
    },
}


def variante(schluessel: str) -> Optional[dict]:
    return VARIANTEN.get(schluessel)


def bestellnummer(db: Session, jahr: int) -> str:
    """Die nächste Bestellnummer des Jahres — `HS-2026-0001`.

    **Aus der Datenbank gezählt, nicht mitgeschrieben.** Ein Zähler im Speicher
    springt bei jedem Neustart zurück, und bei zwei Instanzen vergibt er
    dieselbe Nummer zweimal. Gezählt wird deshalb der höchste vergebene Wert
    des laufenden Jahres.

    **Die Eindeutigkeit sichert die Datenbank**, nicht diese Funktion: Zwei
    gleichzeitige Bestellungen können dieselbe Nummer errechnen. Dann schlägt
    der eindeutige Index zu, und der Aufrufer versucht es erneut — das ist die
    ehrliche Reihenfolge. Eine Sperre über den ganzen Vorgang zu legen, wäre
    teurer als der seltene zweite Versuch.
    """
    from modelle_buch import BookOrder

    praefix = f"HS-{jahr}-"
    hoechste = (db.query(func.max(BookOrder.order_number))
                .filter(BookOrder.order_number.like(f"{praefix}%"))
                .scalar())
    laufend = 0
    if hoechste:
        try:
            laufend = int(str(hoechste).rsplit("-", 1)[-1])
        except ValueError:
            laufend = 0
    return f"{praefix}{laufend + 1:04d}"
