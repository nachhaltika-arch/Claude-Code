# -*- coding: utf-8 -*-
"""Die Trichter-Vorschau baut jede Ansicht — und zeigt keine Innereien.

**Warum das ein Test ist und nicht nur ein Werkzeug.** Die Vorschau
(`scripts/trichter-vorschau.py`) rendert dieselben Erzeugnisse, die ein
Kunde bekommt: Widget, Berichtsseite, die drei Mails. Wenn eine davon
abstürzt oder Datenbankinhalt durchreicht, ist das kein Fehler der
Vorschau — es ist ein Fehler, den der Kunde sehen würde.

Genau so wurde am 10.09.2026 gefunden, dass die neue Berichtsseite die
Kennungen der K.-o.-Kriterien ungeübersetzt anzeigte: Im roten Kasten stand
`kein_impressum. keine_datenschutzerklaerung.` statt der Sätze aus
`BLOCKER_LABELS`. Der Fund kam aus dem Hinsehen, nicht aus einem Test —
deshalb steht er jetzt in einem.

**Was hier NICHT geprüft wird.** Ob die Ansichten richtig aussehen. Ein
Test kann sagen, dass eine Seite gebaut wurde und keine Python-Darstellung
enthält; ob der Kasten an der richtigen Stelle sitzt, sieht nur ein Mensch.
"""
import importlib.util
import json
import os
import re

import pytest

SKRIPT = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                      "scripts", "trichter-vorschau.py")


@pytest.fixture(scope="module")
def vorschau():
    spec = importlib.util.spec_from_file_location("trichter_vorschau", SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


#: Wie eine durchgereichte Python-Darstellung aussieht.
#:
#: **Die maskierte Form gehört dazu.** Die Berichtsvorlage escapt jeden
#: Wert, den sie einsetzt — ein durchgereichtes Wörterbuch steht im
#: Quelltext deshalb als `{&#x27;titel&#x27;: …}` und erst im Browser als
#: `{'titel': …}`. Ein Muster, das nur nach `{'` sucht, findet den Fehler
#: genau dort nicht, wo er auftrat. (Beim ersten Schreiben dieses Tests
#: passiert, gemerkt beim Nachrechnen.)
#:
#: `&#x27;: ` allein wäre zu grob: Der Katalog führt ein Kriterium
#: „Lighthouse-Audit 'font-size'", und das ist keine Innerei, sondern der
#: Name der Prüfung.
INNEREIEN = re.compile(
    r"""\{['"]|\{&\#x27;|\[\{['"]|\[\{&\#x27;|<sqlalchemy|object at 0x""")


#: Ansichten, die kein HTML sind. Sie werden trotzdem gebaut (das prüft,
#: dass sie nicht abstürzen), aber nicht auf durchgereichte Python-
#: Darstellungen abgesucht — in einem PDF-Binärstrom stünde jedes Muster
#: irgendwann zufällig.
OHNE_HTML = {"landingpage", "pdf"}


def _alle_ansichten(vorschau):
    # Die Landingpage ist ein fertiger Export ohne Vorlagensprache — sie
    # wird ausgeliefert, nicht gebaut, und hat deshalb hier nichts zu prüfen.
    return [a for a in vorschau.ANSICHTEN if a["schluessel"] != "landingpage"]


def _html_ansichten(vorschau):
    return [a for a in vorschau.ANSICHTEN if a["schluessel"] not in OHNE_HTML]


def test_es_gibt_jede_stufe_des_trichters(vorschau):
    """Fehlt eine Ansicht, prüft niemand sie mehr — und niemand merkt es."""
    schluessel = {a["schluessel"] for a in vorschau.ANSICHTEN}
    assert schluessel == {
        "landingpage", "widget", "teaser", "mail-bestaetigung",
        "mail-bericht", "bericht", "pdf", "mail-erinnerung",
    }


@pytest.mark.parametrize("regler", [
    {},
    {"punkte": "34"},
    {"punkte": "88"},
    {"punkte": "61", "rabatt": "an", "abnahme": "85",
     "knappheit": "an", "kaufwege": "an"},
])
def test_jede_ansicht_baut(vorschau, regler):
    for ansicht in _alle_ansichten(vorschau):
        seite = ansicht["bauer"](regler)
        assert seite, ansicht["schluessel"]
        assert len(seite) > 500, f"{ansicht['schluessel']} ist verdächtig kurz"


@pytest.mark.parametrize("regler", [
    {}, {"punkte": "34"},
    {"punkte": "61", "rabatt": "an", "abnahme": "85", "knappheit": "an"},
])
def test_keine_ansicht_zeigt_innereien(vorschau, regler):
    """Der Fund vom 10.09.2026, als Wächter.

    Die Berichtsseite zeigte Kennungen aus der Datenbank. Dieselbe Klasse
    hatte kurz zuvor der Leistungsumfang (Python-Wörterbücher statt Text)
    und der Deckungsgrad (`true` statt eines Satzes).
    """
    for ansicht in _html_ansichten(vorschau):
        text = ansicht["bauer"](regler).decode("utf-8", "replace")
        treffer = INNEREIEN.search(text)
        assert not treffer, (
            f"{ansicht['schluessel']} zeigt {treffer.group()!r} — "
            f"Kontext: {text[max(0, treffer.start() - 90):treffer.end() + 90]!r}")


def test_die_kopfzahl_ist_die_summe_der_einzelwertungen(vorschau):
    """Sonst widerspricht der Bericht sich selbst.

    Oben steht die Gesamtpunktzahl, unten die Kategorien. Sind das zwei
    verschiedene Rechnungen, weiß niemand, welche gilt — und ein Kunde,
    der nachzählt, findet einen Fehler, den es nicht gibt.
    """
    for ziel in (34, 61, 80, 88):
        befund = vorschau.Audit(ziel)
        werte = json.loads(befund.item_scores)
        assert sum(werte.values()) == befund.total_score


def test_eine_hohe_punktzahl_bringt_ihre_abdeckung_mit(vorschau):
    """Bei 78 % erhobenen Kriterien sind höchstens 80 Punkte erreichbar.

    Das ist kein Zufall der Vorschau, sondern der Produktivzustand (L-165):
    Solange die Performance-Werte fehlen, ist die Abnahmezusage über 85
    Punkte rechnerisch unerreichbar. Die Vorschau soll das **nicht**
    verdecken, indem sie eine Zahl zeigt, die der Befund nicht trägt.
    """
    niedrig = vorschau.Audit(61)
    hoch = vorschau.Audit(88)
    assert niedrig.coverage < 100
    assert hoch.coverage == 100
    assert hoch.total_score == 88


def test_die_befunddaten_haben_die_form_der_datenbank(vorschau):
    """`item_scores` und die anderen sind `Text`-Spalten (modelle_audit.py).

    Als die Vorschau dort Wörterbücher hinlegte, verweigerte der
    PDF-Erzeuger mit „stammt aus dem früheren Katalog" — ein Fehler, den es
    produktiv nicht gibt. Die Berichtsseite verkraftet beide Formen und
    verdeckte den Unterschied.
    """
    befund = vorschau.Audit(61)
    for feld in ("item_scores", "item_sources", "item_belege",
                 "blockers", "top_issues", "category_scores"):
        wert = getattr(befund, feld)
        assert isinstance(wert, str), f"{feld} ist {type(wert).__name__}"
        json.loads(wert)


def test_die_wertungen_benutzen_die_schluessel_des_katalogs(vorschau):
    """Die erste Fassung erfand `impressum_vorhanden`; der Katalog führt
    `rc_impressum`. Damit fand die Berichtsseite zu keinem Kriterium etwas,
    und die Vorschau zeigte eine hohle Seite, die nichts prüfte."""
    from services.audit_criteria import all_criteria

    echte = {k.key for k in all_criteria()}
    werte = json.loads(vorschau.Audit(61).item_scores)
    assert werte
    assert set(werte) <= echte


def test_die_blocker_sind_kennungen_und_keine_saetze(vorschau):
    """Sonst prüft die Vorschau die Übersetzung nicht mit."""
    from services.audit_criteria import BLOCKING_CRITICAL, BLOCKING_MAJOR

    assert set(vorschau.BLOCKER) <= (BLOCKING_CRITICAL | BLOCKING_MAJOR)


def test_der_katalog_kommt_aus_der_startphase(vorschau):
    """Preise stehen an einer Stelle (L-29). Eine Vorschau mit eigenen
    Zahlen zeigt ein Angebot, das es nicht gibt."""
    zeilen = vorschau.katalog()
    assert zeilen["websprint_relaunch"]["price_netto"] == 3500.00
    assert zeilen["check_plus"]["price_netto"] == 249.00


def test_der_waechter_wuerde_ein_durchgereichtes_woerterbuch_finden(vorschau):
    """Gegenprobe. Ein Wächter, der nie anschlägt, bewacht nichts.

    **Nicht über die Blocker.** Der erste Versuch stellte den Fehler vom
    10.09.2026 nach, indem er Wörterbücher in `blockers` legte — und der
    Wächter schwieg. Zu Recht: Die Reparatur desselben Tages fängt
    Wörterbücher in `_rechtsbefund` ab und holt sich `titel` heraus. Der
    Weg ist zu, und ein Test, der ihn benutzt, prüft nur noch die Reparatur.

    Offen ist der Leistungsumfang: Die Vorlage schreibt `{{ l }}`, also die
    Zeichenkette selbst. Steht im Katalog statt eines Satzes ein Wörterbuch,
    landet dessen Python-Darstellung auf der Verkaufsseite — genau das ist
    am 10.09.2026 schon einmal passiert.
    """
    from services import bericht_seite

    class KatalogMitWoerterbuch(vorschau.KatalogDb):
        def __init__(self):
            super().__init__()
            zeile = dict(self.zeilen["websprint_relaunch"])
            zeile["features"] = [{"name": "Eingangsaudit", "punkte": 100}]
            self.zeilen = {**self.zeilen, "websprint_relaunch": zeile}

    seite = bericht_seite.rendern(
        KatalogMitWoerterbuch(), vorschau.Audit(61),
        token="probe", einstellungen={})
    assert INNEREIEN.search(seite), (
        "Der Wächter erkennt ein durchgereichtes Wörterbuch nicht — "
        "er hätte den Fehler vom 10.09.2026 durchgelassen.")


def test_der_waechter_haelt_echte_kriterienbezeichnungen_aus(vorschau):
    """Gegenrichtung: Er darf nicht bei jedem Apostroph anschlagen.

    Der Katalog führt „Lighthouse-Audit 'font-size'". Ein Wächter, der
    daran scheitert, wird nach dem dritten Fehlalarm abgeschaltet.
    """
    assert not INNEREIEN.search(
        "Lighthouse-Audit &#x27;font-size&#x27;: lesbare Schriftgröße")
    assert not INNEREIEN.search("Ein Satz mit { geschweifter Klammer }")


# ══════════════════════════════════════════════════════════════════════
# Die Auftragsablage
# ══════════════════════════════════════════════════════════════════════
#
# Was in der Vorschau beanstandet wird, ist ein Auftrag an die nächste
# Sitzung. Geht er verloren, merkt es niemand — der Absender glaubt, er sei
# angekommen. Deshalb hat die Ablage Tests wie ein Erzeugnis.

@pytest.fixture
def ablage(vorschau, tmp_path, monkeypatch):
    """Eine eigene Datei je Test — niemals die echte des Nutzers."""
    monkeypatch.setattr(vorschau, "AUFTRAGSDATEI",
                        str(tmp_path / "auftraege.json"))
    return vorschau


def test_ohne_datei_ist_die_ablage_leer_und_kein_fehler(ablage):
    assert ablage.auftraege_lesen() == {"eintraege": []}


def test_ein_auftrag_ueberlebt_das_schreiben(ablage):
    ablage.auftrag_anlegen({"aktion": "neu", "text": "Der Kasten ist zu gelb",
                            "ansicht": "bericht", "art": "pin",
                            "x": 400, "y": 1200, "auszug": "Abnahmezusage"})
    eintraege = ablage.auftraege_lesen()["eintraege"]
    assert len(eintraege) == 1
    assert eintraege[0]["text"] == "Der Kasten ist zu gelb"
    assert eintraege[0]["status"] == "offen"
    assert eintraege[0]["auszug"] == "Abnahmezusage"


def test_ein_auftrag_ohne_text_wird_abgewiesen(ablage):
    """Sonst steht in der Liste ein leerer Eintrag, den niemand deuten kann."""
    with pytest.raises(ValueError):
        ablage.auftrag_anlegen({"text": "   "})


def test_eine_antwort_landet_am_auftrag(ablage):
    eintrag = ablage.auftrag_anlegen({"text": "Frage", "ansicht": "bericht"})
    ablage.auftrag_aendern({"id": eintrag["id"], "antwort": "Antwort",
                            "wer": "Claude", "status": "angenommen"})
    gelesen = ablage.auftraege_lesen()["eintraege"][0]
    assert gelesen["status"] == "angenommen"
    assert gelesen["antworten"][0]["wer"] == "Claude"


def test_eine_unbekannte_kennung_wird_gemeldet_statt_verschluckt(ablage):
    with pytest.raises(ValueError):
        ablage.auftrag_aendern({"id": "gibtsnicht", "status": "erledigt"})
    with pytest.raises(ValueError):
        ablage.auftrag_loeschen({"id": "gibtsnicht"})


def test_eine_kaputte_ablage_wird_nicht_ueberschrieben(ablage):
    """Der teuerste Fall: Wer eine Woche lang gesammelt hat, soll das nicht
    dadurch verlieren, dass ein Schreibvorgang abgebrochen ist."""
    with open(ablage.AUFTRAGSDATEI, "w", encoding="utf-8") as f:
        f.write('{"eintraege": [ kaputt')

    with pytest.raises(RuntimeError):
        ablage.auftraege_lesen()

    with open(ablage.AUFTRAGSDATEI, encoding="utf-8") as f:
        assert "kaputt" in f.read()


def test_geschrieben_wird_erst_daneben_dann_umbenannt(ablage):
    """Ein abgebrochenes Schreiben soll keine halbe Datei hinterlassen."""
    ablage.auftrag_anlegen({"text": "eins"})
    assert not os.path.exists(ablage.AUFTRAGSDATEI + ".neu")


def test_der_status_kommt_aus_der_liste_und_nicht_vom_absender(ablage):
    """Ein erfundener Status würde die Karte unsichtbar machen."""
    eintrag = ablage.auftrag_anlegen({"text": "eins"})
    ablage.auftrag_aendern({"id": eintrag["id"], "status": "gelöscht-hihi"})
    assert ablage.auftraege_lesen()["eintraege"][0]["status"] == "offen"


# ══════════════════════════════════════════════════════════════════════
# Der Melder
# ══════════════════════════════════════════════════════════════════════
#
# `scripts/auftraege-melden.py` liest die Ablage und gibt jeden neuen
# Auftrag als Zeile aus. Als Monitor gestartet wird daraus eine Meldung in
# der laufenden Sitzung — damit weckt ein Klick in der Vorschau die Arbeit.

MELDER = os.path.join(os.path.dirname(__file__), "..", "..", "..",
                      "scripts", "auftraege-melden.py")


@pytest.fixture(scope="module")
def melder():
    spec = importlib.util.spec_from_file_location("auftraege_melden", MELDER)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_ohne_ablage_meldet_er_nichts_und_faellt_nicht_um(melder, tmp_path,
                                                          monkeypatch):
    monkeypatch.setattr(melder, "ABLAGE", str(tmp_path / "gibtsnicht.json"))
    eintraege, fehler = melder.lesen()
    assert eintraege == [] and fehler is None


def test_eine_kaputte_ablage_wird_gemeldet_statt_verschwiegen(melder, tmp_path,
                                                             monkeypatch):
    """Stille ist kein Erfolg. Ein Melder, der nur bei guten Nachrichten
    spricht, sieht im Fehlerfall aus wie einer, bei dem nichts los ist."""
    datei = tmp_path / "a.json"
    datei.write_text("{ kaputt", encoding="utf-8")
    monkeypatch.setattr(melder, "ABLAGE", str(datei))
    eintraege, fehler = melder.lesen()
    assert eintraege is None
    assert fehler and "lesbar" in fehler


def test_die_meldung_traegt_alles_zum_nachstellen(melder):
    """Ohne Stelle und Reglerstand ist „der Kasten sieht falsch aus" nicht
    nachstellbar: Mit Rabatt sieht dieselbe Stelle anders aus als ohne."""
    text = melder.beschreiben({
        "id": "a1", "ansicht": "bericht", "text": "Der Preis steht zweimal da",
        "auszug": "FESTPREIS 3.500,00 € netto",
        "regler": {"punkte": "61", "rabatt": "an"},
    })
    assert "a1" in text
    assert "bericht" in text
    assert "Der Preis steht zweimal da" in text
    assert "FESTPREIS" in text
    assert "rabatt=an" in text


def test_der_melder_schreibt_nicht(melder):
    """Ein Wächter, der in die Datei fasst, die er bewacht, kann sie
    beschädigen — und dann ist eine Woche Beanstandungen weg."""
    with open(MELDER, encoding="utf-8") as f:
        quelle = f.read()
    # Nur die Ausführungsteile ansehen, nicht die Erklärungen darüber.
    ohne_text = re.sub(r'"""[\s\S]*?"""', "", quelle)
    ohne_text = re.sub(r"^\s*#.*$", "", ohne_text, flags=re.MULTILINE)
    for verboten in ('open(ABLAGE, "w"', "os.replace", "json.dump(",
                     ".write(", "os.remove"):
        assert verboten not in ohne_text, f"Der Melder schreibt: {verboten}"


def test_die_vorschau_und_der_melder_lesen_dieselbe_datei(melder, vorschau):
    """Zwei Wahrheiten wären der teuerste Fehler: Der Auftrag läge in der
    einen Datei und der Melder sähe in die andere."""
    assert os.path.basename(melder.ABLAGE) == os.path.basename(vorschau.AUFTRAGSDATEI)
    assert melder.ABLAGE == vorschau.AUFTRAGSDATEI


def test_die_widget_aufrufe_sehen_die_eingestellten_regler(vorschau):
    """Gemeldet von David am 10.09.2026 — und es war die Vorschau, nicht das Widget.

    Der Teaser zeigte „Check PLUS können Sie in Kürze direkt hier
    beauftragen" statt des Kaufknopfs, obwohl der Regler „Kaufknöpfe" an
    war. Grund: Das Widget ruft `/api/widget/config` mit **seiner** Adresse
    auf und trägt die Regler der Vorschau nicht mit; die Schnittstelle sah
    deshalb immer leere Einstellungen.

    Eine Vorschau, die einen Zustand zeigt, den die Einstellungen nicht
    sagen, ist schlimmer als keine: Man repariert etwas, das heil ist.
    """
    vorschau.LETZTE_REGLER.clear()
    vorschau.LETZTE_REGLER.update({"kaufwege": "an", "punkte": "61"})

    angebot = vorschau.api_config(vorschau.LETZTE_REGLER)["check_plus"]
    assert angebot, "ohne Angebot kein Knopf"
    werte = " ".join(str(w) for w in angebot.values())
    assert vorschau.KAUF_CHECK in werte


def test_ohne_den_regler_bleibt_der_knopf_weg(vorschau):
    """Das Gegenstück — sonst prüft der Test nur, dass irgendetwas da ist.

    Ohne Kaufadresse zeigt das Widget den Angebotsblock **ohne** Abschluss.
    Das ist Absicht: Ein Knopf, der eine 404 öffnet, wird von niemandem
    gemeldet; ein fehlender Knopf fällt auf.
    """
    vorschau.LETZTE_REGLER.clear()
    angebot = vorschau.api_config({})["check_plus"]
    werte = " ".join(str(w) for w in (angebot or {}).values())
    assert vorschau.KAUF_CHECK not in werte


def test_das_pdf_ist_ein_pdf_und_nicht_leer(vorschau):
    """Es hängt seit jeher am Trichter und hatte bis zum 10.09.2026 niemand
    angesehen — es entsteht sonst nur hinter einem bestätigten Token."""
    daten = vorschau.ansicht_pdf({"punkte": "61"})
    assert daten.startswith(b"%PDF-"), "kein PDF"
    assert len(daten) > 5000, f"nur {len(daten)} Byte — verdächtig leer"


def test_die_kaufknoepfe_oeffnen_ein_neues_fenster(vorschau):
    """Wunsch David, 10.09.2026 — mit `noopener`, und das ist keine Kosmetik.

    Ohne `rel="noopener"` kann die geöffnete Seite über `window.opener` die
    Berichtsseite umlenken: auf eine, die aussieht wie unsere und nach
    Zahlungsdaten fragt. Der Bericht liegt hinter einem Link aus einer
    E-Mail; genau dort rechnet niemand damit.
    """
    seite = vorschau.ansicht_bericht({"kaufwege": "an"}).decode("utf-8")
    knoepfe = re.findall(r'<a[^>]*buy\.stripe\.com[^>]*>', seite)
    assert len(knoepfe) == 2, f"{len(knoepfe)} Kaufknöpfe gefunden"
    for knopf in knoepfe:
        assert 'target="_blank"' in knopf, knopf[:120]
        assert "noopener" in knopf, knopf[:120]


def test_der_pdf_knopf_zeigt_nicht_ins_produktivsystem(vorschau):
    """Er zeigte auf api.kompagnon.group mit einem erfundenen Token — ein
    Knopf, der im Nichts endet, an einer Stelle, an der produktiv alles
    stimmt. Aus einem Auftrag gelernt, nicht aus einem Test."""
    seite = vorschau.ansicht_bericht({}).decode("utf-8")
    # Nur der PDF-Knopf, nicht die ganze Seite: Die Fusszeile verlinkt
    # bewusst auf kas.kompagnon.group, und das ist richtig so.
    pdf_knoepfe = re.findall(r'<a[^>]*href="([^"]*/pdf)"', seite)
    assert pdf_knoepfe, "kein PDF-Knopf auf der Seite"
    for adresse in pdf_knoepfe:
        assert adresse.startswith(f"http://127.0.0.1:{vorschau.PORT}"), adresse


def test_auch_der_pdf_knopf_oeffnet_ein_neues_fenster(vorschau):
    """Wunsch David, 10.09.2026 — dieselbe Begründung wie beim Kaufknopf:
    Der Bericht soll offen bleiben, wenn man das PDF holt."""
    seite = vorschau.ansicht_bericht({}).decode("utf-8")
    knoepfe = re.findall(r'<a[^>]*href="[^"]*/pdf"[^>]*>', seite)
    assert knoepfe, "kein PDF-Knopf"
    for knopf in knoepfe:
        assert 'target="_blank"' in knopf, knopf[:120]
        assert "noopener" in knopf, knopf[:120]
