# -*- coding: utf-8 -*-
"""Es gibt genau einen Scraper (Entscheidung David, 26.08.2026).

**Der Befund aus L-105.** Drei Wege lasen dieselbe Kundenwebsite aus:

* `/api/crawler/…` — den ruft die Oberfläche (`AnalyseCentrale`), Ablage in
  `website_content_cache`;
* `routers/content_scraper_router.py` — fünf Routen, die niemand ruft, plus
  ein automatischer Lauf beim Anlegen eines Projekts, Ablage in
  `projects.scrape_full_data`;
* `GET /api/projects/{id}/scrape-content` — noch einer, Ablage in
  `projects.scraped_content`.

Von den beiden letzten las **niemand** die Ergebnisse. `scrape_full_data`
wurde nur innerhalb seines eigenen Moduls gelesen, `scraped_content` von
keiner Zeile im Bestand.

**Davids Entscheidung: „der crawler ist der richtige, den anderen weg."**

**Was ich dabei zuerst falsch gesagt habe, und warum es hier steht.** Ich
hatte gemeldet, der Schritt „Content-Vollanalyse" stehe immer auf offen, weil
nur der entfernte Scraper `scrape_full_at` setze. Das Ergebnis stimmte, die
Begründung nicht: Der Lauf **fand** statt (Hintergrundaufgabe beim Anlegen),
nur trug `GET /api/projects/{id}` das Feld nie in seine Antwort — die
Prozesskette las `undefined`. Ein Wert, der nie über die Schnittstelle geht,
ist für die Oberfläche so gut wie nicht vorhanden.

Deshalb reicht das Löschen nicht: Der Schritt braucht ein Signal, und zwar
das des Crawlers.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")

WEG = (
    "/api/projects/{project_id}/scrape-full",
    "/api/projects/{project_id}/scrape-pages",
    "/api/projects/{project_id}/scrape-status",
    "/api/projects/{project_id}/scraped-content",
    "/api/projects/{project_id}/scrape-content",
)


def _pfade():
    """Alle Pfade — ueber `openapi()`, **nicht** ueber `app.routes`.

    `app.routes` zeigt unter Starlette 1.4 nur die oberste Ebene: 88 statt
    414. Eine Zusicherung „dieser Pfad ist weg" waere darauf immer erfuellt.
    Genau daran war der Waechter gegen die Rueckkehr des Abnahme-Endpunkts
    wertlos, bis es am selben Abend auffiel.
    """
    from main import app as anwendung

    return set(anwendung.openapi()["paths"])


class TestDerZweiteUndDritteWegSindWeg:
    @pytest.mark.parametrize("pfad", WEG)
    def test_die_route_gibt_es_nicht_mehr(self, pfad):
        assert pfad not in _pfade()

    def test_und_es_bleibt_einer_uebrig(self):
        """Gegenprobe. Waeren **alle** weg, waere der Test oben gruen und das
        Merkmal verschwunden — der Crawler ist der, den die Oberflaeche
        ruft."""
        pfade = _pfade()

        assert "/api/crawler/scrape-content/{customer_id}" in pfade
        assert "/api/crawler/start/{customer_id}" in pfade

    def test_niemand_importiert_den_entfernten_lauf_mehr(self):
        """`projects.py` importierte `_run_content_scrape`, ohne ihn je zu
        benutzen — ein toter Import haelt ein totes Modul am Leben."""
        import pathlib

        wurzel = pathlib.Path(__file__).resolve().parent.parent
        treffer = [
            str(p.relative_to(wurzel))
            for p in wurzel.rglob("*.py")
            if "venv" not in p.parts and "tests" not in p.parts
            and "_run_content_scrape" in p.read_text(encoding="utf-8",
                                                     errors="ignore")
        ]

        assert treffer == [], f"noch verdrahtet in: {treffer}"


class TestDerSchrittBekommtEinSignal:
    def test_die_projektauskunft_traegt_es(self, client, auth_headers, projekt):
        """Ohne dieses Feld liest die Prozesskette `undefined` und der
        Schritt steht ewig auf offen — genau der Zustand vorher, nur mit
        einem anderen Feldnamen."""
        antwort = client.get(f"/api/projects/{projekt}", headers=auth_headers)

        assert antwort.status_code == 200, antwort.text
        assert "content_analysiert_am" in antwort.json()

    def test_ohne_analyse_ist_es_leer(self, client, auth_headers, projekt):
        assert client.get(f"/api/projects/{projekt}",
                          headers=auth_headers).json()["content_analysiert_am"] is None

    def test_nach_einer_analyse_steht_ein_zeitpunkt_darin(
            self, client, auth_headers, projekt, analysiert):
        wert = client.get(f"/api/projects/{projekt}",
                          headers=auth_headers).json()["content_analysiert_am"]

        assert wert and wert.startswith("20")


@pytest.fixture
def projekt(app):
    from database import Lead, Project, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Scraper Probe GmbH",
                    email="probe@scraper-test.local",
                    website_url="https://scraper-test.local/")
        db.add(lead)
        db.commit()
        db.refresh(lead)

        p = Project(lead_id=lead.id, status="phase_2", fixed_price=2000.0)
        db.add(p)
        db.commit()
        db.refresh(p)
        kennung, lead_kennung = p.id, lead.id
    finally:
        db.close()

    yield kennung

    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM website_content_cache WHERE customer_id = :l"),
                   {"l": lead_kennung})
        db.query(Project).filter(Project.id == kennung).delete(
            synchronize_session=False)
        db.query(Lead).filter(Lead.id == lead_kennung).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


@pytest.fixture
def analysiert(app, projekt):
    """Was der Crawler hinterlässt — eine Zeile im Inhaltsspeicher."""
    from datetime import datetime

    from sqlalchemy import text

    from database import Project, SessionLocal

    db = SessionLocal()
    try:
        lead_id = db.query(Project).filter(Project.id == projekt).first().lead_id
        db.execute(
            text("INSERT INTO website_content_cache (customer_id, url, title, "
                 "scraped_at) VALUES (:c, :u, :t, :s)"),
            {"c": lead_id, "u": "https://scraper-test.local/",
             "t": "Startseite", "s": datetime.utcnow()},
        )
        db.commit()
    finally:
        db.close()
