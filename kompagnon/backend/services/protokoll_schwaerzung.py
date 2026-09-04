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

#: Pfade, deren **naechstes Segment** ein Geheimnis ist.
#:
#: **Der Befund vom 31.08.2026.** Diese Schwaerzung kannte nur
#: Abfrageparameter — und beide Brevo-Webhooks tragen ihr Geheimnis im
#: **Pfad**, weil Brevo nicht signiert und der Pfad die einzige Stelle ist,
#: die Brevo unveraendert weitergibt. Uvicorn schreibt jede Anfragezeile mit
#: vollem Pfad ins Protokoll; damit stand
#: `POST /api/posteingang/brevo/<Geheimnis> 200 OK` im Klartext im
#: Produktivprotokoll, sichtbar fuer jeden mit Render-Zugang.
#:
#: Gefunden nicht beim Suchen danach, sondern beim **Nachlesen des
#: Protokolls** waehrend des Beweislaufs fuer L-18 — dieselbe Art wie L-98,
#: nur eine Ebene weiter: Dort stand der Schluessel in der Abfrage, hier im
#: Weg.
#:
#: **Die Liste ist eng gehalten**, aus demselben Grund wie oben: Wer jeden
#: Pfad schwaerzt, macht das Protokoll unlesbar und schaltet es beim ersten
#: Zwischenfall ab.
#:
#: **Was diese Schwaerzung nicht erreicht, und das gehoert dazugesagt:**
#: Render fuehrt neben unserem Anwendungsprotokoll ein **eigenes**
#: Anfrageprotokoll (`type: request`), und dort steht der volle Pfad als
#: Merkmal — am 31.08.2026 nachgesehen, nachdem unseres sauber war. Kein
#: Filter im Prozess kann das aendern; es entsteht ausserhalb.
#:
#: Der Gewinn bleibt trotzdem: Anwendungsprotokolle werden kopiert, in
#: Fehlermeldungen eingefuegt und an Protokollsenken weitergereicht. Der
#: eigentliche Riegel waere, das Geheimnis gar nicht in den Pfad zu legen —
#: das geht hier nicht, weil Brevo nicht signiert und der Pfad die einzige
#: Stelle ist, die unveraendert ankommt. **Deshalb bleibt eine Handlung offen,
#: und sie gehoert David:** `BREVO_INBOUND_SECRET` wechseln, denn es stand
#: seit dem 28.08. im Klartext im Produktivprotokoll.
GEHEIME_PFADE = (
    "/api/posteingang/brevo/",
    "/api/mail-events/brevo/",
)

_PFADMUSTER = re.compile(
    r"(" + "|".join(re.escape(p) for p in GEHEIME_PFADE) + r")([^\s?\"'<>]+)",
    re.IGNORECASE,
)


def schwaerzen(text: str) -> str:
    """Ersetzt Werte geheimer Abfrageparameter **und Pfadsegmente**.

    Der Name beziehungsweise der Weg bleibt sichtbar, weil er beim Suchen
    hilft („welcher Aufruf war ohne Schlüssel?“) und selbst nichts verrät.
    Ersetzt wird nur, was danach kommt.
    """
    text = _MUSTER.sub(lambda t: t.group(1) + ERSATZ, text)
    return _PFADMUSTER.sub(lambda t: t.group(1) + ERSATZ, text)


class Schwaerzung(logging.Filter):
    """Schwärzt Geheimnisse in jedem Protokollsatz, der die Wurzel erreicht.

    ``logging.Filter`` gibt ``True`` zurück, wenn der Satz durchgelassen wird
    — hier immer. Geschwärzt wird der Inhalt, nicht der Satz unterdrückt: Ein
    verschwundener Aufruf wäre beim Suchen schlimmer als ein anonymisierter.

    **Der häufige Fall darf nichts kosten.** Erst wird billig geprüft, ob der
    Satz überhaupt eines der beiden Muster tragen *kann*; nur dann wird er
    ausformuliert. Sonst bleiben Vorlage und Argumente unangetastet und das
    Formatieren geschieht wie immer erst beim Ausgeben.

    **Die Schranke muss beide Muster kennen — das war der Fehler vom
    31.08.2026.** Die Pfadschwärzung war eine Stunde zuvor in ``schwaerzen``
    eingebaut worden, und sie wirkte nicht: Hier stand ``if "=" not in roh:
    return True``, und die Zeile, um die es geht, hat gar kein ``=``:

        INFO: 1.2.3.4:0 - "POST /api/posteingang/brevo/<Geheimnis>" 403

    Eine erweiterte Funktion hinter einer unveränderten Schranke ist nicht
    angeschlossen — dieselbe Klasse wie ein Endpunkt ohne Knopf, nur eine
    Ebene kleiner. Aufgefallen ist es **nur**, weil der laufende Dienst
    gefragt wurde statt der Code gelesen.
    """

    def filter(self, satz: logging.LogRecord) -> bool:
        roh = str(satz.msg)
        if satz.args:
            roh = f"{roh} {satz.args}"
        unten = roh.lower()

        hat_parameter = "=" in roh and any(f"{p}=" in unten
                                           for p in GEHEIME_PARAMETER)
        hat_pfad = any(p.lower() in unten for p in GEHEIME_PFADE)
        if not (hat_parameter or hat_pfad):
            return True

        # **Zuerst je Argument — die Form des Satzes bleibt erhalten.**
        #
        # Der erste Anlauf am 31.08.2026 hat hier immer ausformuliert und
        # `args = ()` gesetzt. Das Geheimnis war damit weg und das
        # Zugriffsprotokoll kaputt: Uvicorns `AccessFormatter` packt genau
        # fuenf Argumente aus (`client_addr, method, full_path, http_version,
        # status_code`) und warf danach bei **jeder** Anfrage an die beiden
        # Webhooks `ValueError: not enough values to unpack (expected 5,
        # got 0)` — samt Traceback im Protokoll.
        #
        # Ein Leck gegen ein unlesbares Protokoll zu tauschen ist kein
        # Fortschritt. Wer den Pfad schwaerzt, schwaerzt das **Argument**, in
        # dem er steht, und laesst die Stelle frei.
        # **Die Vorlage nur anfassen, wenn keine Argumente daran haengen.**
        # Sonst frisst die Schwaerzung einen Platzhalter: Aus `"… key=%s"`
        # wird `"… key=***geschwaerzt***"`, und das folgende `msg % args`
        # scheitert mit „not all arguments converted". Auch das ist am
        # 31.08.2026 passiert — beim Reparieren der Reparatur.
        if not satz.args:
            if isinstance(satz.msg, str):
                satz.msg = schwaerzen(satz.msg)
            return True

        if isinstance(satz.args, tuple):
            satz.args = tuple(schwaerzen(a) if isinstance(a, str) else a
                              for a in satz.args)
        elif isinstance(satz.args, dict):
            satz.args = {k: (schwaerzen(v) if isinstance(v, str) else v)
                         for k, v in satz.args.items()}

        # **Der Rueckfall fuer den Fall, dass ein Geheimnis erst im fertigen
        # Satz sichtbar wird** — etwa `msg='… key=%s'` mit dem nackten Wert im
        # Argument. Dann bleibt nur das Ausformulieren; Saetze dieser Form
        # kommen aus `httpx` und werden vom gewoehnlichen Formatierer
        # ausgegeben, dem die Argumente nicht fehlen.
        #
        # **Und er darf nie selbst der Fehler sein:** Ein Filter, der eine
        # Ausnahme wirft, verschluckt die Protokollzeile ganz.
        try:
            ausformuliert = satz.getMessage()
        except Exception:                            # noqa: BLE001
            return True
        geschwaerzt = schwaerzen(ausformuliert)
        if geschwaerzt != ausformuliert:
            satz.msg = geschwaerzt
            satz.args = ()
        return True
