"""Die Modelle der eigenen Agenturseiten (L-25).

**Warum eigene Datei, 22.08.2026.** `database.py` hatte 1.361 Zeilen und 39
Modellklassen. KAS heisst KOMPAGNON Agentur Seiten — die eigene Marketingseite, nicht
die eines Kunden.

**Wichtig:** Diese Datei wird von `database.py` am Ende importiert. Ohne das
waere sie nie geladen, und die `relationship()`-Aufrufe der anderen Modelle
faenden ihre Gegenseite nicht — mit einem Fehler zur Laufzeit an einer
Stelle, die mit der Ursache nichts zu tun hat.
`tests/test_modelle_vollstaendig.py` haelt das fest.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from database import Base


class KasPage(Base):
    """KOMPAGNON-eigene Website-Seiten (KAS = KOMPAGNON Agentur Seiten)."""
    __tablename__ = "kas_pages"

    id               = Column(Integer, primary_key=True, index=True)
    titel            = Column(String(255), nullable=False)
    pfad             = Column(String(255), nullable=False)
    meta_description = Column(Text, default="")
    position         = Column(Integer, default=0)
    status           = Column(String(50), default="draft")
    ist_startseite   = Column(Boolean, default=False)
    notizen          = Column(Text, default="")
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    gjs_data = relationship(
        "KasGjsData",
        back_populates="page",
        uselist=False,
        cascade="all, delete-orphan",
    )


class KasGjsData(Base):
    """GrapesJS-Inhalt pro KAS-Seite (separate Tabelle fuer Performance)."""
    __tablename__ = "kas_gjs_data"

    id       = Column(Integer, primary_key=True, index=True)
    page_id  = Column(Integer, ForeignKey("kas_pages.id", ondelete="CASCADE"))
    html     = Column(Text, default="")
    css      = Column(Text, default="")
    gjs_data = Column(JSON, default=dict)
    saved_at = Column(DateTime, default=datetime.utcnow)

    page = relationship("KasPage", back_populates="gjs_data")
