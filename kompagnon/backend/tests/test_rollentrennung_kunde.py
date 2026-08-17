"""Ein angemeldeter Kunde ist kein Mitarbeiter.

Befund vom 17.08.2026: Seit dem 14.08. hängt die Anmeldung am Lead-Router —
aber sie fragt nur, *ob* jemand angemeldet ist (`require_any_auth`), nicht
*wer*. Damit bekam die Rolle `kunde` über `GET /api/leads/` den vollständigen
Betriebsbestand: Firmen, Ansprechpartner, Telefonnummern, Notizen, Scores.
Also die Kundenliste an einen Kunden.

Die Rechtematrix in `admin_settings.py` sagt das längst: `view_leads` haben
superadmin, admin und auditor — `nutzer` und `kunde` nicht. Die Endpunkte
hielten sich nur nicht daran.

Was ein Kunde braucht, ist genau eines: den eigenen Betrieb. Das Kundenportal
ruft `GET /api/leads/{eigene_id}` auf (`KundenPortal.jsx`). Alles andere ist
Innendienst.
"""
import pytest

VERBOTEN = 403

# Der Bestand und alles, was daran hängt — nichts davon geht einen Kunden an.
NUR_INNENDIENST_LESEND = (
    "/api/leads/",
    "/api/leads/customers",
    "/api/leads/export/csv",
)

NUR_INNENDIENST_VERAENDERND = (
    ("post",   "/api/leads/enrich/all"),
    ("post",   "/api/leads/import/manual"),
)


@pytest.mark.parametrize("pfad", NUR_INNENDIENST_LESEND)
def test_ein_kunde_bekommt_den_bestand_nicht(client, kunde_headers, pfad):
    antwort = client.get(pfad, headers=kunde_headers, follow_redirects=True)

    assert antwort.status_code == VERBOTEN, f"{pfad} → {antwort.status_code}"


@pytest.mark.parametrize("methode,pfad", NUR_INNENDIENST_VERAENDERND)
def test_ein_kunde_veraendert_den_bestand_nicht(client, kunde_headers, methode, pfad):
    aufruf = getattr(client, methode)

    antwort = aufruf(pfad, json={}, headers=kunde_headers, follow_redirects=True)

    assert antwort.status_code == VERBOTEN, f"{methode} {pfad} → {antwort.status_code}"


def test_ein_kunde_sieht_den_eigenen_betrieb(client, kunde_headers, kunde_user):
    """Sonst steht das Kundenportal leer da."""
    antwort = client.get(f"/api/leads/{kunde_user.lead_id}", headers=kunde_headers)

    assert antwort.status_code == 200
    assert antwort.json()["id"] == kunde_user.lead_id


def test_ein_kunde_sieht_keinen_fremden_betrieb(client, kunde_headers, fremder_betrieb):
    """Die eigene Nummer hochzuzählen ist der naheliegendste Angriff."""
    antwort = client.get(f"/api/leads/{fremder_betrieb}", headers=kunde_headers)

    assert antwort.status_code == VERBOTEN


def test_ein_kunde_aendert_den_eigenen_betrieb_nicht(client, kunde_headers, kunde_user):
    """Lesen ja, schreiben nein — Stammdaten pflegt der Innendienst."""
    antwort = client.patch(
        f"/api/leads/{kunde_user.lead_id}",
        json={"company_name": "Selbst umbenannt"},
        headers=kunde_headers,
    )

    assert antwort.status_code == VERBOTEN


def test_der_innendienst_kommt_weiterhin_an_alles(client, auth_headers):
    """Die Trennung darf den Betrieb nicht mitnehmen."""
    antwort = client.get("/api/leads/", headers=auth_headers, follow_redirects=True)

    assert antwort.status_code == 200
