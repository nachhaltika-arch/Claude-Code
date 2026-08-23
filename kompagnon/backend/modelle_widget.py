"""Die Modelle des eingebetteten Widgets und der Zustellprotokolle (L-25).

**Warum eigene Datei, 22.08.2026.** `database.py` hatte 1.361 Zeilen und 39
Modellklassen. Was auf fremden Seiten angefragt wird, und was Brevo ueber die
Zustellung zurueckmeldet.

**Wichtig:** Diese Datei wird von `database.py` am Ende importiert. Ohne das
waere sie nie geladen, und die `relationship()`-Aufrufe der anderen Modelle
faenden ihre Gegenseite nicht — mit einem Fehler zur Laufzeit an einer
Stelle, die mit der Ursache nichts zu tun hat.
`tests/test_modelle_vollstaendig.py` haelt das fest.
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base


class WidgetRequest(Base):
    """Anfrage aus dem Einbett-Widget auf einer fremden Landingpage.

    Hält dreierlei zusammen: die Ratenbegrenzung (wie viele Anfragen kamen
    zuletzt von dieser Adresse), den Nachweis der Einwilligung (Zeitpunkt, IP,
    Bestätigung) und die Zustellung des Berichts.
    """
    __tablename__ = "widget_requests"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    website_url = Column(String(500), nullable=False)

    # Nachweis der Einwilligung nach § 7 UWG — ohne Zeitpunkt und Herkunft
    # ist eine Einwilligung im Streitfall wertlos.
    consent_marketing = Column(Boolean, default=False)
    consent_at = Column(DateTime, nullable=True)
    ip_address = Column(String(64), default="")
    user_agent = Column(String(400), default="")
    referrer = Column(String(500), default="")

    # Bestätigung der Adresse. Sie steht vor allem anderen: erst nach diesem
    # Klick verlässt überhaupt ein Berichtslink das Haus. Getrennt vom
    # Marketing-Opt-in darunter — zwei Einwilligungen an einen Klick zu
    # koppeln wäre Bündelung.
    verify_token = Column(String(64), index=True)
    verify_sent_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    # Wie oft der Versand versucht wurde. Begrenzt den zweiten Versuch aus dem
    # Widget: Die Empfaengeradresse steht fest, wer den Knopf drueckt bestimmt
    # sie nicht — ohne Grenze waere der Knopf eine Maschine, die eine fremde
    # Adresse zuschuettet.
    verify_attempts = Column(Integer, default=0)

    # Wer bestätigt hat. Vier Testläufe bestätigten sich von selbst, Minuten
    # nach dem Versand und ohne Zutun eines Menschen — ohne diese Angaben
    # liess sich nicht sagen, welcher Dienst da drückt.
    verified_user_agent = Column(String(400), default="")
    verified_ip = Column(String(64), default="")

    # Double-Opt-in: erst nach Klick im Bestätigungslink darf beworben werden
    confirm_token = Column(String(64), index=True)
    confirmed_at = Column(DateTime, nullable=True)

    # Zugang zur Berichtsseite ohne Login
    report_token = Column(String(64), index=True)

    # Abfrage des Zwischenstands durch das Widget selbst. Bewusst getrennt
    # von report_token: dieser Wert steht im JavaScript der Seite, der
    # Berichts-Token gehört allein in die E-Mail.
    poll_token = Column(String(64), index=True)

    audit_id = Column(Integer, nullable=True, index=True)
    lead_id = Column(Integer, nullable=True)
    report_sent_at = Column(DateTime, nullable=True)

    # Der Klick auf den Berichtslink aus der E-Mail. Er ist der Nachweis, dass
    # die Adresse dem Empfänger gehört — die eingetragene Adresse muss dem
    # Eintragenden nicht gehören.
    report_confirmed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class MailEvent(Base):
    """Was nach dem Versand mit einer Mail geschah — gemeldet von Brevo.

    Der Anlass: Eine Zustellung wurde abgelehnt, weil die Versand-IP des
    Anbieters auf einer Blockliste stand ("554 ... blocked using
    bl.spamcop.net"). Für die Anwendung sah der Versand erfolgreich aus, denn
    Brevo hatte die Mail angenommen — die Ablehnung kam erst danach beim
    Empfänger. Ohne diese Tabelle bleibt so ein Ausfall unsichtbar, und bei
    einem Akquisekanal heißt das: Anschreiben laufen ins Leere und niemand
    merkt es.

    Abgelegt werden nur Störungen, nicht der normale Verlauf. Zustellungen,
    Öffnungen und Klicks würden die Tabelle fluten, ohne etwas zu beantworten.
    """

    __tablename__ = "mail_events"

    id = Column(Integer, primary_key=True, index=True)

    # Der Ereignisname von Brevo, unverändert: hard_bounce, blocked, spam,
    # invalid_email, soft_bounce, error.
    event = Column(String(40), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    reason = Column(String(500), default="")
    subject = Column(String(300), default="")
    sending_ip = Column(String(64), default="")

    # Zur Zuordnung und gegen Doppelzählung: Brevo wiederholt Zustellversuche
    # des Webhooks, und dieselbe Meldung darf nicht mehrfach in der Liste
    # stehen.
    message_id = Column(String(255), default="", index=True)
    event_key = Column(String(255), default="", index=True)

    # Aufgelöst über die Adresse. Bleibt leer, wenn zu der Adresse kein Lead
    # existiert — die Meldung ist trotzdem wertvoll.
    lead_id = Column(Integer, nullable=True, index=True)

    occurred_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
