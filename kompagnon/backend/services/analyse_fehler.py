# -*- coding: utf-8 -*-
"""Ordnet eine gescheiterte Analyse einem Grund zu, den man sagen kann (L-184).

**Wozu.** `error_message` trägt die Ausnahme, so wie sie kam —
``ConnectTimeout:``, ``Timeout: Audit konnte nicht in 240s …``. Das gehört
in die Anfrageliste und ins Protokoll, aber nicht vor den Besucher. Vor ihm
stand bisher bei *jedem* Fehlschlag derselbe Satz, und der schickte ihn
einen Fehler suchen, den es meistens bei ihm nicht gibt.

**Was hier entschieden wird und was nicht.** Diese Datei sagt nur, *welcher*
Fall vorliegt. Wie er formuliert wird, steht im Widget — beim übrigen Text,
den der Besucher liest. Nach draußen geht damit ein Schlüssel, nie die
Meldung.

**Die Reihenfolge ist der ganze Trick.** `ConnectError` trägt zwei
verschiedene Fälle: den Tippfehler in der Adresse und den Hoster, der uns
aussperrt. Der Typname allein ordnet die Hälfte falsch ein; deshalb
entscheidet der Meldungstext zuerst, und der Typ erst danach.
"""

#: Der Name löst sich nicht auf. **Der einzige Fall**, in dem „bitte die
#: Adresse prüfen" hilft statt abzuwälzen.
ADRESSE_UNBEKANNT = "adresse_unbekannt"

#: Die Verbindung kommt nicht zustande. Der gemessene Hauptfall (L-183): Der
#: Hoster nimmt aus dem Rechenzentrum Frankfurt keine Verbindung an, während
#: die Seite von überall sonst antwortet. Die Seite des Besuchers ist in
#: Ordnung — wir kommen nur nicht hin.
NICHT_ERREICHBAR = "nicht_erreichbar"

#: Unser eigener Lauf war zu langsam oder die Gegenstelle antwortete nicht
#: zu Ende. Liegt bei uns, nicht beim Besucher.
ZEITGRENZE = "zeitgrenze"

#: Nicht einzuordnen. Bekommt **keinen** erfundenen Grund — lieber „es hat
#: nicht geklappt" als eine falsche Erklärung, der jemand nachgeht.
UNBEKANNT = "unbekannt"

#: Textstücke, an denen ein nicht auflösbarer Name zu erkennen ist. Sie
#: stammen aus den Meldungen von `getaddrinfo` unter Linux und macOS —
#: dieselbe Ursache, zwei Formulierungen.
NAMENSFEHLER = (
    "name or service not known",
    "nodename nor servname",
    "no address associated with hostname",
    "getaddrinfo",
    "gaierror",
    "name resolution",
    "temporary failure in name resolution",
)

#: Textstücke, die eine nicht zustande gekommene Verbindung anzeigen.
VERBINDUNGSFEHLER = (
    "connecttimeout",
    "connection refused",
    "connectionerror",
    "connecterror",
    "network is unreachable",
    "connection reset",
)

#: Textstücke für abgelaufene Zeit. `Timeout:` steht am Anfang der Meldung
#: aus der Gesamtgrenze des Audits.
ZEITFEHLER = (
    "timeout",
    "timed out",
)


def kategorie(meldung) -> str:
    """Der Grund als Schlüssel — nie die Meldung selbst.

    Nimmt auch ``None`` und Leerstring entgegen: Ein Audit kann auf
    ``failed`` stehen, ohne dass eine Meldung hinterlegt wurde, und ein
    Aufrufer soll dafür keine Fallunterscheidung brauchen.
    """
    text = (meldung or "").strip().lower()
    if not text:
        return UNBEKANNT

    # Zuerst der Namensfehler: Er versteckt sich in `ConnectError` und wäre
    # sonst als Erreichbarkeitsproblem verbucht — also mit einem Satz
    # beantwortet, der dem Besucher nicht hilft, obwohl er hier helfen kann.
    if any(stueck in text for stueck in NAMENSFEHLER):
        return ADRESSE_UNBEKANNT

    if any(stueck in text for stueck in VERBINDUNGSFEHLER):
        return NICHT_ERREICHBAR

    if any(stueck in text for stueck in ZEITFEHLER):
        return ZEITGRENZE

    return UNBEKANNT
