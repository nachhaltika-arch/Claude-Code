"""Die Modelle des Projekt-Assistenten (L-25).

**Warum eigene Datei, 22.08.2026.** `database.py` hatte 1.361 Zeilen und 39
Modellklassen. Unterhaltung und Nachricht — der Kundenweg aus dem Portal.

**Wichtig:** Diese Datei wird von `database.py` am Ende importiert. Ohne das
waere sie nie geladen, und die `relationship()`-Aufrufe der anderen Modelle
faenden ihre Gegenseite nicht — mit einem Fehler zur Laufzeit an einer
Stelle, die mit der Ursache nichts zu tun hat.
`tests/test_modelle_vollstaendig.py` haelt das fest.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class AssistantConversation(Base):
    """Ein Gespräch mit dem Projekt-Assistenten.

    Entscheidung 3.2 der Anforderungen: Assistentengespräche liegen in einer
    eigenen Ablage, getrennt von `messages`. Der Posteingang füllt sich nicht
    mit KI-Nachrichten, der Verlauf bleibt trotzdem nachvollziehbar — auch für
    den Nachweis, was der Assistent geraten hat.

    Projektbezogen von Anfang an, obwohl Ausbau 1 nur das Briefing begleitet:
    So erzwingt Ausbau 2 (Projektbegleitung) keine Migration.

    Neue Tabellen legt `Base.metadata.create_all` beim Start an. Neue *Spalten*
    an bestehenden Tabellen tun das nicht — die gehören in
    `migrations_runtime.py::run_migrations`.
    """

    __tablename__ = "assistant_conversations"

    id          = Column(Integer, primary_key=True)
    lead_id     = Column(Integer, ForeignKey("leads.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    project_id  = Column(Integer, nullable=True, index=True)
    modus       = Column(String(20), nullable=False, default="kunde")
    # Wer das Gespräch führt — für das Tageslimit je Nutzer.
    user_id     = Column(Integer, nullable=True, index=True)
    titel       = Column(String(200), default="")
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Gesetzt, wenn daraus eine echte Nachricht ans Team wurde.
    escalated_at = Column(DateTime, nullable=True)

    messages = relationship("AssistantMessage", back_populates="conversation",
                            cascade="all, delete-orphan",
                            order_by="AssistantMessage.id")


class AssistantMessage(Base):
    """Eine einzelne Nachricht im Assistentengespräch.

    Der Verbrauch steht an der Nachricht, nicht in einer eigenen Tabelle: Jede
    Zeile weiß, was sie gekostet hat, und die Summe je Projekt ist eine Abfrage.
    """

    __tablename__ = "assistant_messages"

    id              = Column(Integer, primary_key=True)
    conversation_id = Column(Integer,
                             ForeignKey("assistant_conversations.id",
                                        ondelete="CASCADE"),
                             nullable=False, index=True)
    rolle           = Column(String(20), nullable=False)   # "nutzer" | "assistent"
    inhalt          = Column(Text, nullable=False)
    # Woran der Nutzer gerade arbeitet — Schritt und Feld des Wizards.
    schritt         = Column(String(60), default="")
    feld            = Column(String(60), default="")
    eingabe_tokens  = Column(Integer, default=0)
    ausgabe_tokens  = Column(Integer, default=0)
    kosten_euro     = Column(Float, default=0.0)
    created_at      = Column(DateTime, default=datetime.utcnow, index=True)

    conversation = relationship("AssistantConversation", back_populates="messages")
