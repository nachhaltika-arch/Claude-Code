"""Wer führt einen Betrieb — und wer eine Kundenbeziehung? (L-105, L-106)

**Die Frage kam am 24.08.2026 aus der Routen-Sichtung:** `customers` und
`usercards` haben zusammen 16 Endpunkte, von denen die Oberfläche nur drei
ruft. Das sah nach zwei Wegen zum selben Gegenstand aus.

**Nachgesehen sind es drei Tabellen mit drei Aufgaben** — und eine
unfertige Zusammenlegung:

| Router | Tabelle | Gegenstand |
|---|---|---|
| `routers/leads.py` | `leads` | Der Betrieb. Alles vor und während des Projekts. |
| `routers/customers.py` | `customers` | Die Kundenbeziehung **nach** dem Go-live: Upsell-Status, Touchpoints, wiederkehrender Umsatz. |
| `routers/usercards.py` | `usercards` | Die geplante Zusammenlegung der beiden — „merges leads + customer management (Part 1/3)". Teil 2 und 3 kamen nie, die Tabelle ist leer (L-106). |

**Entschieden am 24.08.2026 (David): Grenze festschreiben, nichts abbauen.**
Das war die richtige Entscheidung, und der Grund kam erst beim Nachsehen
heraus: Wer hier aufgeräumt hätte, hätte entweder die leere Tabelle gelöscht,
an der das Kundendashboard hängt, oder `customers` entfernt und damit die
Nachbetreuung.

**Wozu diese Tests dann gut sind.** Nicht um die Grenze zu *prüfen* — sie
steht oben und ist Prosa. Sondern um zu verhindern, dass eine **vierte**
Fassung wächst, ohne dass jemand es merkt. Genau so ist die dritte
entstanden.
"""
import pathlib
import re

import pytest

WURZEL = pathlib.Path(__file__).resolve().parent.parent

#: Router → Tabelle, die er führt. Die Zuordnung ist die Grenze.
FASSUNGEN = {
    "routers/leads.py": "leads",
    "routers/customers.py": "customers",
    "routers/usercards.py": "usercards",
}

#: Tabellen, die einen Betrieb oder eine Kundenbeziehung führen.
KUNDENTABELLEN = {"leads", "customers", "usercards"}


#: Wer eine der drei Tabellen **beschreibt** — und warum das erlaubt ist.
#:
#: **Warum Schreiben und nicht Lesen der Maßstab ist.** Der erste Entwurf
#: prüfte, welche Router die Modelle überhaupt erwähnen: 23 Präfixe, von
#: `/api/projects` bis `/api/widget`. Sie alle *benutzen* einen Betrieb, ohne
#: ihn zu führen — eine Ausnahmeliste dafür wäre genau das Ablagefach, das
#: dieses Projekt sonst vermeidet.
#:
#: Eine **Fassung** legt an und löscht. Danach wird gemessen, und dann sind es
#: zehn Stellen mit je erkennbarem Grund: drei führende Router, fünf
#: Eingangswege von außen und zwei Wege aus dem Innendienst.
SCHREIBER = {
    # Die drei Fassungen selbst
    "leads.py": "führt den Betrieb",
    "customers.py": "führt die Kundenbeziehung nach dem Go-live",
    "usercards.py": "die unfertige Zusammenlegung (L-106)",
    # Eingangswege von außen — sie legen Betriebe an, führen sie aber nicht
    "webhooks.py": "Facebook, LinkedIn, Google, Postkarte, Telefon",
    "webhooks_trackdesk.py": "Partnerlinks",
    "widget.py": "das Analyse-Widget auf fremden Seiten",
    "kampagne.py": "Kampagnen-Landingpages",
    "payments.py": "der Kauf legt den Betrieb an (Art. 6 Abs. 1 lit. b)",
    # Innendienst
    "leads_import.py": "CSV- und Domain-Import",
    "leads_portal.py": "das öffentliche Formular",
}

#: Wie ein Schreibzugriff auf eine der drei Tabellen aussieht.
_SCHREIBFORMEN = (
    r"=\s*Lead\(", r"=\s*Customer\(", r"=\s*UserCard\(",
    r"INSERT INTO (?:leads|customers|usercards)\b",
)


class TestEsBleibenDreiFassungen:
    def test_niemand_neues_schreibt_in_die_drei_tabellen(self):
        """Eine vierte Fassung soll auffallen, bevor sie Endpunkte bekommt."""
        # Act
        schreiber = set()
        for pfad in sorted((WURZEL / "routers").glob("*.py")):
            text = pfad.read_text(encoding="utf-8", errors="ignore")
            if any(re.search(form, text, re.IGNORECASE)
                   for form in _SCHREIBFORMEN):
                schreiber.add(pfad.name)

        # Assert
        neu = sorted(schreiber - set(SCHREIBER))
        assert not neu, (
            f"Neue Stellen schreiben in leads/customers/usercards: {neu}. "
            "Ist das ein weiterer Eingangsweg, gehoert er mit Begruendung in "
            "SCHREIBER. Ist es eine vierte Fassung des Betriebs, ist es die "
            "Sorte Doppelung, die L-105 und L-106 beschreiben."
        )

    def test_die_gefuehrte_liste_ist_nicht_veraltet(self):
        """Eine Liste, die Verschwundenes fuehrt, wird beim Lesen geglaubt."""
        # Act
        vorhanden = {p.name for p in (WURZEL / "routers").glob("*.py")}

        # Assert
        verschwunden = sorted(set(SCHREIBER) - vorhanden)
        assert not verschwunden, (
            f"SCHREIBER nennt Dateien, die es nicht mehr gibt: {verschwunden}"
        )

    @pytest.mark.parametrize("datei, tabelle", sorted(FASSUNGEN.items()))
    def test_jede_fassung_gibt_es_noch(self, datei, tabelle):
        """Verschwindet eine, ist die Grenze im Kopf dieser Datei veraltet."""
        assert (WURZEL / datei).exists(), (
            f"{datei} gibt es nicht mehr. Dann stimmt die Tabelle im Kopf "
            "dieser Datei nicht mehr — beides gehoert zusammen nachgezogen."
        )


class TestDieUnfertigeZusammenlegungBleibtSichtbar:
    def test_der_kopierschritt_ist_weiterhin_entfernt(self):
        """Solange er fehlt, bleibt `usercards` leer (L-106).

        Wird er wieder eingebaut, ist das eine gute Nachricht — aber eine,
        die jemand sehen muss: Dann fuellt sich die Tabelle, und die
        Kennungsvermischung in `usercards` faellt zum ersten Mal auf.
        """
        # Arrange
        text = (WURZEL / "migrations_runtime.py").read_text(encoding="utf-8")

        # Assert
        assert "usercards bulk-copy removed" in text, (
            "Der Vermerk zum entfernten Kopierschritt ist weg. Entweder wurde "
            "er wieder eingebaut — dann fuellt sich `usercards`, und L-106 "
            "gehoert neu bewertet — oder der Vermerk ging beim Aufraeumen "
            "verloren. Beides will gesehen werden."
        )

    def test_das_modell_sagt_weiterhin_dass_es_eine_zusammenlegung_ist(self):
        """Der Satz „Part 1/3" ist der einzige Hinweis darauf im System."""
        # Arrange
        text = (WURZEL / "database.py").read_text(encoding="utf-8")

        # Assert
        assert "merges leads + customer management" in text
