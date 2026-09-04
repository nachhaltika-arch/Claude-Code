# -*- coding: utf-8 -*-
"""Welches Pflege-Abo für einen Betrieb gilt — und seit wann (L-101).

**Der Rest, der am 31.08.2026 ausdrücklich offen blieb.** Die Stunden sind
seither zählbar (`services/abo_stunden.py`), aber `monatsstand()` liefert nur
den **Verbrauch** und keine Restzahl, weil an keinem Betrieb steht, welches
Abo gilt. Eine Restzahl auf einer Annahme wäre eine Zusage, die niemand
gegeben hat. Dieses Modul schließt genau diese Lücke.

**Der Vertrag zählt in Monaten, nicht in Tagen.** Das Kontingent ist monatlich
zugesagt („zwei Stunden je Monat und Kunde"). Mit Tagesdaten bräuchte es eine
Regel für den Vertrag, der am 15. beginnt — anteilig? voll? gar nicht? Jede
Antwort darauf wäre erfunden. Ein Vertrag gilt **für Monate**, und der Monat,
in dem er beginnt, zählt ganz.

**Ein Wechsel schreibt eine neue Zeile, er überschreibt keine.** Wer von
ABO-BAS auf ABO-PRO wechselt, bekommt eine zweite Zeile; die erste endet im
Vormonat. Das ist keine Ordnungsliebe: Wird der Juli später noch einmal
aufgerufen, muss das Kontingent gelten, das **im Juli** galt. Ein
überschriebener Vertrag schriebe die Vergangenheit still um, und niemand
könnte sagen, ob eine Überschreitung von damals eine war.

**Kein Preis in dieser Tabelle.** Was ein Abo kostet, steht im Produktkatalog;
hier steht nur, welches gilt. Zwei Orte für denselben Preis laufen
auseinander, und dann rechnet die Rechnung anders als das Angebot.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from database import Base

#: Die Kennungen der beiden Pflege-Abos. Sie stehen hier als Wortschatz und
#: **nicht** mit ihrem Kontingent — das gehört `services/abo_stunden.py`, wo
#: es schon steht. Ein zweiter Ort für dieselbe Zahl ist ein Ort, an dem sie
#: irgendwann abweicht.
ABO_BAS = "ABO-BAS"
ABO_PRO = "ABO-PRO"
ABOS = (ABO_BAS, ABO_PRO)


class AboVertrag(Base):
    """Ein Pflege-Abo eines Betriebs, gültig von Monat bis Monat."""

    __tablename__ = "abo_vertraege"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    #: `ABO-BAS` oder `ABO-PRO`.
    produkt = Column(String(20), nullable=False)

    #: Erster Monat, für den das Abo gilt — `JJJJ-MM`.
    start_monat = Column(String(7), nullable=False, index=True)
    #: Letzter Monat, für den es noch gilt. `NULL` heißt **läuft**.
    #:
    #: Bewusst der letzte gültige und nicht der erste ungültige Monat: „gilt
    #: bis einschließlich März" ist die Auskunft, die ein Mensch geben und
    #: nachlesen will. Der Vergleich `start <= monat <= ende` liest sich dann
    #: ohne Sonderfall.
    end_monat = Column(String(7), nullable=True)

    notiz = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(120), default="")


class InhaltsAnfrage(Base):
    """Ein Änderungswunsch des Kunden an seiner Website (Rang 1, 04.09.2026).

    **Warum das fehlte.** Position 5 und 8 des Leistungsverzeichnisses sagen
    „Inhaltsänderungen bis 30 bzw. 90 Minuten je Monat" zu. Die **Zeiterfassung**
    dafür gibt es seit dem 31.08. (`services/abo_stunden`), die **Abrechnung**
    auch — nur konnte der Kunde nichts anfordern und sah seinen Stand nirgends.
    Ein Guthaben ohne Kontostand wird entweder nicht genutzt oder überzogen;
    das erste kostet Vertrauen, das zweite Geld.

    **Diese Tabelle erfasst keine Zeit.** Sie hält den *Wunsch* — die Minuten
    stehen weiter in `abo_stunden`, wo sie seit jeher stehen. Zwei Orte für
    dieselbe Zahl wären ein Ort, an dem sie irgendwann abweicht; `zeit_id`
    verbindet beide, sobald jemand die Arbeit verbucht hat.

    **`monat` ist der Monat der Anfrage, nicht der Erledigung.** Wer am 30.
    anfragt und am 2. bedient wird, hat im Guthaben des Folgemonats gearbeitet
    — die Zuordnung der Minuten macht deshalb die Zeiterfassung, nicht dieser
    Datensatz. Hier steht der Monat nur, damit die Liste sich gruppieren lässt.
    """

    __tablename__ = "inhalts_anfragen"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    monat = Column(String(7), nullable=False, index=True)
    beschreibung = Column(Text, nullable=False)
    seite = Column(String(300), default="")
    status = Column(String(20), default="offen", index=True)
    angefragt_am = Column(DateTime, default=datetime.utcnow)
    angefragt_von = Column(String(120), default="")
    erledigt_am = Column(DateTime, nullable=True)
    bearbeitet_von = Column(String(120), default="")
    zeit_id = Column(Integer, nullable=True)
    notiz = Column(Text, default="")
