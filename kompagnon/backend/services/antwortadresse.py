# -*- coding: utf-8 -*-
"""Wohin eine Antwort auf unsere Mail gehen soll.

**Der Befund (27.08.2026).** Am 26.08. entstand der Posteingang: Brevo
liefert eingehende Kundenmails an `POST /api/posteingang/brevo/{secret}`, die
Mail wird zur `Message` am Betrieb, und die Glocke meldet sie. Vollständig
gebaut, vollständig getestet.

Nur führte keine Mail dorthin. Jede ausgehende Nachricht trägt
`From: KOMPAGNON <noreply@kompagnon.group>` und keinen `Reply-To`. Wer auf
„Antworten" klickt, schreibt an `noreply@` — und unter der Nachricht stand
wörtlich „antworten Sie direkt auf diese E-Mail".

Der Posteingang hätte nach dem MX-Eintrag dagestanden und nie etwas
empfangen. Auffallen wäre das nicht: Ein Posteingang ohne Eingänge sieht aus
wie ein Tag ohne Rückfragen.

**Warum aus der Umgebung und nicht fest im Programm.** Die Adresse existiert
erst, wenn der MX-Eintrag für `posteingang.kompagnon.group` steht. Fest
eingetragen bekäme jeder antwortende Kunde einen
Unzustellbarkeitsbericht — schlimmer als der heutige Zustand. Ohne die
Variable bleibt alles wie bisher; mit ihr schliesst sich der Kreis, ohne dass
noch eine Zeile geändert werden muss.

**Und deshalb hängt auch der Satz unter der Mail daran.** Ein Hinweis, der
einen Weg verspricht, den es nicht gibt, ist schlechter als kein Hinweis.
"""
import os
import re

#: Die Umgebungsvariable. Denselben Namen trägt der Eintrag in Render.
SCHALTER = "MAIL_ANTWORT_ADRESSE"

#: Absichtlich streng: genau ein `@`, links und rechts etwas, rechts ein
#: Punkt. Wer hier zu grosszügig prüft, verschickt ein `Reply-To`, das kein
#: Mailprogramm versteht — und die Antwort landet irgendwo, während die
#: Absicht erfüllt aussieht.
_FORM = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def rueckadresse() -> str:
    """Die eingerichtete Antwortadresse — oder eine leere Zeichenkette.

    Leer heisst: kein `Reply-To` setzen. Ein **leeres** `Reply-To` wäre etwas
    anderes als gar keines; Brevo lehnt es ab, und SMTP verschickt eine
    Kopfzeile ohne Inhalt.
    """
    roh = os.getenv(SCHALTER, "").strip()
    return roh if _FORM.match(roh) else ""


def ist_eingerichtet() -> bool:
    """Kann ein Kunde auf unsere Mails antworten?"""
    return bool(rueckadresse())
