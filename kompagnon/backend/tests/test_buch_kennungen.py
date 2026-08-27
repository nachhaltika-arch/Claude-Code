"""Kennung und Buchbezeichnung am Kriterium (S5.5, S5.6).

**Der Befund.** Das Buch führt Kriterien als `L1`, `S3`, `E7` — und **nichts
im Repo verband sie bisher mit einem Kriterium**. Wer im Buch „E5 Lokale
Signale" liest und im Katalog nachsehen will, hat keinen Weg dorthin; wer
umgekehrt `se_lokal` ändert, weiß nicht, welche Buchstelle er trifft.

Dasselbe beim Namen: Der Katalog führt Fachjargon („LCP (Ladezeit
Hauptinhalt)"), das Buch braucht eine deutsche Bezeichnung.

**Gespeichert und nicht abgeleitet — mit Wächter.** Die Kennung ließe sich aus
der Position errechnen (drittes Kriterium der Rechtskategorie = `L3`). Das
wäre bequem und gefährlich: Wer zwei Kriterien vertauscht, verschiebt
stillschweigend jede Buchreferenz. Deshalb steht sie am Kriterium — und ein
Test hält fest, dass sie zur Position passt. Wird umsortiert, wird er rot,
und jemand entscheidet bewusst, ob das Buch umnummeriert wird oder die
Reihenfolge zurückkommt.
"""
import pytest

from services.audit_criteria import CATALOGUE, all_criteria, find_criterion

#: Der Buchstabe je Kategorie — so führt ihn der Standard 2026.2.
KATEGORIE_BUCHSTABE = {
    "recht_compliance": "L", "sicherheit": "S", "performance": "P",
    "barrierefreiheit": "B", "seo": "E", "design": "D",
    "conversion": "C", "inhalt": "I",
}


class TestJedesKriteriumHatEineKennung:
    def test_keine_fehlt(self):
        ohne = [c.key for c in all_criteria() if not c.buch_code]
        assert not ohne, f"Ohne Buch-Kennung: {ohne}"

    def test_keine_kommt_zweimal_vor(self):
        codes = [c.buch_code for c in all_criteria()]
        doppelt = {c for c in codes if codes.count(c) > 1}
        assert not doppelt, (
            f"Dieselbe Kennung an mehreren Kriterien: {sorted(doppelt)} — "
            "im Buch zeigt sie dann auf zwei verschiedene Dinge."
        )


class TestDieKennungPasstZurPosition:
    """Der Waechter gegen stillschweigendes Umnummerieren."""

    def test_buchstabe_und_zahl_folgen_der_reihenfolge(self):
        abweichungen = []
        for kategorie in CATALOGUE:
            buchstabe = KATEGORIE_BUCHSTABE.get(kategorie.key)
            assert buchstabe, f"Kategorie ohne Buchstabe: {kategorie.key}"
            for stelle, kriterium in enumerate(kategorie.criteria, start=1):
                erwartet = f"{buchstabe}{stelle}"
                if kriterium.buch_code != erwartet:
                    abweichungen.append(
                        f"{kriterium.key}: traegt {kriterium.buch_code}, "
                        f"steht aber an Stelle {erwartet}")

        assert not abweichungen, (
            "Kennung und Position gehen auseinander. Entweder wurde "
            "umsortiert — dann zeigt jede Buchreferenz auf etwas anderes — "
            f"oder eine Kennung ist falsch eingetragen: {abweichungen}"
        )

    def test_das_siebte_seo_kriterium_heisst_e7(self):
        """Die Spezifikation kennt nur E1–E6 (S4.6)."""
        assert find_criterion("se_ki_lesbar").buch_code == "E7"


class TestBuchbezeichnung:
    """Die Bezeichnungen stammen aus `standard-export-prototyp.py`.

    **Sie sind nicht erfunden, sondern uebernommen.** Der Prototyp aus
    BUCH-F2 fuehrte sie als Tabelle und vermerkte selbst: „Diese Tabelle
    gehoert NICHT hierher, sondern als Feld `buch_label` an das Criterion —
    solange sie hier steht, ist sie eine zweite Wahrheit." Genau dort stehen
    sie jetzt.

    Beim Uebertragen war ein eigener Versuch bereits vorhanden — und wich in
    sieben von elf Faellen ab („Schutzangaben im Seitenkopf" statt
    „Sicherheitsheader", „Aufforderung zum naechsten Schritt" statt „Die
    erwartete Hauptreaktion"). Gilt die aus dem Prototyp: Sie ist die
    Entscheidung, die andere war eine Vermutung.
    """

    def test_jedes_kriterium_hat_eine(self):
        from services.audit_criteria import all_criteria

        ohne = [c.key for c in all_criteria() if not c.buch_label]
        assert not ohne, f"Ohne Buchbezeichnung: {ohne}"

    @pytest.mark.parametrize("schluessel, erwartet", [
        ("tp_lcp", "Ladezeit des Hauptinhalts"),
        ("tp_cls", "Layoutstabilität"),
        ("si_header", "Sicherheitsheader"),
        ("cv_cta", "Die erwartete Hauptreaktion"),
        ("se_schema", "Strukturierte Daten"),
    ])
    def test_die_bezeichnung_stammt_aus_dem_prototyp(self, schluessel, erwartet):
        assert find_criterion(schluessel).buch_name == erwartet

    def test_keine_abkuerzung_ohne_aufloesung(self):
        """`LCP` und `CLS` sind Feldnamen, keine Ueberschriften."""
        from services.audit_criteria import all_criteria

        for kriterium in all_criteria():
            assert kriterium.buch_name[:3].upper() not in ("LCP", "CLS", "INP"), \
                kriterium.key
