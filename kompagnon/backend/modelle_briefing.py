"""Das Modell des Briefings — der Fragebogen zum Auftrag (L-25).

**Warum eigene Datei, 23.08.2026.** 62 Zeilen fuer ein Thema, das sonst
nirgends in `database.py` vorkommt: was der Kunde ueber sein Vorhaben angibt,
bevor gebaut wird. Die zugehoerigen Router liegen seit dem 22.08. ebenfalls
fuer sich (`briefings.py`, `briefings_ki.py`).

**Diese Datei muss geladen werden**, wie alle `modelle_*.py` — siehe den
Importblock am Ende von `database.py`.
"""
from datetime import datetime

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.orm import relationship

from database import Base


class Briefing(Base):
    """Briefing questionnaire for web design projects."""
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True)
    lead_id = Column(Integer, ForeignKey('leads.id', ondelete='CASCADE'), nullable=False, unique=True)
    # Legacy JSON sections (used by BriefingTab)
    projektrahmen = Column(Text, default='{}')
    positionierung = Column(Text, default='{}')
    zielgruppe = Column(Text, default='{}')
    wettbewerb = Column(Text, default='{}')
    inhalte = Column(Text, default='{}')
    funktionen = Column(Text, default='{}')
    branding = Column(Text, default='{}')
    struktur = Column(Text, default='{}')
    hosting = Column(Text, default='{}')
    seo = Column(Text, default='{}')
    projektplan = Column(Text, default='{}')
    freigaben = Column(Text, default='{}')
    # Flat project briefing fields
    project_id = Column(Integer, nullable=True)
    gewerk = Column(Text)
    leistungen = Column(Text)
    einzugsgebiet = Column(Text)
    usp = Column(Text)
    mitbewerber = Column(Text)
    vorbilder = Column(Text)
    farben = Column(Text)
    wunschseiten = Column(Text)
    stil = Column(Text)
    logo_vorhanden = Column(Boolean, default=False)
    fotos_vorhanden = Column(Boolean, default=False)
    sonstige_hinweise = Column(Text)
    status = Column(String(50), default='entwurf')
    hauptziel = Column(Text)
    aktionen = Column(Text)
    typischer_kunde = Column(Text)
    haeufige_anfrage = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
