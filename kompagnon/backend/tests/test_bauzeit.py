# -*- coding: utf-8 -*-
"""Wann die Bauzeit endet — gerechnet statt behauptet (L-166, K3).

**Der Anlass.** Der Angebotsfuss sagt zwei Dinge zu: „Die vereinbarte Bauzeit
beginnt an dem Werktag, an dem saemtliche Mitwirkungsleistungen vollstaendig
vorliegen. Verzoegert sich eine Freigabe nach M7 oder M8, ruht die Frist fuer
die Dauer der Verzoegerung." Die erste Haelfte trug seit dem 03.09.2026
(`mitwirkung_stand.erledigt_am`), die zweite gar nicht: Es gab kein Feld fuer
den **Vorlagezeitpunkt**, also auch keine Spanne, also kein berechenbares Ende.

**Warum die Rechnung ein eigenes Modul ist und nicht im Router steht.** Sie
ist die Zahl, an der im Streit die Garantie haengt. Eine Zahl, die nur beim
Beantworten einer Anfrage entsteht, laesst sich nicht pruefen — und sie wird
an drei Stellen gebraucht: im Kundenkonto, im Innendienst und spaeter in der
Garantiepruefung.
"""
from datetime import date, datetime

from services import bauzeit


# ── Werktage ──────────────────────────────────────────────────────────

def test_das_wochenende_ist_kein_werktag():
    assert bauzeit.ist_werktag(date(2026, 9, 4))       # Freitag
    assert not bauzeit.ist_werktag(date(2026, 9, 5))   # Samstag
    assert not bauzeit.ist_werktag(date(2026, 9, 6))   # Sonntag
    assert bauzeit.ist_werktag(date(2026, 9, 7))       # Montag


def test_bundeseinheitliche_feiertage_zaehlen_nicht_als_werktag():
    """**Warum Feiertage ueberhaupt vorkommen.** Eine Frist von fuenf
    Werktagen, die den 1. Mai mitzaehlt, nimmt dem Kunden einen Tag, den er
    vertraglich hat — und er merkt es. Gezaehlt werden nur die **bundesweit**
    einheitlichen neun; alles Weitere haengt am Bundesland und waere geraten.
    """
    assert not bauzeit.ist_werktag(date(2026, 1, 1))    # Neujahr
    assert not bauzeit.ist_werktag(date(2026, 5, 1))    # Tag der Arbeit
    assert not bauzeit.ist_werktag(date(2026, 10, 3))   # Deutsche Einheit
    assert not bauzeit.ist_werktag(date(2026, 12, 25))  # 1. Weihnachtstag
    assert not bauzeit.ist_werktag(date(2026, 12, 26))  # 2. Weihnachtstag


def test_die_beweglichen_feiertage_haengen_am_ostersonntag():
    """Ostersonntag 2026 ist der 5. April; 2027 der 28. Maerz. Karfreitag,
    Ostermontag, Christi Himmelfahrt und Pfingstmontag folgen daraus."""
    assert bauzeit.ostersonntag(2026) == date(2026, 4, 5)
    assert bauzeit.ostersonntag(2027) == date(2027, 3, 28)

    assert not bauzeit.ist_werktag(date(2026, 4, 3))    # Karfreitag
    assert not bauzeit.ist_werktag(date(2026, 4, 6))    # Ostermontag
    assert not bauzeit.ist_werktag(date(2026, 5, 14))   # Christi Himmelfahrt
    assert not bauzeit.ist_werktag(date(2026, 5, 25))   # Pfingstmontag


def test_werktage_addieren_ueberspringt_wochenende():
    """Montag + 5 Werktage ist der Montag darauf, nicht der Samstag."""
    assert bauzeit.werktage_addieren(date(2026, 9, 7), 5) == date(2026, 9, 14)
    assert bauzeit.werktage_addieren(date(2026, 9, 7), 0) == date(2026, 9, 7)


def test_werktage_addieren_von_einem_wochenende_aus_beginnt_am_werktag():
    """Ein Samstag als Ausgangspunkt ist kein Werktag; der erste gezaehlte Tag
    ist der Montag."""
    assert bauzeit.werktage_addieren(date(2026, 9, 5), 1) == date(2026, 9, 7)


def test_werktage_zwischen_zaehlt_den_ersten_tag_nicht_mit():
    """**Die Spanne ist eine Dauer, kein Kalenderausschnitt.** Von Montag bis
    Montag sind null Werktage vergangen, nicht einer."""
    assert bauzeit.werktage_zwischen(date(2026, 9, 7), date(2026, 9, 7)) == 0
    assert bauzeit.werktage_zwischen(date(2026, 9, 7), date(2026, 9, 8)) == 1
    assert bauzeit.werktage_zwischen(date(2026, 9, 7), date(2026, 9, 14)) == 5
    assert bauzeit.werktage_zwischen(date(2026, 9, 14), date(2026, 9, 7)) == 0


# ── Die Pause je Freigabe ─────────────────────────────────────────────

def test_wer_innerhalb_der_fuenf_werktage_freigibt_pausiert_die_frist_nicht():
    """**Die Auslegung, auf der alles steht.** Der Vertrag sagt „Freigabe
    innerhalb von 5 Werktagen nach Vorlage" **und** „ruht fuer die Dauer der
    Verzoegerung". Verzoegerung ist danach, was **ueber** die fuenf Werktage
    hinausgeht — sonst waere die Zusage der fuenf Tage bedeutungslos.
    """
    p = bauzeit.pause_je_freigabe(vorgelegt_am=date(2026, 9, 7),
                                  freigegeben_am=date(2026, 9, 14),
                                  heute=date(2026, 9, 20))
    assert p.frist_bis == date(2026, 9, 14)
    assert p.werktage == 0
    assert p.laeuft_noch is False


def test_ueber_die_frist_hinaus_ruht_die_frist_tagesgenau():
    """Vorlage Montag 07.09., Frist bis Montag 14.09., freigegeben Donnerstag
    17.09. — drei Werktage Verzug, drei Werktage Pause."""
    p = bauzeit.pause_je_freigabe(vorgelegt_am=date(2026, 9, 7),
                                  freigegeben_am=date(2026, 9, 17),
                                  heute=date(2026, 9, 20))
    assert p.werktage == 3


def test_eine_offene_freigabe_pausiert_ab_heute_weiter():
    """**Die Pause endet nicht dadurch, dass niemand freigibt.** Solange die
    Freigabe aussteht, waechst sie — sonst zeigte das Konto ein Bauzeitende,
    das mit jedem Tag falscher wird und trotzdem gleich bleibt."""
    p = bauzeit.pause_je_freigabe(vorgelegt_am=date(2026, 9, 7),
                                  freigegeben_am=None,
                                  heute=date(2026, 9, 17))
    assert p.werktage == 3
    assert p.laeuft_noch is True


def test_ohne_vorlage_gibt_es_keine_pause():
    """Was nie vorgelegt wurde, kann sich nicht verzoegern — die Wartezeit
    liegt dann bei uns, nicht beim Kunden."""
    p = bauzeit.pause_je_freigabe(vorgelegt_am=None, freigegeben_am=None,
                                  heute=date(2026, 9, 17))
    assert p.werktage == 0
    assert p.frist_bis is None


# ── Das Ende, das im Angebot zugesagt ist ─────────────────────────────

def test_das_bauzeitende_ist_beginn_plus_bauzeit_plus_pausen():
    ende = bauzeit.bauzeitende(fristbeginn=date(2026, 9, 7),
                               bauzeit_werktage=14, pause_werktage=0)
    assert ende == date(2026, 9, 25)

    verschoben = bauzeit.bauzeitende(fristbeginn=date(2026, 9, 7),
                                     bauzeit_werktage=14, pause_werktage=3)
    assert verschoben == date(2026, 9, 30)


def test_ohne_fristbeginn_gibt_es_kein_ende():
    """**Kein geratenes Datum.** Solange die Mitwirkung unvollstaendig ist,
    laeuft keine Frist; ein angezeigtes Ende waere eine Zusage, die niemand
    gegeben hat."""
    assert bauzeit.bauzeitende(fristbeginn=None, bauzeit_werktage=14,
                               pause_werktage=0) is None


def test_der_fristbeginn_ist_der_werktag_des_letzten_eingangs():
    """Der Vertrag sagt „an dem Werktag, an dem saemtliche
    Mitwirkungsleistungen vollstaendig vorliegen" — der Tag selbst, wenn er
    ein Werktag ist, sonst der naechste."""
    assert bauzeit.fristbeginn_aus([datetime(2026, 9, 3, 10, 0),
                                    datetime(2026, 9, 7, 16, 30)]) == date(2026, 9, 7)
    # Letzter Eingang an einem Samstag → Montag.
    assert bauzeit.fristbeginn_aus([datetime(2026, 9, 5, 9, 0)]) == date(2026, 9, 7)


def test_ein_fehlender_eingang_laesst_die_frist_nicht_beginnen():
    """`None` in der Liste heisst: dieser Punkt liegt nicht vor."""
    assert bauzeit.fristbeginn_aus([datetime(2026, 9, 3), None]) is None
    assert bauzeit.fristbeginn_aus([]) is None
