"""Die Zahlen fuer den Beleg — aus der Zeile, aus der auch abgerechnet wird (L-29).

**Warum es diese Datei gibt.** In `auftragsbestaetigung_pdf.py` stand eine
feste Preisliste `PAKETE`, dieselbe Bauart wie das laengst entfernte
`PACKAGE_NAMES` — nur in dem Dokument, das der Kunde als Beleg bekommt. Der
tatsaechlich gezahlte Betrag wurde uebergeben und **nirgends benutzt**. Zwei
Folgen: Ein in `products` geaenderter Preis stand im Beleg weiter alt da, und
ein unbekanntes Paket bekam den KOMPAGNON-Eintrag — falscher Paketname,
2.000 EUR und eine falsch ausgewiesene Umsatzsteuer, egal was gezahlt wurde.

**Die Reihenfolge ist dieselbe wie bei `projekt_festpreis`:** Produktzeile,
sonst der gezahlte Betrag, sonst **nichts**. Ein Beleg mit erfundenen Zahlen
ist schlechter als kein Beleg — deshalb ein `ValueError` und kein Notpaket.

Die Darstellung bekommt das Ergebnis uebergeben und holt es nicht selbst.
Sonst haette die PDF-Erzeugung wieder ihre eigene Quelle, und genau das war
der Fehler.
"""
import logging

log = logging.getLogger("paket_beleg")

#: Der gesetzliche Regelsatz. Kein Preis, sondern Steuerrecht — er steht hier
#: nur als Rueckfall, wenn die Produktzeile keinen eigenen Satz fuehrt.
REGELSATZ_PROZENT = 19


def _netto_aus_brutto(brutto: float, satz: float) -> float:
    return round(brutto / (1 + satz / 100), 2)


def paket_fuer_beleg(db, slug: str, bezahlt: float) -> dict:
    """Name, Brutto, Netto, Umsatzsteuer und Leistungen fuer den Beleg.

    :raises ValueError: wenn weder eine Produktzeile noch ein gezahlter
        Betrag vorliegt — dann gibt es nichts zu bestaetigen.
    """
    from sqlalchemy import text as _text

    zeile = None
    try:
        zeile = db.execute(
            _text("SELECT name, price_brutto, price_netto, tax_rate, features, "
                  "delivery_days FROM products WHERE slug = :s"),
            {"s": slug},
        ).fetchone()
    except Exception as fehler:  # noqa: BLE001 — fehlende Tabelle darf den Kauf nicht kippen
        log.warning("Beleg: Produktzeile nicht lesbar (%s: %s) — der gezahlte "
                    "Betrag traegt den Beleg", type(fehler).__name__, fehler)
        try:
            db.rollback()
        except Exception:  # noqa: BLE001 — eine kaputte Sitzung bleibt kaputt
            pass

    if zeile:
        brutto = float(zeile[1] or 0)
        if brutto > 0:
            satz = float(zeile[3] or REGELSATZ_PROZENT)
            netto = float(zeile[2]) if zeile[2] else _netto_aus_brutto(brutto, satz)
            return {
                "name": zeile[0] or slug,
                "brutto": brutto,
                "netto": round(netto, 2),
                "mwst": round(brutto - netto, 2),
                "leistungen": list(zeile[4] or []),
                # **Nicht der letzte Leistungspunkt.** Die alte feste Liste
                # trug die Lieferzeit als letzten Eintrag, und die Darstellung
                # las sie von dort. Auf `products.features` angewandt haette
                # das „30 Tage Support" als Lieferzeit ausgewiesen.
                "lieferzeit_tage": int(zeile[5]) if zeile[5] else None,
                "quelle": "products",
            }

    betrag = float(bezahlt or 0)
    if betrag <= 0:
        raise ValueError(
            f"Kein Preis fuer '{slug}': weder eine Produktzeile noch ein "
            f"gezahlter Betrag. Ein Beleg mit erfundenen Zahlen waere "
            f"schlechter als keiner.")

    netto = _netto_aus_brutto(betrag, REGELSATZ_PROZENT)
    return {
        # **Kein erfundener Paketname.** Die Kennung ist unschoen, aber wahr.
        "name": slug,
        "brutto": betrag,
        "netto": netto,
        "mwst": round(betrag - netto, 2),
        "leistungen": [],
        "lieferzeit_tage": None,
        "quelle": "zahlung",
    }
