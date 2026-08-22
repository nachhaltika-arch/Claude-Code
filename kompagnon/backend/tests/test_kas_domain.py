"""Die eigene Agenturseite braucht eine eigene Domain (L-19).

**Der Befund.** `routers/kas_router.py` legt die Netlify-Site an und rollt sie
aus — aber es gab keinen Weg, eine Custom-Domain zu setzen. Die eigene
Marketingseite hing damit auf `*.netlify.app`.

**Warum das erst jetzt auffiel, obwohl der Baustein längst da war:** Für
Kundenprojekte gibt es `POST /{id}/netlify/set-domain` seit langem,
vollständig mit DNS-Leitfaden, Kundenmail und Portal-Nachricht. Der Dienst
`set_custom_domain` liegt in `services/netlify_service.py` und wird dort
benutzt. Für die eigene Seite fehlte nur die Route.

**Was hier anders ist als beim Kunden.** Keine E-Mail, keine
Portal-Nachricht: Der Empfänger wäre der Betreiber selbst. Stattdessen kommt
der DNS-Leitfaden in der Antwort zurück — er ist das, was jemand beim
Domain-Anbieter eintragen muss.

**Die Sperre ist dieselbe wie beim Ausrollen.** Eine Domain auf die eigene
Marketingseite zu legen ist eine Veröffentlichung im eigenen Namen, kein
Tagesgeschäft — `deploy_kas_pages`, und das hat laut Matrix nur der
Superadmin.
"""
import pytest


@pytest.fixture(autouse=True)
def _tabellen(app):
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id SERIAL PRIMARY KEY, key VARCHAR(120) UNIQUE,
                value TEXT, updated_by INTEGER,
                updated_at TIMESTAMP DEFAULT NOW())"""))
        db.execute(text("DELETE FROM system_settings WHERE key LIKE 'kas_%'"))
        db.commit()
    finally:
        db.close()


@pytest.fixture
def superadmin_headers(client, app):
    from auth import hash_password
    from sqlalchemy import text
    from database import SessionLocal, User

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM users WHERE email = 'super-l19@example.com'"))
        db.commit()
        db.add(User(email="super-l19@example.com", password_hash=hash_password("egal"),
                    role="superadmin", is_active=True))
        db.commit()
    finally:
        db.close()

    antwort = client.post("/api/auth/login",
                          json={"email": "super-l19@example.com", "password": "egal"})
    assert antwort.status_code == 200, antwort.text[:200]
    return {"Authorization": f"Bearer {antwort.json()['access_token']}"}


def _site_anlegen():
    from sqlalchemy import text
    from database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text(
            "INSERT INTO system_settings (key, value) VALUES "
            "('kas_netlify_site_id', 'site-123'), "
            "('kas_netlify_site_url', 'https://kompagnon-kas.netlify.app') "
            "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"))
        db.commit()
    finally:
        db.close()


class TestSperre:
    def test_der_admin_darf_die_eigene_domain_nicht_setzen(self, client, auth_headers):
        """Dieselbe Grenze wie beim Ausrollen — eine Veroeffentlichung im
        eigenen Namen."""
        antwort = client.post("/api/kas/domain", json={"domain": "kompagnon.eu"},
                              headers=auth_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_ohne_anmeldung_gar_nicht(self, client):
        antwort = client.post("/api/kas/domain", json={"domain": "kompagnon.eu"})

        assert antwort.status_code in (401, 403)


class TestVorbedingungen:
    def test_ohne_site_gibt_es_nichts_zu_verbinden(self, client, superadmin_headers):
        antwort = client.post("/api/kas/domain", json={"domain": "kompagnon.eu"},
                              headers=superadmin_headers)

        assert antwort.status_code == 400
        assert "Site" in antwort.text

    @pytest.mark.parametrize("eingabe", ["", "   ", "keine domain", "http://x",
                                         "punktlos"])
    def test_eine_unbrauchbare_domain_wird_abgewiesen(
            self, client, superadmin_headers, eingabe):
        """Netlify nimmt fast alles entgegen und scheitert spaeter still.

        Ein Tippfehler, der erst beim Domain-Anbieter auffaellt, kostet den
        Umweg ueber eine DNS-Aenderung, die nie greifen konnte.
        """
        _site_anlegen()

        antwort = client.post("/api/kas/domain", json={"domain": eingabe},
                              headers=superadmin_headers)

        assert antwort.status_code == 400, f"{eingabe!r} kam durch"


class TestErfolg:
    def test_die_antwort_traegt_den_dns_leitfaden(
            self, client, superadmin_headers, monkeypatch):
        """Ohne ihn weiss niemand, was beim Anbieter einzutragen ist — und
        genau das ist der Schritt, der die Domain lebendig macht."""
        _site_anlegen()

        async def falsche_domain(site_id, domain):
            return {"custom_domain": domain, "ssl_url": f"https://{domain}"}

        from services import netlify_service
        monkeypatch.setattr(netlify_service, "set_custom_domain", falsche_domain)

        antwort = client.post("/api/kas/domain", json={"domain": "kompagnon.eu"},
                              headers=superadmin_headers)

        assert antwort.status_code == 200, antwort.text[:300]
        daten = antwort.json()
        assert daten["domain"] == "kompagnon.eu"
        assert daten.get("dns"), "kein DNS-Leitfaden in der Antwort"

    def test_die_domain_wird_gemerkt(self, client, superadmin_headers, monkeypatch):
        """Sonst steht sie nur bei Netlify und nirgends bei uns — und die
        Oberflaeche kann nicht zeigen, worauf die Seite laeuft."""
        _site_anlegen()

        async def falsche_domain(site_id, domain):
            return {"custom_domain": domain}

        from services import netlify_service
        monkeypatch.setattr(netlify_service, "set_custom_domain", falsche_domain)

        client.post("/api/kas/domain", json={"domain": "kompagnon.eu"},
                    headers=superadmin_headers)
        stand = client.get("/api/kas/site", headers=superadmin_headers).json()

        assert stand.get("custom_domain") == "kompagnon.eu"

    def test_ein_fehler_bei_netlify_wird_gemeldet_nicht_verschluckt(
            self, client, superadmin_headers, monkeypatch):
        _site_anlegen()

        async def scheitert(site_id, domain):
            raise RuntimeError("Netlify sagt nein")

        from services import netlify_service
        monkeypatch.setattr(netlify_service, "set_custom_domain", scheitert)

        antwort = client.post("/api/kas/domain", json={"domain": "kompagnon.eu"},
                              headers=superadmin_headers)

        assert antwort.status_code == 502
        assert "Netlify" in antwort.text
