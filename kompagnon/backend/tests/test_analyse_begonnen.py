# -*- coding: utf-8 -*-
"""Sender und Empfaenger des Ereignisses „Analyse begonnen" (Fassung 2).

**Was diese Datei kann und was nicht.** Der eigentliche Beleg ist der
Durchlauf im Browser. Was hier geprueft wird, ist enger und trotzdem nicht
wertlos: dass alle drei Fundstellen **denselben Namen** benutzen und dass
die Zusagen im Quelltext stehen, die man beim naechsten Umbau versehentlich
herausnimmt.

**Drei Fundstellen, nicht zwei.** Das Widget sendet; der Empfaenger steht
sowohl in der **ausgelieferten Landingpage** (`docs/landingpage/`) als auch
in der **Einbauanleitung** (`README.md` des Widgets). Laufen die beiden
auseinander, ist die Anleitung eine Falle fuer den Naechsten, der sie
einsetzt — deshalb prueft jeder Test hier beide.

**Weg A, Entscheidung David am 15.09.2026.** Gemeldet wird, wenn die
Adresse eingetippt und das Feld verlassen ist — nicht beim Tippen, nicht
erst beim Absenden. Zuvor war es Weg B (Absenden); die Fassung 2 hat das
umgestellt, weil auf `Lead` die Menge fuer Metas Lernphase nicht erreicht
wird.
"""
import pathlib

import pytest

EMBED = pathlib.Path(__file__).resolve().parents[2] / "frontend" / "public" / "embed"
WIDGET = EMBED / "audit-widget.html"
README = EMBED / "README.md"
LANDINGPAGE = (pathlib.Path(__file__).resolve().parents[3]
               / "docs" / "landingpage" / "websprint-landingpage.html")

#: Der Name der Nachricht. Er steht an drei Stellen, und wenn sie
#: auseinanderlaufen, faellt nichts aus — es wird nur nichts mehr gemessen.
NACHRICHT = "kpg-analyse-begonnen"


@pytest.fixture(scope="module")
def widget():
    return WIDGET.read_text(encoding="utf-8")


def _block_aus_readme() -> str:
    for teil in README.read_text(encoding="utf-8").split("```html")[1:]:
        rumpf = teil.split("```", 1)[0]
        if NACHRICHT in rumpf:
            return rumpf
    raise AssertionError(f"Kein Einbau-Block mit {NACHRICHT} im README")


def _block_aus_landingpage() -> str:
    """Die ausgelieferte Seite ist ein Bundler-Export: Der Block liegt dort
    escaped. Wer hier ohne Rueckverwandlung sucht, findet nichts und haelt
    es fuer ein fehlendes Merkmal.

    **Nicht nur drei Sequenzen aufloesen.** Der erste Anlauf kannte `\\n`,
    `\\u002F` und `\\"` — und scheiterte an den Rahmenstrichen der
    Kommentare, die als `\\u2500` dastehen. Jede `\\uXXXX`-Folge wird
    aufgeloest, sonst prueft der Test seinen eigenen Ausschnitt.
    """
    import re as _re

    text = LANDINGPAGE.read_text(encoding="utf-8", errors="replace")
    text = _re.sub(r"\\u([0-9a-fA-F]{4})",
                   lambda m: chr(int(m.group(1), 16)), text)
    return text.replace("\\n", "\n").replace('\\"', '"')


@pytest.fixture(scope="module", params=["readme", "landingpage"])
def empfaenger(request):
    return (_block_aus_readme() if request.param == "readme"
            else _block_aus_landingpage())


# ── Der Sender ────────────────────────────────────────────────────────

def test_das_widget_meldet_den_beginn(widget):
    assert f"parent.postMessage({{ type: '{NACHRICHT}' }}, '*')" in widget


def test_die_meldung_traegt_nichts_ueber_den_besucher(widget):
    """Die Nachricht geht mit `'*'` an ein fremdes Fenster — alles darin ist
    fuer jeden lesbar, der dort ein Skript hat."""
    zeile = next(z for z in widget.splitlines()
                 if NACHRICHT in z and "postMessage" in z)
    for verboten in ("email", "url", "cleanUrl", "website"):
        assert verboten not in zeile, f"{verboten!r} gehoert nicht in die Meldung"


def test_gemeldet_wird_beim_verlassen_des_adressfeldes(widget):
    """**Weg A.** Beide Ereignisse, weil keins allein reicht: `change`
    bleibt aus, wenn der Wert unveraendert bleibt; `blur` bleibt aus, wenn
    jemand mit der Eingabetaste abschickt."""
    rumpf = widget.split("urlEl.addEventListener('input'", 1)[1][:1200]
    assert "'blur'" in rumpf and "'change'" in rumpf
    assert "meldeAnalyseBegonnen()" in rumpf


def test_nicht_beim_tippen(widget):
    """Ein `input`-Ereignis feuerte bei jedem Zeichen. Das vorhandene
    `input` darf die Meldung deshalb **nicht** ausloesen."""
    zeile = next(z for z in widget.splitlines()
                 if "addEventListener('input'" in z)
    assert "meldeAnalyseBegonnen" not in zeile


def test_das_absenden_meldet_nach(widget):
    """Der Fall, der sonst durchfaellt: Eingabetaste, ohne das Feld je
    verlassen zu haben."""
    rumpf = widget.split("function startAudit(", 1)[1]
    assert "meldeAnalyseBegonnen();" in rumpf.split("\n")[1]


def test_ein_tippanfang_zaehlt_nicht_als_begonnene_analyse(widget):
    """**Es gab keine Adresspruefung zum Wiederverwenden** — `normalizeUrl`
    setzt nur `https://` davor. Ohne eine eigene wuerde ein einzelner
    Buchstabe als begonnene Analyse zaehlen, und die Wochenmenge bedeutete
    nichts mehr."""
    assert "function adresseWirktVollstaendig" in widget
    rumpf = widget.split("function adresseWirktVollstaendig", 1)[1][:400]
    assert "test(" in rumpf


def test_genau_einmal_je_sitzung(widget):
    rumpf = widget.split("function meldeAnalyseBegonnen()", 1)[1][:300]
    assert "if (analyseBegonnenGemeldet) return;" in rumpf
    assert "analyseBegonnenGemeldet = true;" in rumpf


# ── Der Empfaenger, in beiden Fassungen ───────────────────────────────

def test_der_empfaenger_hoert_auf_dieselbe_nachricht(empfaenger):
    """**Der Fund, den nur ein Vergleich zeigt.** Laufen die Namen
    auseinander, faellt nichts aus: Das Widget sendet weiter, die Seite
    hoert weiter zu, und gemessen wird nichts mehr."""
    assert f"d.type === '{NACHRICHT}'" in empfaenger


def test_der_empfaenger_prueft_die_einwilligung_vor_dem_ereignis(empfaenger):
    """Mit **derselben** Funktion, die auch vor dem Laden des Pixels steht.
    Zwei Pruefungen fuer dieselbe Frage laufen auseinander — und die
    Abweichung faellt genau dann auf, wenn jemand widersprochen hat."""
    zweig = empfaenger.split(f"d.type === '{NACHRICHT}'", 1)[1].split("fbq(", 1)[0]
    assert "einwilligung()" in zweig
    assert ".marketing" in zweig


def test_der_empfaenger_meldet_meta_und_ga4(empfaenger):
    """Zwei Haeuser, zwei Vokabulare, ein Ereignis.

    **Am 17.09.2026 von der Zeichenkette auf die Sache umgestellt.** Hier
    stand `"fbq('track', 'InitiateCheckout')"` mit schliessender Klammer —
    und schlug fehl, sobald der Aufruf eine `eventID` bekam. Der Test hatte
    damit eine richtige Ergaenzung als Fehler gemeldet. Geprueft wird jetzt,
    dass das Ereignis gemeldet wird, nicht wie der Aufruf buchstabiert ist.
    """
    zweig = empfaenger.split(f"d.type === '{NACHRICHT}'", 1)[1][:900]
    assert "fbq('track', 'InitiateCheckout'" in zweig
    assert "gtag('event', 'begin_checkout')" in zweig


def test_das_meta_ereignis_traegt_eine_eigene_kennung(empfaenger):
    """**Die zweite Absicherung, unabhaengig von unserer Sperre** (17.09.2026).

    Die Sperre `begonnenGemeldet` haelt, solange diese Seite laeuft. Sie
    haelt nicht bei zwei Tabs, nicht bei einem fremden Skript, das die
    Nachricht spiegelt, und nicht bei einem iframe aus dem Zwischenspeicher
    neben einer frisch geladenen Seite — genau die Lage, die am 17.09. zu
    der Meldung „feuert doppelt" gefuehrt hat.

    Mit einer Kennung, die bei einer Wiederholung **dieselbe** ist, verwirft
    Meta die zweite Meldung selbst. Deshalb steht ihre Bildung **ausserhalb**
    des Empfaengers: Im Empfaenger gebildet waere sie bei jeder Meldung neu
    und damit wirkungslos.
    """
    assert "eventID: begonnenKennung" in empfaenger, (
        "Der InitiateCheckout traegt keine Kennung — Metas Entdopplung "
        "haengt dann an einem Verhalten, das nicht zugesagt ist.")

    # Positiv daneben: Sie wird ueberhaupt gebildet, und zwar **vor** der
    # Stelle, die sie benutzt. Ohne diese Zusicherung waere die obige auch
    # dann gruen, wenn `begonnenKennung` nirgends entsteht
    # (`waechter_ohne_wirkung`).
    #
    # **Nicht am ersten `addEventListener('message'` schneiden.** Die
    # ausgelieferte Seite hat davon vier — Relay, iframe-Hoehe, Messblock,
    # Einwilligung —, und der erste steht weit vor dieser Stelle. Ein
    # Schnitt dort prueft einen Abschnitt, in dem die Kennung gar nicht
    # stehen soll. (Selbst hineingelaufen, 17.09.2026.)
    assert "var begonnenKennung" in empfaenger, (
        "Die Kennung wird nirgends gebildet.")
    assert empfaenger.index("var begonnenKennung") < \
        empfaenger.index("eventID: begonnenKennung"), (
        "Die Kennung steht hinter ihrer Verwendung.")

    # Und sie liegt ausserhalb des Empfaenger-Zweigs: Im Zweig gebildet
    # waere sie bei jeder Meldung neu und damit wirkungslos.
    zweig = empfaenger.split(f"d.type === '{NACHRICHT}'", 1)[1]
    assert "var begonnenKennung" not in zweig, (
        "Die Kennung entsteht im Empfaenger-Zweig statt davor — dann ist "
        "sie bei jeder Meldung neu und entdoppelt nichts.")


def test_ga4_nur_wenn_es_gtag_gibt(empfaenger):
    """`gtag` entsteht erst nach Statistik-Einwilligung — dieselbe Pruefung
    wie beim Lead darunter, nicht eine zweite eigene."""
    zweig = empfaenger.split(f"d.type === '{NACHRICHT}'", 1)[1][:900]
    vor_gtag = zweig.split("gtag('event'", 1)[0]
    assert "typeof window.gtag === 'function'" in vor_gtag


def test_der_empfaenger_prueft_herkunft_und_absender(empfaenger):
    """Ohne beides nimmt die Seite ein `InitiateCheckout` von jedem an, der
    ihr eine Nachricht schickt."""
    assert "e.origin !== URSPRUNG" in empfaenger
    assert "f.contentWindow !== e.source" in empfaenger


def test_der_empfaenger_meldet_nur_einmal_je_seitenaufruf(empfaenger):
    zweig = empfaenger.split(f"d.type === '{NACHRICHT}'", 1)[1].split("fbq(", 1)[0]
    assert "begonnenGemeldet" in zweig


def test_der_lead_bleibt_unveraendert(empfaenger):
    """Die Fassung 2 sagt es ausdruecklich: „Der Lead bleibt unveraendert,
    wie er ist.\""""
    assert "fbq('track', 'Lead'" in empfaenger
    assert "gtag('event', 'generate_lead'" in empfaenger


def test_anleitung_und_ausgelieferte_seite_stimmen_ueberein():
    """**Die teuerste Abweichung dieser Strecke.** Am 15.09.2026 stand der
    Empfaenger nur im README, weil ich die versionierte Landingpage
    uebersehen hatte — die Anleitung war aktuell, die Seite nicht. Wer das
    nicht bemerkt, laedt eine Seite hoch, die das Ereignis nicht kennt.
    """
    import re

    fest = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731
    readme, seite = _block_aus_readme(), _block_aus_landingpage()

    anfang = "/* ── 3. Was das Widget meldet"
    schnitt = lambda t: fest(t[t.index(anfang):])[:1800]  # noqa: E731
    assert schnitt(readme) == schnitt(seite), (
        "Einbauanleitung und ausgelieferte Landingpage sind verschieden")
