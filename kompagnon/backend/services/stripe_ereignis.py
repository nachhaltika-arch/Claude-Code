# -*- coding: utf-8 -*-
"""Ein Stripe-Ereignis wird zu gewoehnlichen Python-Daten.

**Der Anlass (27.08.2026, erster echter Testkauf).** Die Kette stand: Kasse,
Schluessel, drei Webhook-Adressen, Signaturpruefung. Der erste echte Kauf
antwortete mit **HTTP 500**.

    KeyError: 'get'
    AttributeError: get

`stripe.Webhook.construct_event` liefert kein `dict`, sondern ein
`StripeObject`. Und seit **stripe 15** ist das **keine dict-Unterklasse
mehr**:

    >>> issubclass(stripe.StripeObject, dict)
    False

`StripeObject.__getattr__` schlaegt jeden Attributzugriff im Datenteil nach.
`sitzung.get("metadata", {})` sucht also nicht die Methode `get`, sondern
einen **Schluessel namens „get"** — und wirft, wenn es ihn nicht gibt. Der
Zugriff ueber `sitzung["metadata"]` funktioniert weiter; nur die
dict-Methoden fehlen.

**Warum das niemand vorher bemerkt hat.** Alle Tests reichen ein `dict`
herein — so, wie man eine Stripe-Meldung von Hand aufschreibt. Sie waren
gruen, und sie haben nichts Falsches geprueft: Die Logik stimmt. Was ihnen
fehlte, war das **echte Objekt**. Bis heute Abend hat nie eine echte
Stripe-Meldung dieses System erreicht; der Fehler lag seit dem Einbau da und
konnte nicht auffallen.

**Deshalb steht die Umwandlung an der Grenze und nicht in jedem Aufrufer.**
Wer sie an zwanzig Stellen einzeln machen muesste, vergisst die einundzwanzigste
— und das ist dann wieder ein Fehler, den erst ein Kaeufer findet. Ab der
Grenze arbeitet der ganze Bestand mit gewoehnlichen Daten, genau so, wie die
Tests es beschreiben.
"""


def als_dict(wert):
    """Macht aus einem `StripeObject` (und allem darin) gewoehnliche Daten.

    Rekursiv, weil `to_dict()` nur die oberste Ebene aufloest: `metadata`
    und `customer_details` blieben sonst StripeObjects, und der Fehler
    verschoebe sich eine Ebene tiefer statt zu verschwinden.

    **Erkannt wird an der Klasse, nicht am Objekt** (`getattr(type(...))`).
    Ein `hasattr(wert, "to_dict")` ginge ueber genau das `__getattr__`,
    das hier das Problem ist.
    """
    umwandeln = getattr(type(wert), "to_dict", None)
    if callable(umwandeln):
        wert = umwandeln(wert)
    if isinstance(wert, dict):
        return {schluessel: als_dict(inhalt) for schluessel, inhalt in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [als_dict(inhalt) for inhalt in wert]
    return wert


def gegenstand(ereignis) -> dict:
    """Der Vorgang aus einem Stripe-Ereignis — als gewoehnliches `dict`.

    Fehlt `data.object`, ist das ein leeres `dict` und keine Ausnahme: Ein
    Webhook, der beim Auspacken abstuerzt, laesst Stripe tagelang
    wiederholen, und im Protokoll steht ein Absturz statt einer Aussage.
    """
    try:
        return als_dict(ereignis["data"]["object"]) or {}
    except Exception:                       # noqa: BLE001 — siehe Kopftext
        return {}
