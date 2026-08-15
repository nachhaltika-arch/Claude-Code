"""
Mails außerhalb des Widgets — Betreff und Inhalt an einer Stelle.

Bis zum 15.08.2026 lagen diese Texte in ``email_service.py``, einer als
veraltet markierten Datei, und bestanden aus vier Zeilen nacktem HTML. Der
Empfänger einer Widget-Analyse bekam derweil eine gestaltete Mail. Beides
kommt vom selben Absender.
"""
import html as _html

from services import brand
from services.mail_layout import knopf, rahmen

FUSS_PROJEKT = ("Sie erhalten diese E-Mail, weil wir für Sie eine "
                "Website-Analyse durchgeführt haben.")


def _esc(text: str) -> str:
    return _html.escape(text or "", quote=False)


def audit_fertig_mail(company: str, report_url: str = "") -> tuple:
    """Betreff und HTML für „Ihr Audit ist fertig".

    Ohne Adresse zum Bericht kündigte die alte Fassung ein Ergebnis an und
    ließ den Empfänger ohne jeden Weg dorthin stehen. Fehlt die Adresse, sagt
    die Mail jetzt, dass wir uns melden — und verspricht keinen Klick, den es
    nicht gibt.
    """
    name = _esc(company)

    if report_url:
        weg = (knopf(report_url, "Bericht ansehen")
               + f'<p style="margin:0;font-size:14px;line-height:1.7;'
                 f'color:{brand.TEXT_60}">Im Bericht sehen Sie zu jedem '
                 f'Kriterium, ob es gemessen, abgeleitet oder eingeschätzt '
                 f'wurde — und was konkret zu tun ist.</p>')
    else:
        weg = (f'<p style="margin:16px 0 0;font-size:14px;line-height:1.7;'
               f'color:{brand.TEXT_60}">Wir melden uns mit dem Ergebnis bei '
               f'Ihnen.</p>')

    inner = (f'<h1 style="margin:0 0 12px;font-size:21px;font-weight:900;'
             f'line-height:1.25;color:{brand.DARK}">Ihre Website-Analyse ist '
             f'fertig</h1>'
             f'<p style="margin:0;font-size:15px;line-height:1.7;'
             f'color:{brand.TEXT}">Wir haben die Website von '
             f'<strong>{name}</strong> geprüft.</p>'
             f'{weg}')

    return (f"Ihre Website-Analyse für {company} ist fertig",
            rahmen(inner, FUSS_PROJEKT))
