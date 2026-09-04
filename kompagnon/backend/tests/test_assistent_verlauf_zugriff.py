"""Ein Gespraechsverlauf gehoert dem Betrieb, nicht jedem Angemeldeten.

**Der Befund (31.08.2026, L-14).** `GET /api/assistant/conversations/{id}` und
`POST /…/escalate` trugen nur `require_any_auth` — das heisst „irgendwer ist
angemeldet". Wer die Nummer hochzaehlte, las fremde Gespraeche: Betriebsname,
Inhalt jeder Nachricht und die Kosten je Aufruf. Eskalieren konnte er sie auch,
und dabei faehrt der Verlauf im Klartext ans Team.

**Gefunden, weil der Endpunkt angeschlossen werden sollte.** Er hatte bis dahin
keinen Aufrufer; ohne den Auftrag „der Assistent soll sich erinnern" waere die
Luecke stehengeblieben. Ein ungerufener Endpunkt ist nicht ungefaehrlich — er
ist nur unbeobachtet.

Die Pruefung ist dieselbe wie in `leads_portal.lead_oder_403`: **nicht** „ist
Kunde", sondern „gehoert nicht zum Innendienst". Die Umkehrung stammt vom
18.08.2026, als die erste Fassung die Rolle `nutzer` durchliess.
"""
import pytest

from database import AssistantConversation, Lead, SessionLocal


@pytest.fixture()
def fremdes_gespraech(app):
    """Ein Gespraech an einem Betrieb, der dem Testkunden nicht gehoert."""
    db = SessionLocal()
    try:
        lead = Lead(company_name="Fremder Betrieb Assistent-Test")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        g = AssistantConversation(lead_id=lead.id, modus="kunde")
        db.add(g)
        db.commit()
        db.refresh(g)
        yield g.id, lead.id
        db.query(AssistantConversation).filter(
            AssistantConversation.id == g.id).delete()
        db.query(Lead).filter(Lead.id == lead.id).delete()
        db.commit()
    finally:
        db.close()


def test_ein_fremdes_gespraech_ist_gesperrt(client, kunde_headers, fremdes_gespraech):
    gespraech_id, _ = fremdes_gespraech

    antwort = client.get(f"/api/assistant/conversations/{gespraech_id}",
                         headers=kunde_headers)

    assert antwort.status_code == 403, antwort.text


def test_ein_fremdes_gespraech_laesst_sich_auch_nicht_eskalieren(
        client, kunde_headers, fremdes_gespraech):
    """Die zweite Haelfte — sonst waere der Verlauf gesperrt und der Weg ans
    Team offen, und das ist derselbe Inhalt."""
    gespraech_id, _ = fremdes_gespraech

    antwort = client.post(f"/api/assistant/conversations/{gespraech_id}/escalate",
                          json={"anliegen": "fremd"}, headers=kunde_headers)

    assert antwort.status_code == 403, antwort.text


def test_der_innendienst_darf_hinein(client, auth_headers, fremdes_gespraech):
    """Die positive Gegenprobe.

    Ohne sie waeren die Tests darueber auch dann gruen, wenn die Pruefung
    **jeden** aussperrte — und dann waere der Endpunkt kaputt statt sicher.
    """
    gespraech_id, lead_id = fremdes_gespraech

    antwort = client.get(f"/api/assistant/conversations/{gespraech_id}",
                         headers=auth_headers)

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["lead_id"] == lead_id


def test_ein_gespraech_das_es_nicht_gibt_bleibt_404(client, auth_headers):
    """404 und 403 duerfen nicht zusammenfallen.

    Der Innendienst geht denselben Weg und muss „gibt es nicht" von „gehoert
    dir nicht" unterscheiden koennen.
    """
    assert client.get("/api/assistant/conversations/999999",
                      headers=auth_headers).status_code == 404


def test_ohne_anmeldung_geht_gar_nichts(client, fremdes_gespraech):
    gespraech_id, _ = fremdes_gespraech

    assert client.get(
        f"/api/assistant/conversations/{gespraech_id}").status_code in (401, 403)
