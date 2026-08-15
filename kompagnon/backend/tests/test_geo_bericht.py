"""
Was der GEO-Teil des Berichts behaupten darf.

Der Abschnitt „GEO & KI-Sichtbarkeit" führte fünf Prüfpunkte, von denen keiner
erhoben war, und die Roadmap machte daraus Aufträge. Ein Betrieb, dessen
robots.txt niemanden sperrt, las „robots.txt: GPTBot-Blockierung entfernen".
Wer das nachsieht und nichts findet, schließt, dass wir seine Seite nicht
gelesen haben — dasselbe wie beim Kandidatenauftritt am SHK-Maßstab.

Regel: gemessen wird angezeigt, nicht Gemessenes heißt „nicht erhoben" und
erzeugt keine Handlungsaufforderung.
"""
from services.pdf_generator import geo_pruefpunkte, roadmap_massnahmen


ERHOBEN_ALLES_GUT = {
    "llms_txt": True, "robots_ai_friendly": True, "structured_data": True,
}
ERHOBEN_MIT_LUECKEN = {
    "llms_txt": False, "robots_ai_friendly": False, "structured_data": False,
    "gesperrte_ki_crawler": ["GPTBot"],
}
NICHTS_ERHOBEN = {}


def _punkt(punkte, name):
    return next(p for p in punkte if p["pruefpunkt"] == name)


# ── Die Statusspalte ───────────────────────────────────────────────

def test_status_kommt_ohne_sonderzeichen_aus():
    # Arrange — jedes PDF ist in Helvetica gesetzt, dort fehlen ✓ und ✗
    for daten in (ERHOBEN_ALLES_GUT, ERHOBEN_MIT_LUECKEN, NICHTS_ERHOBEN):
        for punkt in geo_pruefpunkte(daten):
            # Act & Assert
            assert punkt["status"] in ("erfüllt", "offen", "nicht erhoben")
            assert all(ord(z) < 0x2000 for z in punkt["status"]), \
                f"„{punkt['status']}“ enthält ein Zeichen, das Helvetica nicht kennt"


def test_ohne_erhebung_steht_nicht_erhoben_und_keine_empfehlung():
    # Act
    punkte = geo_pruefpunkte(NICHTS_ERHOBEN)

    # Assert
    for punkt in punkte:
        assert punkt["status"] == "nicht erhoben"
        assert not punkt["empfehlung"], \
            f"„{punkt['pruefpunkt']}“ empfiehlt etwas, ohne gemessen zu haben"


def test_ki_erwaehnungen_werden_nicht_behauptet():
    # Arrange — dafür gibt es keine Erhebung, auch nicht bei vollem Scan
    punkte = geo_pruefpunkte(ERHOBEN_ALLES_GUT)

    # Act & Assert
    assert _punkt(punkte, "KI-Erwähnungen")["status"] == "nicht erhoben"
    assert _punkt(punkte, "Google AI Overview")["status"] == "nicht erhoben"


def test_erhobene_punkte_zeigen_ihr_ergebnis():
    # Act
    gut = geo_pruefpunkte(ERHOBEN_ALLES_GUT)
    luecken = geo_pruefpunkte(ERHOBEN_MIT_LUECKEN)

    # Assert
    assert _punkt(gut, "llms.txt vorhanden")["status"] == "erfüllt"
    assert _punkt(luecken, "llms.txt vorhanden")["status"] == "offen"
    assert _punkt(gut, "robots.txt KI-freundlich")["status"] == "erfüllt"
    assert not _punkt(gut, "robots.txt KI-freundlich")["empfehlung"], \
        "Wer niemanden sperrt, braucht keine Empfehlung zum Entsperren"


def test_die_gesperrten_crawler_werden_benannt():
    # Act
    punkt = _punkt(geo_pruefpunkte(ERHOBEN_MIT_LUECKEN), "robots.txt KI-freundlich")

    # Assert — nicht „GPTBot nicht blockieren" ins Blaue, sondern der Fund
    assert "GPTBot" in punkt["empfehlung"]


# ── Die Roadmap ────────────────────────────────────────────────────

def test_roadmap_verlangt_nichts_ungemessenes():
    # Act
    massnahmen = roadmap_massnahmen(NICHTS_ERHOBEN)

    # Assert
    alle = " ".join(m for phase in massnahmen.values() for m in phase)
    assert "GPTBot" not in alle
    assert "llms.txt anlegen" not in alle


def test_roadmap_nennt_die_gptbot_sperre_nur_wenn_es_eine_gibt():
    # Act
    mit = " ".join(m for p in roadmap_massnahmen(ERHOBEN_MIT_LUECKEN).values() for m in p)
    ohne = " ".join(m for p in roadmap_massnahmen(ERHOBEN_ALLES_GUT).values() for m in p)

    # Assert
    assert "GPTBot" in mit
    assert "GPTBot" not in ohne


def test_roadmap_bleibt_bei_erfuellten_punkten_still():
    # Act
    massnahmen = roadmap_massnahmen(ERHOBEN_ALLES_GUT)

    # Assert — kein „llms.txt anlegen", wenn sie da ist
    alle = " ".join(m for phase in massnahmen.values() for m in phase)
    assert "llms.txt anlegen" not in alle
    assert "LocalBusiness einbauen" not in alle


def test_jede_zeile_sagt_etwas_in_der_letzten_spalte():
    # Arrange — eine über alle Zeilen leere Spalte liest sich als Fehler.
    # Wo nichts zu tun ist, steht warum; eine Aufforderung ist das nicht.
    for daten in (ERHOBEN_ALLES_GUT, ERHOBEN_MIT_LUECKEN, NICHTS_ERHOBEN):
        for punkt in geo_pruefpunkte(daten):
            # Act & Assert
            assert punkt["empfehlung"] or punkt["hinweis"], \
                f"„{punkt['pruefpunkt']}“ lässt die letzte Spalte leer"


def test_nicht_erhobene_punkte_erklaeren_sich():
    # Act
    punkt = _punkt(geo_pruefpunkte(NICHTS_ERHOBEN), "KI-Erwähnungen")

    # Assert
    assert "nicht" in punkt["hinweis"].lower()
    assert not punkt["empfehlung"]


def test_roadmap_behaelt_die_allgemeinen_langfrist_punkte():
    # Arrange & Act — Backlinks und Profilpflege gelten unabhängig vom Befund
    massnahmen = roadmap_massnahmen(NICHTS_ERHOBEN)

    # Assert
    assert any("Backlink" in m for m in massnahmen.get("langfristig", []))
