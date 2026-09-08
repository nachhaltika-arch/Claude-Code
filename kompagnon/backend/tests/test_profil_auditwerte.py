# -*- coding: utf-8 -*-
"""Das Betriebsblatt zeigte den Audit aus Spalten, die niemand mehr fuellt.

**Der Befund (08.09.2026, gemeldet an Betrieb 87).** Unter „Audits" fehlte
das vollstaendige Ergebnis. Die Ursache liegt nicht im Audit — es steht
komplett in der Datenbank —, sondern im Weg dorthin.

Am 11.08.2026 wurde der Kriterienkatalog von Einzelspalten auf JSON
umgestellt. Das Datenmodell sagt es woertlich: *„Die Einzelspalten oberhalb
sind Altbestand und werden nicht mehr gefuellt."* `routers/leads_profil.py`
lieferte je Audit aber genau diese Altspalten — 33 fest im Code aufgezaehlte
Schluessel, von denen **14 den Katalog laengst verlassen haben** (`ux_*`,
`ho_*`, `rc_ecommerce`, `se_seo`, `si_formulare`, `bf_screenreader`) und die
uebrigen seit vier Wochen auf 0 stehen.

**Betroffen waren zwei Reiter, nicht einer.** „Audits" reichte das
Listenobjekt an den Bericht weiter; „Checklisten" liest dieselben Felder.
Beide zeigten Nullen und nannten sie „fehlt".

**Die ehrliche Anzeige gab es schon.** `getStatus` in den Checklisten kennt
`unknown` fuer `score == null`. Sie bekam nur nie ein `null` zu sehen, weil
der Server 0 schickte — und **0 heisst „geprueft und nicht erfuellt"**, nicht
„nicht erhoben". Genau dieser Unterschied ist die Luecke.
"""
import json

import pytest
from sqlalchemy import text


@pytest.fixture()
def betrieb_mit_audit(app):
    """Ein Betrieb mit einem Audit im heutigen Format (JSON, kein Altbestand)."""
    from database import AuditResult, Lead, SessionLocal

    db = SessionLocal()
    try:
        lead = Lead(company_name="Pruefbetrieb Auditwerte",
                    website_url="https://pruefbetrieb.example")
        db.add(lead)
        db.commit()

        audit = AuditResult(
            lead_id=lead.id,
            website_url="https://pruefbetrieb.example",
            company_name="Pruefbetrieb Auditwerte",
            status="completed",
            total_score=61,
            level="Silber",
            # Der heutige Weg: Kriterien als JSON, Altspalten bleiben leer.
            item_scores=json.dumps({"rc_impressum": 3, "rc_cookie": 1,
                                    "cv_cta": 2, "dg_typografie": 3,
                                    "ih_textqualitaet": 1}),
            item_belege=json.dumps({"rc_impressum": "vollstaendig"}),
            category_scores=json.dumps([{"key": "rc", "label": "Recht",
                                         "score": 4, "max": 15}]),
            coverage=78,
            blockers=json.dumps(["rc_impressum"]),
        )
        db.add(audit)
        db.commit()
        kennung = lead.id
        audit_kennung = audit.id
    finally:
        db.close()

    yield kennung, audit_kennung

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM audit_results WHERE lead_id = :l"),
                   {"l": kennung})
        db.execute(text("DELETE FROM leads WHERE id = :l"), {"l": kennung})
        db.commit()
    finally:
        db.close()


#: Schluessel, die der Katalog seit dem 11.08.2026 nicht mehr kennt.
VERLASSEN = ("ux_cta", "ux_erstindruck", "ux_kontakt", "ux_navigation",
             "ux_vertrauen", "ux_content", "ho_backup", "ho_anbieter",
             "ho_uptime", "ho_http", "ho_cdn", "rc_ecommerce",
             "rc_urheberrecht", "se_seo", "si_formulare", "bf_screenreader",
             "bf_lesbarkeit")


class TestProfilLiefertEchteWerte:

    def test_die_gemessenen_kriterien_kommen_an(self, client, auth_headers,
                                                betrieb_mit_audit):
        kennung, _ = betrieb_mit_audit
        antwort = client.get(f"/api/leads/{kennung}/profile", headers=auth_headers)
        assert antwort.status_code == 200, antwort.text

        audit = antwort.json()["audits"][0]
        assert audit["rc_impressum"] == 3
        assert audit["cv_cta"] == 2
        assert audit["dg_typografie"] == 3
        assert audit["ih_textqualitaet"] == 1

    def test_kein_schluessel_aus_dem_alten_katalog(self, client, auth_headers,
                                                  betrieb_mit_audit):
        """**Die entscheidende Haelfte.**

        Ein verlassener Schluessel mit dem Wert 0 ist schlimmer als gar
        keiner: Die Checkliste liest ihn als „geprueft und nicht erfuellt"
        und meldet einen Mangel, den niemand gemessen hat.
        """
        kennung, _ = betrieb_mit_audit
        audit = client.get(f"/api/leads/{kennung}/profile",
                           headers=auth_headers).json()["audits"][0]

        uebrig = [k for k in VERLASSEN if k in audit]
        assert uebrig == [], (
            "Diese Schluessel gibt es im Katalog nicht mehr, das Profil "
            f"liefert sie aber weiter: {uebrig}")

    def test_die_aufbereiteten_felder_kommen_mit(self, client, auth_headers,
                                                 betrieb_mit_audit):
        kennung, _ = betrieb_mit_audit
        audit = client.get(f"/api/leads/{kennung}/profile",
                           headers=auth_headers).json()["audits"][0]

        assert audit["coverage"] == 78
        assert audit["blockers"] == ["rc_impressum"]
        assert audit["category_scores"][0]["key"] == "rc"
        assert audit["item_belege"]["rc_impressum"] == "vollstaendig"

    def test_die_kopfangaben_bleiben(self, client, auth_headers,
                                     betrieb_mit_audit):
        """Die Liste braucht weiterhin Punktzahl, Stufe, Datum und Adresse."""
        kennung, _ = betrieb_mit_audit
        audit = client.get(f"/api/leads/{kennung}/profile",
                           headers=auth_headers).json()["audits"][0]

        assert audit["total_score"] == 61
        assert audit["level"] == "Silber"
        assert audit["status"] == "completed"
        assert audit["website_url"] == "https://pruefbetrieb.example"
        assert audit["created_at"]

    def test_ein_kriterium_ohne_messung_fehlt_statt_null_zu_sein(
            self, client, auth_headers, betrieb_mit_audit):
        """`se_lokal` wurde in diesem Lauf nicht erhoben.

        Es darf deshalb **nicht** als 0 erscheinen — `getStatus` in den
        Checklisten macht aus `null` ein „unbekannt", aus 0 aber ein „fehlt".
        """
        kennung, _ = betrieb_mit_audit
        audit = client.get(f"/api/leads/{kennung}/profile",
                           headers=auth_headers).json()["audits"][0]

        assert "se_lokal" not in audit
