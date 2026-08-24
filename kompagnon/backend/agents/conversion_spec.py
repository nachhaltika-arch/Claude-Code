"""Die verbindlichen Regeln aus `docs/conversion-spec-shk.md` (L-15).

Die Spec liegt seit Mai 2026 im Repo und erklärt sich in ihrem § 6 selbst für
verbindlich — für den `content_writer`, die Vorlagen und den QA-Agenten. Bis
zum 24.08.2026 kam davon nichts an: Im Texter gab es keinen Treffer auf
„Hormozi", „Offer", „Garantie" oder „Wertebox". Er schrieb Leistungen als
Feature-Liste, ohne bezifferte Garantien und ohne Wertebox.

**Warum ein eigenes Modul und nicht Text im Prompt.** Zwei Gründe, und der
zweite ist der wichtigere:

1. Ein Prompt ist nicht prüfbar, eine Liste schon. `tests/
   test_conversion_spec_im_texter.py` hält fest, dass die Regeln ankommen —
   und dass die Liste hier nicht auseinanderläuft mit § 7 der Spec.
2. **§ 7 ist Recht, nicht Stil.** „Geld-zurück-Garantie" ist bei Werkverträgen
   (BGB § 631 ff.) nicht erfüllbar und AGB-rechtlich angreifbar;
   „Heizkosten um 80 % senken garantiert" ist UWG § 5 Irreführung und
   abmahnfähig; ein Phantasie-Anker verstößt gegen PreisAngVO. Was
   abmahnfähig ist, gehört an eine benannte Stelle mit Begründung — nicht
   mitten in einen f-String.

**Was hier nicht steht.** § 6 verlangt außerdem neue Pflichtfelder im
Generator-Eingang (Innungs-Mitgliedsnummer, Hersteller-Partnerschaften,
BAFA-Listing, Google-Place-ID, drei Referenzfälle mit Zahlen). Das ist
Datenmodell und Oberfläche, nicht Textproduktion — es bleibt in L-15 offen.
"""

#: Was jeder Seiten-Text erfüllen muss (Spec § 1, § 2, § 3, § 4, § 5).
#: Reihenfolge ist Absicht: Sie folgt dem Offer-Stack-Sequencing aus § 3.
SPEC_REGELN = (
    ("Hero nach der Value Equation",
     "Ein Satz, der Outcome, Zeit bis zum Ergebnis und den Aufwand für den "
     "Kunden nennt — nicht die Leistung, sondern das Ergebnis "
     "(„Festpreis in 7 Tagen, Installation in 30 Tagen“)."),
    ("Leistungen als Ergebnis-Versprechen",
     "Kein „Wir installieren Wärmepumpen“, sondern was der Kunde danach hat, "
     "mit Zeitangabe."),
    ("Bezifferte Wertebox",
     "Der Offer-Stack als Bullet-Liste mit EUR-Wert je Position, Ankerwert "
     "und Aktionspreis. Anker nur marktbelegbar."),
    ("Konkrete Garantien statt vager Qualitätsversprechen",
     "Vier bis fünf bezifferte Versprechen (Termintreue, Festpreis, "
     "Reaktionszeit, Nachbesserung) — jede einzeln nachprüfbar."),
    ("FAQ als Einwand-Behandlung",
     "Mit konkreten Zahlen zu Altbau-Eignung, Lautstärke in dB und "
     "Kälte-Leistung — nicht funktionale Fragen zu Öffnungszeiten."),
    ("Fünf Outcome-CTA-Varianten",
     "Verb plus konkretes Ergebnis plus Aufwands-Abbau, A/B-fähig. "
     "Kein „Mehr erfahren“."),
    ("Ehrliche Dringlichkeit",
     "Nur echte BAFA-/GEG-Stichtage und tatsächliche Terminverfügbarkeit."),
    ("Offer-Naming nach Formel",
     "Anlass, Zielgruppe, Ziel, Zeit, Gefäß — „Koblenzer "
     "Wärmepumpen-Komplettpaket, warm in 30 Tagen“."),
    ("Höchstens acht Bonus-Elemente",
     "Mehr wirkt im SHK-Markt wie eine Drückerkolonne."),
)

#: Was **nicht** geschrieben werden darf (Spec § 7). Jede Zeile trägt ihren
#: Grund, weil eine Verbotsliste ohne Begründung beim nächsten Umbau fällt.
#: `stichwort` muss so in der Spec stehen — ein Test hält das fest.
ANTI_MUSTER = (
    {"stichwort": "Geld-zurück-Garantie",
     "grund": "Bei Werkverträgen (BGB § 631 ff.) nicht erfüllbar und "
              "AGB-rechtlich angreifbar."},
    {"stichwort": "Übertriebene Heils-Versprechen",
     "grund": "„Heizkosten um 80 % senken garantiert“ ist UWG § 5 "
              "Irreführung — abmahnfähig."},
    {"stichwort": "Künstliche FOMO-Banner",
     "grund": "Countdown-Timer und „nur noch 2 Stunden“ wirken bei der "
              "Zielgruppe 50+ unseriös."},
    {"stichwort": "Hormozi-Sales-Sprache",
     "grund": "US-Tonalität wirkt im deutschen Handwerk marktschreierisch."},
    {"stichwort": "Personalisierte Anrede mit Vorname",
     "grund": "DSGVO/TTDSG-heikel und kulturell zu intim."},
    {"stichwort": "Maximaler Bonus-Stack",
     "grund": "15+ Elemente wirken wie eine Drückerkolonne; höchstens acht."},
    {"stichwort": "Affiliate-Bonus-Stacking",
     "grund": "UWG-Transparenzpflicht."},
    {"stichwort": "Anti-Guarantee",
     "grund": "Konflikt mit dem Verbraucher-Widerrufsrecht."},
    {"stichwort": "Hochpreis-Anker als reine Phantasie",
     "grund": "PreisAngVO und UWG-Irreführung."},
)

#: Felder, die die Spec zusätzlich zum bisherigen Text verlangt.
PFLICHT_FELDER = ("garantien", "wertebox", "cta_varianten", "einwand_faq")


def spec_regeln() -> str:
    """Die Regeln als Auftragstext — nummeriert, damit man sie zitieren kann."""
    zeilen = [
        f"{nr}. {titel}: {erklaerung}"
        for nr, (titel, erklaerung) in enumerate(SPEC_REGELN, start=1)
    ]
    return "\n".join(zeilen)


def verbotene_formulierungen() -> str:
    """Die Verbote mit Begründung — der Grund gehört dazu.

    Ein Modell, das weiß **warum** etwas verboten ist, findet auch die
    Variante, die in der Liste nicht steht.
    """
    zeilen = [
        f"- {m['stichwort']}: {m['grund']}" for m in ANTI_MUSTER
    ]
    return "\n".join(zeilen)
