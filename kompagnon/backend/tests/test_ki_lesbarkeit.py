"""L-58 (a): Der Audit erhebt die KI-Lesbarkeit — und bewertete sie nicht.

Gefunden am HubSpot-Konto (19.08.2026), dessen `/ai-visibility/` genau das
aus Marke und Domain prueft. Nachgezaehlt am 21.08.: 8 Kategorien, 42
Kriterien, 100 Punkte — **kein Treffer auf KI, ChatGPT, Perplexity oder AEO**.

Beim Nachsehen war der Befund enger als notiert. Es fehlte **nicht** die
Erhebung: `services/audit_runner.audit_facts` legt seit dem 16.08. vier Werte
ab — `llms_txt`, `robots_ai_friendly`, `structured_data` und
`gesperrte_ki_crawler`. Das PDF druckt sie. Nur **bewertet** sie kein
Kriterium, und damit wirken sie auf keine einzige Zahl.

Zwei der vier waren ohnehin abgedeckt: Strukturierte Daten stecken in
`se_schema`, die Inhaltstiefe in `se_struktur`. Neu ist deshalb genau das,
was sonst nirgends steht:

  * ob KI-Crawler ueberhaupt hereingelassen werden (robots.txt), und
  * ob eine `llms.txt` existiert.

**Was dieses Kriterium ausdruecklich nicht misst:** ob eine Maschine den
Betrieb auf eine Frage hin **nennt**. Das ist L-58 (b), kostet je Lauf Geld
und ist ein eigenes Produkt. Hier steht Lesbarkeit, nicht Sichtbarkeit — und
das Kriterium heisst deshalb auch so.
"""
import pytest

from services.audit_criteria import CATALOGUE, Source
from services.audit_scoring import score_audit


def _kriterium(schluessel):
    for kategorie in CATALOGUE:
        for kriterium in kategorie.criteria:
            if kriterium.key == schluessel:
                return kategorie, kriterium
    return None, None


class TestKatalog:
    def test_der_katalog_kennt_die_ki_lesbarkeit(self):
        kategorie, kriterium = _kriterium("se_ki_lesbar")
        assert kriterium is not None, "Kein Kriterium fuer die KI-Lesbarkeit"
        assert kategorie.key == "seo"

    def test_es_heisst_lesbarkeit_und_nicht_sichtbarkeit(self):
        """Wir messen, ob eine Maschine den Betrieb lesen **kann** — nicht,
        ob sie ihn nennt. Der Name darf nicht mehr versprechen."""
        _, kriterium = _kriterium("se_ki_lesbar")
        assert "sichtbar" not in kriterium.label.lower()

    def test_der_gesamtscore_bleibt_auf_null_bis_hundert(self):
        """Die Rohpunkte muessen **nicht** 100 ergeben — der Katalog normiert
        (so steht es im Kopf von `audit_criteria.py`, und genau deshalb laesst
        sich ein Kriterium ergaenzen, ohne anderswo Gewicht wegzunehmen).

        Was das trotzdem bedeutet, gehoert gesagt: Mit 103 statt 100
        Rohpunkten wiegt **jedes** bestehende Kriterium etwas weniger. Zwei
        Audits derselben Website vor und nach dieser Aenderung koennen sich um
        wenige Punkte unterscheiden. Das ist gewollt und die Folge jeder
        Katalogerweiterung — es soll nur niemanden ueberraschen.
        """
        # Arrange — alles erfuellt, was sich ohne KI-Erhebung erfuellen laesst
        ergebnis = score_audit({"qa": {}, "word_count": 0})

        # Assert
        assert 0 <= ergebnis["total_score"] <= 100


class TestBewertung:
    def _facts(self, **qa_zusatz):
        """Die KI-Werte stehen in `qa`, nicht eine Ebene hoeher.

        `summarise_facts` hebt sie zwar hoch — aber `routers/audit.py:180`
        uebergibt an `score_audit` die Ausgabe von `collect_facts`. Der erste
        Entwurf las oben und haette ein Kriterium gebaut, das produktiv **nie**
        gelaufen waere. Aufgefallen ist es am Referenzseiten-Test.
        """
        return {
            "qa": {
                "title_vorhanden": True, "title_laenge_ok": True,
                "meta_desc_vorhanden": True, "meta_desc_laenge_ok": True,
                "h1_genau_eins": True, "h2_vorhanden": True,
                "robots_txt": True, "robots_txt_indexiert": True,
                "sitemap_xml": True, "canonical_vorhanden": True,
                "schema_markup": True,
                **qa_zusatz,
            },
            "word_count": 900,
            "city": "Koblenz",
        }

    def _punkte(self, facts):
        ergebnis = score_audit(facts)
        _, kriterium = _kriterium("se_ki_lesbar")
        assert "se_ki_lesbar" in ergebnis["sources"], (
            "se_ki_lesbar taucht in der Bewertung nicht auf"
        )
        return {
            "points": ergebnis["items"].get("se_ki_lesbar", 0),
            "max_points": kriterium.max_points,
            "source": ergebnis["sources"]["se_ki_lesbar"],
        }

    def test_offene_robots_txt_und_llms_txt_geben_die_volle_punktzahl(self):
        # Arrange
        facts = self._facts(llms_txt=True, gesperrte_ki_crawler=[])

        # Act
        eintrag = self._punkte(facts)

        # Assert
        assert eintrag["points"] == eintrag["max_points"]
        assert eintrag["source"] == Source.MEASURED.value

    def test_ein_gesperrter_ki_crawler_kostet_den_groesseren_teil(self):
        """Wer GPTBot aussperrt, ist fuer ChatGPT nicht vorhanden. Das wiegt
        schwerer als eine fehlende `llms.txt`, die kaum eine Seite hat."""
        # Arrange
        gesperrt = self._facts(llms_txt=True, gesperrte_ki_crawler=["GPTBot"])
        ohne_llms = self._facts(llms_txt=False, gesperrte_ki_crawler=[])

        # Act / Assert
        assert self._punkte(gesperrt)["points"] < self._punkte(ohne_llms)["points"]

    def test_ohne_erhebung_faellt_das_kriterium_aus_der_rechnung(self):
        """`None` heisst unbekannt und ist nicht dasselbe wie `False`. Eine
        fehlende Messung darf nicht als „nicht erfuellt" verkauft werden —
        dieselbe Lehre wie beim GEO-Bericht vom 16.08."""
        # Arrange — keine QA-Erhebung
        facts = {"word_count": 0, "city": ""}

        # Act
        eintrag = self._punkte(facts)

        # Assert
        assert eintrag["source"] == Source.NOT_COLLECTED.value

    def test_eine_alte_erhebung_ohne_die_felder_faellt_ebenfalls_aus(self):
        """Audits von vor dem 16.08. kennen `llms_txt` nicht. Sie duerfen
        nicht rueckwirkend Punkte verlieren."""
        # Arrange
        facts = self._facts()  # weder llms_txt noch gesperrte_ki_crawler

        # Act
        eintrag = self._punkte(facts)

        # Assert
        assert eintrag["source"] == Source.NOT_COLLECTED.value
