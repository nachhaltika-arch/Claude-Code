"""Eine Lektion muss sich anlegen lassen.

Befund vom 18.08.2026, am laufenden Backend geprueft: `POST
/api/academy/modules/{id}/lessons` antwortet mit **500**.

    TypeError: 'checklist_items_json' is an invalid keyword argument
    for AcademyLesson

Der Router uebergibt das Feld beim Anlegen, das Modell kennt es nicht — die
Spalte existiert nur in der Datenbank, angelegt von `migrations_runtime.py::run_migrations`
(Zeile 251). Damit ist der Kern der Akademie kaputt: Kurse und Module lassen
sich anlegen, **Inhalte nicht**. Beide Kurseditoren rufen denselben Endpunkt.

Warum es niemandem auffiel: Die Oberflaeche zeigt Fehler beim Speichern nicht
an — `catch (e) { console.error(e); }` in beiden Editoren. Der Knopf hoert auf
zu drehen, und nichts sagt, dass es scheiterte. Dieselbe Bauart wie L-36.

Warum kein Test es fand: Das Testschema entsteht aus den Modellen
(`create_all`), also fehlte die Spalte dort ebenso — und angefasst wurde der
Endpunkt nie.
"""


def _kurs_und_modul(client, auth_headers):
    kurs = client.post(
        "/api/academy/courses",
        json={"title": "Testkurs Lektionen", "description": "", "target_audience": "both"},
        headers=auth_headers,
    )
    assert kurs.status_code in (200, 201), kurs.text
    kurs_id = kurs.json()["id"]

    modul = client.post(
        f"/api/academy/courses/{kurs_id}/modules",
        json={"title": "Testmodul"},
        headers=auth_headers,
    )
    assert modul.status_code in (200, 201), modul.text
    return kurs_id, modul.json()["id"]


def test_eine_lektion_laesst_sich_anlegen(client, auth_headers):
    _, modul_id = _kurs_und_modul(client, auth_headers)

    antwort = client.post(
        f"/api/academy/modules/{modul_id}/lessons",
        json={"title": "Erste Lektion", "type": "text", "content_text": "Hallo"},
        headers=auth_headers,
    )

    assert antwort.status_code in (200, 201), antwort.text
    assert antwort.json()["title"] == "Erste Lektion"


def test_die_lektion_taucht_im_kurs_auf(client, auth_headers):
    """Anlegen genuegt nicht — sie muss auch am Kurs haengen."""
    kurs_id, modul_id = _kurs_und_modul(client, auth_headers)
    client.post(
        f"/api/academy/modules/{modul_id}/lessons",
        json={"title": "Sichtbare Lektion", "type": "text"},
        headers=auth_headers,
    )

    kurs = client.get(f"/api/academy/courses/{kurs_id}", headers=auth_headers)

    titel = [
        lektion["title"]
        for modul in kurs.json().get("modules", [])
        for lektion in modul.get("lessons", [])
    ]
    assert "Sichtbare Lektion" in titel, kurs.json()


def test_checklistenpunkte_einer_lektion_bleiben_erhalten(client, auth_headers):
    # Das Feld, ueber das der Aufruf stolperte. Der Modul-Editor schickt es.
    _, modul_id = _kurs_und_modul(client, auth_headers)

    angelegt = client.post(
        f"/api/academy/modules/{modul_id}/lessons",
        json={"title": "Mit Liste", "type": "text",
              "checklist_items": ["Erstens", "Zweitens"]},
        headers=auth_headers,
    )
    assert angelegt.status_code in (200, 201), angelegt.text

    gelesen = client.get(f"/api/academy/lessons/{angelegt.json()['id']}", headers=auth_headers)

    assert gelesen.json().get("checklist_items") == ["Erstens", "Zweitens"]
