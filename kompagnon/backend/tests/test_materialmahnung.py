# -*- coding: utf-8 -*-
"""Die Materialmahnung sagt, **welche** Materialien fehlen (L-159, Schritt 5).

**Der Anlass des ganzen Eintrags.** `job_check_missing_materials` schickte dem
Betrieb gestaffelt die Nachricht, dass Materialien fehlen — ohne zu sagen
welche, und ohne dass er den Stand nachsehen konnte. Vier von fuenf Schritten
sind seit dem 04./06.09. gebaut: Katalog als Daten, Stand je Punkt, Anzeige im
Konto, Fristrechnung. Dieser hier fehlte.

**Zwei Fehler stecken darin, und der zweite ist der groessere.**

Erstens **sagt die Vorlage etwas anderes** als der Vertrag: Sie listet fest
„Unternehmensfotos, Leistungsbeschreibung, Team-Informationen, Oeffnungszeiten,
Kontaktdaten" — eine zweite Fassung dessen, was wir brauchen, neben M1 bis M11.

Zweitens **prueft der Job gar nicht, ob etwas fehlt.** Er mahnt nach Tagen. Ein
Betrieb, der alles geliefert hat, bekommt die Mahnung trotzdem — und das ist
die Sorte Mail, nach der niemand mehr eine Mail von uns ernst nimmt.
"""
import pytest


@pytest.fixture
def projekt_in_phase_2(app, kunde_user):
    from datetime import datetime, timedelta

    from database import MitwirkungStand, Project, SessionLocal

    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.lead_id == kunde_user.lead_id).first()
        if not p:
            p = Project(lead_id=kunde_user.lead_id)
            db.add(p)
        p.status = "phase_2"
        p.start_date = datetime.utcnow() - timedelta(days=9)
        db.commit(); db.refresh(p)
        db.query(MitwirkungStand).filter_by(project_id=p.id).delete()
        db.commit()
        return p.id
    finally:
        db.close()


def _alle_erledigt(projekt_id):
    from datetime import datetime

    from database import MitwirkungStand, Project, SessionLocal
    from services import mitwirkung as kat

    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == projekt_id).first()
        for punkt in kat.gilt_fuer(set()):
            if punkt.wirkung != kat.FRISTBEGINN:
                continue
            db.add(MitwirkungStand(project_id=p.id, kennung=punkt.kennung,
                                   erledigt_am=datetime.utcnow(),
                                   bestaetigt_von="test@example.org"))
        db.commit()
    finally:
        db.close()


def test_wer_alles_geliefert_hat_bekommt_keine_mahnung(projekt_in_phase_2):
    """**Der zweite und groessere Fehler.** Der Job mahnte nach Tagen, nicht
    nach Sachlage — eine Mahnung an jemanden, der alles geliefert hat, ist die
    Sorte Mail, nach der niemand mehr eine Mail von uns ernst nimmt."""
    from automations import scheduler_kontakt as sk

    _alle_erledigt(projekt_in_phase_2)
    versendet = []
    sk._send_phase_email = lambda pid, key, **kw: versendet.append((pid, key))

    sk.job_check_missing_materials()

    assert versendet == [], "ohne fehlende Punkte darf keine Mahnung hinausgehen"


def test_wer_etwas_schuldet_bekommt_die_punkte_beim_namen(projekt_in_phase_2):
    """**Der Anlass.** „Materialien fehlen" ohne die Liste laesst den Betrieb
    raten, und raten tut er nicht — er legt die Mail weg."""
    from automations import scheduler_kontakt as sk

    gesendet = {}
    sk._send_phase_email = lambda pid, key, **kw: gesendet.update(
        {"pid": pid, "key": key, "kw": kw})

    sk.job_check_missing_materials()

    assert gesendet, "mit offenen Punkten muss die Mahnung hinausgehen"
    liste = gesendet["kw"].get("zusatz", {}).get("fehlende_punkte", "")
    assert liste, "die Mahnung nennt die fehlenden Punkte nicht"
    # Sie kommen aus dem Katalog, in Kundensprache — nicht als „M3".
    assert "Logo und Bilder" in liste or "Ihre Texte" in liste
    assert "M3" not in liste, "die Kennung sagt dem Betrieb nichts"


def test_die_vorlage_traegt_keine_zweite_liste_mehr():
    """**Zwei Fassungen dessen, was wir brauchen, laufen auseinander.** Die
    Vorlage listete fest fuenf Dinge, die im Mitwirkungskatalog so nicht
    stehen — und der Katalog ist der, der im Angebot steht."""
    from automations.email_templates import TEMPLATES

    rumpf = TEMPLATES["material_reminder"]["body"]

    assert "{fehlende_punkte}" in rumpf
    for alt in ("Unternehmensfotos", "Team-Informationen", "Öffnungszeiten"):
        assert alt not in rumpf, f"{alt} steht nicht im Mitwirkungskatalog"


def test_die_mahnung_verweist_auf_die_seite_im_konto(projekt_in_phase_2):
    """Wer lesen soll, was fehlt, soll es auch abhaken koennen — die Seite
    gibt es seit dem 04.09."""
    from automations.email_templates import TEMPLATES

    rumpf = TEMPLATES["material_reminder"]["body"]
    assert "{upload_link}" in rumpf
