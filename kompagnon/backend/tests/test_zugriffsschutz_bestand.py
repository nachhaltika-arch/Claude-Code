"""Der Bestand schwach geschuetzter Routen — gemessen, nicht geschaetzt (L-67).

**Was hier festgehalten wird.** Am 22.08.2026 wurde jede Route unter `/api/`
an der **geladenen Anwendung** durchgegangen: 466 insgesamt, davon 369 mit
einer Rollen- oder Rechtepruefung, 46 mit nur „irgendwer ist angemeldet" und
51 ganz ohne Anmeldepruefung (die sind Gegenstand von L-51).

Die 46 sind **einzeln geprueft** und bleiben mit Grund:

| Bereich | Zahl | Grund |
|---|---|---|
| `academy` | 14 | Kundenweg. Jede Route filtert auf `current_user.id`; die Zertifikatsausstellung nimmt keine Nutzerkennung entgegen. |
| `portal` | 7 | Kundenweg. Fuenf nehmen **gar keine** Fremdkennung entgegen, zwei pruefen den eigenen Betrieb. |
| `auth` | 7 | Eigene Daten. Keine einzige nimmt eine Fremdkennung entgegen — sie koennen nur den Angemeldeten treffen. |
| `assistant` | 5 | Kundenweg aus dem Portal; die drei mit Kennung pruefen, die zwei ohne koennen nichts Fremdes treffen. |
| `projects` | 3 | `eigenes_projekt_pruefen` beziehungsweise Rollenzweig. |
| `leads` | 3 | Betriebs-Eigentum wird geprueft. **Seit 26.08.2026** dazu `PATCH /{id}/stammdaten` — der Kunde pflegt die Angaben seines eigenen Betriebs; dieselbe Eigentumspruefung wie beim Lesen, dazu eine Erlaubnisliste der Felder. |
| `audit` | 2 | `_audit_oder_404` — Einmal-Token **oder** Anmeldung; das ist der Berichtsweg des Kunden. |
| `geo-payments` | 2 | Seit dem 22.08. `eigenes_projekt_pruefen`. |
| `usercards` | 1 | `_check_kunde_access`. |
| `tickets` | 1 | filtert auf `current_user.email`. |
| `invoices` | 1 | filtert auf `current_user.email`. |
| `versand` | 1 | Ein Ja/Nein zum automatischen Versand, kein Kundendatum — siehe unten. |
| `geo` | 1 | **Neu am 26.08.2026.** Der Kunde sieht seinen GEO-Wert (L-95). `eigenes_projekt_pruefen` haelt die Grenze, und die Antwort ist **verkuerzt**: keine Rohpruefungen, kein Upsell-Preis, keine Betriebsfehler. Die uebrigen zehn `geo`-Routen — Analyse anstossen, Monitoring schalten, `admin/run-monitoring-now` — liegen unveraendert hinter `require_innendienst`. |
| `briefings` | 5 | **Neu am 26.08.2026.** Der Kunde fuellt sein Briefing selbst aus. Alle drei tragen `_eigener_betrieb` — dieselbe Umkehrung wie ueberall: Wer nicht zum Innendienst gehoert, kommt nur an den eigenen Betrieb. Ein eigenes Wegstueck `/mein/…`, damit sich die zwei Router nicht ueberdecken (L-27). |
| `files` | 3 | **Neu am 26.08.2026.** Logo, Fotos, Unterlagen zum eigenen Betrieb. Der Download prueft am **Datensatz**, nicht am Pfad: Die Dateikennung ist eine fortlaufende Zahl, und der Pfad nennt keinen Betrieb. |
| `messages` | 2 | **Neu am 26.08.2026.** Der Nachrichtenverlauf des Kunden. Beide Routen nahmen bisher **nur** einen `customer_token` und zaehlten deshalb zu den ganz offenen; seit dem Chat im angemeldeten Portal nehmen sie auch eine Anmeldung. `_zugang_pruefen` entscheidet an **einer** Stelle: Ein mitgeschickter Token muss stimmen, sonst muss der Angemeldete zum Innendienst gehoeren oder den Betrieb besitzen. Sie sind damit **staerker** geschuetzt als vorher, nicht schwaecher — die Zahl unten steigt, weil sie aus der offenen Liste hierher gewandert sind. |

**Warum diese Zahl bewacht wird.** Sie ist dreimal gewandert: von „166" ueber
„120" auf 85 und schliesslich 46 — und die ersten beiden Zahlen waren zu
hoch, weil eine Sperre am **Router** haengen kann, waehrend die Signatur
schwach aussieht. Ohne Wache waechst so ein Bestand mit jeder neuen Route
zurueck, und niemand merkt es, weil nichts rot wird.

Der Test scheitert bewusst auch, wenn die Zahl **faellt**: Dann ist etwas
geschlossen worden, und die Tabelle oben gehoert nachgezogen. Eine Zahl, die
niemand mehr nachfuehrt, ist keine Messung mehr.
"""
import importlib.util
import pathlib

import pytest


#: Stand vom 22.08.2026, an der geladenen Anwendung gemessen.
#: 22.08.2026: 46
#: 26.08.2026: 49 — `PATCH /api/leads/{id}/stammdaten` (Kunde pflegt seine
#:   Stammdaten) und die beiden `messages`-Routen, die aus der **offenen**
#:   Liste hierher gewandert sind, weil sie jetzt auch eine Anmeldung nehmen.
#: 26.08.2026, spaeter: 55 — der Kunde fuellt sein Briefing aus (3) und laedt
#:   Dateien hoch (3). Alle sieben pruefen den eigenen Betrieb selbst.
#: 26.08.2026, abends: 57 — `GET /api/geo/mein/{id}/result`. Der GEO-Wert war
#:   berechnet und dem Kunden nie gezeigt (L-95).
#: 26.08.2026, spaet: 58 — `PATCH /api/briefings/{id}/freigabe` ist aus der
#:   **offenen** Liste hierher gewandert: Der Endpunkt las den JWT aus dem
#:   Rumpf und entschluesselte ihn von Hand; jetzt `get_current_user` wie
#:   ueberall, dazu Rollen- und Eigentumspruefung. Staerker als vorher.
ERWARTET = 58

#: Wo die 46 liegen duerfen. Ein neuer Bereich ist ein Befund, keine Zahl.
ERLAUBTE_BEREICHE = {
    "academy", "portal", "auth", "assistant", "projects", "leads",
    "audit", "geo-payments", "usercards", "tickets", "invoices", "versand",
    "messages", "briefings", "files", "geo",
}

#: Routen ganz **ohne** Anmeldepruefung, Stand 25.08.2026 (L-51).
#:
#: 22.08.2026: 49
#: 25.08.2026: 53 — vier Routen des Buchverkaufs (BUCH-05). Ein Kaeufer ist
#:   nicht angemeldet und wird es auch nicht: Er kauft ein Buch, kein Konto.
#: 26.08.2026: 51 — die beiden `messages`-Routen des Kunden sind **hoch**
#:   gewandert: Sie nehmen jetzt neben dem Token auch eine Anmeldung und
#:   zaehlen damit zu den schwach geschuetzten statt zu den offenen.
#: 26.08.2026, spaet: 50 — `PATCH /api/briefings/{id}/freigabe` ebenso.
#: 26.08.2026, Posteingang: 51 — `POST /api/posteingang/brevo/{secret}`.
#: Brevo signiert eingehende Mails nicht; das Geheimnis steht im Pfad, wie
#: beim `mail-events`-Webhook, von dem dieser Weg die Absicherung uebernimmt.
#: 27.08.2026: 52 — `POST /api/auth/resend-verification`. Sie **muss** offen
#:   sein: Wer sie braucht, kommt gerade nicht durch die Anmeldung (der
#:   Bestaetigungsriegel haelt ihn auf). Eine Anmeldepruefung davor waere die
#:   verschlossene Tuer, hinter der der Schluessel liegt. Abgesichert ist sie
#:   anders — gedrosselt je Herkunft, und ihre Antwort ist fuer „gibt es
#:   nicht", „schon bestaetigt" und „gesendet" **dieselbe**, damit sie kein
#:   Adressverzeichnis wird.
#: 27.08.2026, spaet: 51 — `GET /api/audit/analysen/anzahl` entfernt. Er
#:   speiste den Werbesatz „Ueber X Handwerksbetriebe analysiert" im Widget;
#:   der Satz kam am 24.08. weg (L-65/L-95), der Hook dazu am 27.08. Damit
#:   war der Endpunkt oeffentlich, ungerufen und ohne Zweck.
#: 27.08.2026, ORDERS_03: 52 — `POST /api/shop/checkout`. Sie **muss** offen
#:   sein: Wer ein digitales Produkt kauft, hat noch kein Konto; das Konto
#:   entstuende erst mit dem Kauf. Abgesichert ist sie anders — der Preis
#:   kommt aus dem Katalog und nie aus der Anfrage, ein Entwurf ist nicht
#:   bestellbar, und ein Verbraucher ohne Widerrufsverzicht wird abgelehnt.
#: 29.08.2026, ORDERS_04: 54 — zwei Routen, beide zwingend offen.
#:   `POST /api/shop/webhook` ruft **Stripe** auf, nicht ein angemeldeter
#:   Mensch. Eine Anmeldepruefung waere hier keine Sicherung, sondern ein
#:   Ausfall: Stripe kann sich nicht anmelden und wiederholte die Meldung
#:   tagelang. Abgesichert ist sie staerker als durch eine Anmeldung — jede
#:   Anfrage muss eine gueltige Signatur mit **eigenem** Geheimnis tragen
#:   (`SHOP_STRIPE_WEBHOOK_SECRET`, L-138), sonst 400. Ohne eingerichtetes
#:   Geheimnis nimmt sie **gar nichts** an.
#:   `GET /api/shop/orders/{order_number}/status` fragt die Danke-Seite ab,
#:   waehrend die Zahlung bestaetigt wird — der Kaeufer hat kein Konto. Sie
#:   gibt genau drei Felder heraus: Bestellnummer, Status, Produktkennung.
#:   **Keine Mail, kein Betrag, keine Anschrift** — die Bestellnummer steht im
#:   Browserverlauf und in E-Mails und ist deshalb kein Geheimnis, aus dem
#:   sich ein Datensatz ableiten darf. Zwei Zusicherungen in
#:   `tests/test_shop_webhook.py` halten das fest.
#: 29.08.2026, ORDERS_06: 55 — `GET /api/shop/download/{token}`. Zwingend
#:   offen: Der Kaeufer hat kein Konto, und eines anzulegen, nur um eine
#:   gekaufte Datei abzuholen, waere eine Huerde nach der Zahlung.
#:   **Der Token ist das Geheimnis**, nicht die Anmeldung — 32 Byte aus
#:   `secrets.token_urlsafe`, eindeutig indiziert, dreissig Tage gueltig.
#:   Ein unbekannter und ein unbezahlter Abruf antworten **gleich** (404),
#:   damit der Unterschied nicht verraet, welche Bestellungen es gibt; ein
#:   abgelaufener bekommt 410 mit eigener Auskunft. Die Datei selbst laeuft
#:   nicht durch uns: Es wird auf eine signierte R2-Adresse weitergeleitet,
#:   die Minuten lebt. Zwoelf Zusicherungen in `tests/test_shop_auslieferung.py`.
#: 29.08.2026, ORDERS_07: 56 — `GET /api/shop/orders/{nr}/invoice`. Zwingend
#:   offen aus demselben Grund wie der Abruf: Der Kaeufer hat kein Konto.
#:   **Abgesichert ist sie schaerfer als der Abruf**, weil die Rechnung Name
#:   und Anschrift traegt: Sie verlangt die Bestellnummer **und** denselben
#:   Token wie die Datei, und beide muessen zur selben Bestellung gehoeren.
#:   Die Bestellnummer allein genuegt nicht — sie steht im Browserverlauf und
#:   in E-Mails, und wer sie kennt, bekaeme sonst einen Datensatz. Ein
#:   falscher Token ist 404, nicht 403: Auch die Auskunft „diese Bestellung
#:   gibt es" gehoert nicht heraus.
#: 01.09.2026, BUCH-09: 57 — `GET /api/health/cors`. Die Diagnose fuer die
#:   Verbindung Browser→Backend. **Offen mit Absicht:** Wer wissen will, ob
#:   eine *fremde* Landingpage das Backend erreicht, hat dort kein Token; hinter
#:   der Anmeldung beantwortete der Endpunkt genau die Frage nicht, fuer die er
#:   gebaut ist. Heraus gehen nur die erlaubten Herkuenfte, die Herkunft des
#:   Aufrufs, ob sie passt, und der Deploy-Stand — dieselbe Liste, die ohnehin
#:   in jeder Preflight-Antwort steht. Eine Zusicherung in
#:   `test_cors_herkuenfte` haelt fest, dass dort nichts weiter hinzukommt;
#:   der Anlass dafuer ist der 15.08.2026, als Datenbank-Zugangsdaten auf einem
#:   Auskunftsendpunkt offenlagen.
OFFEN_ERWARTET = 57

#: Wo sie liegen duerfen — jeder Bereich mit dem Grund, aus dem er offen ist.
#:
#: `widget`, `kampagne`      Das eingebettete Widget laeuft auf fremden Seiten.
#: `webhooks`, `mail-events`,
#: `posteingang`             Rufe von aussen; sie weisen sich mit einem
#:                           Geheimnis im Pfad aus.
#: `auth`                    Anmelden, Registrieren, Passwort zuruecksetzen.
#: `leads`, `messages`,
#: `projects`, `briefings`   Kundenwege ueber Einmal-Token.
#: `payments`,
#: `geo-payments`            Kasse und Stripe-Rueckruf.
#: `products`                Der Katalog ist oeffentlich.
#: `tickets`                 **Nur** das Anlegen — der Rueckmeldeweg des
#:                           `FeedbackButton`. Die Leserouten sind seit dem
#:                           22.08. gesperrt (L-90).
#: `audit`                   Analyse starten und die Anzahl abfragen; beides
#:                           gehoert dem Widget.
#: `academy`                 Zertifikatspruefung ueber den Code.
#: `book`                    Der Buchverkauf. Vier Routen: die Kasse und die
#:                           Preisliste (ein Kaeufer ist nicht angemeldet),
#:                           der Stripe-Rueckruf (weist sich per Signatur aus,
#:                           siehe `test_buch_bestellung`) und die Auskunft
#:                           fuer die Danke-Seite. Letztere gibt bewusst nur
#:                           Nummer, Ausgabe, Zahlungsstand und eine
#:                           **verkuerzte** Adresse heraus — keine Anschrift,
#:                           kein Abruftoken.
#: `health`, `ping`          Betriebsanzeigen ohne Inhalt — dazu seit dem
#:                           01.09.2026 `health/cors`, die Verbindungs-
#:                           diagnose aus BUCH-09.
#: `shop`                    Der Bezahlvorgang fuer digitale Produkte
#:                           (L-100, 27.08.2026). Offen aus demselben Grund
#:                           wie `payments` und `book`: Wer kauft, hat noch
#:                           kein Konto. Abgesichert ist er anders — der
#:                           Preis kommt aus dem Katalog und nie aus der
#:                           Anfrage, ein Entwurf ist nicht bestellbar, und
#:                           ein Verbraucher ohne Widerrufsverzicht wird
#:                           abgelehnt.
OFFENE_BEREICHE = {
    "widget", "webhooks", "auth", "leads", "payments", "tickets",
    "products", "projects", "audit", "messages", "briefings", "kampagne",
    "academy", "geo-payments", "mail-events", "health", "ping", "book",
    "posteingang", "shop",
}


def _werkzeug():
    pfad = (pathlib.Path(__file__).resolve().parent.parent.parent.parent
            / "tools" / "schwacher-zugriffsschutz.py")
    if not pfad.exists():
        pytest.skip(f"Werkzeug nicht gefunden: {pfad}")
    spec = importlib.util.spec_from_file_location("wz", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _routen_nach_klasse():
    """Alle `/api/`-Routen, getrennt nach Schutzklasse."""
    wz = _werkzeug()
    from main import app

    schwach, offen = [], []
    for route in wz.alle_routen(app):
        pfad = getattr(route, "path", "")
        if not pfad.startswith("/api/"):
            continue
        namen = wz.namen(route.dependant)
        if namen & wz.STARK:
            continue
        (schwach if namen & wz.SCHWACH else offen).append(pfad)
    return schwach, offen


def _schwache_routen():
    return _routen_nach_klasse()[0]


def _offene_routen():
    return _routen_nach_klasse()[1]


def test_der_bestand_ist_nicht_gewachsen():
    """Waechst er, ist eine neue Route ohne Rollenpruefung hinzugekommen."""
    schwach = _schwache_routen()

    assert len(schwach) <= ERWARTET, (
        f"{len(schwach)} statt {ERWARTET} schwach geschuetzte Routen. "
        f"Neu hinzugekommen und ungeprueft:\n  " + "\n  ".join(sorted(schwach)))


def test_und_die_zahl_stimmt_noch():
    """Faellt sie, gehoert die Tabelle im Kopf dieser Datei nachgezogen —
    sonst steht dort bald eine Begruendung fuer etwas, das es nicht mehr gibt.
    """
    schwach = _schwache_routen()

    assert len(schwach) == ERWARTET, (
        f"{len(schwach)} statt {ERWARTET}. Wurde etwas geschlossen? Dann "
        f"`ERWARTET` und die Tabelle im Kopf dieser Datei anpassen.")


def test_sie_liegen_nur_in_geprueften_bereichen():
    """Ein neuer Bereich ist ein Befund, keine Zahl."""
    bereiche = {p.split("/")[2] for p in _schwache_routen() if len(p.split("/")) > 2}

    assert bereiche <= ERLAUBTE_BEREICHE, (
        f"Ungeprueft: {sorted(bereiche - ERLAUBTE_BEREICHE)}")


# ── Routen ganz ohne Anmeldung (L-51) ─────────────────────────────────
#
# **Warum das hier mitgezaehlt wird.** `test_zugriffsschutz_werkzeug.py`
# prueft eine von Hand gepflegte Liste von Pfaden. Eine solche Liste waechst
# nicht mit dem Code mit: Der Bestand stieg seit dem 19.08.2026 von 42 auf
# 51, ohne dass etwas rot wurde — darunter `GET /api/tickets/`, das **alle**
# Support-Tickets samt Namen, Adressen und Bildschirmfotos herausgab (L-90).
#
# Gezaehlt wird deshalb am **gesamten** Routenbaum, nicht an einer Liste.


def test_der_offene_bestand_ist_nicht_gewachsen():
    offen = _offene_routen()

    assert len(offen) <= OFFEN_ERWARTET, (
        f"{len(offen)} statt {OFFEN_ERWARTET} Routen ohne Anmeldepruefung. "
        f"Neu und ungeprueft:\n  " + "\n  ".join(sorted(offen)))


def test_und_die_offene_zahl_stimmt_noch():
    offen = _offene_routen()

    assert len(offen) == OFFEN_ERWARTET, (
        f"{len(offen)} statt {OFFEN_ERWARTET}. Wurde etwas geschlossen? Dann "
        f"`OFFEN_ERWARTET` und die Begruendungsliste anpassen.")


def test_offene_routen_liegen_nur_in_begruendeten_bereichen():
    """Ein neuer offener Bereich ist ein Befund, keine Zahl."""
    bereiche = {p.split("/")[2] for p in _offene_routen() if len(p.split("/")) > 2}

    assert bereiche <= OFFENE_BEREICHE, (
        f"Ohne Anmeldung und ohne Begruendung: {sorted(bereiche - OFFENE_BEREICHE)}")
