"""Wer wird **stattdessen** genannt? (L-85, zweite Hälfte)

Die erste Hälfte von L-85 ist seit dem 22.08.2026 zu: Der Verlauf sammelt,
statt zu überschreiben. Offen blieb der Wettbewerbsvergleich — „drei von fünf
Antworten nennen Sie nicht" ist eine Zahl, „und stattdessen nennen sie diese
zwei Betriebe" ist die Auskunft, für die ein Betrieb zahlt.

**Gezählt werden Quellen, nicht Prosa.** Steht eine Adresse unter den
herangezogenen Quellen, hat die Suche sie wirklich benutzt — dieselbe harte
Regel, mit der `ist_genannt` die eigene Nennung belegt. Firmennamen aus
Fließtext zu erkennen wäre Raten; ein falsch erkannter „Mitbewerber" im
Kundenbericht ist teurer als eine fehlende Zeile.

**Ein Verzeichnis ist kein Mitbewerber.** `11880.com` steht unter fast jeder
Antwort. Es als Wettbewerber auszuweisen wäre die falsche Auskunft — und es
still wegzuwerfen die zweite: Dann ließe sich nicht unterscheiden, ob nichts
gefunden oder alles gefiltert wurde. Beides steht deshalb im Befund, getrennt.

**Ein Lauf ohne Erhebung bekommt keine leere Liste.** Sie läse sich wie „kein
Wettbewerb genannt" — dieselbe Verwechslung von „nicht erhoben" mit „Null",
gegen die der ganze Dienst gebaut ist.
"""
from services.ki_sichtbarkeit import verlaufseintrag
from services.ki_wettbewerb import mitbewerber_ermitteln


def _antwort(belege, genannt=False):
    return {"frage": "Wer bietet Heizung in Kassel an?", "genannt": genannt,
            "belege": list(belege), "auszug": "…"}


def _befund(anbieter):
    """Ein Befund in der Form, die `pruefe_ki_sichtbarkeit` liefert."""
    return {"collected": True, "hinweis": "…", "fragen_gestellt": 2,
            "anbieter": anbieter, "erhoben_bei": len(anbieter), "genannt_bei": 0}


# ── Die eigene Adresse ───────────────────────────────────────────────

class TestEigeneAdresse:
    def test_eigene_domain_ist_kein_mitbewerber(self):
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://mustermann-heizung.de/leistungen",
                                 "https://konkurrent.de/"], genannt=True)],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        domains = [m["domain"] for m in ergebnis["mitbewerber"]]
        assert "mustermann-heizung.de" not in domains
        assert domains == ["konkurrent.de"]

    def test_eigene_domain_auch_mit_www_und_protokoll_erkannt(self):
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://www.mustermann-heizung.de/x"])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(
            befund, domain="https://mustermann-heizung.de/")

        # Assert
        assert ergebnis["mitbewerber"] == []


# ── Verzeichnisse ────────────────────────────────────────────────────

class TestVerzeichnisse:
    def test_portal_steht_nicht_unter_mitbewerbern(self):
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://www.11880.com/suche/heizung/kassel",
                                 "https://konkurrent.de/"])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert [m["domain"] for m in ergebnis["mitbewerber"]] == ["konkurrent.de"]
        assert [v["domain"] for v in ergebnis["verzeichnisse"]] == ["11880.com"]

    def test_verzeichnis_wird_ausgewiesen_statt_weggeworfen(self):
        """Sonst ist „nichts gefunden" nicht von „alles gefiltert" zu
        unterscheiden — und der Betrieb liest das als gute Nachricht."""
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://www.gelbeseiten.de/x",
                                 "https://www.dasoertliche.de/y"])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["mitbewerber"] == []
        assert len(ergebnis["verzeichnisse"]) == 2

    def test_unterdomain_eines_portals_gilt_als_portal(self):
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://branchenbuch.meinestadt.de/kassel"])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["mitbewerber"] == []
        assert [v["domain"] for v in ergebnis["verzeichnisse"]] == \
               ["branchenbuch.meinestadt.de"]


# ── Zählen ───────────────────────────────────────────────────────────

class TestZaehlen:
    def test_haeufigster_zuerst_und_systeme_benannt(self):
        # Arrange
        befund = _befund({
            "chatgpt": {"collected": True, "anzeige": "ChatGPT", "von": 2,
                        "beantwortet": 2, "fragen": [
                            _antwort(["https://oft.de/a"]),
                            _antwort(["https://oft.de/b", "https://selten.de/"]),
                        ]},
            "claude": {"collected": True, "anzeige": "Claude", "von": 1,
                       "beantwortet": 1,
                       "fragen": [_antwort(["https://oft.de/c"])]},
        })

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert [m["domain"] for m in ergebnis["mitbewerber"]] == ["oft.de", "selten.de"]
        assert ergebnis["mitbewerber"][0]["genannt_bei"] == 3
        assert ergebnis["mitbewerber"][0]["systeme"] == ["chatgpt", "claude"]
        assert ergebnis["mitbewerber"][1]["systeme"] == ["chatgpt"]

    def test_dieselbe_quelle_zweimal_in_einer_antwort_zaehlt_einmal(self):
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort(["https://konkurrent.de/a",
                                 "https://www.konkurrent.de/b"])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["mitbewerber"][0]["genannt_bei"] == 1

    def test_gescheiterte_frage_zaehlt_nicht_als_ausgewertete_antwort(self):
        """Ein Ausfall darf den Nenner nicht füllen — sonst sieht ein
        halber Lauf aus wie ein ganzer mit schlechtem Ergebnis."""
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 2, "beantwortet": 1,
            "fragen": [
                _antwort(["https://konkurrent.de/"]),
                {"frage": "…", "genannt": None, "fehler": "Zeitüberschreitung",
                 "belege": []},
            ],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["antworten_ausgewertet"] == 1

    def test_nicht_erhobener_anbieter_traegt_nichts_bei(self):
        # Arrange
        befund = _befund({
            "chatgpt": {"collected": True, "anzeige": "ChatGPT", "von": 1,
                        "beantwortet": 1,
                        "fragen": [_antwort(["https://konkurrent.de/"])]},
            "perplexity": {"collected": False, "anzeige": "Perplexity",
                           "grund": "PERPLEXITY_API_KEY nicht gesetzt"},
        })

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["antworten_ausgewertet"] == 1
        assert ergebnis["mitbewerber"][0]["systeme"] == ["chatgpt"]
        assert ergebnis["nicht_erhoben"] == ["perplexity"]


# ── Kein Ergebnis ist kein Nullergebnis ──────────────────────────────

class TestOhneErhebung:
    def test_lauf_ohne_erhebung_bekommt_keine_leere_liste(self):
        # Arrange
        befund = {"collected": False, "grund": "Kein KI-Zugang konfiguriert"}

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["collected"] is False
        assert "mitbewerber" not in ergebnis

    def test_erhoben_aber_ohne_fremde_quelle_ist_eine_leere_liste(self):
        """Hier ist die leere Liste die richtige Auskunft: gefragt wurde,
        genannt wurde niemand sonst."""
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "fragen": [_antwort([])],
        }})

        # Act
        ergebnis = mitbewerber_ermitteln(befund, domain="mustermann-heizung.de")

        # Assert
        assert ergebnis["collected"] is True
        assert ergebnis["mitbewerber"] == []
        assert ergebnis["antworten_ausgewertet"] == 1


# ── Der Verlauf ──────────────────────────────────────────────────────

class TestVerlauf:
    def test_verlauf_traegt_die_drei_haeufigsten_ohne_quellen(self):
        """Ohne Verlauf ist der Wettbewerbsvergleich wieder eine
        Momentaufnahme — genau der Befund, der L-85 aufgemacht hat."""
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 4, "beantwortet": 4,
            "genannt_bei": 0, "quote": 0.0,
            "fragen": [
                _antwort(["https://a.de/", "https://b.de/", "https://c.de/"]),
                _antwort(["https://a.de/", "https://b.de/"]),
                _antwort(["https://a.de/"]),
                _antwort(["https://d.de/"]),
            ],
        }})
        befund["wettbewerb"] = mitbewerber_ermitteln(
            befund, domain="mustermann-heizung.de")

        # Act
        eintrag = verlaufseintrag(befund, am="2026-08-29T10:00:00")

        # Assert
        assert eintrag["mitbewerber"] == [
            {"domain": "a.de", "genannt_bei": 3},
            {"domain": "b.de", "genannt_bei": 2},
            {"domain": "c.de", "genannt_bei": 1},
        ]

    def test_verlauf_ohne_wettbewerbsteil_bleibt_lesbar(self):
        """Altbestand aus der Zeit vor diesem Bau hat den Schlüssel nicht."""
        # Arrange
        befund = _befund({"chatgpt": {
            "collected": True, "anzeige": "ChatGPT", "von": 1, "beantwortet": 1,
            "genannt_bei": 1, "quote": 1.0, "fragen": [_antwort([], genannt=True)],
        }})

        # Act
        eintrag = verlaufseintrag(befund, am="2026-08-29T10:00:00")

        # Assert
        assert eintrag["mitbewerber"] == []
        assert eintrag["anbieter"]["chatgpt"]["genannt_bei"] == 1


# ── Am Gegenstand, nicht an der Vorlage ──────────────────────────────

class TestAmEchtenLauf:
    """Die Prüfungen oben bauen den Befund selbst. Damit ließe sich nicht
    bemerken, wenn der Wettbewerbsteil im echten Lauf gar nicht entsteht oder
    woanders landet — genau der Fehler, der `se_ki_lesbar` beinahe still ins
    Leere gebaut hätte (L-58). Deshalb hier der Weg durch die echte Funktion."""

    def test_echter_lauf_traegt_den_wettbewerbsteil(self):
        # Arrange
        import asyncio

        from services.ki_anbieter import Anbieter
        from services.ki_sichtbarkeit import pruefe_ki_sichtbarkeit

        antworten = [
            ("Empfohlen wird Schmidt & Söhne.",
             ["https://schmidt-heizung.de/", "https://www.11880.com/kassel"]),
            ("Auch Meier ist dort tätig.", ["https://meier-waerme.de/"]),
        ]
        rest = list(antworten)

        async def aufruf(_frage):
            return rest.pop(0) if rest else ("keine Angabe", [])

        anbieter = Anbieter(schluessel="chatgpt", anzeige="ChatGPT",
                            env_name="OPENAI_API_KEY", modell="test",
                            _aufruf=aufruf)

        # Act
        befund = asyncio.run(pruefe_ki_sichtbarkeit(
            name="Mustermann Heizung GmbH", domain="mustermann-heizung.de",
            gewerk="Heizung", ort="Kassel", max_fragen=2, anbieter=[anbieter]))

        # Assert
        wettbewerb = befund["wettbewerb"]
        assert wettbewerb["collected"] is True
        assert wettbewerb["antworten_ausgewertet"] == 2
        assert [m["domain"] for m in wettbewerb["mitbewerber"]] == [
            "meier-waerme.de", "schmidt-heizung.de"]
        assert [v["domain"] for v in wettbewerb["verzeichnisse"]] == ["11880.com"]

    def test_lauf_ohne_zugang_traegt_keinen_leeren_vergleich(self):
        # Arrange
        import asyncio

        from services.ki_sichtbarkeit import pruefe_ki_sichtbarkeit

        # Act — kein einziger Anbieter angebunden
        befund = asyncio.run(pruefe_ki_sichtbarkeit(
            name="Mustermann Heizung GmbH", domain="mustermann-heizung.de",
            gewerk="Heizung", ort="Kassel", anbieter=[]))

        # Assert
        assert befund["collected"] is False
        assert "wettbewerb" not in befund
