"""Seiten loeschen und Inhalte aendern konnte jeder Angemeldete (L-67).

**Der Bestand.** Von den 85 Routen, die nur „irgendwer ist angemeldet"
verlangen, fuehren 24 die Seiten und Inhalte der Kundenprojekte:
`pages_router` in `sitemap.py` (15) und `routers/content.py` (9). Beide
Router tragen **keine** Sperre; die Routen verlassen sich auf
`require_any_auth` oder `get_current_user`, und **Kunden haben Konten**.

Darunter sind keine Leseabfragen:

* `DELETE /api/pages/{id}` — eine Seite des Kunden entfernen
* `PUT /api/content/section/{id}` — den Text einer Seite ueberschreiben
* `DELETE /api/content/media/{id}` — ein Bild entfernen
* `POST /api/pages/templates/upload` — eine Vorlage einspielen

**Vor der Sperre gemessen, wie die Vorgabe es verlangt.** Die Adressen
werden aus `PageManager`, `PublicPageEditor`, `PageTemplateEditor`,
`CustomerDetail`, `ContentManager`, `LeadProfile` und `KasWebsite` gerufen —
alle unter `PrivateRoute roles={['admin']}` beziehungsweise
`['admin','auditor']` und `['admin','superadmin']`. **Kein Pfad unter
`pages/customer/`, kein Aufruf aus `KundenPortal.jsx`.** Der Seitenbau ist
Innendienstarbeit.

**Die Sperre haengt am Router, nicht je Route.** Sonst ist die naechste
hinzugefuegte Route wieder offen — genau die Bauart hinter L-51.
"""
import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def _tabellen(app):
    """`public_pages` entsteht nur im Migrationsblock — hier selbst anlegen,
    sonst antwortet die Seitenliste mit 500 statt mit ihrem Inhalt."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        # **Erst weg, dann neu.** `CREATE TABLE IF NOT EXISTS` laesst eine
        # Tabelle stehen, die aus einem frueheren Lauf mit anderer Definition
        # stammt — und dann fehlen Spalten, die die Route erwartet. Kein
        # anderer Test baut auf diesen beiden auf (nachgesehen).
        db.execute(text("DROP TABLE IF EXISTS public_pages CASCADE"))
        db.execute(text("DROP TABLE IF EXISTS page_templates CASCADE"))
        db.execute(text("""CREATE TABLE IF NOT EXISTS public_pages (
            id              SERIAL PRIMARY KEY,
            slug            VARCHAR(200) UNIQUE NOT NULL,
            name            VARCHAR(200) NOT NULL,
            description     TEXT DEFAULT '',
            page_type       VARCHAR(50) DEFAULT 'custom',
            status          VARCHAR(20) DEFAULT 'draft',
            html_content    TEXT DEFAULT '',
            grapesjs_data   JSONB DEFAULT '{}',
            css_content     TEXT DEFAULT '',
            react_component VARCHAR(100) DEFAULT '',
            product_id      INTEGER,
            template_id     INTEGER,
            meta_title      VARCHAR(200) DEFAULT '',
            meta_description VARCHAR(300) DEFAULT '',
            published_at    TIMESTAMP,
            created_at      TIMESTAMP DEFAULT NOW(),
            updated_at      TIMESTAMP DEFAULT NOW()
        )"""))
        db.execute(text("""CREATE TABLE IF NOT EXISTS page_templates (
            id              SERIAL PRIMARY KEY,
            name            VARCHAR(200) NOT NULL,
            description     TEXT DEFAULT '',
            category        VARCHAR(100) DEFAULT 'allgemein',
            thumbnail_url   VARCHAR(500) DEFAULT '',
            grapesjs_data   JSONB DEFAULT '{}',
            html_content    TEXT DEFAULT '',
            css_content     TEXT DEFAULT '',
            is_builtin      BOOLEAN DEFAULT FALSE,
            sort_order      INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT NOW()
        )"""))
        db.commit()
    finally:
        db.close()


SEITEN = [
    ("get",    "/api/pages/", None),
    ("post",   "/api/pages/", {"slug": "x", "title": "X"}),
    ("get",    "/api/pages/1", None),
    ("put",    "/api/pages/1", {"title": "X"}),
    ("delete", "/api/pages/1", None),
    ("patch",  "/api/pages/1/link-product", {}),
    ("get",    "/api/pages/1/editor", None),
    ("post",   "/api/pages/1/editor", {}),
    ("get",    "/api/pages/templates/list", None),
    ("get",    "/api/pages/templates/1", None),
    ("put",    "/api/pages/templates/1", {}),
    ("delete", "/api/pages/templates/1", None),
]

INHALTE = [
    ("get",    "/api/content/1", None),
    ("get",    "/api/content/page/1", None),
    ("put",    "/api/content/section/1", {"content": "X"}),
    ("put",    "/api/content/media/1", {}),
    ("delete", "/api/content/media/1", None),
    ("post",   "/api/content/section/1/generate", {}),
    ("post",   "/api/content/page/1/generate-all", {}),
    ("get",    "/api/content/jobs/abc", None),
]


def _ruf(client, methode, pfad, rumpf, headers=None):
    zusatz = {"json": rumpf} if rumpf is not None else {}
    if headers:
        zusatz["headers"] = headers
    return getattr(client, methode)(pfad, **zusatz)


class TestDerKundeKommtNichtHeran:
    @pytest.mark.parametrize("methode,pfad,rumpf", SEITEN + INHALTE)
    def test_kein_kunde(self, client, kunde_headers, methode, pfad, rumpf):
        """**Kunden haben Konten.** Ein Loeschen wiegt schwerer als ein
        Einblick: Es ist Datenverlust bei einem fremden Betrieb."""
        antwort = _ruf(client, methode, pfad, rumpf, kunde_headers)

        assert antwort.status_code == 403, (
            f"{methode.upper()} {pfad} → {antwort.status_code}")

    @pytest.mark.parametrize("methode,pfad,rumpf", SEITEN + INHALTE)
    def test_ohne_anmeldung_erst_recht_nicht(self, client, methode, pfad, rumpf):
        antwort = _ruf(client, methode, pfad, rumpf)

        assert antwort.status_code in (401, 403)


class TestDerInnendienstArbeitetWeiter:
    def test_der_admin_sieht_die_seitenliste(self, client, auth_headers):
        """Die Sperre darf die Arbeit nicht mitnehmen, fuer die es sie gibt."""
        antwort = client.get("/api/pages/", headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]

    def test_und_die_vorlagenliste(self, client, auth_headers):
        antwort = client.get("/api/pages/templates/list", headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]


class TestDieSperreHaengtAmRouter:
    def test_beide_router_tragen_sie(self):
        """Je Route waere sie beim naechsten Hinzufuegen wieder offen — genau
        die Bauart hinter L-51."""
        import pathlib

        from routers import content, sitemap

        for modul in (content, sitemap):
            quelle = pathlib.Path(modul.__file__).read_text(encoding="utf-8")
            assert "Depends(require_innendienst)" in quelle, modul.__name__
