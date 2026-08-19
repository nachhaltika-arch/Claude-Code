"""Eine Zuweisung, die nichts bewirkt, ist keine Zuweisung.

Befund vom 19.08.2026 beim Abschluss der Akademie. Zwei Dinge waren gebaut,
gespeichert, bedienbar — und **von keinem Lesepfad konsultiert**:

- `AcademyCustomerAccess` (Tabelle, drei Endpunkte, Oberfläche im Kundenblatt).
  `list_courses` filtert nach Rolle, Zielgruppe und `is_published` — die
  Zuweisung kommt darin **nicht vor**. Einem Kunden einen Kurs zuzuweisen
  bewirkte also gar nichts; er sah ohnehin jeden veröffentlichten Kundenkurs.
- `AcademyModule.is_locked` — gespeichert, im Admin als Häkchen „Gesperrt"
  anklickbar, mitserialisiert, und nirgends gelesen. Ein Schalter, der nichts
  schaltet.

Es ist dieselbe Familie wie L-05: eine Rechtematrix, die niemand fragt.

Statt ein drittes Feld daneben zu erfinden, bekommen die vorhandenen ihre
Bedeutung — die aus dem Memberspot-Vergleich
(`docs/akademie-vorbild-memberspot.md`), wo genau zwei Zustände existieren:

    veröffentlicht  → für jeden, der den Kurs hat
    „Manuell"       → nur für ausdrücklich Zugewiesene

Bei uns heißt der zweite `is_locked`. Neu ist nur, dass er wirkt — und dass es
ihn jetzt auch am **Kurs** gibt, damit die Kurszuweisung etwas bedeutet.

**Was diese Datei vor allem festhält, ist die Nicht-Änderung:** Ein Kurs oder
Modul ohne Sperre bleibt sichtbar wie bisher. Wäre die Zuweisung ab sofort
zwingend, verschwände der ganze Bestand vor den Augen der heutigen Kunden —
und das ist kein Rechtekonzept, das ist ein Ausfall.
"""
import pytest

from database import (
    SessionLocal, AcademyCourse, AcademyModule, AcademyLesson,
    AcademyCustomerAccess, AcademyModuleAccess,
)

TITEL_OFFEN = "Zuweisungsprobe offen"
TITEL_GESPERRT = "Zuweisungsprobe gesperrt"


@pytest.fixture
def db(app):
    sitzung = SessionLocal()
    try:
        yield sitzung
    finally:
        sitzung.close()


@pytest.fixture(autouse=True)
def aufraeumen(db):
    yield
    for titel in (TITEL_OFFEN, TITEL_GESPERRT):
        for kurs in db.query(AcademyCourse).filter(AcademyCourse.title == titel).all():
            db.query(AcademyCustomerAccess).filter(
                AcademyCustomerAccess.course_id == kurs.id).delete(synchronize_session=False)
            for modul in db.query(AcademyModule).filter(
                    AcademyModule.course_id == kurs.id).all():
                db.query(AcademyModuleAccess).filter(
                    AcademyModuleAccess.module_id == modul.id).delete(synchronize_session=False)
                db.query(AcademyLesson).filter(
                    AcademyLesson.module_id == modul.id).delete(synchronize_session=False)
                db.delete(modul)
            db.delete(kurs)
    db.commit()


def _kurs(db, titel, gesperrt=False):
    kurs = AcademyCourse(
        title=titel, is_published=True, target_audience='both',
        is_locked=gesperrt,
    )
    db.add(kurs)
    db.commit()
    db.refresh(kurs)
    return kurs


def _modul(db, kurs_id, titel, gesperrt=False, lektionen=0, minuten=0):
    modul = AcademyModule(course_id=kurs_id, title=titel, is_locked=gesperrt)
    db.add(modul)
    db.commit()
    db.refresh(modul)
    for i in range(lektionen):
        db.add(AcademyLesson(module_id=modul.id, title=f"{titel} L{i}",
                             duration_minutes=minuten))
    db.commit()
    return modul


def _titel_im_kursverzeichnis(client, headers):
    antwort = client.get("/api/academy/courses", headers=headers)
    assert antwort.status_code == 200, antwort.text
    return [k["title"] for k in antwort.json()]


# ── Kursebene: die Nicht-Änderung zuerst ──────────────────────────────

def test_ein_offener_kurs_bleibt_ohne_zuweisung_sichtbar(client, kunde_headers, db):
    """Der wichtigste Test hier: Der Bestand darf nicht verschwinden."""
    # Arrange
    _kurs(db, TITEL_OFFEN)

    # Act / Assert
    assert TITEL_OFFEN in _titel_im_kursverzeichnis(client, kunde_headers)


def test_ein_gesperrter_kurs_ist_ohne_zuweisung_nicht_da(client, kunde_headers, db):
    # Arrange
    _kurs(db, TITEL_GESPERRT, gesperrt=True)

    # Act / Assert
    assert TITEL_GESPERRT not in _titel_im_kursverzeichnis(client, kunde_headers)


def test_mit_zuweisung_ist_der_gesperrte_kurs_da(client, kunde_headers, kunde_user, db):
    # Arrange
    kurs = _kurs(db, TITEL_GESPERRT, gesperrt=True)
    db.add(AcademyCustomerAccess(customer_id=kunde_user.id, course_id=kurs.id))
    db.commit()

    # Act / Assert
    assert TITEL_GESPERRT in _titel_im_kursverzeichnis(client, kunde_headers)


def test_der_innendienst_sieht_auch_gesperrte_kurse(client, auth_headers, db):
    """Wer sie pflegt, muss sie sehen — sonst ist der Kurs unbearbeitbar."""
    # Arrange
    _kurs(db, TITEL_GESPERRT, gesperrt=True)

    # Act / Assert
    assert TITEL_GESPERRT in _titel_im_kursverzeichnis(client, auth_headers)


# ── Modulebene ────────────────────────────────────────────────────────

def _modultitel(client, headers, kurs_id):
    antwort = client.get(f"/api/academy/courses/{kurs_id}", headers=headers)
    assert antwort.status_code == 200, antwort.text
    return [m["title"] for m in antwort.json()["modules"]]


def test_ein_offenes_modul_bleibt_sichtbar(client, kunde_headers, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Pflichtmodul")

    # Act / Assert
    assert "Pflichtmodul" in _modultitel(client, kunde_headers, kurs.id)


def test_ein_gesperrtes_modul_fehlt_ohne_zuweisung(client, kunde_headers, db):
    """Der Vertriebler sieht die Buchhaltungsschulung nicht."""
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Pflichtmodul")
    _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)

    # Act
    titel = _modultitel(client, kunde_headers, kurs.id)

    # Assert
    assert "Pflichtmodul" in titel
    assert "Abteilung Buchhaltung" not in titel


def test_mit_modulzuweisung_ist_es_da(client, kunde_headers, kunde_user, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    modul = _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)
    db.add(AcademyModuleAccess(customer_id=kunde_user.id, module_id=modul.id))
    db.commit()

    # Act / Assert
    assert "Abteilung Buchhaltung" in _modultitel(client, kunde_headers, kurs.id)


def test_der_innendienst_sieht_alle_module(client, auth_headers, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)

    # Act / Assert
    assert "Abteilung Buchhaltung" in _modultitel(client, auth_headers, kurs.id)


def test_auch_die_modulliste_filtert(client, kunde_headers, db):
    """Zwei Wege zu denselben Modulen — beide müssen filtern."""
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)

    # Act
    antwort = client.get(f"/api/academy/courses/{kurs.id}/modules",
                         headers=kunde_headers)

    # Assert
    assert antwort.status_code == 200
    assert [m["title"] for m in antwort.json()] == []


# ── Die Zuweisungs-Endpunkte ──────────────────────────────────────────

def test_zuweisen_auflisten_entziehen(client, auth_headers, kunde_user, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    modul = _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)
    basis = f"/api/academy/customer/{kunde_user.id}/modules"

    # Act — zuweisen
    zuweisen = client.post(f"{basis}/{modul.id}/assign", headers=auth_headers)
    assert zuweisen.status_code in (200, 201), zuweisen.text

    # Assert — auflisten
    liste = client.get(basis, headers=auth_headers)
    assert liste.status_code == 200
    assert [m["module_id"] for m in liste.json()] == [modul.id]

    # Act — zweimal zuweisen geht nicht
    assert client.post(f"{basis}/{modul.id}/assign",
                       headers=auth_headers).status_code == 409

    # Act — entziehen
    assert client.delete(f"{basis}/{modul.id}",
                         headers=auth_headers).status_code == 200
    assert client.get(basis, headers=auth_headers).json() == []


def test_ein_kunde_darf_sich_nicht_selbst_zuweisen(client, kunde_headers, kunde_user, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    modul = _modul(db, kurs.id, "Abteilung Buchhaltung", gesperrt=True)

    # Act
    antwort = client.post(
        f"/api/academy/customer/{kunde_user.id}/modules/{modul.id}/assign",
        headers=kunde_headers)

    # Assert
    assert antwort.status_code in (401, 403)


# ── Die drei Zahlen ───────────────────────────────────────────────────

def test_der_kurs_nennt_module_lektionen_und_dauer(client, auth_headers, db):
    """Memberspot zeigt genau diese drei je Kurs — berechnet, nicht gespeichert."""
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Modul A", lektionen=3, minuten=5)
    _modul(db, kurs.id, "Modul B", lektionen=2, minuten=10)

    # Act
    antwort = client.get(f"/api/academy/courses/{kurs.id}", headers=auth_headers)

    # Assert
    daten = antwort.json()
    assert daten["module_count"] == 2
    assert daten["lesson_count"] == 5
    assert daten["duration_minutes"] == 35  # 3×5 + 2×10


def test_die_zahlen_stehen_auch_in_der_liste(client, auth_headers, db):
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)
    _modul(db, kurs.id, "Modul A", lektionen=2, minuten=4)

    # Act
    eintrag = [k for k in client.get("/api/academy/courses", headers=auth_headers).json()
               if k["id"] == kurs.id][0]

    # Assert
    assert eintrag["module_count"] == 1
    assert eintrag["lesson_count"] == 2
    assert eintrag["duration_minutes"] == 8


def test_ein_leerer_kurs_nennt_nullen_statt_zu_fehlen(client, auth_headers, db):
    """Sonst muss die Oberfläche zwei Fälle unterscheiden, wo einer reicht."""
    # Arrange
    kurs = _kurs(db, TITEL_OFFEN)

    # Act
    daten = client.get(f"/api/academy/courses/{kurs.id}", headers=auth_headers).json()

    # Assert
    assert daten["module_count"] == 0
    assert daten["lesson_count"] == 0
    assert daten["duration_minutes"] == 0


# ── Die Zweideutigkeit der Kundenkennung ──────────────────────────────

def test_die_zuweisung_ueber_die_betriebs_id_landet_beim_benutzer(
        client, auth_headers, kunde_user, db):
    """Das Kundenblatt weist unter `lead.id` zu, gelesen wird über `user.id`.

    Aufgelöst wird beim **Schreiben**: Der Endpunkt übersetzt die Betriebs-ID
    in die Benutzer-ID. Beim Lesen einfach beide zuzulassen wäre eine
    Hintertür — die zwei Zahlenräume laufen unabhängig und überschneiden sich.
    """
    # Arrange
    assert kunde_user.lead_id, "Fixture ohne Betrieb — der Fall ist nicht prüfbar"
    kurs = _kurs(db, TITEL_GESPERRT, gesperrt=True)

    # Act — zuweisen, wie es das Kundenblatt tut: mit der Betriebs-ID
    antwort = client.post(
        f"/api/academy/customer/{kunde_user.lead_id}/courses/{kurs.id}/assign",
        headers=auth_headers)
    assert antwort.status_code in (200, 201), antwort.text

    # Assert — gespeichert ist die Benutzer-ID
    zeile = db.query(AcademyCustomerAccess).filter(
        AcademyCustomerAccess.course_id == kurs.id).first()
    assert zeile.customer_id == kunde_user.id


def test_und_der_kunde_sieht_den_kurs_danach(client, auth_headers, kunde_headers,
                                             kunde_user, db):
    """Der Durchstich: zuweisen wie die Oberfläche, nachsehen wie der Kunde."""
    # Arrange
    kurs = _kurs(db, TITEL_GESPERRT, gesperrt=True)
    client.post(f"/api/academy/customer/{kunde_user.lead_id}/courses/{kurs.id}/assign",
                headers=auth_headers)

    # Act / Assert
    assert TITEL_GESPERRT in _titel_im_kursverzeichnis(client, kunde_headers)


def test_die_zuweisung_eines_anderen_kunden_oeffnet_nichts(client, kunde_headers,
                                                          kunde_user, db):
    """Die Sperre gilt je Kunde, nicht global."""
    # Arrange — eine Kennung, die sicher niemandem hier gehört
    fremd = kunde_user.id + 10_000
    kurs = _kurs(db, TITEL_GESPERRT, gesperrt=True)
    db.add(AcademyCustomerAccess(customer_id=fremd, course_id=kurs.id))
    db.commit()

    # Act / Assert
    assert TITEL_GESPERRT not in _titel_im_kursverzeichnis(client, kunde_headers)


def test_zwei_zahlenraeume_koennen_sich_ueberschneiden(kunde_user, fremder_betrieb):
    """Der Grund, warum beim Schreiben aufgelöst wird und nicht beim Lesen.

    Im Testbestand fiel die Betriebs-ID eines **fremden** Betriebs mit der
    Benutzer-ID unseres Kunden zusammen. Genau deshalb ist „beim Lesen einfach
    beide Kennungen zulassen" keine Brücke, sondern eine Hintertür — und
    genau deshalb bleibt für alte Zeilen, die noch eine Betriebs-ID enthalten,
    ein Rest offen (L-54).

    Dieser Test behauptet nichts über eine Kollision; er hält fest, dass die
    beiden Zahlen **unabhängig** vergeben werden und deshalb nichts über
    einander aussagen.
    """
    assert isinstance(kunde_user.id, int)
    assert isinstance(fremder_betrieb, int)
    assert kunde_user.lead_id is not None
