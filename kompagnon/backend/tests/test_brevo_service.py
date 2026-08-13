"""
Brevo-Anbindung — geprueft gegen einen nachgestellten Transport.

Diese Tests sprechen nie mit Brevo. httpx.MockTransport faengt die Anfrage ab,
sodass Pfad, Kopfzeilen und Nutzdaten genauso geprueft werden koennen wie die
Reaktion auf Fehlerantworten.

Hintergrund: Bis 2026-08-08 rief der Dienst `import brevo_python` auf. Das Paket
`brevo-python` liefert aber das Modul `brevo`, nie `brevo_python` — der Import
schlug also immer fehl, wurde stillschweigend gefangen und der Newsletter war
dauerhaft abgeschaltet, ohne dass es jemandem auffiel.
"""
import json

import httpx
import pytest

from services.brevo_service import BREVO_API, BrevoError, BrevoService


def _service(handler):
    """BrevoService mit nachgestelltem Transport statt echtem Netz."""
    return BrevoService(api_key="test-key", transport=httpx.MockTransport(handler))


def _json_response(status_code, payload):
    return httpx.Response(status_code, json=payload)


# ── Konfiguration ────────────────────────────────────────────────────────────

def test_ohne_api_key_wird_der_dienst_nicht_gebaut(monkeypatch):
    monkeypatch.delenv("BREVO_API_KEY", raising=False)

    with pytest.raises(BrevoError, match="BREVO_API_KEY"):
        BrevoService()


def test_leerer_api_key_zaehlt_als_nicht_gesetzt(monkeypatch):
    monkeypatch.setenv("BREVO_API_KEY", "   ")

    with pytest.raises(BrevoError, match="BREVO_API_KEY"):
        BrevoService()


def test_jede_anfrage_traegt_den_api_key_im_kopf():
    gesehen = {}

    def handler(request):
        gesehen["api_key"] = request.headers.get("api-key")
        gesehen["url"] = str(request.url)
        return _json_response(201, {"id": 1})

    with _service(handler) as brevo:
        brevo.create_list("Test")

    assert gesehen["api_key"] == "test-key"
    assert gesehen["url"].startswith(BREVO_API)


# ── Kontakte ─────────────────────────────────────────────────────────────────

def test_create_contact_sendet_attribute_und_liefert_id():
    gesehen = {}

    def handler(request):
        gesehen["method"] = request.method
        gesehen["path"] = request.url.path
        gesehen["body"] = json.loads(request.content)
        return _json_response(201, {"id": 4711})

    with _service(handler) as brevo:
        contact_id = brevo.create_contact("a@b.de", "Anna", "Beispiel", [7])

    assert contact_id == 4711
    assert gesehen["method"] == "POST"
    assert gesehen["path"].endswith("/contacts")
    assert gesehen["body"]["email"] == "a@b.de"
    assert gesehen["body"]["attributes"] == {"FIRSTNAME": "Anna", "LASTNAME": "Beispiel"}
    assert gesehen["body"]["listIds"] == [7]


def test_bekannter_kontakt_wird_nachgeschlagen_statt_als_fehler_zu_gelten():
    """Brevo antwortet bei bereits vorhandenen Kontakten mit 204 ohne Rumpf."""
    def handler(request):
        if request.method == "POST":
            return httpx.Response(204)
        return _json_response(200, {"id": 99, "email": "a@b.de"})

    with _service(handler) as brevo:
        contact_id = brevo.create_contact("a@b.de", "Anna", "Beispiel", [7])

    assert contact_id == 99


def test_abgelehnter_kontakt_wirft_mit_brevos_begruendung():
    def handler(request):
        return _json_response(400, {"code": "invalid_parameter", "message": "Invalid email address"})

    with _service(handler) as brevo:
        with pytest.raises(BrevoError, match="Invalid email address"):
            brevo.create_contact("keine-mail", "", "", [7])


def test_netzfehler_wird_als_brevo_fehler_gemeldet():
    def handler(request):
        raise httpx.ConnectError("keine Verbindung")

    with _service(handler) as brevo:
        with pytest.raises(BrevoError, match="nicht erreichbar"):
            brevo.create_contact("a@b.de", "", "", [7])


# ── Listen ───────────────────────────────────────────────────────────────────

def test_create_list_liefert_die_brevo_id():
    def handler(request):
        assert request.url.path.endswith("/contacts/lists")
        assert json.loads(request.content)["name"] == "Kunden"
        return _json_response(201, {"id": 12})

    with _service(handler) as brevo:
        assert brevo.create_list("Kunden") == 12


# ── Kampagnen ────────────────────────────────────────────────────────────────

def test_create_email_campaign_baut_die_nutzdaten_in_brevos_schreibweise():
    gesehen = {}

    def handler(request):
        gesehen["path"] = request.url.path
        gesehen["body"] = json.loads(request.content)
        return _json_response(201, {"id": 55})

    with _service(handler) as brevo:
        campaign_id = brevo.create_email_campaign(
            title="August",
            subject="Neues von KOMPAGNON",
            html_content="<p>Hallo</p>",
            list_id=7,
        )

    assert campaign_id == 55
    assert gesehen["path"].endswith("/emailCampaigns")
    assert gesehen["body"]["name"] == "August"
    assert gesehen["body"]["htmlContent"] == "<p>Hallo</p>"
    assert gesehen["body"]["recipients"] == {"listIds": [7]}
    assert "scheduledAt" not in gesehen["body"], "ohne Termin darf kein Feld gesendet werden"


def test_geplante_kampagne_traegt_den_termin():
    gesehen = {}

    def handler(request):
        gesehen["body"] = json.loads(request.content)
        return _json_response(201, {"id": 56})

    with _service(handler) as brevo:
        brevo.create_email_campaign(
            title="September",
            subject="Vorschau",
            html_content="<p>Hallo</p>",
            list_id=7,
            scheduled_at="2026-09-01T08:00:00Z",
        )

    assert gesehen["body"]["scheduledAt"] == "2026-09-01T08:00:00Z"


def test_send_campaign_now_akzeptiert_die_leere_antwort():
    def handler(request):
        assert request.url.path.endswith("/emailCampaigns/55/sendNow")
        return httpx.Response(204)

    with _service(handler) as brevo:
        brevo.send_campaign_now(55)  # wirft nicht


def test_fehlgeschlagener_versand_wirft_statt_erfolg_zu_melden():
    """Der Ausloeser fuer diese Runde: ein Fehler darf nicht als 'gesendet' enden."""
    def handler(request):
        return _json_response(400, {"message": "Campaign is not in draft status"})

    with _service(handler) as brevo:
        with pytest.raises(BrevoError, match="draft status"):
            brevo.send_campaign_now(55)


# ── Statistik ────────────────────────────────────────────────────────────────

def test_stats_werden_als_anteile_geliefert():
    """Die Oberflaeche rechnet mal 100 — Brevo liefert Prozent, hier also /100."""
    def handler(request):
        return _json_response(200, {
            "id": 55,
            "statistics": {
                "globalStats": {
                    "sent": 200,
                    "delivered": 180,
                    "uniqueViews": 90,
                    "uniqueClicks": 18,
                    "opensRate": 50.0,
                    "unsubscriptions": 3,
                }
            },
        })

    with _service(handler) as brevo:
        stats = brevo.get_campaign_stats(55)

    assert stats["sentCount"] == 200
    assert stats["openRate"] == pytest.approx(0.5)
    assert stats["clickRate"] == pytest.approx(0.1)
    assert stats["unsubscriptions"] == 3


def test_stats_ohne_zustellungen_rechnen_nicht_durch_null():
    def handler(request):
        return _json_response(200, {
            "statistics": {"globalStats": {"sent": 0, "delivered": 0, "unsubscriptions": 0}}
        })

    with _service(handler) as brevo:
        stats = brevo.get_campaign_stats(55)

    assert stats["sentCount"] == 0
    assert stats["openRate"] is None
    assert stats["clickRate"] is None


def test_stats_ohne_statistikblock_liefern_leere_werte():
    """Frisch angelegte Kampagnen haben noch keine Statistik."""
    def handler(request):
        return _json_response(200, {"id": 55})

    with _service(handler) as brevo:
        stats = brevo.get_campaign_stats(55)

    assert stats == {"openRate": None, "clickRate": None, "unsubscriptions": None, "sentCount": None}
