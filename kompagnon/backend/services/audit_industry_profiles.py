"""Wogegen je Branchenklasse gemessen wird.

Bewertungslogik „Homepage Standard 2026.2", § 3 — die eigentliche Arbeit der
Ausweitung. Die Klasse kommt aus `audit_industry_map`, hier steht, was sie für
den Maßstab bedeutet.

Die Zeile, die das ganze Branchenmodell trägt, ist C5 bei K2: Eine
Steuerkanzlei ohne Preisrahmen ist nicht schlechter als eine mit, sondern
berufsrechtlich korrekt. Sie dafür abzuwerten macht den Bericht als
Akquiseinstrument unbrauchbar.

**Nur ein Teil davon erreicht das Modell.** `cv_klarheit`, `cv_angebot` und
`ih_textqualitaet` werden geschätzt — für sie wandert der Maßstab in den
Prompt. `cv_cta`, `cv_kontakt`, `cv_vertrauen`, `se_meta`, `se_schema` und
`ih_leistungsseiten` werden gemessen oder abgeleitet; ihr Maßstab steht hier
vollständig, wirkt aber noch nicht auf die Bewertung. Das ist eine offene
Lücke und keine Auslassung — siehe `docs/Audit/`.
"""
from typing import Dict

from services.audit_industry_map import KLASSEN

# Die Kriterien, deren Maßstab tatsächlich in den KI-Prompt geht. Alles andere
# in PROFILE ist Nachschlagewerk, bis die Erhebung klassenabhängig wird.
KI_KRITERIEN_MIT_PROFIL = ("cv_klarheit", "cv_angebot")

# {Kriterium: {Klasse: Maßstab}}
PROFILE: Dict[str, Dict[str, str]] = {
    # C1 — Klarheit above the fold. Gemeinsam: in fünf Sekunden erkennbar,
    # was angeboten wird und für wen. Klassenabhängig kommt hinzu:
    "cv_klarheit": {
        "K1": "Zusätzlich erkennbar: das Einsatzgebiet — ein Ort oder ein Umkreis.",
        "K2": "Zusätzlich erkennbar: Fachgebiet und Zulassung oder Qualifikation.",
        "K3": "Zusätzlich erkennbar: Standort und Öffnungszeiten oder eine "
              "Möglichkeit zu reservieren.",
        "K4": "Zusätzlich erkennbar: das Zielkundensegment — Branche oder "
              "Unternehmensgröße. Ein Ortsbezug wird ausdrücklich NICHT erwartet.",
        "K5": "Zusätzlich erkennbar: der Sortimentsbereich und die Versandbedingungen.",
    },
    # C2 — Primär-CTA: erwartete primäre Zielhandlung.
    "cv_cta": {
        "K1": "Anfrage, Rückruf, Termin vor Ort oder Notdienstnummer.",
        "K2": "Terminvereinbarung, Erstgespräch oder Rückruf.",
        "K3": "Reservierung, Tischbuchung, Anfahrt oder Anruf.",
        "K4": "Erstgespräch, Demo, Whitepaper oder Kontaktformular.",
        "K5": "In den Warenkorb oder Direktkauf.",
    },
    # C3 — Kontaktwege.
    "cv_kontakt": {
        "K1": "Telefonnummer klickbar, Formular mit höchstens fünf Feldern, "
              "Reaktionszeit benannt.",
        "K2": "Telefonnummer klickbar, Sprechzeiten oder Onlineterminbuchung.",
        "K3": "Telefonnummer klickbar, Öffnungszeiten strukturiert, Anfahrt oder Karte.",
        "K4": "Formular oder Terminbuchung, benannte Ansprechperson.",
        "K5": "Kundenservice-Kontakt, Bestell- und Retourenweg erkennbar.",
    },
    # C4 — Vertrauenssignale: mindestens zwei passende Signale der Klasse.
    # Erkennbare Bildagenturmotive zählen in keiner Klasse.
    "cv_vertrauen": {
        "K1": "Meisterbrief, Innung, Herstellerpartnerschaften, Bewertungen, "
              "echte Objektfotos, Gründungsjahr.",
        "K2": "Kammerzugehörigkeit, Fachkunde und Schwerpunkte, Team mit "
              "Qualifikation, Bewertungen soweit berufsrechtlich zulässig.",
        "K3": "Bewertungen, Auszeichnungen, Fotos der Räumlichkeiten, Mitgliedschaften.",
        "K4": "Benannte Referenzkunden, Fallstudien mit Zahlen, Zertifizierungen, Team.",
        "K5": "Käuferbewertungen, Gütesiegel, Zahlungsarten, sichtbare Rückgaberegelung.",
    },
    # C5 — Angebots-Klarheit: das Kriterium mit dem größten Klassenunterschied.
    "cv_angebot": {
        "K1": "Erwartet: Leistungen konkret benannt, Ablauf beschrieben, "
              "Preisrahmen oder Kostenlogik, Garantie oder Risk Reversal.",
        "K2": "Erwartet: Leistungsfelder konkret, Ablauf des Mandats oder der "
              "Behandlung, Erwartung an den Ersttermin. "
              "NICHT erwartet: Preisangaben — sie sind in diesen Berufen teils "
              "unzulässig. Ihr Fehlen darf keinen Punktabzug bewirken und "
              "gehört nicht in die Begründung.",
        "K3": "Erwartet: Sortiment oder Karte einsehbar, Preise, Öffnungszeiten. "
              "NICHT erwartet: eine Ablaufbeschreibung.",
        "K4": "Erwartet: Leistungsmodule, Vorgehensmodell, Projektgrößen oder "
              "Investitionsrahmen. NICHT erwartet: ein Ortsbezug.",
        "K5": "Erwartet: vollständige Produktangaben, Gesamtpreis inklusive "
              "Umsatzsteuer, Versandkosten, Lieferzeit.",
    },
    # E1 — Title & Meta.
    "se_meta": {
        "K1": "Im Title erwartet: Leistung und Ort.",
        "K2": "Im Title erwartet: Leistung und Ort.",
        "K3": "Im Title erwartet: Leistung und Ort.",
        "K4": "Im Title erwartet: Leistung und Zielsegment. Ein Ort wird NICHT erwartet.",
        "K5": "Im Title erwartet: Sortiment oder Marke. Ein Ort wird NICHT erwartet.",
    },
    # E4 — Strukturierte Daten: erwarteter Haupttyp.
    "se_schema": {
        "K1": "LocalBusiness oder ein spezifischer Untertyp, dazu Service und FAQPage.",
        "K2": "LocalBusiness, MedicalBusiness oder LegalService, dazu Person "
              "für die Berufsträger.",
        "K3": "Restaurant, Store oder LodgingBusiness, dazu "
              "OpeningHoursSpecification und Menu.",
        "K4": "Organization, dazu Service und Article.",
        "K5": "Organization mit Product und Offer, dazu AggregateRating.",
        "K6": "Organization oder Person.",
    },
    # I1 — Eigene Leistungsseiten.
    "ih_leistungsseiten": {
        "K1": "Je Gewerk oder Hauptleistung eine eigene Seite statt einer Sammelseite.",
        "K2": "Je Rechtsgebiet, Fachgebiet oder Behandlungsschwerpunkt eine Seite.",
        "K3": "Sortiment, Speisekarte oder Leistungsübersicht als eigene Seite.",
        "K4": "Je Leistungsmodul eine Seite, zusätzlich Fallstudien.",
        "K5": "Kategorieseiten mit eigenem Text, nicht nur Produktlisten.",
    },
}


def massstab_fuer(kriterium: str, klasse: str) -> str:
    """Der Maßstab eines Kriteriums in dieser Klasse — leer, wenn keiner gilt."""
    return PROFILE.get(kriterium, {}).get(klasse or "", "")


def rubric_fuer_prompt(klasse: str) -> str:
    """Der klassenabhängige Maßstab, wie ihn das Modell zu sehen bekommt.

    Leer bei K6 und bei unbekannten Klassen: Dort gilt keines der
    angebotsbezogenen Kriterien, und ein leerer Abschnitt ist ehrlicher als
    ein fremder Maßstab.
    """
    beschreibung = KLASSEN.get(klasse)
    zeilen = [
        f"- **{k}**: {massstab_fuer(k, klasse)}"
        for k in KI_KRITERIEN_MIT_PROFIL
        if massstab_fuer(k, klasse)
    ]
    if not zeilen or beschreibung is None:
        return ""

    return (f"MASZSTAB DIESER BRANCHENKLASSE — {klasse}, "
            f"{beschreibung.bezeichnung} ({beschreibung.merkmal}):\n"
            + "\n".join(zeilen))
