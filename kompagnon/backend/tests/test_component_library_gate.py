"""
Das Tor zur Bibliothek.

Ein Block kommt auf drei Wegen herein — Neuanlage, „als Custom speichern",
Bearbeitung — und auf jedem gilt derselbe Vertrag. Verletzt er ihn, wird er
nicht verworfen (die Arbeit waere weg und der Grund unsichtbar), sondern
landet als Entwurf. Entwuerfe erreichen weder den Wireframe-Editor noch eine
Kundenseite; die Freigabe ist der Punkt, an dem der Vertrag zaehlt.
"""
import pytest

SAUBER = """<section data-block="{slug}" class="py-16 bg-white">
  <div class="mx-auto max-w-3xl px-4">
    <h2 class="text-3xl text-gray-900">{{{{headline}}}}</h2>
    <p class="text-gray-700">{{{{subtext}}}}</p>
  </div>
</section>"""

SLOTS = [
    {"key": "headline", "label": "Ueberschrift", "default": "Waermepumpe vom Meisterbetrieb"},
    {"key": "subtext",  "label": "Subtext",      "default": "Beratung, Foerderantrag und Einbau aus einer Hand."},
]


def _sauber(slug: str) -> str:
    return SAUBER.format(slug=slug)


def _mit_fremder_karte(slug: str) -> str:
    """Genau der Fehler, den zwei echte Bibliotheksbloecke heute machen."""
    return (f'<section data-block="{slug}" class="py-16">'
            f'<h2 class="text-3xl">{{{{headline}}}}</h2>'
            f'<iframe src="https://www.google.com/maps/embed?pb=x"></iframe>'
            f'</section>')


@pytest.fixture
def aufraeumen():
    """Legt die im Test erzeugten Bloecke danach wieder weg."""
    slugs: list[str] = []
    yield slugs
    from database import ComponentLibrary, SessionLocal
    db = SessionLocal()
    try:
        (db.query(ComponentLibrary)
           .filter(ComponentLibrary.slug.in_(slugs))
           .delete(synchronize_session=False))
        db.commit()
    finally:
        db.close()


def _anlegen(client, headers, slug, html, slots=SLOTS):
    return client.post("/api/components", headers=headers, json={
        "slug": slug, "name": f"Test {slug}", "category": "HERO",
        "html_template": html, "slots": slots,
    })


# ── Neuanlage ────────────────────────────────────────────────────────────

def test_sauberer_block_wird_freigegeben_angelegt(client, auth_headers, aufraeumen):
    slug = "pytest-gate-sauber"
    aufraeumen.append(slug)

    antwort = _anlegen(client, auth_headers, slug, _sauber(slug))

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["status"] == "approved"
    assert daten["contract"]["konform"] is True
    assert daten["contract"]["verstoesse"] == []


def test_block_mit_fremder_karte_landet_als_entwurf(client, auth_headers, aufraeumen):
    """Der iframe schickt die Besucher-IP an Google, bevor jemand klickt."""
    slug = "pytest-gate-karte"
    aufraeumen.append(slug)

    antwort = _anlegen(client, auth_headers, slug, _mit_fremder_karte(slug))

    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["status"] == "draft"
    assert daten["contract"]["konform"] is False
    assert any(v["regel"] == "R1" for v in daten["contract"]["verstoesse"])


def test_block_ohne_data_block_landet_als_entwurf(client, auth_headers, aufraeumen):
    """Ohne die Markierung findet der Editor den Block nicht wieder."""
    slug = "pytest-gate-ohne-marker"
    aufraeumen.append(slug)

    html = '<section class="py-16"><h2>{{headline}}</h2></section>'
    antwort = _anlegen(client, auth_headers, slug, html, slots=SLOTS[:1])

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["status"] == "draft"
    assert any(v["regel"] == "R2" for v in antwort.json()["contract"]["verstoesse"])


# ── Sichtbarkeit ─────────────────────────────────────────────────────────

def test_entwurf_erscheint_nicht_in_der_bibliothek(client, auth_headers, aufraeumen):
    slug = "pytest-gate-unsichtbar"
    aufraeumen.append(slug)
    _anlegen(client, auth_headers, slug, _mit_fremder_karte(slug))

    ohne = client.get("/api/components?include_html=false", headers=auth_headers)
    assert ohne.status_code == 200
    assert slug not in [b["slug"] for b in ohne.json()]

    mit = client.get("/api/components?include_html=false&include_drafts=true",
                     headers=auth_headers)
    assert slug in [b["slug"] for b in mit.json()]


# ── Freigabe ─────────────────────────────────────────────────────────────

def test_freigabe_eines_unsauberen_blocks_wird_verweigert(client, auth_headers, aufraeumen):
    slug = "pytest-gate-freigabe-nein"
    aufraeumen.append(slug)
    _anlegen(client, auth_headers, slug, _mit_fremder_karte(slug))

    antwort = client.post(f"/api/components/{slug}/approve", headers=auth_headers)

    assert antwort.status_code == 422, antwort.text
    detail = antwort.json()["detail"]
    assert detail["contract"]["konform"] is False
    assert any(v["regel"] == "R1" for v in detail["contract"]["verstoesse"])

    # und der Block ist danach immer noch Entwurf
    stand = client.get(f"/api/components/{slug}", headers=auth_headers).json()
    assert stand["status"] == "draft"


def test_nach_reparatur_ist_die_freigabe_moeglich(client, auth_headers, aufraeumen):
    slug = "pytest-gate-repariert"
    aufraeumen.append(slug)
    _anlegen(client, auth_headers, slug, _mit_fremder_karte(slug))

    repariert = client.put(f"/api/components/{slug}", headers=auth_headers,
                           json={"html_template": _sauber(slug)})
    assert repariert.status_code == 200, repariert.text
    assert repariert.json()["contract"]["konform"] is True

    freigabe = client.post(f"/api/components/{slug}/approve", headers=auth_headers)
    assert freigabe.status_code == 200, freigabe.text
    assert freigabe.json()["status"] == "approved"


def test_bearbeitung_kann_die_freigabe_wieder_entziehen(client, auth_headers, aufraeumen):
    """Sonst bliebe ein Block freigegeben, den eine spaetere Aenderung bricht."""
    slug = "pytest-gate-rueckfall"
    aufraeumen.append(slug)
    assert _anlegen(client, auth_headers, slug, _sauber(slug)).json()["status"] == "approved"

    kaputt = client.put(f"/api/components/{slug}", headers=auth_headers,
                        json={"html_template": _mit_fremder_karte(slug)})

    assert kaputt.status_code == 200, kaputt.text
    assert kaputt.json()["status"] == "draft"
    assert kaputt.json()["contract"]["konform"] is False


# ── Zweite Tuer: "als Custom speichern" ──────────────────────────────────

def test_custom_speichern_prueft_denselben_vertrag(client, auth_headers, aufraeumen):
    """Sonst kaeme unsauberes Markup einfach durch die andere Tuer herein."""
    slug = "pytest-gate-custom"
    aufraeumen.append(slug)

    antwort = client.post("/api/components/save-custom", headers=auth_headers, json={
        "new_slug": slug, "new_name": "Custom-Probe",
        "html_template": _mit_fremder_karte(slug), "slots": SLOTS[:1],
    })

    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["status"] == "draft"
    assert antwort.json()["contract"]["konform"] is False


# ── Der Generator-Job: Vertrag, Reparaturrunde, Befund ───────────────────
#
# Geprueft wird die Logik um den KI-Aufruf herum, nicht der Aufruf selbst:
# `_ki_runde` wird ersetzt, sodass kein Token flieszt und das Ergebnis
# vorhersagbar ist. Was hier zaehlt, ist die Entscheidung — reparieren,
# uebernehmen, verwerfen — und die faellt im Code, nicht im Modell.

class _Antwort:
    """Platzhalter fuer das Response-Objekt; nur `content` wird weitergereicht."""
    content = []


def _job(monkeypatch, runden):
    """Laesst den Generator-Job mit vorgegebenen KI-Antworten laufen."""
    from routers import component_library as cl

    folge = iter(runden)
    monkeypatch.setattr(cl, "_ki_runde",
                        lambda client, messages: (_Antwort(), next(folge)))
    monkeypatch.setattr(cl, "Anthropic", lambda api_key: object())

    job_id = "pytest-job"
    cl._component_gen_jobs.pop(job_id, None)
    cl._run_component_gen_job(
        job_id, cl.GenerateComponentRequest(category="HERO"), "schluessel")
    return cl._component_gen_jobs.pop(job_id)


def _ki_block(slug, html, slots=SLOTS):
    return {"slug": slug, "name": "Erzeugt", "html_template": html, "slots": slots}


def test_generator_liefert_sauberen_block_ohne_reparatur(monkeypatch):
    slug = "erzeugt-sauber"
    job = _job(monkeypatch, [_ki_block(slug, _sauber(slug))])

    assert job["status"] == "done", job
    assert job["result"]["contract"]["konform"] is True
    assert job["result"]["category"] == "HERO"


def test_generator_repariert_einen_verstoss(monkeypatch):
    """Die Verstoesse gehen zurueck ans Modell — eine Runde, dann ist Schluss."""
    slug = "erzeugt-repariert"
    job = _job(monkeypatch, [
        _ki_block(slug, _mit_fremder_karte(slug)),
        _ki_block(slug, _sauber(slug)),
    ])

    assert job["status"] == "done", job
    assert job["result"]["contract"]["konform"] is True
    assert "iframe" not in job["result"]["html_template"]


def test_generator_behaelt_die_bessere_der_beiden_fassungen(monkeypatch):
    """Eine Reparatur, die es schlimmer macht, wird nicht uebernommen."""
    slug = "erzeugt-schlechter"
    schlechter = (f'<section data-block="{slug}" id="x">'
                  f'<h2>{{{{headline}}}}</h2>'
                  f'<iframe src="https://maps.example/x"></iframe>'
                  f'<script>alert(1)</script></section>')
    job = _job(monkeypatch, [
        _ki_block(slug, _mit_fremder_karte(slug)),
        _ki_block(slug, schlechter),
    ])

    assert job["status"] == "done", job
    assert "script" not in job["result"]["html_template"]
    assert job["result"]["contract"]["konform"] is False


def test_generator_meldet_unbrauchbaren_slug_als_fehler(monkeypatch):
    job = _job(monkeypatch, [_ki_block("Kein Slug!", _sauber("egal"))])

    assert job["status"] == "error"
    assert "slug" in job["error"].lower()


def test_generator_meldet_fehlendes_pflichtfeld(monkeypatch):
    job = _job(monkeypatch, [{"slug": "ohne-html", "name": "x", "slots": []}])

    assert job["status"] == "error"
    assert "html_template" in job["error"]
