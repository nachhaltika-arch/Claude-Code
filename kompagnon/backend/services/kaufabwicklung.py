# -*- coding: utf-8 -*-
"""Welche Schritte nach einem Kauf laufen — je Produkt, nicht je Annahme.

**Der Befund (27.08.2026).** `_handle_successful_payment` fuehrte nach
**jeder** Zahlung dieselben fuenf Schritte aus: Lead, Benutzerkonto, Projekt,
Willkommensmail, Content-Scraper. Das ist der Websprint-Ablauf.

Wer das **Workbook** kauft, bekaeme damit ein Website-Projekt angelegt, eine
Willkommensmail ueber seine neue Website und einen Scraper-Lauf — fuer eine
PDF-Datei. Davids ORDERS_00 benennt genau das: „Wuerde man sie durch
denselben Ablauf schicken, bliebe sie beim Schritt ‚Veroeffentlichung'
haengen, weil es keine Domain gibt."

**Das Bauteil dafuer gab es bereits.** `products.webhook_actions` traegt bei
den Websprints exakt diese fuenf Namen, wird im Produkt-Editor angezeigt und
gespeichert — und wurde von **keiner Zeile gelesen**. Dieselbe Bauart wie
`RolePermission` vor L-05: ein Haken, der sich setzen laesst und nichts tut.

**Die Vorgabe ist das Verhalten von heute.** Ein Produkt ohne eingetragene
Aktionen bekommt weiterhin alle fuenf. Das ist die Bedingung, unter der man
so etwas nachruesten darf: Wer nichts umstellt, merkt von der Aenderung
nichts, und an den Websprints aendert sich kein Schritt.

> Eine leere Liste heisst hier **„nie eingerichtet"**, nicht „ausdruecklich
> keine Schritte". Der Unterschied ist wichtig: Die Spalte hat den Vorgabewert
> `'[]'`, und jedes Produkt, das vor heute entstand, traegt ihn. Wer wirklich
> keine Schritte will, traegt `AKTION_KEINE` ein — dann steht es da, statt
> geraten zu werden.
"""
import json
import logging

logger = logging.getLogger(__name__)

#: Die Schritte, die es gibt. Wer einen dazunimmt, traegt ihn hier ein **und**
#: baut ihn in `_handle_successful_payment` — sonst steht im Produkt-Editor
#: ein Haken, der wieder nichts tut.
LEAD = "create_lead"
KONTO = "create_user"
PROJEKT = "create_project"
WILLKOMMEN = "send_welcome_email"
AUFTRAGSBESTAETIGUNG = "send_pdf"
SCRAPER = "scrape_content"

#: Ausdrueckliches Nichts. Siehe Kopftext: Es unterscheidet sich von der
#: leeren Liste, die „nie eingerichtet" heisst.
AKTION_KEINE = "none"

#: **`create_lead` ist nicht wirklich waehlbar** — und das steht hier, weil es
#: im Produkt-Editor so aussieht. Der Lead ist der Anker des
#: Idempotenz-Schutzes: `_handle_successful_payment` erkennt eine wiederholt
#: zugestellte Stripe-Meldung daran, dass die Sitzungskennung schon in
#: `leads.notes` steht. Ohne Lead wuerde jede Wiederholung den ganzen Kauf
#: erneut verarbeiten — Stripe wiederholt bei Zeitueberschreitung.
#:
#: Er steht trotzdem in `BEKANNT`, damit die vorhandenen Katalogzeilen nicht
#: als „unbekannte Aktion" gemeldet werden.
IMMER = (LEAD,)

BEKANNT = frozenset({LEAD, KONTO, PROJEKT, WILLKOMMEN,
                     AUFTRAGSBESTAETIGUNG, SCRAPER, AKTION_KEINE})

#: Was ein Produkt bekommt, das keine Aktionen eingetragen hat. **Genau das
#: Verhalten vom 26.08.2026** — nachgelesen an `_handle_successful_payment`,
#: nicht aus dem Gedaechtnis.
VORGABE = (LEAD, KONTO, PROJEKT, WILLKOMMEN, AUFTRAGSBESTAETIGUNG, SCRAPER)


def _liste(roh) -> list:
    """Die Spalte kommt je nach Treiber als Liste oder als Zeichenkette."""
    if isinstance(roh, str):
        try:
            roh = json.loads(roh)
        except Exception:                   # noqa: BLE001
            return []
    return list(roh) if isinstance(roh, (list, tuple)) else []


def schritte_fuer(produktzeile) -> frozenset:
    """Welche Schritte dieser Kauf ausloest.

    `produktzeile` ist die Zeile aus `products` — oder `None`, wenn zu der
    gekauften Kennung keine gefunden wurde. **Auch dann gilt die Vorgabe**:
    Ein Kauf ohne erkennbares Produkt ist ein Websprint-Kauf, bis jemand das
    Gegenteil eintraegt. Alles andere hiesse, bei einem Datenfehler die
    Kundenanlage stillschweigend zu ueberspringen.
    """
    roh = _liste(produktzeile.get("webhook_actions") if produktzeile else None)

    unbekannt = [a for a in roh if a not in BEKANNT]
    if unbekannt:
        # Nicht stillschweigend ignorieren: Ein Name, den niemand ausfuehrt,
        # ist ein Haken ohne Wirkung — genau der Fehler, den dieses Modul
        # beendet.
        logger.warning("Unbekannte Kaufaktionen werden nicht ausgefuehrt: %s",
                       ", ".join(sorted(unbekannt)))

    gewaehlt = [a for a in roh if a in BEKANNT]
    if not gewaehlt:
        return frozenset(VORGABE)
    if AKTION_KEINE in gewaehlt:
        return frozenset()
    return frozenset(gewaehlt)
