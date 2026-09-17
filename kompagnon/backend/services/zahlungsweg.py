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
    product_code = "…"      routers/shop.py
    order_number = "…"      routers/buch.py
    package = "starter"     routers/payments.py

**Der vierte Weg kam am 29.08.2026 dazu, und er war ein Fehler.** Bis dahin
galt „Bestellnummer heißt Buch". Seit ORDERS_03 trägt aber auch die
Shop-Kasse eine Bestellnummer — ein gekauftes Workbook wäre im Buch-Pfad
gelandet, dort auf `paid` gesetzt und dann durch `ist_digital` gefallen:
`variant` ist bei Katalogprodukten `"katalog"`, nicht `"pdf"` oder
`"bundle"`. **Bezahlt, kein Abruf-Token, keine Auslieferung.** Aufgefallen ist
es beim Bauen von ORDERS_04, nicht im Betrieb — die drei Katalogprodukte
stehen bis ORDERS_05 auf `draft`, der Fehler lag bereit, nicht offen.

Unterschieden wird an `product_code`: Den setzt nur die Shop-Kasse, das Buch
setzt `variant` und `book_version`.

**Warum der Websprint der Rückfall ist und nicht ein vierter Marker.** Er ist
der älteste Weg, und es kann in Stripe Sitzungen von vor dieser Änderung
geben. Eine Sitzung ohne jeden Marker weiter dort zu behandeln, wo sie bisher
behandelt wurde, ändert für den Bestand nichts — und die Stelle in
`_handle_successful_payment`, die ein fehlendes `package` bewusst zulässt
(L-97), bleibt gültig.

**Und seit dem 14.09.2026 reicht der Rückfall allein nicht mehr.** Er ruhte
auf einer Annahme, die bis zum 13.09. stimmte: dass **jede** Kasse dieses
Kontos von uns angelegt wird. Der Stripe-Zahllink für Check PLUS (L-187)
bricht sie — er erzeugt eine Kasse ganz ohne unsere Angaben. Deshalb fragt
`von_uns` unten zusätzlich nach der **Herkunft**, nicht nur nach dem Weg.
"""
import logging

logger = logging.getLogger(__name__)

#: Die vier Wege.
GEO = "geo"
SHOP = "shop"
BUCH = "buch"
WEBSPRINT = "websprint"


def weg_der_sitzung(metadaten) -> str:
    """Der Weg, zu dem diese Kasse gehört — nie leer.

    Die Reihenfolge ist Absicht und seit dem 29.08.2026 nicht mehr folgenlos:
    `addon_type` ist der engste Marker, dann `product_code`, dann die
    Bestellnummer, dann der Rückfall. **`product_code` muss vor
    `order_number` stehen** — die Shop-Kasse setzt beide, und in der alten
    Reihenfolge hieße jede Shop-Sitzung „Buch".
    """
    metadaten = metadaten or {}
    if str(metadaten.get("addon_type") or "").strip() == GEO:
        return GEO
    if str(metadaten.get("product_code") or "").strip():
        return SHOP
    if str(metadaten.get("order_number") or "").strip():
        return BUCH
    return WEBSPRINT


#: Die Angaben, die **dieses System** an eine Kasse schreibt, wenn es sie
#: anlegt — `routers/payments.py`, `buch.py`, `shop.py`, `geo_payments.py`.
#: Keine davon setzt Stripe von sich aus.
EIGENE_MARKER = ("addon_type", "product_code", "order_number", "package",
                 "abo_produkt", "lead_id", "customer_email", "company_name",
                 "customer_name", "website_url")


def von_uns(metadaten) -> bool:
    """Ob diese Kasse aus diesem System stammt.

    **Der Befund vom 14.09.2026, beim Nachmessen von L-100 gefunden.** Der
    Rueckfall in `weg_der_sitzung` — „ohne Marker ist es ein Websprint" — war
    richtig, solange **jede** Sitzung des Kontos von uns angelegt wurde. Seit
    dem 13.09.2026 stimmt das nicht mehr: Check PLUS wird ueber einen festen
    Stripe-Zahllink verkauft (L-187), und der legt eine Kasse an, die keine
    einzige unserer Angaben traegt.

    Ohne diese Unterscheidung laeuft ein Zahllink-Kauf durch
    `_handle_successful_payment` und erzeugt Lead, Benutzerkonto,
    Website-Projekt und Willkommensmail — fuer jemanden, der einen
    Pruefbericht bestellt hat. Das ist woertlich der Schaden, gegen den die
    Weiche vom 27.08. gebaut wurde, nur aus der anderen Richtung: damals ein
    fremder **Weg**, jetzt eine fremde **Herkunft**.

    **Ein leerer Wert zaehlt nicht als Angabe.** Stripe raeumt leere
    Metadaten weg; wer hier auf das blosse Vorhandensein des Schluessels
    pruefte, haette eine Erkennung, die vom Verhalten eines Fremdsystems
    abhinge.
    """
    metadaten = metadaten or {}
    return any(str(metadaten.get(schluessel) or "").strip()
               for schluessel in EIGENE_MARKER)


def gehoert_hierher(erwartet: str, metadaten) -> bool:
    """Ob diese Sitzung von dem Weg verarbeitet werden soll, der fragt."""
    return weg_der_sitzung(metadaten) == erwartet


def merkmale_mit_agb(merkmale: dict) -> dict:
    """Die Metadaten der Kassensitzung, ergaenzt um die geltende AGB-Fassung.

    **Der Punkt, den fast alle vergessen** (L-181, 06.09.2026). Aendern sich
    die AGB, muss nachweisbar bleiben, **welche Fassung** der Kaeufer
    akzeptiert hat — sonst belegt die Zustimmung nur, dass jemand irgendwann
    irgendetwas angehakt hat. Der Shop haelt sie seit ORDERS_05 fest
    (`bestellungen.terms_version`); beim **Websprint** ueber Stripe kam `agb`
    bis heute **null Mal** vor, und das ist der teurere der beiden Wege.

    **Der Server bestimmt die Fassung, nicht der Browser.** Kaeme sie aus dem
    Aufruf, koennte der Absender bestimmen, welcher Fassung er zugestimmt
    haben will.

    **Ohne hinterlegte Fassung steht ein leeres Feld da** — nicht eine
    erfundene Kennung. Ein Nachweis ueber nichts waere schlechter als die
    sichtbare Luecke; sie steht dafuer in `/health`.
    """
    from services import agb

    return {**(merkmale or {}), "agb_fassung": agb.fassung() or ""}
