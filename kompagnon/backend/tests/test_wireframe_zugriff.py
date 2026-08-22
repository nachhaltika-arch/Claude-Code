"""Die Sperre der Wireframe-Routen bleibt, wo sie ist (L-09).

**Entstanden aus einem Fehlalarm — und deshalb erst recht wertvoll.** Beim
Schliessen der Testluecke „Wireframe" fiel auf, dass alle sechs
projektbezogenen Routen unter `/api/projects/{id}/wireframe…` in ihrer
Signatur `require_any_auth` tragen. Das gibt nur den angemeldeten Nutzer
zurueck, ohne zu pruefen, ob ihm das Projekt gehoert — dieselbe Bauart wie
`GET /api/invoices` aus PR #45, wo jeder Angemeldete die Abrechnungsdaten
aller Betriebe lesen konnte.

**Der Schluss war falsch, und der Test hat ihn widerlegt, bevor jemand
etwas repariert haette.** Der `wireframe_router` traegt
`dependencies=[Depends(require_innendienst)]` auf **Router**-Ebene
(`component_library.py:1509`), und die greift vor jeder Signatur. Wer nur
die Funktionskoepfe liest, sieht die halbe Sperre — genau das ist hier
passiert.

Die Signaturen sind seither auf `require_innendienst` gezogen, damit
Funktionskopf und Wirklichkeit dasselbe sagen. Eine schwaechere Angabe
neben einer strengeren Sperre ist keine Luecke, aber eine Falle fuer den
naechsten Leser.

**Was diese Tests halten:** Dass die Sperre bleibt. Verschwindet die
Router-Zeile — beim Umbau, beim Aufteilen der Datei, beim Verschieben einer
Route —, faellt sie ohne einen einzigen roten Punkt weg, und dann trifft
zu, was hier faelschlich vermutet wurde: Lesen und **Ueberschreiben**
fremder Entwuerfe. Das Ueberschreiben wiegt schwerer als das Lesen; es ist
kein Einblick, sondern Datenverlust bei einem fremden Kunden.

**Warum Innendienst und keine Eigentumspruefung.** Nachgemessen ruft kein
Kundenweg diese Routen auf: `WireframeView` haengt in `ComponentLibrary`
(`roles={['admin']}`), `OnlineFertigEditor` unter `/app/projects/:id`
(`roles={['admin','auditor']}`). Der Website-Bau ist Innendienstarbeit.
"""
import pytest


PROJEKTWEGE = [
    ("get",  "/api/projects/{id}/wireframe", None),
    ("post", "/api/projects/{id}/wireframe", {"pages": []}),
    ("post", "/api/projects/{id}/wireframe/generate", {}),
    ("post", "/api/projects/{id}/wireframe/variant", {}),
    ("post", "/api/projects/{id}/wireframe/compose", {}),
]


@pytest.fixture
def projekt(app):
    from database import Lead, Project, SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM leads WHERE company_name = 'L87 Betrieb'"))
        db.commit()
        lead = Lead(company_name="L87 Betrieb")
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
                        "(SELECT id FROM leads WHERE company_name = 'L87 Betrieb')"))
        db.execute(text("DELETE FROM leads WHERE company_name = 'L87 Betrieb'"))
        db.commit()
    finally:
        db.close()


class TestDerKundeKommtNichtHeran:
    @pytest.mark.parametrize("methode,pfad,rumpf", PROJEKTWEGE)
    def test_kein_kunde_auf_fremden_entwuerfen(
            self, client, kunde_headers, projekt, methode, pfad, rumpf):
        """Lesen **und** Schreiben. Das Schreiben wiegt schwerer: Es ist kein
        Einblick, sondern Datenverlust bei einem fremden Kunden."""
        adresse = pfad.format(id=projekt)
        antwort = getattr(client, methode)(
            adresse, headers=kunde_headers, **({"json": rumpf} if rumpf is not None else {}))

        assert antwort.status_code == 403, (
            f"{methode.upper()} {adresse} → {antwort.status_code}: "
            f"der Kunde kommt an ein fremdes Projekt")

    @pytest.mark.parametrize("methode,pfad,rumpf", PROJEKTWEGE)
    def test_ohne_anmeldung_erst_recht_nicht(
            self, client, projekt, methode, pfad, rumpf):
        adresse = pfad.format(id=projekt)
        antwort = getattr(client, methode)(
            adresse, **({"json": rumpf} if rumpf is not None else {}))

        assert antwort.status_code in (401, 403)


class TestDerInnendienstArbeitetWeiter:
    def test_der_admin_liest_den_entwurf(self, client, auth_headers, projekt):
        """Die Sperre darf die Arbeit nicht mitnehmen, fuer die es sie gibt."""
        antwort = client.get(f"/api/projects/{projekt}/wireframe",
                             headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]

    def test_und_speichert_ihn(self, client, auth_headers, projekt):
        antwort = client.post(f"/api/projects/{projekt}/wireframe",
                              json={"pages": []}, headers=auth_headers)

        assert antwort.status_code == 200, antwort.text[:200]
