"""L-63: Zwei Endpunkte scheiterten seit vier Monaten an jedem Aufruf.

Gefunden am 21.08.2026 beim Zusammenlegen der zwei Template-Router (L-28).

`routers/templates.py` schrieb sein SQL mit `%(name)s`-Platzhaltern in einem
`sqlalchemy.text(...)`. Diese Schreibweise kennt SQLAlchemy nicht — es bindet
nichts, und Postgres bekommt das Prozentzeichen roh zu sehen:

    psycopg2.errors.SyntaxError: syntax error at or near "%"

Betroffen: `POST /api/templates/upload` und `POST /api/templates/import-url`.
Beide ruft das Frontend auf; beide antworteten seit `afa35a3` (10.04.2026)
mit einem Fehler.

**Der Grund im damaligen Commit ist lehrreich:** „SQL uses %(x)s parameter
style to avoid colon conflicts with CSS :root and :: pseudo-elements in
content". Die Sorge ist unbegruendet — SQLAlchemy liest **nur den SQL-Text**
nach Platzhaltern ab, nie die gebundenen Werte. Ein `:root` im CSS kann dort
gar nicht ankommen. Die Vorsichtsmassnahme hat genau das kaputtgemacht, was
sie schuetzen sollte.

Der letzte Test hier haelt diese Tuer zu: Er schiebt ein CSS mit `:root`,
`::before` und `a:hover` durch und beweist, dass nichts passiert.
"""
import pytest
from sqlalchemy import text

from database import SessionLocal


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture(autouse=True)
def tabelle(db):
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS website_templates (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200), description TEXT, source VARCHAR(50),
            source_url TEXT, thumbnail_url TEXT,
            html_content TEXT, css_content TEXT,
            tags TEXT, category VARCHAR(100),
            created_at TIMESTAMP, updated_at TIMESTAMP)
    """))
    db.execute(text("DELETE FROM website_templates WHERE name LIKE 'Probe-%'"))
    db.commit()
    yield
    db.execute(text("DELETE FROM website_templates WHERE name LIKE 'Probe-%'"))
    db.commit()


def _zip_mit(html: str, css: str = "") -> bytes:
    import io
    import zipfile

    puffer = io.BytesIO()
    with zipfile.ZipFile(puffer, "w") as zf:
        zf.writestr("index.html", html)
        if css:
            zf.writestr("style.css", css)
    return puffer.getvalue()


CSS_MIT_DOPPELPUNKTEN = """
:root { --farbe: #008EAA; }
a:hover { color: var(--farbe); }
.karte::before { content: ''; }
"""


class TestHochladen:
    def test_eine_vorlage_laesst_sich_ueberhaupt_hochladen(self, client, auth_headers, db):
        # Act
        antwort = client.post(
            "/api/templates/upload",
            headers=auth_headers,
            files={"file": ("probe.zip", _zip_mit("<html><body><p>Hallo</p></body></html>"),
                            "application/zip")},
            data={"name": "Probe-Upload", "description": "", "category": "test", "tags": ""},
        )

        # Assert
        assert antwort.status_code == 200, antwort.text
        assert antwort.json()["name"] == "Probe-Upload"

    def test_css_mit_doppelpunkten_geht_unveraendert_durch(self, client, auth_headers, db):
        """Der Grund fuer die kaputte Schreibweise war die Angst vor `:root`.

        Gebundene Werte werden nicht nach Platzhaltern durchsucht — hier ist
        der Beweis, damit die Vorsichtsmassnahme nicht zurueckkommt.
        """
        # Act
        antwort = client.post(
            "/api/templates/upload",
            headers=auth_headers,
            files={"file": ("probe.zip",
                            _zip_mit("<html><body><p>x</p></body></html>", CSS_MIT_DOPPELPUNKTEN),
                            "application/zip")},
            data={"name": "Probe-CSS", "description": "", "category": "test", "tags": ""},
        )

        # Assert
        assert antwort.status_code == 200, antwort.text
        gespeichert = db.execute(
            text("SELECT css_content FROM website_templates WHERE name = 'Probe-CSS'")
        ).scalar()
        assert ":root" in gespeichert
        assert "::before" in gespeichert
        assert "a:hover" in gespeichert

    def test_eine_kaputte_zip_datei_bekommt_eine_klare_antwort(self, client, auth_headers):
        # Act
        antwort = client.post(
            "/api/templates/upload",
            headers=auth_headers,
            files={"file": ("probe.zip", b"keine zip-datei", "application/zip")},
            data={"name": "Probe-Kaputt", "description": "", "category": "test", "tags": ""},
        )

        # Assert — 400, nicht 500: Der Aufrufer hat etwas falsch gemacht.
        assert antwort.status_code == 400


def test_kein_endpunkt_benutzt_mehr_die_prozent_schreibweise():
    """Ein Waechter auf die Bauart, nicht auf die zwei Stellen.

    `%(x)s` in einem `text(...)` bindet nichts und faellt erst zur Laufzeit
    auf — genau deshalb blieb es vier Monate liegen.
    """
    import pathlib
    import re

    wurzel = pathlib.Path(__file__).resolve().parent.parent
    treffer = []
    for datei in list((wurzel / "routers").rglob("*.py")) + list((wurzel / "services").rglob("*.py")):
        for nummer, zeile in enumerate(datei.read_text(encoding="utf-8").split("\n"), 1):
            # Kommentare zitieren die kaputte Schreibweise absichtlich — sie
            # soll nachlesbar bleiben, ohne wieder zu gelten. Dieselbe
            # Entscheidung wie bei `PACKAGE_NAMES` (L-29).
            if zeile.lstrip().startswith("#"):
                continue
            if "%(asctime)s" in zeile or "logging" in zeile:
                continue
            if re.search(r"%\([a-zA-Z_]+\)s", zeile):
                treffer.append(f"{datei.relative_to(wurzel)}:{nummer}")

    assert treffer == [], f"SQL mit %(x)s-Platzhaltern: {treffer}"
