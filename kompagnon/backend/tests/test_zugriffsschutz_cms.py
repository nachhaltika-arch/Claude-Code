"""Ein angemeldeter Kunde darf nicht auf fremde Websites veroeffentlichen.

Gefunden am 21.08.2026 beim Auftrennen der Naht `/api/customers` (Modulkarte).
`routers/cms_connect.py` haengt vier Routen unter dieses Praefix:

    GET  /api/customers/{id}/cms-connection
    PUT  /api/customers/{id}/cms-connection
    POST /api/customers/{id}/cms-test
    POST /api/customers/{id}/publish

Alle vier trugen **nur** `require_any_auth` und **keine Zeilenpruefung**. Ein
angemeldeter Kunde — und Kunden haben Konten — konnte damit die CMS-Adresse
und den Benutzernamen **jedes** anderen Kunden lesen und, schwerer,
**beliebiges HTML auf dessen Live-Website veroeffentlichen**. Das Passwort
bleibt verschluesselt; es wird serverseitig entschluesselt und benutzt, ohne
dass der Aufrufer es je sieht. Genau das macht es schlimmer, nicht besser: Der
Angreifer braucht es gar nicht.

**Warum es die bisherigen Sweeps nicht gefunden haben.** L-51 hat am 19.08.
gezaehlt, welche Routen **ohne Anmeldung** antworten — diese hier verlangen
eine. Die Frage „wer angemeldet ist, darf aber trotzdem nicht" ist eine
andere, und sie ist bisher nur fuer Leads, Projekte und die Kundenkartei
gestellt worden (L-12), nicht flaechendeckend.

**Und warum es niemandem aufgefallen ist:** Der einzige Bildschirm, der diese
Routen ruft, ist `CustomerDetail.jsx` — und der haengt an
`<PrivateRoute roles={['admin']}>`. Wer nur die Oberflaeche prueft, sieht eine
Sperre. Die Sperre stand aber in der Oberflaeche, nicht am Endpunkt.
"""
import pytest


CMS_ROUTEN = (
    ("get",  "/api/customers/1/cms-connection"),
    ("put",  "/api/customers/1/cms-connection"),
    ("post", "/api/customers/1/cms-test"),
    ("post", "/api/customers/1/publish"),
)


@pytest.mark.parametrize("verb,pfad", CMS_ROUTEN)
def test_ein_kunde_kommt_an_keine_cms_route(client, kunde_headers, verb, pfad):
    # Act — `get` kennt kein `json`, deshalb je nach Verb.
    ruf = getattr(client, verb)
    antwort = (ruf(pfad, headers=kunde_headers) if verb == "get"
               else ruf(pfad, headers=kunde_headers, json={}))

    # Assert — 403 heisst „du nicht", 404 „gibt es nicht". Beides ist recht;
    # 200 und 400 waeren beide falsch, denn dann ist er drin gewesen.
    assert antwort.status_code in (401, 403, 404), (
        f"{verb.upper()} {pfad} antwortete {antwort.status_code} — "
        "ein Kunde ist an einer fremden CMS-Verbindung."
    )


@pytest.mark.parametrize("verb,pfad", CMS_ROUTEN)
def test_ohne_anmeldung_erst_recht_nicht(client, verb, pfad):
    ruf = getattr(client, verb)
    antwort = ruf(pfad) if verb == "get" else ruf(pfad, json={})
    assert antwort.status_code in (401, 403, 404)


def test_der_innendienst_kommt_weiterhin_durch(client, auth_headers):
    """Die Sperre darf nicht den treffen, der die Seite bedient.

    `CustomerDetail.jsx` ist der einzige Aufrufer und admin-only. 404 ist die
    richtige Antwort fuer einen Kunden, den es nicht gibt — sie beweist, dass
    die Anfrage **durch** die Sperre und bis zur Datenbank gekommen ist.
    """
    # Act
    antwort = client.get("/api/customers/999999/cms-connection", headers=auth_headers)

    # Assert
    assert antwort.status_code == 404, antwort.text
