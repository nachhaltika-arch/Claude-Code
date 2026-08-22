"""Ein Blocktausch loeschte den Style-Guide (L-09 → L-88).

**Gefunden am 22.08.2026** beim Schliessen der Testluecke „Style-Guide-
Freigabe". `WireframeData` fuehrt drei Felder — `pages`, `style_guide` und
`style_guide_approved` —, und `save_wireframe` schreibt das **ganze** Objekt
zurueck. Wer nur die Seiten schickt, bekommt fuer die anderen beiden die
Pydantic-Vorgaben: `None` und `False`.

Genau das tat die Oberflaeche an **fuenf von sieben** Speicherstellen
(`WireframeView.jsx`): `const nextData = { pages: … }` ohne den bisherigen
Zustand. Ein Blocktausch loeschte damit den kompletten Style-Guide — Farben,
Typografie, Buttons, Abstaende — **und** die Freigabe, die das Tor zur
DesignView ist. Stillschweigend; nichts meldete es, und beim naechsten
Aufruf sah die Seite einfach anders aus.

**Warum die Sperre in den Server gehoert und nicht nur in die Oberflaeche.**
Die fuenf Stellen sind repariert, aber die naechste kommt bestimmt: Wer eine
sechste Speicherstelle schreibt, denkt an `pages` — an einen Style-Guide,
den er nicht anfasst, denkt niemand. Ein weggelassenes Feld darf einen
vorhandenen Wert nicht loeschen.

**Unterschieden wird „nicht geschickt" von „absichtlich zurueckgenommen".**
Wer `style_guide_approved: false` **schickt**, nimmt die Freigabe zurueck,
und das muss gehen — sonst waere sie unwiderruflich.
"""
import pytest
from sqlalchemy import text


STIL = {"farben": {"primaer": "#008eaa"}, "typo": {"grund": "Noto Sans"}}


@pytest.fixture
def projekt(app):
    from database import Lead, Project, SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE company_name = 'L88 Betrieb'"))
        db.commit()
        lead = Lead(company_name="L88 Betrieb")
        db.add(lead)
        db.commit()
        db.refresh(lead)
        proj = Project(lead_id=lead.id,
                       wireframe_data={"pages": [], "style_guide": STIL,
                                       "style_guide_approved": True})
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
                        "(SELECT id FROM leads WHERE company_name = 'L88 Betrieb')"))
        db.execute(text("DELETE FROM leads WHERE company_name = 'L88 Betrieb'"))
        db.commit()
    finally:
        db.close()


def _speichern(client, headers, kennung, rumpf):
    """**Mit Statuspruefung.** Ohne sie war der erste Anlauf dieses Tests
    falsch gruen: `page_id` ist ein `int`, der Test schickte `"start"`, der
    Aufruf lief auf 422 — und weil nichts gespeichert wurde, blieb der
    Style-Guide „erhalten". Ein Test, dessen Aufruf scheitert, prueft nichts
    und meldet Erfolg."""
    antwort = client.post(f"/api/projects/{kennung}/wireframe",
                          json=rumpf, headers=headers)
    assert antwort.status_code == 200, antwort.text[:300]
    return antwort.json()


def _stand(client, headers, kennung):
    antwort = client.get(f"/api/projects/{kennung}/wireframe", headers=headers)
    assert antwort.status_code == 200, antwort.text[:200]
    return antwort.json()


class TestWeglassenLoeschtNicht:
    def test_ein_blocktausch_behaelt_den_style_guide(
            self, client, auth_headers, projekt):
        """Der Fall aus der Oberflaeche: nur `pages` geschickt."""
        _speichern(client, auth_headers, projekt, {"pages": [{"page_id": 1, "blocks": []}]})

        assert _stand(client, auth_headers, projekt)["style_guide"] == STIL

    def test_und_die_freigabe(self, client, auth_headers, projekt):
        """Sie ist das Tor zur DesignView — faellt sie weg, steht der Ablauf."""
        _speichern(client, auth_headers, projekt, {"pages": []})

        assert _stand(client, auth_headers, projekt)["style_guide_approved"] is True

    def test_die_seiten_werden_sehr_wohl_uebernommen(
            self, client, auth_headers, projekt):
        """Sonst waere die Sperre eine Blockade."""
        _speichern(client, auth_headers, projekt, {"pages": [{"page_id": 1, "blocks": []}]})

        assert len(_stand(client, auth_headers, projekt)["pages"]) == 1


class TestZuruecknehmenGehtWeiterhin:
    def test_wer_false_schickt_nimmt_die_freigabe_zurueck(
            self, client, auth_headers, projekt):
        """„Nicht geschickt" und „auf false gesetzt" sind verschiedene
        Aussagen. Waere das nicht so, waere die Freigabe unwiderruflich."""
        _speichern(client, auth_headers, projekt, {"pages": [], "style_guide_approved": False})

        assert _stand(client, auth_headers, projekt)["style_guide_approved"] is False

    def test_und_ein_neuer_style_guide_ersetzt_den_alten(
            self, client, auth_headers, projekt):
        neu = {"farben": {"primaer": "#123456"}}

        _speichern(client, auth_headers, projekt, {"pages": [], "style_guide": neu})

        assert _stand(client, auth_headers, projekt)["style_guide"] == neu


class TestOhneVorgeschichte:
    def test_ein_leeres_projekt_bekommt_keine_erfundenen_werte(
            self, client, auth_headers, projekt):
        """Erst leeren, dann speichern — es darf nichts auftauchen."""
        client.post(f"/api/projects/{projekt}/wireframe",
                    json={"pages": [], "style_guide": None,
                          "style_guide_approved": False}, headers=auth_headers)
        _speichern(client, auth_headers, projekt, {"pages": []})

        stand = _stand(client, auth_headers, projekt)
        assert stand["style_guide"] is None
        assert stand["style_guide_approved"] is False
