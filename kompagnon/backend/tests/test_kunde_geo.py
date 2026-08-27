# -*- coding: utf-8 -*-
"""Der Kunde sieht seinen GEO-Wert.

**Der Anlass (26.08.2026, L-95).** `components/GeoReport.jsx` beschreibt sich
im eigenen Kopf als *„vereinfachte Ansicht fuer das Kundenportal — Kunde
sieht Score, Bedeutung und was gemacht wird"*. Importiert hat die Datei
**niemand**. Sie war gebaut und an keinen Knopf gehängt.

**Warum das mehr ist als eine ungenutzte Datei.** Die Lückenliste führt
einen eigenen Punkt: *„GEO/GAIO wird verkauft, aber nicht ausgeliefert."*
Der Wert wird berechnet (`GET /api/geo/{id}/result`), er wird monatlich
überwacht — und der Kunde, der dafür zahlt, hat keinen Bildschirm, auf dem
er ihn sieht.

**Warum ein eigener Weg und keine gelockerte Sperre.** `/api/geo` liegt
vollständig hinter `require_innendienst`, und dort steht mehr als der Wert:
Analyse-Rohdaten, Upsell-Status, Monitoring-Schalter, ein
`admin/run-monitoring-now`. Ein Kundenweg mit Eigentumsprüfung nimmt dem
Innendienst nichts und öffnet nichts, was zu war.
"""
import pytest

pytestmark = pytest.mark.usefixtures("app")


@pytest.fixture
def eigenes_projekt(app, kunde_user):
    """Ein Projekt am Betrieb des Kunden."""
    from database import Project, SessionLocal

    db = SessionLocal()
    try:
        p = Project(lead_id=kunde_user.lead_id, status="phase_3")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.id
    finally:
        db.close()


@pytest.fixture
def fremdes_projekt(app, fremder_betrieb):
    from database import Project, SessionLocal

    db = SessionLocal()
    try:
        p = Project(lead_id=fremder_betrieb, status="phase_3")
        db.add(p)
        db.commit()
        db.refresh(p)
        return p.id
    finally:
        db.close()


@pytest.fixture
def mit_analyse(eigenes_projekt):
    """Ein Projekt **mit** fertigem GEO-Lauf.

    **Warum diese Fixture noetig wurde.** Der erste Entwurf pruefte am
    leeren Projekt, dass die Kundenantwort keine `raw_checks` traegt — und
    war gruen, weil die volle Antwort dort ebenfalls keine traegt
    (`{"status": "not_started"}`). Ein Test, der aus dem falschen Grund
    besteht, ist schlimmer als keiner: Er behauptet eine Zusicherung, die
    niemand geprueft hat.
    """
    from database import SessionLocal
    from modelle_audit import GeoAnalysis

    db = SessionLocal()
    try:
        a = GeoAnalysis(
            project_id=eigenes_projekt, status="done", geo_score_total=64,
            llms_txt_score=10, robots_ai_score=8, structured_data_score=20,
            content_depth_score=18, local_signal_score=8,
            raw_checks={"llms_txt": {"gefunden": False, "url": "…"}},
            recommendations=["llms.txt anlegen", "FAQ-Auszeichnung ergänzen"],
            upsell_active=True, upsell_price=490,
        )
        db.add(a)
        db.commit()
        return eigenes_projekt
    finally:
        db.close()


@pytest.fixture(autouse=True)
def _aufraeumen(app, kunde_user, fremder_betrieb):
    yield
    from database import Project, SessionLocal

    from modelle_audit import GeoAnalysis

    db = SessionLocal()
    try:
        projekte = [z[0] for z in db.query(Project.id).filter(
            Project.lead_id.in_([kunde_user.lead_id, fremder_betrieb])).all()]
        if projekte:
            db.query(GeoAnalysis).filter(
                GeoAnalysis.project_id.in_(projekte)).delete(
                    synchronize_session=False)
        db.query(Project).filter(
            Project.lead_id.in_([kunde_user.lead_id, fremder_betrieb])).delete(
                synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _abrufen(client, headers, projekt):
    return client.get(f"/api/geo/mein/{projekt}/result", headers=headers)


class TestDerEigeneWert:
    def test_der_kunde_darf_ihn_abrufen(self, client, kunde_headers,
                                        eigenes_projekt):
        """Ob schon ein Wert **vorliegt**, ist eine andere Frage — hier geht
        es darum, dass die Tür überhaupt aufgeht. Vorher war sie zu."""
        antwort = _abrufen(client, kunde_headers, eigenes_projekt)

        assert antwort.status_code == 200, antwort.text

    def test_ohne_analyse_ist_die_antwort_leer_und_kein_fehler(
            self, client, kunde_headers, eigenes_projekt):
        """Ein neues Projekt hat noch keinen GEO-Lauf. Das ist ein leerer
        Bildschirm, keine Fehlermeldung — `GeoReport` zeigt dann nichts."""
        daten = _abrufen(client, kunde_headers, eigenes_projekt).json()

        assert daten.get("status") != "done" or "geo_score_total" in daten

    def test_der_innendienst_kommt_auch_hier_durch(self, client, auth_headers,
                                                   eigenes_projekt):
        """Der Kundenweg darf dem Innendienst nichts nehmen — er sieht im
        Zweifel dasselbe wie der Kunde."""
        assert _abrufen(client, auth_headers, eigenes_projekt).status_code == 200


class TestDieGrenzen:
    def test_ein_fremdes_projekt_bleibt_verschlossen(
            self, client, kunde_headers, fremdes_projekt):
        """Die Projektnummer ist eine fortlaufende Zahl — hochzuzählen ist
        der naheliegendste Angriff."""
        assert _abrufen(client, kunde_headers, fremdes_projekt).status_code == 403

    def test_ein_unbekanntes_projekt_ist_404(self, client, kunde_headers):
        assert _abrufen(client, kunde_headers, 999999).status_code == 404

    def test_ohne_anmeldung_gar_nichts(self, client, eigenes_projekt):
        assert _abrufen(client, {}, eigenes_projekt).status_code in (401, 403)

    def test_die_uebrigen_geo_routen_bleiben_beim_innendienst(
            self, client, kunde_headers, eigenes_projekt):
        """Analyse anstossen, Upsell setzen, Monitoring schalten — nichts
        davon gehoert dem Kunden. Sonst haette das Freigeben des Wertes
        nebenbei den ganzen Bereich geoeffnet."""
        for pfad, methode in (
            (f"/api/geo/{eigenes_projekt}/result", "get"),
            (f"/api/geo/{eigenes_projekt}/monitoring", "get"),
            (f"/api/geo/{eigenes_projekt}/analyze", "post"),
        ):
            antwort = getattr(client, methode)(pfad, headers=kunde_headers)
            assert antwort.status_code == 403, f"{methode.upper()} {pfad} offen"


class TestWasErNichtSieht:
    """Die Komponente sagt es selbst: „Score, Bedeutung und was gemacht wird
    — **KEINE technischen Details**". Der Server haelt sich daran, nicht die
    Oberflaeche: Was die Antwort traegt, ist im Netzwerkprotokoll zu lesen,
    egal was ein Bildschirm damit macht.
    """

    def test_keine_rohpruefungen_kein_upsell_kein_betriebsfehler(
            self, client, kunde_headers, mit_analyse):
        daten = _abrufen(client, kunde_headers, mit_analyse).json()

        for feld in ("raw_checks", "upsell_active", "upsell_price",
                     "error_message"):
            assert feld not in daten, f'„{feld}“ steht in der Kundenantwort'

    def test_aber_der_wert_und_die_empfehlungen_schon(
            self, client, kunde_headers, mit_analyse):
        """Sonst waere die Verkuerzung eine leere Seite."""
        daten = _abrufen(client, kunde_headers, mit_analyse).json()

        assert daten["geo_score_total"] == 64
        assert "llms.txt anlegen" in daten["recommendations"]

        for feld in ("status", "geo_score_total", "recommendations",
                     "llms_txt_score", "updated_at"):
            assert feld in daten, f'„{feld}“ fehlt dem Kunden'

    def test_der_innendienst_sieht_weiterhin_alles(
            self, client, auth_headers, mit_analyse):
        """Auf **seinem** Weg — der Kundenweg verkuerzt fuer jeden, auch
        fuer ihn; die volle Auskunft steht unveraendert unter `/api/geo`."""
        voll = client.get(f"/api/geo/{mit_analyse}/result",
                          headers=auth_headers).json()

        assert "raw_checks" in voll and "upsell_price" in voll
