# -*- coding: utf-8 -*-
"""Zu welchem Verkaufsweg eine Stripe-Sitzung gehört.

**Der Anlass (27.08.2026, vor der Einrichtung der Webhooks).** In Stripe
werden drei Adressen eingetragen — `/api/payments/webhook`,
`/api/book/webhook` und `/api/geo-payments/webhook`. Wer das zum ersten Mal
macht, nimmt an, jede Adresse bekäme ihre eigenen Vorgänge.

**Sie bekommen alle dasselbe.** Ein Stripe-Endpunkt ist ein Abonnement auf
Ereignisarten, nicht auf Vorgänge: Wer `checkout.session.completed`
abonniert, bekommt **jede** abgeschlossene Kasse dieses Kontos — den
Websprint, das Buch, das Shop-Produkt, das GEO-Abo. Jede Adresse muss selbst
erkennen, was ihr gehört.

Ohne diese Unterscheidung hätte der Kauf eines Buchs für 49 EUR im
Websprint-Pfad einen Lead, ein Benutzerkonto, ein Website-Projekt und eine
Willkommensmail ausgelöst — der Käufer hätte Zugangsdaten für ein Projekt
bekommen, das er nie bestellt hat.

**Woran es erkannt wird.** An den Metadaten, die wir selbst beim Anlegen der
Kasse mitgeben:

    addon_type = "geo"      routers/geo_payments.py
    order_number = "B-…"    routers/shop.py und routers/buch.py
    package = "starter"     routers/payments.py

**Warum der Websprint der Rückfall ist und nicht ein vierter Marker.** Er ist
der älteste Weg, und es kann in Stripe Sitzungen von vor dieser Änderung
geben. Eine Sitzung ohne jeden Marker weiter dort zu behandeln, wo sie bisher
behandelt wurde, ändert für den Bestand nichts — und die Stelle in
`_handle_successful_payment`, die ein fehlendes `package` bewusst zulässt
(L-97), bleibt gültig.
"""
import logging

logger = logging.getLogger(__name__)

#: Die drei Wege.
GEO = "geo"
BUCH = "buch"
WEBSPRINT = "websprint"


def weg_der_sitzung(metadaten) -> str:
    """Der Weg, zu dem diese Kasse gehört — nie leer.

    Die Reihenfolge ist Absicht: `addon_type` ist der engste Marker, dann die
    Bestellnummer, dann der Rückfall. Ein GEO-Abo trägt keine Bestellnummer
    und ein Buch kein `addon_type`; die Reihenfolge entscheidet also heute
    nichts — sie hält nur fest, was gälte, wenn ein Weg beide trüge.
    """
    metadaten = metadaten or {}
    if str(metadaten.get("addon_type") or "").strip() == GEO:
        return GEO
    if str(metadaten.get("order_number") or "").strip():
        return BUCH
    return WEBSPRINT


def gehoert_hierher(erwartet: str, metadaten) -> bool:
    """Ob diese Sitzung von dem Weg verarbeitet werden soll, der fragt."""
    return weg_der_sitzung(metadaten) == erwartet
