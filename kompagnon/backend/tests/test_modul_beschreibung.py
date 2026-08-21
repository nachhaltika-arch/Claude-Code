"""Ein Modul sagt, worum es geht — und zeigt ein Bild.

Aus dem Memberspot-Audit vom 19.08.2026
(`docs/akademie-vorbild-memberspot.md`): Dort trägt **jedes** der zwölf Module
eine Beschreibungszeile und ein Vorschaubild.

    „Dieses Modul schafft den Kontext für neue Mitarbeiter/innen, …"

`AcademyModule` hatte nur `title`, `position`, `is_locked`, `sort_order`. Eine
Modulliste war damit eine Aufzählung von Überschriften — man musste ein Modul
aufklappen, um zu ahnen, was drinsteht.

Zwei Spalten, und die Liste wird lesbar. Das war der billigste Gewinn auf der
Empfehlungsliste, deshalb kommt er zuerst.

**Warum diese Datei mehr prüft als „Feld wird gespeichert":**

Module lassen sich über **zwei** Wege anlegen — `POST /api/academy/modules`
und `POST /api/academy/courses/{id}/modules`. Zwei Wege, die dasselbe tun, sind
genau die Stelle, an der ein neues Feld an einem davon vergessen wird; dieselbe
Bauart hat am 18.08. die Lektionen zerlegt und am 19.08. die Zugriffsrechte.
Der letzte Test hält deshalb fest, dass beide Wege dieselben Schlüssel
annehmen — nicht, dass sie es heute tun.

Dazu die Rundreise durch die Datenbank, wie in [[test_spalten_kommen_an]]:
Ein Feld, das nur im Modell steht, geht beim Speichern still verloren.
"""
import pytest

BESCHREIBUNG = "Dieses Modul schafft den Kontext für neue Betriebe."
BILD = "https://example.invalid/modul.jpg"


@pytest.fixture
def kurs_id(client, auth_headers):
    antwort = client.post(
        "/api/academy/courses",
        json={"title": "Testkurs Modulbeschreibung"},
        headers=auth_headers,
    )
    assert antwort.status_code in (200, 201), antwort.text
    return antwort.json()["id"]


# ── Anlegen ───────────────────────────────────────────────────────────

def test_der_kursweg_nimmt_beschreibung_und_bild(client, auth_headers, kurs_id):
    # Act
    antwort = client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Modul I", "description": BESCHREIBUNG,
              "thumbnail_url": BILD},
        headers=auth_headers,
    )

    # Assert
    assert antwort.status_code in (200, 201), antwort.text
    modul = antwort.json()
    assert modul["description"] == BESCHREIBUNG
    assert modul["thumbnail_url"] == BILD


def test_der_zweite_anlegeweg_auch(client, auth_headers, kurs_id):
    """`POST /modules` — der Weg, an dem ein Feld gern vergessen wird."""
    # Act
    antwort = client.post(
        "/api/academy/modules",
        json={"course_id": kurs_id, "title": "Modul II",
              "description": BESCHREIBUNG, "thumbnail_url": BILD},
        headers=auth_headers,
    )

    # Assert
    assert antwort.status_code in (200, 201), antwort.text
    modul = antwort.json()
    assert modul["description"] == BESCHREIBUNG
    assert modul["thumbnail_url"] == BILD


def test_ohne_angabe_bleibt_es_leer_nicht_null(client, auth_headers, kurs_id):
    """Leer ist ein Wert, `None` ist eine Fallunterscheidung in der Oberfläche."""
    # Act
    antwort = client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Modul ohne alles"},
        headers=auth_headers,
    )

    # Assert
    modul = antwort.json()
    assert modul["description"] == ""
    assert modul["thumbnail_url"] == ""


# ── Ändern und Lesen ──────────────────────────────────────────────────

def test_beides_laesst_sich_nachtragen(client, auth_headers, kurs_id):
    # Arrange
    modul_id = client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Modul III"}, headers=auth_headers,
    ).json()["id"]

    # Act
    antwort = client.put(
        f"/api/academy/modules/{modul_id}",
        json={"description": BESCHREIBUNG, "thumbnail_url": BILD},
        headers=auth_headers,
    )

    # Assert
    assert antwort.status_code == 200, antwort.text
    assert antwort.json()["description"] == BESCHREIBUNG
    assert antwort.json()["thumbnail_url"] == BILD


def test_die_liste_traegt_die_felder_mit(client, auth_headers, kurs_id):
    """Genau dafür ist das Feld da — die Liste soll lesbar werden."""
    # Arrange
    client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Modul IV", "description": BESCHREIBUNG,
              "thumbnail_url": BILD},
        headers=auth_headers,
    )

    # Act
    antwort = client.get(
        f"/api/academy/courses/{kurs_id}/modules", headers=auth_headers)

    # Assert
    assert antwort.status_code == 200
    modul = [m for m in antwort.json() if m["title"] == "Modul IV"][0]
    assert modul["description"] == BESCHREIBUNG
    assert modul["thumbnail_url"] == BILD


# ── Die Rundreise durch die Datenbank ─────────────────────────────────

def test_der_wert_ueberlebt_das_neuladen(app, client, auth_headers, kurs_id):
    """Ein Feld, das nur im Modell steht, verschwindet beim Speichern still."""
    from database import SessionLocal, AcademyModule

    # Arrange
    modul_id = client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Modul V", "description": BESCHREIBUNG,
              "thumbnail_url": BILD},
        headers=auth_headers,
    ).json()["id"]

    # Act
    db = SessionLocal()
    try:
        db.expire_all()
        modul = db.query(AcademyModule).filter(
            AcademyModule.id == modul_id).first()

        # Assert
        assert modul.description == BESCHREIBUNG
        assert modul.thumbnail_url == BILD
    finally:
        db.close()


# ── Die Richtung, nicht der Einzelfall ────────────────────────────────

def test_beide_anlegewege_nehmen_dieselben_schluessel(app):
    """Zwei Wege für dieselbe Sache — der zweite wird vergessen.

    Geprüft wird an der Quelle statt an einem Aufruf: Ein künftiges Feld soll
    hier auffallen, nicht erst, wenn ein Nutzer es an einem der beiden Wege
    vermisst.
    """
    import inspect
    import re

    from routers import academy

    def schluessel(funktion):
        quelle = inspect.getsource(funktion)
        return set(re.findall(r"data\.get\(\s*'([a-z_]+)'", quelle))

    ueber_kurs = schluessel(academy.create_module_for_course)
    direkt = schluessel(academy.create_module)

    # `course_id` kommt beim Kursweg aus dem Pfad, nicht aus dem Rumpf.
    assert ueber_kurs == direkt - {"course_id"}, (
        f"Die zwei Anlegewege sind auseinandergelaufen: "
        f"nur über Kurs {ueber_kurs - direkt}, nur direkt {direkt - ueber_kurs}"
    )
