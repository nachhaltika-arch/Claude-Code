# -*- coding: utf-8 -*-
"""Das Check-PLUS-Angebot, wie das Widget es anzeigt (10.09.2026).

**Der Anlass.** Der Teaser-Entwurf bringt Check PLUS als bezahltes Angebot in
das Widget — mit Preis, Leistungsliste, Anrechnungszusage und Kaufknopf. Im
Entwurf stehen `249 €` als Text und ein fester Stripe-Zahllink im `href`.

**Warum beides hier entsteht und nicht dort.** Das Widget laeuft eingebettet
auf **fremden** Seiten. Ein Preis, der dort im Quelltext steht, ist eine
zweite Preisquelle neben `products` — genau L-29, nur an der Stelle mit der
geringsten Sichtbarkeit: Wer den Katalog pflegt, sieht die alte Zahl nie.
Der Preis kommt deshalb aus der Katalogzeile, aus der auch die Kasse ihren
Betrag zieht.

**Kein Knopf ohne Ziel.** `verfuegbar` ist nur wahr, wenn das Produkt `live`
steht **und** eine Kaufadresse hinterlegt ist. Fehlt eines, zeigt das Widget
den Block ohne Knopf. Das ist die Klasse „gebaut, nicht angeschlossen", die
in diesem Projekt schon fuenfmal auftrat: ein Knopf, der eine 404 oeffnet,
ist schlimmer als kein Knopf, weil ihn niemand meldet.

**Netto und brutto stehen beide da.** Der Entwurf zeigt „249 € netto"; die
Kasse bucht `price_brutto` ab. Genau diese Luecke war L-61 — die Seite
schrieb „netto, zzgl. MwSt.", belastet wurde ein anderer Betrag. Wer netto
zeigt, stellt den Zahlbetrag daneben; welcher davon gross gesetzt wird, ist
eine Sache der Gestaltung, nicht der Daten.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

#: Artikelnummer aus Datenblatt CHK-PLU-01. Sie steht in keiner Spalte —
#: **eine** Stelle im Code ist die kleinste ehrliche Loesung; fuenf waeren
#: L-29 in klein.
KENNUNG = "CHK-PLU-01"

#: Die Leistungszeile, die im Entwurf kein Listenpunkt ist, sondern ein
#: hervorgehobener Kasten. Sie wird aus der Liste genommen, damit dieselbe
#: Zusage nicht zweimal untereinander steht.
ANRECHNUNG_MERKMAL = "Anrechenbar"


def _sichere_adresse(roh: str) -> str:
    """Nur, was in einem `href` auf einer fremden Seite stehen darf.

    Der Wert kommt aus einer Einstellung im Werkzeug und landet ungeprueft in
    einem Link auf der Seite eines Kunden. `javascript:` gehoert dort nicht
    hin — dieselbe Schranke wie `safeHref` im Widget, nur eine Ebene frueher.
    """
    wert = (roh or "").strip()
    if not wert:
        return ""
    if wert.startswith(("https://", "http://", "/")):
        return wert
    logger.warning("Kaufadresse fuer Check PLUS verworfen (Schema): %r", wert[:40])
    return ""


def aus_zeile(zeile, kaufadresse: str = "") -> Optional[dict]:
    """Das Angebot aus einer Katalogzeile — oder `None`, wenn es sie nicht gibt.

    **Kein Rueckfall auf Standardwerte.** Fehlt das Produkt, entsteht kein
    Angebot. Ein erfundener Preis waere schlimmer als ein fehlender Block:
    Der fehlende faellt auf, der erfundene wird bezahlt.
    """
    if not zeile:
        return None

    def wert(name, vorgabe=None):
        try:
            return zeile[name]
        except (KeyError, TypeError):
            return getattr(zeile, name, vorgabe)

    leistungen = [
        text for text in (wert("features") or [])
        if ANRECHNUNG_MERKMAL not in text
    ]
    url = _sichere_adresse(kaufadresse)
    live = (wert("status") or "") == "live"

    return {
        "kennung": KENNUNG,
        "name": wert("name") or "Check PLUS",
        "preis_netto": float(wert("price_netto") or 0),
        "preis_brutto": float(wert("price_brutto") or 0),
        "leistungen": leistungen,
        "lieferzeit_tage": int(wert("delivery_days") or 0),
        "anrechnung_monate": int(wert("credit_months") or 0),
        "url": url,
        # Beides muss stimmen: ein `live`-Produkt ohne Adresse hat kein Ziel,
        # eine Adresse auf einen Entwurf verkauft etwas, das nicht angeboten
        # werden darf.
        "verfuegbar": bool(live and url),
    }
