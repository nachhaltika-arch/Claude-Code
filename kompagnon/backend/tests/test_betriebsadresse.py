"""Straße, PLZ und Öffnungszeiten am Betrieb (L-15, L-99, L-105).

**Warum diese drei Felder.** Am 24.08.2026 sollte der SEO/GEO-Agent einen
Knopf bekommen — er war gebaut und rief niemand auf. Er ließ sich nicht
anschließen: `POST /api/agents/{id}/seo` verlangt `CompanyData` mit
``street``, ``postal_code`` und ``opening_hours``, und **diese Felder gab es
im Datenmodell nicht**. `Lead` führte `company_name`, `phone`, `email`,
`website_url`, `city` und `trade` — mehr nicht.

Der Agent war also nie anzuschließen, weil seine Eingabe nie existierte.
Dieselbe Lücke blockiert:

* **L-99** — GEO/GAIO wird verkauft, aber nicht ausgeliefert. Weder
  `llms.txt` noch `schema.org`-Auszeichnung lassen sich ohne Anschrift und
  Öffnungszeiten erzeugen; `LocalBusiness` verlangt beides.
* **L-15 § 6** — die Conversion-Spec fordert neue Pflichtfelder im
  Generator-Eingang, damit der Likelihood-Faktor überhaupt befüllbar wird.

**Öffnungszeiten als JSON-Text und nicht als sieben Spalten.** Sie sind eine
Struktur, keine Skalare, und `schema.org/openingHours` will sie ohnehin
zusammengesetzt. Sieben Spalten wären sieben Migrationen beim ersten
Sonderfall („Mo–Do 8–17, Fr 8–13, Sa nach Vereinbarung").
"""
import json
import pathlib

import pytest

from database import Lead
from services.betriebsadresse import (
    adresse_vollstaendig,
    als_company_data,
    oeffnungszeiten_lesen,
)


class TestDieFelderGibtEs:
    @pytest.mark.parametrize("feld", ["street", "postal_code", "opening_hours"])
    def test_das_modell_fuehrt_das_feld(self, feld):
        assert hasattr(Lead, feld), (
            f"`Lead.{feld}` fehlt — ohne dieses Feld ist der SEO-Agent nicht "
            "anzuschliessen und GEO nicht auszuliefern."
        )


class TestOeffnungszeiten:
    def test_leer_ergibt_ein_leeres_verzeichnis(self):
        """Kein Eintrag heisst nicht 'geschlossen', sondern 'nicht erhoben'."""
        assert oeffnungszeiten_lesen(None) == {}
        assert oeffnungszeiten_lesen("") == {}

    def test_gueltiges_json_wird_gelesen(self):
        # Arrange
        roh = json.dumps({"Mo-Do": "08:00-17:00", "Fr": "08:00-13:00"})

        # Act & Assert
        assert oeffnungszeiten_lesen(roh) == {
            "Mo-Do": "08:00-17:00", "Fr": "08:00-13:00"}

    def test_kaputtes_json_wirft_nicht(self):
        """Ein Feld aus der Oberflaeche darf keine Route zerlegen."""
        assert oeffnungszeiten_lesen("{kaputt") == {}
        assert oeffnungszeiten_lesen("[1,2,3]") == {}


class TestVollstaendigkeit:
    @staticmethod
    def _betrieb(**felder):
        werte = {
            "company_name": "Muster GmbH", "street": "Hauptstrasse 1",
            "postal_code": "56070", "city": "Koblenz",
            "phone": "0261 1", "email": "a@b.de",
            "website_url": "https://muster.de",
            "opening_hours": json.dumps({"Mo-Fr": "08:00-17:00"}),
            "trade": "Heizung",
        }
        werte.update(felder)
        return type("L", (), werte)()

    def test_vollstaendig_wenn_alles_da_ist(self):
        assert adresse_vollstaendig(self._betrieb()) is True

    @pytest.mark.parametrize("fehlend", ["street", "postal_code", "city",
                                         "opening_hours"])
    def test_ein_fehlendes_feld_genuegt(self, fehlend):
        assert adresse_vollstaendig(self._betrieb(**{fehlend: ""})) is False

    def test_die_umwandlung_liefert_was_der_agent_verlangt(self):
        """Genau die Felder aus `CompanyData` — nicht mehr, nicht weniger."""
        # Act
        daten = als_company_data(self._betrieb(), leistungen=["Waermepumpe"])

        # Assert
        for pflicht in ("company_name", "street", "postal_code", "city",
                        "country", "phone", "email", "website", "services",
                        "opening_hours"):
            assert pflicht in daten, f"{pflicht} fehlt fuer den SEO-Agenten"
        assert daten["opening_hours"] == {"Mo-Fr": "08:00-17:00"}
        assert daten["services"] == ["Waermepumpe"]
        assert daten["country"] == "DE"

    def test_ohne_anschrift_wird_nichts_erfunden(self):
        """Lieber ein leeres Feld als eine erfundene Adresse."""
        # Act
        daten = als_company_data(self._betrieb(street=""), leistungen=[])

        # Assert
        assert daten["street"] == ""


class TestDieFelderKommenDurchDieSchnittstelle:
    """Angenommen und verworfen waere schlimmer als gar nicht angenommen.

    Beim Ergaenzen am 24.08.2026 nahm `LeadCreate` die drei Felder bereits
    entgegen, waehrend der `INSERT` sie nicht schrieb: Die Oberflaeche haette
    gemeldet, alles sei gespeichert, und beim naechsten Laden waere die
    Anschrift weg gewesen. Dieselbe Familie wie L-55 — nur andersherum.
    """

    def test_der_insert_schreibt_alle_drei(self):
        import pathlib

        quelle = (pathlib.Path(__file__).resolve().parent.parent
                  / "routers" / "leads.py").read_text(encoding="utf-8")
        anfang = quelle.index("INSERT INTO leads (")
        block = quelle[anfang:anfang + 2000]
        for feld in ("street", "postal_code", "opening_hours"):
            assert f":{feld}" in block, (
                f"`{feld}` wird von LeadCreate angenommen, aber nicht "
                "geschrieben."
            )

    def test_das_modell_hat_jedes_feld_genau_einmal(self):
        """Zwei Definitionen desselben Feldes — die spaetere gewinnt still."""
        import re

        import database

        quelle = pathlib.Path(database.__file__).read_text(encoding="utf-8")
        anfang = quelle.index("class Lead(Base)")
        ende = quelle.index("\nclass ", anfang + 10)
        block = quelle[anfang:ende]
        for feld in ("street", "postal_code", "opening_hours", "house_number"):
            treffer = re.findall(r"^\s+" + feld + r"\s*=\s*Column", block, re.M)
            assert len(treffer) == 1, (
                f"`Lead.{feld}` ist {len(treffer)}x definiert. Bei SQLAlchemy "
                "gewinnt stillschweigend die spaetere."
            )


class TestDerSeoAgentHoltSichDieDatenSelbst:
    """Der Endpunkt war nie anzuschliessen, weil er alles vom Aufrufer verlangte.

    `POST /api/agents/{id}/seo` erwartete die vollstaendige `CompanyData` im
    Rumpf — Strasse, PLZ und Oeffnungszeiten inbegriffen. Das Frontend haette
    sie liefern muessen, und die Oeffnungszeiten gab es im Datenmodell nicht.
    Seit dem 24.08.2026 holt der Endpunkt sie selbst.
    """

    def test_unvollstaendige_anschrift_wird_benannt_statt_geraten(
            self, client, auth_headers, aufraeumen):
        # Arrange — ein Betrieb ohne Anschrift, wie fast alle im Bestand
        from database import Lead, Project, SessionLocal

        db = SessionLocal()
        try:
            betrieb = Lead(company_name="Ohne Anschrift GmbH", city="Koblenz")
            db.add(betrieb); db.commit(); db.refresh(betrieb)
            projekt = Project(lead_id=betrieb.id, status="phase_1")
            db.add(projekt); db.commit(); db.refresh(projekt)
            projekt_id, betrieb_id = projekt.id, betrieb.id
        finally:
            db.close()

        # Act
        antwort = client.post(f"/api/agents/{projekt_id}/seo",
                              headers=auth_headers, json=None)

        # Assert — 400 mit den fehlenden Feldern, kein Rateversuch
        assert antwort.status_code == 400
        meldung = antwort.json()["detail"]
        assert "street" in meldung and "opening_hours" in meldung
        assert "geraten wird hier nichts" in meldung

        # Aufraeumen
        db = SessionLocal()
        try:
            db.query(Project).filter(Project.id == projekt_id).delete()
            db.query(Lead).filter(Lead.id == betrieb_id).delete()
            db.commit()
        finally:
            db.close()
