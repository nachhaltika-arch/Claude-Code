# -*- coding: utf-8 -*-
"""Die Kampagne reist mit — von der Anzeige bis in den Lead (15.09.2026).

**Der Anlass.** Am 15.09. war an den Render-Protokollen gemessen worden: rund
71 Besucher aus der Anzeige, **null** abgeschickte Analysen (L-195). Die
naechste Frage ist nicht mehr „wie viele", sondern „welche Karte" — und die
laesst sich ohne diese Strecke nicht beantworten. Am Monatsende stuende sonst
fest, wie viele Leads kamen, aber nicht, welche Tonlage sie gebracht hat.

**Drei Ebenen, und jede kann fuer sich stillschweigend ausfallen:**

    Landingpage   haengt die fuenf Werte an die iframe-Adresse
    Widget        liest sie aus der eigenen Adresse und sendet sie mit
    Backend       schreibt sie an den Lead und gibt sie an Brevo weiter

Faellt eine aus, faellt nichts auf: Es wird nur nichts mehr gemessen. Deshalb
prueft diese Datei jede Ebene einzeln **und** den Durchlauf am Ende.

**Warum genau fuenf und nicht beliebige Parameter.** Was durchgereicht wird,
landet in der Datenbank und bei Brevo. Eine offene Liste hiesse, dass jeder,
der einen Link auf die Landingpage setzt, Werte in unsere Daten schreibt.
"""
import pathlib
import re

import pytest

from database import Lead, SessionLocal

EMBED = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "public" / "embed"
WIDGET = EMBED / "widget.js"
README = EMBED / "README.md"
LANDINGPAGE = (pathlib.Path(__file__).resolve().parents[3]
               / "docs" / "landingpage" / "websprint-landingpage.html")

FELDER = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")


def _entschluesselt(pfad: pathlib.Path) -> str:
    """Der Bundler-Export der Landingpage liegt escaped — auch Nicht-ASCII."""
    text = pfad.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), text)
    return text.replace("\\n", "\n").replace('\\"', '"')


@pytest.fixture(scope="module")
def widget():
    return WIDGET.read_text(encoding="utf-8")


@pytest.fixture(scope="module", params=["readme", "landingpage"])
def traegerseite(request):
    """Beide Fassungen: die Anleitung und die Seite, die hochgeladen wird."""
    if request.param == "landingpage":
        return _entschluesselt(LANDINGPAGE)
    for teil in README.read_text(encoding="utf-8").split("```html")[1:]:
        rumpf = teil.split("```", 1)[0]
        if "herkunft" in rumpf:
            return rumpf
    raise AssertionError("Kein Einbau-Block im README")


# ── Ebene 3: Die Trägerseite reicht durch ────────────────────────────

def test_die_traegerseite_reicht_alle_fuenf_durch(traegerseite):
    for feld in FELDER:
        assert f"'{feld}'" in traegerseite, f"{feld} fehlt in der Trägerseite"


def test_sie_reicht_nur_diese_fuenf_durch(traegerseite):
    """**Keine offene Liste.** Wer beliebige Parameter durchreicht, laesst
    jeden, der einen Link setzt, in unsere Datenbank schreiben."""
    block = traegerseite.split("function herkunft()", 1)[1].split("})();", 1)[0]
    assert "forEach" in block
    # Die Schleife laeuft ueber eine feste Liste, nicht ueber eigene Parameter
    assert "eigene.forEach" not in block
    assert "for (var" not in block


def test_die_laenge_wird_begrenzt(traegerseite):
    block = traegerseite.split("function herkunft()", 1)[1].split("})();", 1)[0]
    assert "200" in block, "Ohne Grenze passt der Wert nicht in die Spalte"


# ── Ebene 2: Das Widget liest und sendet ─────────────────────────────

def test_das_widget_liest_die_fuenf_aus_seiner_adresse(widget):
    assert "function utmParam" in widget
    for feld in FELDER:
        assert f"utmParam('{feld}')" in widget


def test_das_widget_sendet_sie_mit(widget):
    rumpf = widget.split("body: JSON.stringify({", 1)[1].split("})", 1)[0]
    for feld in FELDER:
        assert f"{feld}:" in rumpf, f"{feld} fehlt im Absende-Rumpf"


def test_die_pruefung_laesst_kampagnennamen_durch(widget):
    """`traegerParam` waere zu eng: Sie erlaubt nur `A-Za-z0-9._-`, und ein
    Kampagnenname traegt Leerzeichen und Umlaute. Eine eigene Pruefung, aber
    keine offene."""
    rumpf = widget.split("function utmParam", 1)[1][:400]
    assert "200" in rumpf
    assert "<>" in rumpf or "\\r\\n" in rumpf or "[<>" in rumpf


# ── Ebene 1 und 4: Schnittstelle und Datenbank ───────────────────────

def _lead_weg(domain: str) -> None:
    """Der Lead wird ueber die Domain wiedergefunden. Ein Rest aus einem
    frueheren Lauf machte den Test gruen, ohne dass etwas geschrieben wurde."""
    db = SessionLocal()
    try:
        for lead in db.query(Lead).filter(Lead.website_url.ilike(f"%{domain}%")).all():
            db.delete(lead)
        db.commit()
    finally:
        db.close()


def test_die_schnittstelle_nimmt_sie_entgegen(client, monkeypatch):
    """**Ebene 2 des Verbindungschecks:** Das Backend darf sie nicht
    abweisen — ein unbekanntes Feld liesse die ganze Anfrage scheitern."""
    import routers.audit as audit_router

    async def keine_analyse(*_a, **_k):
        return {"id": None}

    monkeypatch.setattr(audit_router, "start_audit", keine_analyse)
    _lead_weg("example.com")

    antwort = client.post("/api/widget/audit", json={
        "email": "utm-pruefung@example.de",
        "website_url": "https://example.com",
        "utm_source": "facebook", "utm_medium": "paid_social",
        "utm_campaign": "websprint-audit-0926",
        "utm_content": "b6k-karte-3", "utm_term": "",
    })
    assert antwort.status_code == 200, antwort.text


def test_der_lead_traegt_die_kampagne(client, monkeypatch):
    """**Ebene 1 und 4 in einem:** Ein Aufruf mit `utm_content=b6k-karte-3`
    erzeugt einen Lead, an dem `b6k-karte-3` steht. Das ist die Frage, die
    am Monatsende zaehlt — welche Karte hat verkauft."""
    import routers.audit as audit_router

    async def keine_analyse(*_a, **_k):
        return {"id": None}

    monkeypatch.setattr(audit_router, "start_audit", keine_analyse)
    _lead_weg("example.org")

    antwort = client.post("/api/widget/audit", json={
        "email": "karte3@example.de",
        "website_url": "https://example.org",
        "utm_source": "facebook", "utm_medium": "paid_social",
        "utm_campaign": "websprint-audit-0926",
        "utm_content": "b6k-karte-3", "utm_term": "handwerk",
    })
    assert antwort.status_code == 200, antwort.text

    db = SessionLocal()
    try:
        lead = (db.query(Lead)
                .filter(Lead.website_url.ilike("%example.org%"))
                .order_by(Lead.id.desc()).first())
        assert lead is not None, "Kein Lead angelegt"
        assert lead.utm_content == "b6k-karte-3"
        assert lead.utm_source == "facebook"
        assert lead.utm_campaign == "websprint-audit-0926"
        assert lead.utm_term == "handwerk"
    finally:
        db.close()


def test_ein_zu_langer_wert_kostet_keine_analyse(client, monkeypatch):
    """**Gekuerzt, nicht abgewiesen.** Ein zu langer Kampagnenname ist der
    Fehler dessen, der den Link gebaut hat — der Besucher darf ihn nicht
    mit seiner Analyse bezahlen."""
    import routers.audit as audit_router

    async def keine_analyse(*_a, **_k):
        return {"id": None}

    monkeypatch.setattr(audit_router, "start_audit", keine_analyse)
    _lead_weg("example.net")

    antwort = client.post("/api/widget/audit", json={
        "email": "langer-wert@example.de",
        "website_url": "https://example.net",
        "utm_campaign": "x" * 500,
    })
    assert antwort.status_code == 200, antwort.text

    db = SessionLocal()
    try:
        lead = (db.query(Lead)
                .filter(Lead.website_url.ilike("%example.net%"))
                .order_by(Lead.id.desc()).first())
        assert lead is not None
        assert len(lead.utm_campaign) == 200
    finally:
        db.close()


# ── Brevo ─────────────────────────────────────────────────────────────

def test_brevo_kennt_die_fuenf_merkmale():
    """**In Brevo muss nichts von Hand angelegt werden** — `ensure_attributes`
    legt fehlende Merkmale selbst an, und die Schleife darueber laeuft ueber
    genau diese Liste. Fehlt eines hier, weist Brevo den **ganzen** Kontakt
    ab, nicht nur das Merkmal."""
    from services import widget_crm

    namen = {n for n, _typ in widget_crm.MERKMALE}
    for feld in FELDER:
        assert feld.upper() in namen, f"{feld.upper()} fehlt in MERKMALE"


def test_leere_werte_gehen_nicht_an_brevo(monkeypatch):
    """Ein leeres `UTM_CONTENT` in Brevo saehe aus wie „Kampagne ohne
    Karte". Fehlt es, ist sichtbar, dass nichts erhoben wurde."""
    from services import widget_crm

    gesehen = {}

    class _Brevo:
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

        def ensure_attributes(self, *_a, **_k):
            # Seit dem 20.09.2026 ruft `uebertrage` diese Methode statt
            # `ensure_attribute` je Merkmal. Die Nachbildung hier hatte das
            # nicht mitbekommen und meldete einen Brevo-Fehlschlag, wo
            # keiner war — eine Nachbildung altert mit dem Gegenstand.
            pass

        def create_contact(self, **kwargs):
            gesehen.update(kwargs.get("attributes") or {})

    monkeypatch.setattr("services.brevo_service.BrevoService", _Brevo)
    widget_crm.uebertrage("a@example.de", 7, website="x.de",
                          utm={"utm_source": "facebook", "utm_content": ""})

    assert gesehen.get("UTM_SOURCE") == "facebook"
    assert "UTM_CONTENT" not in gesehen
