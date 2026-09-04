"""Die Modelle der Meldungen (L-25).

`Message` (die interne Nachricht), `Benachrichtigung` (was ein Mensch im
Werkzeug angezeigt bekommt) und `Meldungsvorliebe` (welche Arten er ueberhaupt
will). Am 2026-08-30 aus `database.py` herausgeloest.

**Warum die drei zusammengehoeren:** Sie beschreiben denselben Vorgang in drei
Stufen — etwas passiert, jemand erfaehrt es, jemand will es erfahren. Die
dritte ist der Schalter zur zweiten; sie getrennt abzulegen hiesse, den Schalter
vom Licht zu trennen.

**Diese Datei muss geladen werden**, wie alle `modelle_*.py` — siehe den
Importblock am Ende von `database.py`.
"""
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from database import Base


class Message(Base):
    __tablename__ = "messages"
    id          = Column(Integer, primary_key=True)
    lead_id     = Column(Integer, ForeignKey("leads.id"), nullable=False)
    sender_role = Column(String, nullable=False)   # "admin" | "kunde"
    sender_name = Column(String)                   # z.B. "David" oder Firmenname
    channel     = Column(String, default="in_app") # "in_app" | "email"
    subject     = Column(String)                   # nur bei channel="email"
    content     = Column(Text, nullable=False)
    is_read     = Column(Boolean, default=False)
    read_at     = Column(DateTime, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Benachrichtigung(Base):
    """Was vom Kunden hereinkommt — Ticket, Chatnachricht, spaeter E-Mail.

    **Warum eine eigene Tabelle und nicht „die ungelesenen zusammenzaehlen"
    (26.08.2026, L-18).** Ein Ticket, eine Chatnachricht und eine Mail liegen
    in drei Tabellen mit drei Formen. Sie beim Anzeigen zusammenzurechnen
    hiesse, an jeder Stelle alle drei zu kennen — und die vierte, die
    dazukommt, wird vergessen.

    Eine Meldung ist ein eigener Vorgang: Sie entsteht einmal, sie wird einmal
    gelesen, und sie traegt ein **Ziel**, das man anklicken kann. Eine Meldung
    ohne Weg dorthin verlangt vom Leser, selbst zu suchen.
    """

    __tablename__ = "benachrichtigungen"

    id         = Column(Integer, primary_key=True)
    #: "ticket" | "chat" | "mail". Bewusst eine Zeichenkette und kein Enum —
    #: eine vierte Quelle soll eine Zeile kosten, keine Migration.
    art        = Column(String(20), nullable=False)
    lead_id    = Column(Integer, ForeignKey("leads.id"), nullable=True)
    titel      = Column(String(300), nullable=False)
    hinweis    = Column(Text)
    #: Wohin der Klick fuehrt, als Pfad im Werkzeug.
    ziel       = Column(String(300))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    gelesen_am  = Column(DateTime, nullable=True)


class Meldungsvorliebe(Base):
    """Ob ein Ereignis zusaetzlich per Mail gemeldet wird.

    **Warum eine Zeile je Ereignis und kein Feld je Benutzer
    (26.08.2026).** KOMPAGNON wird von einer Person bedient; ein
    Vorlieben-Satz je Konto waere eine Verallgemeinerung auf Vorrat. Kommt
    ein zweiter Innendienst dazu, kostet die Erweiterung eine Spalte — heute
    kostet sie Bedienoberflaeche, die niemand braucht.

    **Kein Eintrag heisst nicht „aus".** Fehlt die Zeile, gilt die Vorgabe
    aus `services/meldungsvorlieben.EREIGNISSE` — und die ist fuer jedes
    Ereignis genau das Verhalten von heute. Ein leerer Bestand darf keinen
    Versand heimlich abschalten.
    """

    __tablename__ = "meldungsvorlieben"

    schluessel  = Column(String(40), primary_key=True)
    aktiv       = Column(Boolean, nullable=False, default=True)
    geaendert_am = Column(DateTime, default=datetime.utcnow)
