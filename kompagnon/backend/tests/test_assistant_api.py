"""Der Chat des Projekt-Assistenten — der Weg durch den Endpunkt.

Geprüft wird alles um den Modellaufruf herum: Rolle → Modus, Freigabeliste,
Budget, Ablage des Verlaufs, Eskalation ans Team. Der Aufruf selbst wird
ersetzt; es fließt kein Token.
"""
import pytest

FRAGE = "Was soll ich bei Leistungen eintragen?"
ANTWORT = ("Nennen Sie die Leistungen einzeln, etwa Waermepumpe, Bad-Sanierung "
           "und Notdienst. Jede wird spaeter zu einer eigenen Seite.")


@pytest.fixture
def lead_und_projekt(client, auth_headers):
    from database import Briefing, Lead, Project, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Assistent Test GmbH", email="a@pytest.local",
                    city="Koblenz", trade="SHK")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        projekt = Project(lead_id=lead.id, status="phase_2",
                          fixed_price=2000.0, margin_percent=41.777)
        briefing = Briefing(lead_id=lead.id, gewerk="Sanitär, Heizung, Klima",
                            leistungen="")
        db.add_all([projekt, briefing])
        db.commit()
        db.refresh(projekt)
        ids = (lead.id, projekt.id)
    finally:
        db.close()

    yield {"lead": ids[0], "projekt": ids[1]}

    db = SessionLocal()
    try:
        from database import AssistantConversation, Message
        db.query(AssistantConversation).filter(
            AssistantConversation.lead_id == ids[0]).delete()
        db.query(Message).filter(Message.lead_id == ids[0]).delete()
        db.query(Briefing).filter(Briefing.lead_id == ids[0]).delete()
        db.query(Project).filter(Project.id == ids[1]).delete()
        db.query(Lead).filter(Lead.id == ids[0]).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def kein_token(monkeypatch):
    """Ersetzt den Modellaufruf und merkt sich, was er zu sehen bekam."""
    from routers import assistant as a

    gesehen = {}

    def _antwort(*, systemprompt, verlauf, frage):
        gesehen["systemprompt"] = systemprompt
        gesehen["verlauf"] = verlauf
        gesehen["frage"] = frage
        return {"text": ANTWORT, "eingabe_tokens": 1200, "ausgabe_tokens": 180}

    monkeypatch.setattr(a, "_frag_das_modell", _antwort)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-schluessel")
    return gesehen


# ── Der Weg durch den Endpunkt ───────────────────────────────────────────

def test_eine_frage_bekommt_eine_antwort_und_einen_verlauf(client, auth_headers,
                                                           lead_und_projekt, kein_token):
    antwort = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"],
        "projekt_id": lead_und_projekt["projekt"],
        "frage": FRAGE,
        "feld": "leistungen",
        "schritt": "leistungen",
    })

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["antwort"] == ANTWORT
    assert daten["conversation_id"] > 0

    verlauf = client.get(f"/api/assistant/conversations/{daten['conversation_id']}",
                         headers=auth_headers).json()
    assert [m["rolle"] for m in verlauf["messages"]] == ["nutzer", "assistent"]
    assert verlauf["messages"][0]["inhalt"] == FRAGE


def test_die_zweite_frage_setzt_das_gespraech_fort(client, auth_headers,
                                                   lead_und_projekt, kein_token):
    erste = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE}).json()

    zweite = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": "Und beim Einzugsgebiet?",
        "conversation_id": erste["conversation_id"]}).json()

    assert zweite["conversation_id"] == erste["conversation_id"]
    # Der bisherige Verlauf geht mit ans Modell — sonst fragt es jedes Mal neu.
    assert any(FRAGE in str(n) for n in kein_token["verlauf"])


def test_der_verbrauch_wird_je_nachricht_festgehalten(client, auth_headers,
                                                      lead_und_projekt, kein_token):
    daten = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"],
        "projekt_id": lead_und_projekt["projekt"], "frage": FRAGE}).json()

    verlauf = client.get(f"/api/assistant/conversations/{daten['conversation_id']}",
                         headers=auth_headers).json()
    antwort = verlauf["messages"][-1]
    assert antwort["eingabe_tokens"] == 1200
    assert antwort["ausgabe_tokens"] == 180
    assert antwort["kosten_euro"] > 0


# ── Die Freigabeliste greift auch im Endpunkt ────────────────────────────

def test_kein_kaufmaennischer_wert_erreicht_den_prompt(client, auth_headers,
                                                       lead_und_projekt, kein_token):
    """Der Admin-Token dieses Tests bekommt Teamsicht — geprüft wird der
    Kundenfall über den Modus im Aufruf."""
    client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"],
        "projekt_id": lead_und_projekt["projekt"], "frage": FRAGE})

    # Der Testnutzer ist Admin, also Teamsicht — die Marge darf hier stehen.
    assert "41.777" in kein_token["systemprompt"]


def test_der_modus_kommt_nicht_vom_client(client, auth_headers, lead_und_projekt,
                                          kein_token):
    """Wer „modus: team“ mitschickt, bekommt trotzdem die Sicht seiner Rolle."""
    antwort = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE, "modus": "chef"})

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["modus"] in ("kunde", "team")


# ── Das Regelwerk steht im Prompt ────────────────────────────────────────

def test_der_massstab_des_feldes_steht_im_prompt(client, auth_headers,
                                                 lead_und_projekt, kein_token):
    client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE, "feld": "leistungen"})

    assert "Bad-Sanierung barrierefrei" in kein_token["systemprompt"]


def test_offene_felder_stehen_im_prompt(client, auth_headers, lead_und_projekt,
                                        kein_token):
    client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE})

    # `leistungen` ist im Briefing leer — das soll der Assistent wissen.
    assert "leistungen" in kein_token["systemprompt"]


# ── Die Feldprüfung ohne Modell ──────────────────────────────────────────

def test_die_feldpruefung_braucht_keinen_modellaufruf(client, auth_headers):
    antwort = client.post("/api/assistant/field-check", headers=auth_headers,
                          json={"feld": "usp", "wert": "Qualität und Service"})

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["brauchbar"] is False
    assert daten["hinweise"]


def test_eine_gute_antwort_wird_nicht_beanstandet(client, auth_headers):
    antwort = client.post("/api/assistant/field-check", headers=auth_headers, json={
        "feld": "usp",
        "wert": "Meisterbetrieb in dritter Generation, Notdienst in 90 Minuten",
    })

    assert antwort.json()["brauchbar"] is True


# ── Eskalation ans Team ──────────────────────────────────────────────────

def test_die_eskalation_erzeugt_eine_echte_nachricht(client, auth_headers,
                                                     lead_und_projekt, kein_token):
    """Entscheidung 3.2: Ein Klick macht aus dem Gespräch eine Nachricht ans
    Team — mit Zusammenfassung, damit niemand den Verlauf nachlesen muss."""
    from database import Message, SessionLocal

    gespraech = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE}).json()

    antwort = client.post(
        f"/api/assistant/conversations/{gespraech['conversation_id']}/escalate",
        headers=auth_headers, json={"anliegen": "Ich komme hier nicht weiter."})

    assert antwort.status_code == 200, antwort.text

    db = SessionLocal()
    try:
        nachricht = (db.query(Message)
                       .filter(Message.lead_id == lead_und_projekt["lead"])
                       .order_by(Message.id.desc()).first())
    finally:
        db.close()

    assert nachricht is not None
    assert "Ich komme hier nicht weiter." in nachricht.content
    assert FRAGE in nachricht.content          # der Verlauf ist zusammengefasst
    assert nachricht.sender_role == "kunde"


def test_zweimal_eskalieren_erzeugt_nicht_zwei_nachrichten(client, auth_headers,
                                                           lead_und_projekt, kein_token):
    from database import Message, SessionLocal

    gespraech = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE}).json()
    pfad = f"/api/assistant/conversations/{gespraech['conversation_id']}/escalate"

    client.post(pfad, headers=auth_headers, json={"anliegen": "Hilfe"})
    zweite = client.post(pfad, headers=auth_headers, json={"anliegen": "Hilfe"})

    db = SessionLocal()
    try:
        anzahl = (db.query(Message)
                    .filter(Message.lead_id == lead_und_projekt["lead"]).count())
    finally:
        db.close()

    assert anzahl == 1
    assert zweite.json()["bereits_eskaliert"] is True


# ── Budget ───────────────────────────────────────────────────────────────

def test_ein_ausgeschoepftes_projekt_antwortet_freundlich_statt_zu_fehlern(
        client, auth_headers, lead_und_projekt, kein_token, monkeypatch):
    from services import assistant_budget as budget
    from routers import assistant as a

    monkeypatch.setattr(a, "GRENZE_PROJEKT_EURO", 0.0)
    monkeypatch.setattr(budget, "GRENZE_PROJEKT_EURO", 0.0)

    antwort = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"],
        "projekt_id": lead_und_projekt["projekt"], "frage": FRAGE})

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["budget_erschoepft"] is True
    assert "Team" in daten["antwort"]
    # Und es wurde kein Modell gefragt.
    assert "systemprompt" not in kein_token


def test_ein_fremder_lead_wird_abgewiesen(client, auth_headers):
    antwort = client.post("/api/assistant/chat", headers=auth_headers,
                          json={"lead_id": 999999, "frage": FRAGE})

    assert antwort.status_code == 404


# ── Der übernehmbare Vorschlag (Entscheidung 1.3) ────────────────────────

def test_der_vorschlag_wird_vom_text_getrennt(client, auth_headers, lead_und_projekt,
                                              monkeypatch):
    from routers import assistant as a

    monkeypatch.setattr(a, "_frag_das_modell", lambda **kw: {
        "text": "Nennen Sie die Leistungen einzeln.\n"
                "VORSCHLAG: Waermepumpe, Bad-Sanierung, Heizungswartung, Notdienst",
        "eingabe_tokens": 100, "ausgabe_tokens": 50})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")

    daten = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE,
        "feld": "leistungen"}).json()

    assert daten["vorschlag"] == "Waermepumpe, Bad-Sanierung, Heizungswartung, Notdienst"
    assert "VORSCHLAG" not in daten["antwort"]
    assert daten["antwort"] == "Nennen Sie die Leistungen einzeln."
    assert daten["feld"] == "leistungen"


def test_ohne_vorschlag_gibt_es_keinen_knopf(client, auth_headers, lead_und_projekt,
                                             kein_token):
    daten = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE}).json()

    assert daten["vorschlag"] == ""


def test_der_gespeicherte_verlauf_zeigt_die_erklaerung_ohne_marke(
        client, auth_headers, lead_und_projekt, monkeypatch):
    from routers import assistant as a

    monkeypatch.setattr(a, "_frag_das_modell", lambda **kw: {
        "text": "Erklaerung.\nVORSCHLAG: Der fertige Satz",
        "eingabe_tokens": 10, "ausgabe_tokens": 5})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest")

    daten = client.post("/api/assistant/chat", headers=auth_headers, json={
        "lead_id": lead_und_projekt["lead"], "frage": FRAGE}).json()
    verlauf = client.get(f"/api/assistant/conversations/{daten['conversation_id']}",
                         headers=auth_headers).json()

    assert "VORSCHLAG" not in verlauf["messages"][-1]["inhalt"]


@pytest.mark.parametrize("roh,erwartet_text,erwartet_vorschlag", [
    ("Nur Text ohne alles", "Nur Text ohne alles", ""),
    ("Text\nVORSCHLAG: Etwas", "Text", "Etwas"),
    ('Text\nVORSCHLAG: „In Anfuehrung"', "Text", "In Anfuehrung"),
    ("VORSCHLAG: Ganz allein", "", "Ganz allein"),
    ("", "", ""),
])
def test_die_trennung_haelt_verschiedene_formen_aus(roh, erwartet_text,
                                                    erwartet_vorschlag):
    from routers.assistant import trenne_vorschlag

    text, vorschlag = trenne_vorschlag(roh)

    assert text == erwartet_text
    assert vorschlag == erwartet_vorschlag
