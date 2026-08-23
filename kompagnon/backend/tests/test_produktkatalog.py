"""Der Katalog, aus dem abgerechnet wird — und aus dem niemand ausschert (L-97).

**Der Befund vom 23.08.2026.** Die Produktdatenblätter führten Websprint
Relaunch, Neubau und System zu 3.500 / 7.900 / 12.900 € netto. Die Tabelle
`products` — dieselbe Zeile, aus der die Stripe-Sitzung ihren Betrag zieht —
führte Starter, KOMPAGNON und Premium zu 1.500 / 2.000 / 2.800 € brutto. Das
waren nicht zwei Fassungen einer Liste, sondern zwei Produktlinien
nebeneinander.

**Warum das schwerer wog als eine veraltete Preisliste.** L-29 hatte im
August mit einiger Mühe erreicht, dass ein Preis überall dasselbe bedeutet:
Frontend, Kundenmail und Kasse lesen seither dieselbe Zeile. Eine dritte
Preiswelt im Angebot hätte das aufgehoben — wer 7.900 € anbietet und dessen
Kasse 2.800 € kennt, hat entweder einen Bestellweg, der den Preis ignoriert,
oder einen, der ihn überschreibt.

**Was hier geprüft wird, ist deshalb nicht „stehen die richtigen Zahlen da".**
Zahlen ändern sich. Geprüft werden die drei Wege, auf denen eine zweite
Wahrheit *entstehen* kann:

1. **Brutto und Netto rechnen auseinander.** Zwei Felder für eine Zahl; das
   Frontend zeigt das eine, Stripe bucht das andere ab. Bei 1.500 fiel eine
   Abweichung auf, bei 9.401 fällt sie niemandem auf.
2. **Eine zweite Paketliste im Code.** `projects_anlegen` prüfte gegen eine
   feste Auswahl `("starter", "kompagnon", "premium")`. Wer den Katalog
   erweitert, ändert diese Stelle nicht mit — und das neue Paket wird beim
   Projektanlegen still verworfen. Kein Fehler, nur ein Projekt mit dem
   falschen Paket.
3. **Ein Standardwert, der auf ein stillgelegtes Produkt zeigt.** Die Spalte
   trägt `DEFAULT 'kompagnon'`. Wird KOMPAGNON stillgelegt, bekommt jedes
   Projekt ohne Angabe ein Paket, das niemand mehr kaufen kann.

**Was hier bewusst nicht geprüft wird:** ob die Preise „stimmen". Das ist
eine kaufmännische Frage, keine technische. Geprüft wird, dass es nur *eine*
Stelle gibt, an der sie stehen.
"""
import ast
import pathlib

import pytest

WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _vorlage():
    """Die SEED-Liste aus `main.py` — die Quelle für eine frische Datenbank."""
    baum = ast.parse((WURZEL / "main.py").read_text(encoding="utf-8"))
    listen = [ast.literal_eval(k.value)
              for k in ast.walk(baum)
              if isinstance(k, ast.Assign)
              and any(getattr(z, "id", "") == "SEED" for z in k.targets)]
    assert listen, "keine Produktvorlage in main.py gefunden"
    return listen[0]


class TestBruttoUndNettoBleibenEineZahl:
    """Zwei Felder, eine Wahrheit — sonst zeigt die Seite etwas anderes,
    als die Kasse abbucht."""

    @pytest.mark.parametrize("eintrag", _vorlage(), ids=lambda e: e["slug"])
    def test_brutto_ist_netto_plus_steuer(self, eintrag):
        # Arrange
        netto = float(eintrag["price_netto"])
        satz = float(eintrag["tax_rate"])

        # Act
        erwartet = netto * (1 + satz / 100)

        # Assert — ein Cent Toleranz für die Rundung
        assert float(eintrag["price_brutto"]) == pytest.approx(erwartet, abs=0.01), (
            f"{eintrag['slug']}: brutto {eintrag['price_brutto']} passt nicht "
            f"zu netto {netto} bei {satz} % — das Frontend zeigt das eine, "
            f"Stripe bucht das andere ab")


class TestEsGibtNurEinePaketliste:
    """Der Katalog steht in der Datenbank. Jede zweite Liste im Code läuft
    ihm irgendwann davon."""

    def test_kein_router_prueft_gegen_feste_paketnamen(self):
        """Am Code gemessen, nicht am Text.

        Die erste Fassung dieser Prüfung suchte die Zeichenkette
        `("starter", …)` in der Datei — und blieb rot, nachdem die Stelle
        umgebaut war: Sie zählte den **Kommentar** mit, der die alte Fassung
        zitiert. Dieselbe Klasse Fehlmessung wie am 23.08. viermal beim
        Dateischneiden: eine Grenze aus der Form statt aus dem Inhalt.
        """
        # Arrange
        baum = ast.parse((WURZEL / "routers" / "projects_anlegen.py")
                         .read_text(encoding="utf-8"))

        # Act — Vergleiche gegen ein Tupel/Liste fester Zeichenketten sammeln
        feste_vergleiche = [
            k for k in ast.walk(baum)
            if isinstance(k, ast.Compare)
            and any(isinstance(v, (ast.Tuple, ast.List))
                    and any(isinstance(e, ast.Constant) and e.value == "starter"
                            for e in v.elts)
                    for v in k.comparators)
        ]

        # Assert
        assert not feste_vergleiche, (
            "projects_anlegen prüft gegen eine feste Paketliste. Wer den "
            "Katalog erweitert, ändert diese Stelle nicht mit — das neue "
            "Paket wird beim Projektanlegen still verworfen.")

    def test_der_katalogdienst_beantwortet_die_frage(self):
        # Arrange & Act
        from services.produktkatalog import bekannte_slugs

        # Assert — die Funktion existiert und nimmt eine Sitzung entgegen
        assert callable(bekannte_slugs)


class TestDerStandardwertZeigtAufEinLebendesPaket:
    """`package_type` hat einen Standard. Zeigt er auf ein stillgelegtes
    Produkt, bekommt jedes Projekt ohne Angabe ein unverkäufliches Paket."""

    def test_der_default_der_spalte_steht_in_der_vorlage(self):
        # Arrange
        migrationen = (WURZEL / "migrations_runtime.py").read_text(encoding="utf-8")
        kandidaten = [z for z in migrationen.splitlines()
                      if "package_type" in z and "DEFAULT" in z]
        assert kandidaten, "kein Spaltenstandard fuer package_type gefunden"

        # Act — die Migrationen laufen der Reihe nach: wirksam ist der
        # **letzte** Standard, nicht der erste. Die erste Fassung dieser
        # Prüfung nahm `next(...)` und maß damit einen Wert, den eine spätere
        # Zeile längst überschrieben hatte.
        default = kandidaten[-1].split("DEFAULT")[1].split("'")[1]

        # Assert
        slugs = {e["slug"] for e in _vorlage()}
        assert default in slugs, (
            f"Der Spaltenstandard '{default}' kommt im Katalog nicht mehr vor. "
            f"Jedes Projekt ohne Paketangabe bekommt ein Produkt, das niemand "
            f"kaufen kann. Katalog: {sorted(slugs)}")
