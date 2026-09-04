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

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text)

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

    #: Wie dieser Vertrag eingezogen wird — `rechnung` oder `stripe`.
    #:
    #: **Warum das am Vertrag steht und nicht am Betrieb (04.09.2026).** Am
    #: 01.09. war entschieden, monatlich per Rechnung abzurechnen; am 04.09.
    #: hat David entschieden, das Pflege-Abo über Stripe laufen zu lassen.
    #: Beides ist richtig gewesen — aber nicht rückwirkend: Wer einen Vertrag
    #: unter „Rechnung" abgeschlossen hat, hat keine Einzugsermächtigung
    #: erteilt. Eine laufende Zeile auf `stripe` umzustellen hieße, Geld von
    #: einem Konto zu holen, für das niemand zugestimmt hat.
    #:
    #: **Der Vorgabewert ist `rechnung`, nicht `stripe`** — und zwar hier
    #: wie in der Datenbank. Eine Zeile, bei der niemand die Abrechnungsart
    #: genannt hat, ist ein Vertrag, den niemand abbuchen wollte. Wer
    #: `stripe` will, sagt es; `abo_vertrag.anlegen` tut das für alles Neue.
    #: Der Wechsel eines bestehenden Vertrags ist ein Vorgang mit Zustimmung,
    #: kein Feld-Update.
    abrechnung = Column(String(10), nullable=False, default="rechnung")

    #: Das Stripe-Abonnement, sobald der Kunde den Kaufweg abgeschlossen hat.
    #: Leer heißt: Vertrag steht, Einzug noch nicht eingerichtet.
    stripe_subscription_id = Column(String(200), default="")
    #: Der Stripe-Preis, gegen den das Abonnement läuft — zum Nachvollziehen,
    #: welcher Betrag zum Zeitpunkt des Abschlusses galt.
    stripe_price_id = Column(String(200), default="")

    notiz = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(120), default="")

    @property
    def laeuft_ueber_stripe(self) -> bool:
        """Zieht Stripe dieses Abo ein — und ist es dort auch eingerichtet?

        **Beide Bedingungen, und das ist der Punkt.** Ein Vertrag auf
        `stripe` ohne Abonnement wird von niemandem eingezogen: Stripe kennt
        ihn nicht, und der Aufstellungslauf hielte ihn für erledigt. Genau
        dort entsteht der Monat, den keiner berechnet.
        """
        return self.abrechnung == "stripe" and bool(self.stripe_subscription_id)


class Leistungsbericht(Base):
    """Der Monatsbericht eines Betriebs — was gemessen wurde, Monat für Monat.

    **Warum es diese Tabelle gibt (L-160, Rang 2, 04.09.2026).** Der
    Monatsbericht läuft seit Langem (`automations/scheduler_bericht.py`): Er
    misst PageSpeed, lässt einen Kommentar schreiben und verschickt eine
    Mail. **Gespeichert wurde davon nur der letzte Messwert** — in zwei
    Spalten am Betrieb, die der nächste Lauf überschreibt. Der Bericht
    existierte damit ausschließlich im Postfach des Kunden; im Kundenkonto,
    für das er monatlich zahlt, war er nicht abrufbar.

    ABO-PRO sagt einen „monatlichen Leistungsbericht" zu. Eine Mail, die man
    gelöscht hat, ist keine Auskunft mehr.

    **Eine Zeile je Betrieb und Monat.** Ein zweiter Lauf im selben Monat
    überschreibt sie, statt eine zweite anzulegen — sonst stünde derselbe
    Monat zweimal im Verlauf, und der Vergleich zum Vormonat wäre nicht mehr
    eindeutig.
    """

    __tablename__ = "leistungsberichte"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)

    #: `JJJJ-MM` — derselbe Zuschnitt wie bei den Abo-Zeiten.
    monat = Column(String(7), nullable=False, index=True)

    #: Die Messwerte. `NULL` heißt **nicht erhoben**, nicht null Punkte —
    #: dieselbe Regel wie im Audit (§ 3.5): Was nicht gemessen wurde, darf
    #: nicht als schlechtes Ergebnis erscheinen.
    mobile = Column(Integer, nullable=True)
    desktop = Column(Integer, nullable=True)

    #: Wogegen verglichen wurde. Steht mit in der Zeile, damit der Verlauf
    #: auch dann stimmt, wenn ein Monat fehlt.
    vormonat_mobile = Column(Integer, nullable=True)

    #: Ob die Mail hinausging. **Getrennt vom Messwert, und das ist der
    #: Punkt:** Bis zum 04.09.2026 wurde überhaupt nur gespeichert, *wenn*
    #: der Versand geklappt hat. Eine gescheiterte Mail warf damit die
    #: Messung weg, und der nächste Monat verglich gegen einen veralteten
    #: Stand. Gemessen ist gemessen.
    versendet = Column(Boolean, default=False)

    erstellt_am = Column(DateTime, default=datetime.utcnow)


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
