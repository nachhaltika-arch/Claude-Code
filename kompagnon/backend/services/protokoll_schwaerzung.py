"""Geheimnisse aus dem Protokoll halten (L-98).

**Warum es das gibt.** ``httpx`` protokolliert jede Anfrage auf INFO mit der
**vollständigen URL**. Steht ein Schlüssel als Abfrageparameter darin, steht
er im Klartext im Render-Protokoll::

    HTTP Request: GET …/runPagespeed?url=…&strategy=mobile&key=AIzaSy… "200 OK"

Wer Leserechte auf die Protokolle hat, hat den Schlüssel — und Protokolle
werden weitergegeben.

**Der bessere Riegel steht woanders.** Wo es geht, gehört der Schlüssel gar
nicht erst in die URL: PageSpeed schickt ihn seit dem 24.08.2026 als Kopfzeile
(``services.audit_pagespeed.auth_headers``). Was nicht in der URL steht, kann
keine Protokollstelle ausplaudern — auch kein Traceback und kein
Proxy-Protokoll.

**Dieses Modul ist für den Rest.** Die *alte* Places-Schnittstelle
(``maps.googleapis.com/maps/api/place/…``) nimmt die Kopfzeile nicht. Am
24.08.2026 am echten Endpunkt geprüft, nicht angenommen: mit
``X-Goog-Api-Key`` antwortet sie ``REQUEST_DENIED — You must use an API key to
authenticate each request``. Dort *muss* der Schlüssel in der URL bleiben.
Also wird er beim Protokollieren geschwärzt.

Der Filter hängt an der Wurzel, nicht an ``httpx``: Eine Bibliothek, die
morgen dazukommt, soll nicht erst wieder auffallen müssen.
"""
import logging
import re

#: Abfrageparameter, deren Wert nie ins Protokoll gehört.
#: Bewusst eng gehalten — eine Schwärzung, die zu viel schwärzt, macht das
#: Protokoll unlesbar und wird beim ersten Zwischenfall abgeschaltet.
GEHEIME_PARAMETER = (
    "key", "api_key", "apikey", "access_token", "token",
    "password", "passwd", "secret", "client_secret", "signature", "sig",
)

ERSATZ = "***geschwaerzt***"

_MUSTER = re.compile(
    r"([?&](?:" + "|".join(GEHEIME_PARAMETER) + r")=)([^&\s\"'<>]+)",
    re.IGNORECASE,
)


def schwaerzen(text: str) -> str:
    """Ersetzt die Werte geheimer Abfrageparameter — der Name bleibt stehen.

    Der Name bleibt sichtbar, weil er beim Suchen hilft („welcher Aufruf war
    ohne Schlüssel?“) und selbst nichts verrät.
    """
    return _MUSTER.sub(lambda t: t.group(1) + ERSATZ, text)


class Schwaerzung(logging.Filter):
    """Schwärzt Geheimnisse in jedem Protokollsatz, der die Wurzel erreicht.

    ``logging.Filter`` gibt ``True`` zurück, wenn der Satz durchgelassen wird
    — hier immer. Geschwärzt wird der Inhalt, nicht der Satz unterdrückt: Ein
    verschwundener Aufruf wäre beim Suchen schlimmer als ein anonymisierter.

    **Der häufige Fall darf nichts kosten.** Erst wird nur nach einem ``=``
    plus einem der Parameternamen gesucht; nur wenn beides vorkommt, wird der
    Satz überhaupt ausformuliert. Sonst bleiben Vorlage und Argumente
    unangetastet und das Formatieren geschieht wie immer erst beim Ausgeben.
    """

    def filter(self, satz: logging.LogRecord) -> bool:
        roh = str(satz.msg)
        if satz.args:
            roh = f"{roh} {satz.args}"
        if "=" not in roh:
            return True
        unten = roh.lower()
        if not any(f"{p}=" in unten for p in GEHEIME_PARAMETER):
            return True

        # Ab hier wird ausformuliert: Die Argumente stecken im fertigen Satz,
        # also ist das die einzige Stelle, an der beide zugleich sichtbar sind.
        ausformuliert = satz.getMessage()
        geschwaerzt = schwaerzen(ausformuliert)
        if geschwaerzt != ausformuliert:
            satz.msg = geschwaerzt
            satz.args = ()
        return True
