"""Stufe B: Ein Block, für diesen Kunden umgeschrieben.

Bis hierher war jede Kundenseite eine Permutation derselben Blöcke —
individuell wurden nur Texte und Farben. Eine Variante bringt eigenes Markup
mit (`html_override`) und wird beim Rendern dem Bibliotheks-Template
vorgezogen.

Dasselbe Tor wie bei der Bibliothek: Was nicht durch den Vertrag kommt, wird
nicht gespeichert. Der Unterschied ist die zusätzliche Bedingung, die eine
Variante erfüllen muss — sie darf die Slots nicht umbenennen. `generate-copy`
und der Slot-Editor lesen die Slot-Angaben des Bibliotheksblocks; erfindet die
Variante eigene Schlüssel, füllt sie niemand mehr.
"""
import time

import pytest

VARIANTE = """<section data-block="{slug}" class="py-20 bg-gray-50">
  <div class="mx-auto max-w-4xl px-4 text-center">
    <h2 class="text-4xl text-gray-900">{{{{headline}}}}</h2>
    <p class="mt-4 text-gray-700">{{{{subtext}}}}</p>
  </div>
</section>"""

SLOTS = [
    {"key": "headline", "label": "Ueberschrift", "default": "Waermepumpe"},
    {"key": "subtext", "label": "Subtext", "default": "Vom Meisterbetrieb."},
]


@pytest.fixture
def projekt_mit_block(client, auth_headers):
    """Ein Projekt mit einer Wireframe-Seite und einem Bibliotheksblock."""
    from database import ComponentLibrary, Lead, Project, SessionLocal, engine
    from routers.sitemap import SitemapPage

    # `sitemap_pages` steht in routers/sitemap.py — beim Anlegen des
    # Testschemas ist die Klasse noch nicht importiert. Stufe C liest daraus
    # den Seitennamen und den Zweck.
    SitemapPage.__table__.create(bind=engine, checkfirst=True)

    slug = "pytest-variante-block"
    db = SessionLocal()
    try:
        lead = Lead(company_name="Pytest Variante GmbH", email="variante@pytest.local")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        projekt = Project(lead_id=lead.id)
        db.add(projekt)
        db.commit()
        db.refresh(projekt)

        db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).delete()
        db.add(ComponentLibrary(
            slug=slug, name="Probe", category="HERO", status="approved",
            html_template=VARIANTE.format(slug=slug), slots=SLOTS, tags=[],
        ))
        db.commit()
        ids = (lead.id, projekt.id)
    finally:
        db.close()

    yield {"projekt": ids[1], "slug": slug}

    db = SessionLocal()
    try:
        db.query(ComponentLibrary).filter(ComponentLibrary.slug == slug).delete()
        db.query(Project).filter(Project.id == ids[1]).delete()
        db.query(Lead).filter(Lead.id == ids[0]).delete()
        db.commit()
    finally:
        db.close()


def _wireframe(slug, override=None):
    block = {"slug": slug, "order": 0, "slots": {}}
    if override is not None:
        block["html_override"] = override
    return {"pages": [{"page_id": 1, "page_name": "Start", "blocks": [block]}]}


def test_eine_saubere_variante_wird_gespeichert(client, auth_headers, projekt_mit_block):
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    eigenes = VARIANTE.format(slug=slug).replace("max-w-4xl", "max-w-6xl")

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug, eigenes))

    assert antwort.status_code == 200, antwort.text
    gespeichert = client.get(f"/api/projects/{p}/wireframe", headers=auth_headers).json()
    assert gespeichert["pages"][0]["blocks"][0]["html_override"] == eigenes


def test_ohne_variante_bleibt_alles_wie_bisher(client, auth_headers, projekt_mit_block):
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug))

    assert antwort.status_code == 200, antwort.text
    block = client.get(f"/api/projects/{p}/wireframe",
                       headers=auth_headers).json()["pages"][0]["blocks"][0]
    assert block.get("html_override") in (None, "")


def test_eine_variante_mit_fremder_karte_wird_abgewiesen(client, auth_headers,
                                                         projekt_mit_block):
    """Der Vertrag gilt für die Variante genauso — sonst wäre er zu umgehen,
    indem man den Block nicht in der Bibliothek, sondern beim Kunden schreibt."""
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    kaputt = (f'<section data-block="{slug}"><h2>{{{{headline}}}}</h2>'
              f'<iframe src="https://maps.example/x"></iframe></section>')

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug, kaputt))

    assert antwort.status_code == 422, antwort.text
    detail = antwort.json()["detail"]
    assert any(v["regel"] == "R1" for v in detail["verstoesse"])
    assert detail["slug"] == slug


def test_eine_variante_darf_die_slots_nicht_umbenennen(client, auth_headers,
                                                       projekt_mit_block):
    """Sonst füllt `generate-copy` sie nie — es liest die Angaben des
    Bibliotheksblocks, nicht das Markup der Variante."""
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    umbenannt = (f'<section data-block="{slug}" class="py-20">'
                 f'<h2>{{{{ueberschrift}}}}</h2></section>')

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug, umbenannt))

    assert antwort.status_code == 422, antwort.text
    verstoesse = antwort.json()["detail"]["verstoesse"]
    assert any("ueberschrift" in v["text"] for v in verstoesse)


def test_eine_variante_darf_slots_weglassen(client, auth_headers, projekt_mit_block):
    """Weniger ist erlaubt: Eine kürzere Fassung ohne Subtext ist eine
    Gestaltungsentscheidung, kein Fehler."""
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    kuerzer = (f'<section data-block="{slug}" class="py-20">'
               f'<h2 class="text-4xl text-gray-900">{{{{headline}}}}</h2></section>')

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug, kuerzer))

    assert antwort.status_code == 200, antwort.text


def test_eine_variante_muss_zum_block_gehoeren(client, auth_headers, projekt_mit_block):
    """Trägt sie eine fremde Markierung, findet der Editor den Block nicht mehr."""
    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    fremd = '<section data-block="ein-anderer"><h2>{{headline}}</h2></section>'

    antwort = client.post(f"/api/projects/{p}/wireframe", headers=auth_headers,
                          json=_wireframe(slug, fremd))

    assert antwort.status_code == 422, antwort.text
    assert any(v["regel"] == "R2" for v in antwort.json()["detail"]["verstoesse"])


# ── Der Endpunkt ─────────────────────────────────────────────────────────

def test_der_auftrag_laeuft_und_liefert_eine_variante(client, auth_headers,
                                                      projekt_mit_block, monkeypatch):
    """Geprueft wird der Weg durch den Endpunkt, nicht das Modell: `_ki_runde`
    wird ersetzt, es fliesst kein Token."""
    from routers import component_library as cl

    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]
    eigenes = VARIANTE.format(slug=slug).replace("py-20", "py-28")

    class _Antwort:
        content = []

    monkeypatch.setattr(cl, "_ki_runde", lambda client_, nachrichten: (
        _Antwort(), {"html_override": eigenes, "begruendung": "Luftiger."}))
    monkeypatch.setattr(cl, "Anthropic", lambda api_key: object())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-schluessel")

    start = client.post(f"/api/projects/{p}/wireframe/variant", headers=auth_headers,
                        json={"page_id": 1, "slug": slug, "wunsch": "kürzer"})
    assert start.status_code == 200, start.text
    job_id = start.json()["job_id"]

    # Der Thread ist bereits durch — der Job liegt im Store.
    for _ in range(50):
        job = cl._variant_jobs.get(job_id, {})
        if job.get("status") in ("done", "error"):
            break
        time.sleep(0.05)

    abgeholt = client.get(f"/api/projects/wireframe-variant-jobs/{job_id}",
                          headers=auth_headers)
    assert abgeholt.status_code == 200, abgeholt.text
    daten = abgeholt.json()
    assert daten["status"] == "done", daten
    assert daten["result"]["contract"]["konform"] is True
    assert daten["result"]["begruendung"] == "Luftiger."


def test_ohne_bibliotheksblock_gibt_es_keine_variante(client, auth_headers,
                                                      projekt_mit_block, monkeypatch):
    from routers import component_library as cl

    monkeypatch.setattr(cl, "Anthropic", lambda api_key: object())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-schluessel")

    antwort = client.post(
        f"/api/projects/{projekt_mit_block['projekt']}/wireframe/variant",
        headers=auth_headers, json={"page_id": 1, "slug": "gibt-es-nicht"})

    assert antwort.status_code == 404


# ── Stufe C: die Abfolge einer Seite ─────────────────────────────────────

def test_die_komposition_schlaegt_eine_abfolge_vor(client, auth_headers,
                                                   projekt_mit_block, monkeypatch):
    from routers import component_library as cl

    p, slug = projekt_mit_block["projekt"], projekt_mit_block["slug"]

    class _Antwort:
        content = []

    monkeypatch.setattr(cl, "_ki_runde", lambda client_, nachrichten: (_Antwort(), {
        "aufbau": "Vom Versprechen zum Termin.",
        "sections": [{"slug": slug, "rolle": "Hero", "auftrag": "Versprechen klar."}],
    }))
    monkeypatch.setattr(cl, "Anthropic", lambda api_key: object())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-schluessel")

    start = client.post(f"/api/projects/{p}/wireframe/compose", headers=auth_headers,
                        json={"page_id": 1})
    assert start.status_code == 200, start.text
    job_id = start.json()["job_id"]

    for _ in range(50):
        if cl._compose_jobs.get(job_id, {}).get("status") in ("done", "error"):
            break
        time.sleep(0.05)

    daten = client.get(f"/api/projects/wireframe-compose-jobs/{job_id}",
                       headers=auth_headers).json()
    assert daten["status"] == "done", daten
    assert daten["result"]["contract"]["konform"] is True
    section = daten["result"]["sections"][0]
    assert section["slug"] == slug
    # Der Name aus der Bibliothek faehrt mit — sonst zeigt die Oberflaeche Slugs.
    assert section["name"] == "Probe"


def test_ein_entwurf_taucht_in_der_komposition_nicht_auf(client, auth_headers,
                                                         projekt_mit_block, monkeypatch):
    """Was nicht freigegeben ist, darf auch nicht vorgeschlagen werden."""
    from database import ComponentLibrary, SessionLocal
    from routers import component_library as cl

    p = projekt_mit_block["projekt"]
    entwurf = "pytest-komposition-entwurf"
    db = SessionLocal()
    try:
        db.add(ComponentLibrary(slug=entwurf, name="Entwurf", category="HERO",
                                status="draft", html_template="<section></section>",
                                slots=[], tags=[]))
        db.commit()
    finally:
        db.close()

    gesehen = {}

    class _Antwort:
        content = []

    def _runde(client_, nachrichten):
        gesehen["prompt"] = nachrichten[0]["content"]
        return _Antwort(), {"aufbau": "x", "sections": [
            {"slug": projekt_mit_block["slug"], "rolle": "Hero", "auftrag": "y"}]}

    monkeypatch.setattr(cl, "_ki_runde", _runde)
    monkeypatch.setattr(cl, "Anthropic", lambda api_key: object())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "pytest-schluessel")

    try:
        start = client.post(f"/api/projects/{p}/wireframe/compose",
                            headers=auth_headers, json={"page_id": 1})
        job_id = start.json()["job_id"]
        for _ in range(50):
            if cl._compose_jobs.get(job_id, {}).get("status") in ("done", "error"):
                break
            time.sleep(0.05)
        client.get(f"/api/projects/wireframe-compose-jobs/{job_id}", headers=auth_headers)

        assert entwurf not in gesehen.get("prompt", "")
    finally:
        db = SessionLocal()
        try:
            db.query(ComponentLibrary).filter(ComponentLibrary.slug == entwurf).delete()
            db.commit()
        finally:
            db.close()
