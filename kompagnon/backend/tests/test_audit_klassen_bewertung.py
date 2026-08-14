"""Gemessen wird gegen den Maßstab der eigenen Branche — nicht nur beschrieben.

Seit dem 14.08.2026 nennt der Bericht die Branchenklasse und beschreibt die
Kriterien in ihrer Sprache. Gerechnet wurde weiter handwerklich: „Eigene
Leistungsseiten" suchte `wärmepumpe` und `wallbox`, „Vertrauenssignale"
`meisterbetrieb` und `innung`. Ein Ingenieurbüro verlor Punkte für etwas, das
es gar nicht haben kann.

Diese Tests laufen durch die Erhebung **und** die Bewertung: Die Stichworte
allein sind ein Datensatz, erst die Punktzahl ist die Aussage.
"""
from bs4 import BeautifulSoup

from services.audit_collectors import analyse_cta, analyse_service_pages, analyse_trust
from services.audit_scoring import score_audit

BASIS = "https://beispiel.de"

NAVIGATION_KANZLEI = """
<nav>
  <a href="/rechtsgebiete/arbeitsrecht">Arbeitsrecht</a>
  <a href="/fachgebiet/erbrecht">Erbrecht</a>
  <a href="/gutachten">Gutachten</a>
  <a href="/kontakt">Kontakt</a>
</nav>
"""

NAVIGATION_HANDWERK = """
<nav>
  <a href="/leistungen/waermepumpe">Wärmepumpe</a>
  <a href="/leistungen/bad">Bad</a>
  <a href="/notdienst">Notdienst</a>
  <a href="/kontakt">Kontakt</a>
</nav>
"""


def _punkte(kriterium: str, klasse: str, **fakten) -> int:
    ergebnis = score_audit(fakten, {"branchenklasse": klasse})
    return ergebnis["items"][kriterium]


def _services(html: str) -> dict:
    return analyse_service_pages(BeautifulSoup(html, "html.parser"), BASIS)


def _trust(html: str) -> dict:
    return analyse_trust(BeautifulSoup(html, "html.parser"))


def _cta(html: str) -> dict:
    return analyse_cta(BeautifulSoup(html, "html.parser"))


# ── Eigene Leistungsseiten ────────────────────────────────────────────

def test_eine_kanzlei_bekommt_ihre_rechtsgebiete_angerechnet():
    assert _punkte("ih_leistungsseiten", "K2",
                   services=_services(NAVIGATION_KANZLEI)) == 2


def test_derselbe_auftritt_gegen_den_handwerksmassstab_verliert_die_punkte():
    """Der Beleg, dass die Klasse wirklich entscheidet und nicht nur dabeisteht."""
    assert _punkte("ih_leistungsseiten", "K1",
                   services=_services(NAVIGATION_KANZLEI)) == 0


def test_ein_handwerksbetrieb_behaelt_seine_punkte():
    assert _punkte("ih_leistungsseiten", "K1",
                   services=_services(NAVIGATION_HANDWERK)) == 2


def test_die_basisbegriffe_tragen_auch_ohne_klassenwort():
    """„/leistungen" allein reicht in jeder Klasse für den ersten Punkt."""
    services = _services('<a href="/leistungen">Leistungen</a>')

    assert _punkte("ih_leistungsseiten", "K4", services=services) == 1


# ── Vertrauenssignale ─────────────────────────────────────────────────

def test_die_kammer_zaehlt_beim_ingenieurbuero():
    trust = _trust("<p>Mitglied der Ingenieurkammer Rheinland-Pfalz</p>")

    assert _punkte("cv_vertrauen", "K2", trust=trust) == 1


def test_der_meisterbrief_zaehlt_beim_ingenieurbuero_nicht():
    trust = _trust("<p>Meisterbetrieb seit 1998</p>")

    assert _punkte("cv_vertrauen", "K2", trust=trust) == 0
    assert _punkte("cv_vertrauen", "K1", trust=trust) == 1


def test_die_uebrigen_signale_gelten_in_jeder_klasse():
    """Bewertungen, Referenzen, Team und Garantie sind branchenunabhängig."""
    trust = _trust("<p>Unser Team · Referenzen · Kundenstimmen · Garantie</p>")

    assert _punkte("cv_vertrauen", "K2", trust=trust) == 3
    assert _punkte("cv_vertrauen", "K5", trust=trust) == 3


# ── Zielhandlung ──────────────────────────────────────────────────────

def test_der_warenkorb_ist_die_zielhandlung_des_shops():
    cta = _cta('<a href="/cart">In den Warenkorb</a>')

    assert _punkte("cv_cta", "K5", cta=cta) == 2
    assert _punkte("cv_cta", "K1", cta=cta) == 0


def test_die_terminanfrage_gilt_ueberall():
    cta = _cta('<a href="/termin">Termin vereinbaren</a>')

    assert _punkte("cv_cta", "K1", cta=cta) == 2
    assert _punkte("cv_cta", "K5", cta=cta) == 2


# ── Altbestand ────────────────────────────────────────────────────────

def test_fakten_ohne_begriffe_behalten_ihre_punktzahl():
    """Erhebungen von vor dem Branchenmodell dürfen nicht nachträglich fallen."""
    alt = {"collected": True, "service_page_count": 4}

    assert _punkte("ih_leistungsseiten", "K2", services=alt) == 2


def test_ohne_erkannte_klasse_wird_grosszuegig_gezaehlt():
    """Wen die Erkennung nicht einordnen konnte, werten wir dafür nicht ab."""
    ergebnis = score_audit({"services": _services(NAVIGATION_KANZLEI)}, {})

    assert ergebnis["items"]["ih_leistungsseiten"] == 2
