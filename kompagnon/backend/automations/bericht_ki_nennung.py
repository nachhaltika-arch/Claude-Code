# -*- coding: utf-8 -*-
"""Der wöchentliche Nennungsbericht an den Abonnenten (L-58 b).

**Warum es ihn gibt.** Die Kundenkarte hat ihn bis zum 25.08.2026 versprochen
— „Den nächsten Report erhalten Sie automatisch per E-Mail" — und es gab ihn
nie. Die Zusage ist entfernt worden; hier wird sie eingelöst.

**Warum eine Mail und nicht nur die Ansicht im Portal.** Ein Abo, das sich nur
meldet, wenn der Kunde von sich aus nachsieht, wird vergessen und gekündigt.
Die Mail ist die Leistung, die er wöchentlich spürt.

**Was drinsteht und was nicht.** Je System die Trefferzahl und die Richtung
gegenüber dem letzten Lauf. **Keine Antworttexte** — sie nennen fremde
Betriebe, und der Kunde hat sie nicht bestellt. **Keine Zusicherung** einer
Nennung: Ob ein Assistent ihn nennt, entscheidet dessen Anbieter.

**Kein Bericht ohne Messung.** Wo nichts erhoben wurde, geht nichts hinaus.
Eine Mail „0 von 3" für ein System, das mangels Schlüssel nie gefragt wurde,
wäre die teuerste Nachricht, die dieses Produkt verschicken kann.
"""
import logging
from typing import Optional

from automations.versandmodus import probemodus

logger = logging.getLogger(__name__)

BETREFF = "Ihre KI-Sichtbarkeit diese Woche"


def _richtung(jetzt: int, vorher: Optional[int]) -> str:
    """Mehr, weniger oder gleich — die Frage, die der Verlauf beantwortet."""
    if vorher is None:
        return ""
    if jetzt > vorher:
        return f" (vorher {vorher})"
    if jetzt < vorher:
        return f" (vorher {vorher})"
    return " (unverändert)"


def _vorheriger_stand(verlauf: list) -> dict:
    """Die Trefferzahlen des vorletzten Laufs, je System.

    Der letzte Eintrag ist der soeben geschriebene — verglichen wird mit dem
    davor. Gibt es keinen, ist dies der erste Bericht und es wird nichts
    verglichen, statt einen Anstieg aus dem Nichts zu behaupten.
    """
    if not verlauf or len(verlauf) < 2:
        return {}
    return {schluessel: werte.get("genannt_bei")
            for schluessel, werte in (verlauf[-2].get("anbieter") or {}).items()}


def baue_bericht(name: str, befund: dict, verlauf: list) -> tuple:
    """(Betreff, HTML, Text) — oder (None, None, None), wenn nichts zu melden ist."""
    systeme = [(s, b) for s, b in (befund.get("anbieter") or {}).items()
               if b.get("collected")]
    if not systeme:
        return None, None, None

    vorher = _vorheriger_stand(verlauf or [])
    zeilen_html, zeilen_text = [], []
    for schluessel, block in systeme:
        genannt = block.get("genannt_bei", 0)
        von = block.get("beantwortet", block.get("von", 0))
        richtung = _richtung(genannt, vorher.get(schluessel))
        anzeige = block.get("anzeige", schluessel)
        zeilen_html.append(
            f'<tr><td style="padding:6px 0">{anzeige}</td>'
            f'<td style="padding:6px 0;text-align:right"><strong>{genannt} von {von}</strong>'
            f'<span style="color:#6b7280">{richtung}</span></td></tr>')
        zeilen_text.append(f"  {anzeige}: {genannt} von {von} Fragen{richtung}")

    nicht_gefragt = [b.get("anzeige", s) for s, b in (befund.get("anbieter") or {}).items()
                     if not b.get("collected")]
    hinweis_html = hinweis_text = ""
    if nicht_gefragt:
        # **Ausweisen, nicht verschweigen.** Sonst liest der Kunde drei Systeme
        # und hält sie für alle.
        namen = ", ".join(nicht_gefragt)
        hinweis_html = (f'<p style="color:#6b7280;font-size:13px">Nicht abgefragt '
                        f'in dieser Woche: {namen}.</p>')
        hinweis_text = f"\nNicht abgefragt in dieser Woche: {namen}.\n"

    html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#004F59;padding:22px;border-radius:12px 12px 0 0">
    <h2 style="color:#fff;margin:0;font-size:19px">Ihre KI-Sichtbarkeit</h2>
  </div>
  <div style="padding:22px;background:#fff;border:1px solid #e5e7eb;border-top:0">
    <p>Hallo {name},</p>
    <p>wir haben diese Woche gefragt, was Ihre Kundschaft fragen würde — nach
       Ihrer Leistung und Ihrem Ort. So oft wurden Sie genannt:</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px">{''.join(zeilen_html)}</table>
    {hinweis_html}
    <p style="color:#6b7280;font-size:13px">Ob ein KI-System Sie nennt,
       entscheidet dessen Anbieter. Wir messen es wöchentlich und zeigen Ihnen
       die Entwicklung — eine Nennung zusichern kann niemand.</p>
  </div>
</div>"""

    text = (f"Hallo {name},\n\nwir haben diese Woche gefragt, was Ihre Kundschaft "
            f"fragen würde — nach Ihrer Leistung und Ihrem Ort.\n\n"
            + "\n".join(zeilen_text) + "\n" + hinweis_text
            + "\nOb ein KI-System Sie nennt, entscheidet dessen Anbieter. Wir "
              "messen es wöchentlich; zusichern kann es niemand.\n")

    return BETREFF, html, text


def sende_bericht(empfaenger: str, name: str, befund: dict, verlauf: list) -> bool:
    """Verschickt den Bericht — oder sagt im Protokoll, warum nicht."""
    if not empfaenger:
        logger.info("Nennungsbericht ohne Empfängeradresse — nicht versendet")
        return False

    betreff, html, text = baue_bericht(name or "", befund, verlauf)
    if not betreff:
        logger.info("Nennungsbericht für %s entfällt — nichts erhoben", empfaenger)
        return False

    if probemodus():
        logger.info("[PROBE] Nennungsbericht an %s: %s", empfaenger, betreff)
        return True

    from services.email import send_email
    return send_email(to_email=empfaenger, subject=betreff,
                      html_body=html, text_body=text)
