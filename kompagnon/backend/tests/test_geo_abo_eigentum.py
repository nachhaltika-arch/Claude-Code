"""Ein Kunde konnte ein GEO-Abo fuer ein fremdes Projekt anstossen (L-67).

**Der Befund, 22.08.2026.** `POST /api/geo-payments/{project_id}/create-subscription`
trug `_=Depends(require_any_auth)` — der angemeldete Nutzer wurde nicht
einmal an eine Variable gebunden, geschweige denn geprueft. Die Projektnummer
kam aus der Adresse, und hochzuzaehlen ist der naheliegendste Angriff.

**Warum das mehr ist als eine falsche Rechnung.** Die Stripe-Sitzung wird mit
den Daten des Betriebs erzeugt, dem das Projekt gehoert:

    customer_email = getattr(lead, "email", "")
    company_name   = getattr(lead, "company_name", "")

Wer die Nummer hochzaehlt, bekommt eine Zahlungsseite mit **E-Mail-Adresse
und Firmenname eines fremden Kunden**. Das Abo waere die zweite Folge; die
erste ist ein Datenleck.

**Warum Eigentumspruefung und nicht Rollensperre.** Das ist ein echter
Kundenweg — `GeoAddonCard` haengt in `KundenPortal.jsx`, der Kunde bucht das
Add-on selbst. Eine Rollensperre haette hier das Produkt gesperrt. Die
richtige Frage ist nicht „welche Rolle", sondern **„wessen Zeile"**.

Geprueft wird mit `eigenes_projekt_pruefen` aus `projects_helfer.py` — dem
Muster, das es fuer genau diesen Fall schon gibt. Fuer den Innendienst ist
es nur ein Nachschlagen: Er kommt an alle.
"""
import pytest
from sqlalchemy import text


@pytest.fixture
def fremdes_projekt(app):
    """Ein Projekt, das dem Testkunden **nicht** gehoert."""
    from database import Lead, Project, SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE company_name = 'L67 Fremd'"))
        db.commit()
        lead = Lead(company_name="L67 Fremd", email="fremd@example.com")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        proj = Project(lead_id=lead.id)
        db.add(proj)
        db.commit()
        db.refresh(proj)
        kennung = proj.id
    finally:
        db.close()

    yield kennung

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM projects WHERE lead_id IN "
                        "(SELECT id FROM leads WHERE company_name = 'L67 Fremd')"))
        db.execute(text("DELETE FROM leads WHERE company_name = 'L67 Fremd'"))
        db.commit()
    finally:
        db.close()


class TestFremdesProjekt:
    def test_der_kunde_stoesst_kein_fremdes_abo_an(
            self, client, kunde_headers, fremdes_projekt):
        """Die erste Folge waere kein Abo, sondern eine Zahlungsseite mit der
        E-Mail-Adresse eines fremden Kunden."""
        antwort = client.post(
            f"/api/geo-payments/{fremdes_projekt}/create-subscription",
            headers=kunde_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_und_sieht_auch_den_stand_nicht(
            self, client, kunde_headers, fremdes_projekt):
        antwort = client.get(f"/api/geo-payments/{fremdes_projekt}/status",
                             headers=kunde_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_und_kuendigt_es_erst_recht_nicht(
            self, client, kunde_headers, fremdes_projekt):
        """Eine fremde Kuendigung ist der Schaden, den man nicht zurueckholt."""
        antwort = client.post(f"/api/geo-payments/{fremdes_projekt}/cancel",
                              headers=kunde_headers)

        assert antwort.status_code == 403, antwort.text[:200]

    def test_ein_unbekanntes_projekt_ist_404_nicht_403(
            self, client, auth_headers):
        """Fuer den Innendienst ist es nur ein Nachschlagen."""
        antwort = client.get("/api/geo-payments/99999999/status",
                             headers=auth_headers)

        assert antwort.status_code == 404, antwort.text[:200]


class TestDerKundenwegBleibtOffen:
    def test_der_innendienst_kommt_an_den_stand(
            self, client, auth_headers, fremdes_projekt):
        """Die Sperre darf die Arbeit nicht mitnehmen, fuer die es sie gibt."""
        antwort = client.get(f"/api/geo-payments/{fremdes_projekt}/status",
                             headers=auth_headers)

        assert antwort.status_code != 403, antwort.text[:200]
