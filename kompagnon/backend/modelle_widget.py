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

    # Wann an den bereitliegenden Bericht erinnert wurde (L-185, 10.09.2026).
    # **Der Zeitpunkt ist die Sperre, nicht ein Merker:** Ohne ihn schickt
    # jeder Scheduler-Lauf dieselbe Mail erneut — viermal am Tag an jemanden,
    # der ohnehin nicht reagiert hat.
    erinnerung_bericht_at = Column(DateTime, nullable=True)

    # Wann an die ausstehende Bestaetigung erinnert wurde (L-185, 14.09.2026).
    erinnerung_bestaetigung_at = Column(DateTime, nullable=True)

    # Ob die erste Mail dieser Anfrage eine Erinnerung **angekuendigt** hat.
    #
    # **Warum das an der Zeile steht und nicht als Datum im Code.** Bis zum
    # 14.09.2026 sagte `verify_email` zu: „Ohne Ihre Bestaetigung schicken wir
    # nichts weiter und melden uns nicht von selbst." Der Satz kuendigt jetzt
    # genau eine Erinnerung an. Wer stattdessen ein Stichtagsdatum in den Code
    # schriebe, muesste raten, wann der neue Text **produktiv** ankam — das
    # haengt am Merge, nicht am Schreiben. Raet er zu frueh, geht eine Mail an
    # Empfaenger, denen Ruhe zugesagt wurde; raet er zu spaet, fallen Leads
    # weg. Die Zeile weiss es genau: Sie traegt, welche Zusage ihr zugegangen
    # ist.
    erinnerung_angekuendigt = Column(Boolean, default=False)

    # Ob die Anfrage mit einer Klickkennung der Anzeige ankam (L-192).
    #
    # **Nur das Ob, nie die Kennung.** Fuer die Frage, welche Stufe bei der
    # Kampagne leckt, genuegt, *dass* geklickt wurde. Die `fbclid` selbst ist
    # eine Kennung; sie an eine Mailadresse zu heften waere mehr, als die
    # Auswertung braucht — und Daten, die man nicht hat, koennen nicht
    # abfliessen.
    aus_anzeige = Column(Boolean, default=False)

    # Die Kennung des Seitenaufrufs, an dem die Einwilligung erteilt wurde
    # (17.09.2026). Verweist auf `einwilligungen.nachweis` — bewusst **ohne**
    # Fremdschluessel: Die Anfrage darf nicht daran scheitern, dass die
    # Einwilligungsmeldung unterwegs verlorenging. Ein Nachweis, der die
    # Analyse verhindert, waere schlimmer als ein fehlender Nachweis.
    nachweis = Column(String(64), nullable=True, index=True)

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


class Einwilligung(Base):
    """Der Nachweis, dass eine Einwilligung erteilt — oder verweigert — wurde.

    **Der Anlass (17.09.2026, L-195).** Die Entscheidung am Einwilligungs-
    dialog lag bis hierher **ausschliesslich** in `localStorage` auf dem
    Geraet des Besuchers. Das hat zwei Loecher, und beide sind teuer:

    1. **Art. 7 Abs. 1 DSGVO verlangt, die Einwilligung nachweisen zu
       koennen.** Ein Wert im Browser eines Fremden ist kein Nachweis — er
       ist geloescht, sobald jemand seine Websitedaten leert, und wir sehen
       ihn ohnehin nie.
    2. **Ohne diese Zeile ist nicht zu unterscheiden, warum jemand bei Meta
       fehlt.** Am 17.09. gemessen: Von 353 echten Besuchern kamen bei Meta
       12 an und bei GA4 11 — rund 3 %. Ob die uebrigen 97 % abgelehnt
       haben, einen Werbeblocker benutzen oder im In-App-Browser von
       Facebook sitzen, war **nicht erhoben**. Drei Ursachen, drei voellig
       verschiedene Reparaturen.

    **Warum diese Meldung durchkommt, wo Metas Pixel es nicht tut.** Sie geht
    an die eigene erste Adresse (`api.kompagnon.group`) und laedt kein
    fremdes Skript. Blocklisten kennen Trackerdomains; In-App-Browser
    beschneiden Drittanbieter. Die Differenz zwischen dieser Zaehlung und
    Metas Zaehlung **ist** die gesuchte Trennung.

    ── Was hier bewusst **nicht** steht ──

    **Keine vollstaendige IP.** Diese Tabelle nimmt auch die auf, die
    *abgelehnt* haben. Wer Tracking ablehnt und dafuer eine vollstaendig
    gespeicherte Adresse bekommt, ist schlechter dran als vorher; das waere
    das Gegenteil dessen, was der Eintrag bezweckt. Gespeichert wird das
    Netz (IPv4 /24, IPv6 /48) — genug, um einen Eintrag im Streitfall
    einzuordnen, zu wenig, um jemanden wiederzuerkennen.

    **Keine Kennung auf dem Geraet.** `nachweis` wird bei jedem Laden neu
    gewuerfelt und **nirgends** gespeichert — nicht im `localStorage`, nicht
    als Cookie. Eine wiederverwendbare Kennung waere eine Speicherung auf
    dem Endgeraet und damit nach § 25 TDDDG selbst einwilligungspflichtig:
    Der Nachweis der Einwilligung braeuchte eine Einwilligung. Der Preis
    dafuer ist, dass ein Wiederkehrer als neuer Eintrag erscheint — fuer die
    gesuchte Quote ist das richtig, denn der Nenner (`/api/widget/config`)
    zaehlt genauso.

    **Der Personenbezug entsteht erst, wenn es ihn ohnehin gibt.** Schickt
    derselbe Besucher spaeter das Formular ab, traegt `widget_requests` die
    Kennung aus `nachweis` mit. Dort stehen Adresse, Zeitpunkt und volle IP
    — und dort ist es begruendet, weil eine Person die Analyse angefordert
    hat. Fuer alle anderen bleibt dieser Eintrag pseudonym.
    """

    __tablename__ = "einwilligungen"

    id = Column(Integer, primary_key=True, index=True)

    # Die Kennung eines Seitenaufrufs. Eindeutig, weil dieselbe Meldung
    # zweimal kommt: einmal beim Laden („was stand da schon?") und einmal,
    # wenn der Besucher den Dialog beantwortet. Die zweite **aktualisiert**
    # die erste, sonst zaehlte jeder Entschluss doppelt.
    nachweis = Column(String(64), nullable=False, unique=True, index=True)

    # 'erteilt' | 'abgelehnt' | 'unbekannt'
    #
    # `unbekannt` ist der wichtigste der drei Werte und ausdruecklich **nicht**
    # dasselbe wie `abgelehnt`: Die Traegerseite hat nichts gesagt. Entweder
    # hat sie keinen Dialog, oder der Besucher hat ihn stehen lassen. Wer
    # beides zu „nein" zusammenfasst, verliert genau die Unterscheidung,
    # derentwegen die Tabelle existiert.
    entscheidung = Column(String(20), nullable=False, index=True)

    # Die einzelnen Haken. `None` heisst „nicht mitgeteilt" — die Spalten sind
    # deshalb nullable und werden nie auf False vorbelegt.
    marketing = Column(Boolean, nullable=True)
    statistik = Column(Boolean, nullable=True)

    # Woher die Aussage stammt: 'nachricht' (postMessage der Traegerseite),
    # 'parameter' (`consent=` im iframe-Aufruf) oder 'keine'.
    quelle = Column(String(20), default="keine")

    # Die Fassung des Einwilligungstextes, die dem Besucher vorlag. Ohne sie
    # ist der Nachweis wertlos: Zustimmung wozu?
    fassung = Column(String(40), default="")

    # Die einbettende Seite, nur der Host. Das Widget laeuft auf fremden
    # Seiten; ohne diese Angabe waere nicht zu sagen, wessen Dialog gemeint
    # ist. Der Pfad bleibt draussen — er kann Suchbegriffe tragen.
    seite = Column(String(200), default="", index=True)

    # Das Netz, nicht die Adresse. Siehe oben.
    netz = Column(String(64), default="")

    # Fuer die Trennung der Ursachen: Geraeteklasse und ob der Aufruf aus
    # einem In-App-Browser kam ('facebook', 'instagram', 'sonstige', '').
    mobil = Column(Boolean, default=False)
    app_browser = Column(String(20), default="")

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
