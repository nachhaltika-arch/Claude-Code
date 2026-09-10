# -*- coding: utf-8 -*-
"""Eine Erinnerung an den bereitliegenden Bericht — genau eine (L-185).

**Der Befund vom 10.09.2026.** Wer im Trichter steckenbleibt, hoert nie
wieder etwas. Im Scheduler gab es dafuer keinen Auftrag: Die vorhandenen
Erinnerungsstrecken (Material, Briefing, Tag 5 bis 30) gelten alle fuer
**Projekte nach dem Kauf**, und `_do_send_email` haelt ausdruecklich fest,
dass der Widget-Weg nicht durch die Versandsperre laeuft — also auch nicht
durch diese Automatiken. Ab Kampagnenstart ist jeder haengengebliebene Lead
bezahlt und verloren.

**Was hier bewusst fehlt: die Erinnerung an die Bestaetigung.** Dort faellt
der groesste Teil weg, und trotzdem wird sie nicht gebaut. Der Grund steht
in der Mail, die wir vorher geschickt haben (`widget_report.verify_email`):

    Haben Sie das nicht angefordert? Dann ignorieren Sie diese E-Mail
    einfach. Ohne Ihre Bestaetigung schicken wir nichts weiter und **melden
    uns nicht von selbst**.

Eine Erinnerung an eine unbestaetigte Adresse waere genau das, was dieser
Satz ausschliesst. Ob der Satz geaendert wird, ist eine Entscheidung ueber
das eigene Wort und gehoert David. Solange er steht, wird er gehalten.

**Warum diese Strecke unproblematisch ist.** Der Empfaenger hat seine
Adresse bestaetigt und den Bericht angefordert. Dass er bereitliegt und noch
nicht abgeholt wurde, ist Auskunft ueber eine angeforderte Leistung — keine
Werbung. Die Mail enthaelt deshalb auch nichts anderes als den Link.
"""
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

#: Wie lange nach dem Versand erinnert wird. Drei Tage: kurz genug, dass die
#: Analyse noch praesent ist, lang genug, dass niemand gedraengt wird.
FRIST_TAGE = 3

#: **Die wichtigste Zahl in dieser Datei.** Beim ersten Lauf nach dem Deploy
#: liegt der gesamte Bestand vor. Ohne Obergrenze ginge eine Erinnerung an
#: jede Anfrage seit August — das ist kein Nachfassen mehr, sondern eine
#: Aussendung, und der erste Lauf waere zugleich der teuerste Fehler.
HOECHSTALTER_TAGE = 14

#: Wie viele je Lauf hoechstens angeschrieben werden. Eine zweite Schranke
#: gegen dieselbe Gefahr: Wer `HOECHSTALTER_TAGE` heraufsetzt, ohne daran zu
#: denken, trifft hier auf eine Grenze statt auf den Verteiler.
HOECHSTZAHL_JE_LAUF = 25


def faelliger_bericht(db, jetzt: datetime = None) -> list:
    """Anfragen, deren Bericht bereitliegt und nicht abgeholt wurde.

    Vier Bedingungen, jede mit einem Grund:

    * `report_sent_at` liegt mindestens `FRIST_TAGE` zurueck — **die Frist
      zaehlt ab dem Versand, nicht ab dem Eingang der Anfrage.** Wer den
      Bericht spaet bekam, hatte auch spaet Gelegenheit.
    * `report_confirmed_at` ist leer: Der Link wurde nie geoeffnet.
    * `erinnerung_bericht_at` ist leer: **genau einmal.**
    * Die Anfrage ist juenger als `HOECHSTALTER_TAGE`.
    """
    from modelle_widget import WidgetRequest

    jetzt = jetzt or datetime.utcnow()
    faellig_ab = jetzt - timedelta(days=FRIST_TAGE)
    zu_alt_vor = jetzt - timedelta(days=HOECHSTALTER_TAGE)

    return (
        db.query(WidgetRequest)
        .filter(WidgetRequest.report_sent_at.isnot(None),
                WidgetRequest.report_sent_at <= faellig_ab,
                WidgetRequest.report_confirmed_at.is_(None),
                WidgetRequest.erinnerung_bericht_at.is_(None),
                WidgetRequest.report_sent_at >= zu_alt_vor)
        .order_by(WidgetRequest.report_sent_at)
        .limit(HOECHSTZAHL_JE_LAUF)
        .all()
    )


def erinnerung_bericht_mail(company: str, report_token: str) -> tuple:
    """Die Erinnerung: der Link, sonst nichts.

    **Kein Angebot darin.** Der Empfaenger hat eine Analyse angefordert, kein
    Verkaufsgespraech. Ein Preis in dieser Mail machte aus einer Auskunft
    eine Werbesendung — und aus einer sauberen Strecke eine angreifbare.
    """
    from services import widget_report as wr

    inner = f"""
<h1 style="margin:0 0 12px;font-size:21px;font-weight:900;line-height:1.25;
           color:{wr.brand.DARK}">Ihr Bericht liegt bereit</h1>
<p style="margin:0;font-size:15px;line-height:1.7;color:{wr.brand.TEXT}">
Vor ein paar Tagen haben wir Ihnen den vollständigen Bericht zu
<strong>{wr._esc(company)}</strong> geschickt. Geöffnet wurde er noch nicht —
vielleicht ist die E-Mail untergegangen.</p>
{wr._mail_knopf(wr.report_url(report_token), 'Bericht ansehen')}
<p style="margin:0 0 14px;font-size:14px;line-height:1.7;color:{wr.brand.TEXT_60}">
Sie finden dort {wr._katalog_umfang()}, jeweils mit Bewertung und Empfehlung,
dazu den Bericht als PDF.</p>
<p style="margin:0;padding:14px 16px;background:{wr.brand.SURFACE};
          border-radius:8px;font-size:13px;line-height:1.6;color:{wr.brand.TEXT_60}">
Das ist unsere einzige Erinnerung — von uns kommt dazu nichts weiter.</p>"""
    return (f"Ihr Bericht zu {company} liegt bereit", wr._shell(inner))
