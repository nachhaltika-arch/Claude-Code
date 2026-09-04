"""Der Kriterienkatalog — 103 Punkte, der Inhalt des Massstabs.

Am 2026-08-30 aus `audit_criteria.py` herausgeloest (L-25). Hier steht, **was**
geprueft wird; in `audit_kriterium.py` steht, woraus ein Kriterium besteht, und
in `audit_criteria.py`, wie daraus eine Note wird.

**Diese Datei ist eine Liste, kein Modul mit Logik** — dieselbe Einordnung wie
`templates_zusatz.js` im Frontend. Sie ist gross, weil der Massstab 103 Punkte
hat, und nicht, weil sie schlecht gegliedert waere. Wer sie weiter zerlegt,
zerlegt den Massstab.

**Wahrheitsquelle.** Bis 2026-08-11 stand die Kriterienliste dreifach im Code:
im KI-Prompt, in der Fallback-Bewertung und im Frontend. Die drei Listen sind
auseinandergelaufen. Sie steht seither einmal — jetzt hier.
"""
from typing import Tuple

from services.audit_kriterium import Abstufung, Category, Criterion, Source, Stufe

# ═══════════════════════════════════════════════════════════════════
# Katalog
# ═══════════════════════════════════════════════════════════════════
#
# **Jeder `hint` sagt, was tatsächlich geprüft wird — nicht mehr (S3).**
#
# Am 24.08.2026 versprachen zwölf Hinweise Prüfungen, die die Bewertung nicht
# durchführt. Der Hinweis erscheint im Kundenbericht; wer dort „Tap-Targets
# groß genug" liest und dafür einen Punkt verliert, sucht an der falschen
# Stelle. Gekürzt wurde, was nicht eingelöst wird:
#
#   rc_formular_dsgvo  der Link zur Datenschutzerklärung wird nicht geprüft
#   si_ssl             Domain-Übereinstimmung fließt in `valid` ein
#   si_drittanbieter   Karten werden nicht geprüft
#   tp_bilder          Dateigröße und Größenangaben sind **eine** Prüfung
#   bf_alt             geprüft wird das Vorhandensein, nicht die Güte
#   se_index           noindex hängt an der robots.txt, keine eigene Prüfung
#   se_schema          es genügt **ein** passender Zusatztyp
#   se_lokal           von den NAP-Angaben nur die Telefonnummer
#   dg_mobil           Tap-Targets werden nicht geprüft
#   ih_aktualitaet     `und` → `oder`; das Kriterium ist milder als beschrieben
#   cv_cta             gezählt wird die Anzahl, nicht die Formulierung
#   ih_textqualitaet   „Worthülsen" gestrichen — `audit_ai.py:72` untersagt dem
#                      Modell genau dieses Wort in der Ausgabe. Ein Hinweis,
#                      der es führt, verlangt, was der Prompt verbietet.
#
# **Keine Punktänderung.** Gekürzt wurde die Beschreibung, nicht der Maßstab;
# die Katalogsumme bleibt 103 (Entscheidung aus C4, Szenario B).

CATALOGUE: Tuple[Category, ...] = (
    Category(
        key="recht_compliance",
        label="Recht & Compliance",
        buch_label="Recht und Compliance",
        buch_kapitel=5,
        criteria=(
            Criterion("rc_impressum", "Impressum (§ 5 DDG)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtangaben vollständig", buch_code="L1", buch_label="Impressum",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(3, None, "Die Impressumsseite ist erreichbar"),
                          Stufe(3, None, "Die geprüften Pflichtangaben sind vollständig — zählt nur, wenn die Seite erreichbar ist"),
                      ))),
            Criterion("rc_datenschutz", "Datenschutzerklärung (DSGVO)", 6, Source.MEASURED,
                      "Unterseite erreichbar und Pflichtinhalte vorhanden", buch_code="L2", buch_label="Datenschutzerklärung",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(3, None, "Die Datenschutzerklärung ist erreichbar"),
                          Stufe(3, None, "Die geprüften Pflichtinhalte sind vorhanden — zählt nur, wenn die Seite erreichbar ist"),
                      ))),
            # **Zwei Erhebungsarten (S2.2).** Gemessen, wenn ein
            # Consent-Werkzeug erkannt wird; abgeleitet, wenn aus „keine
            # einwilligungspflichtigen Dienste" auf „kein Banner noetig"
            # geschlossen wird. Beides kommt vor, beides gehoert deklariert.
            Criterion("rc_cookie", "Cookie-Consent (TDDDG)", 4, Source.MEASURED,
                      "Consent-Tool erkannt, nicht bloß das Wort 'Cookie' — "
                      "oder kein einwilligungspflichtiger Dienst vorhanden",
                      alt_source=Source.DERIVED, buch_code="L3", buch_label="Einwilligung für Cookies und Tracking",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(4, None, "Ein Einwilligungswerkzeug ist erkannt — oder es ist kein einwilligungspflichtiger Dienst eingebunden"),
                          Stufe(0, None, "Einwilligungspflichtige Dienste laden, ohne dass ein Einwilligungswerkzeug erkannt wurde"),
                      ))),
            Criterion("rc_bfsg", "Barrierefreiheitserklärung (BFSG)", 2, Source.MEASURED,
                      "Erklärung zur Barrierefreiheit verlinkt", buch_code="L4", buch_label="Barrierefreiheitserklärung",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(2, None, "Eine Erklärung zur Barrierefreiheit ist verlinkt"),
                          Stufe(0, None, "Es ist keine Erklärung zur Barrierefreiheit verlinkt"),
                      ))),
            Criterion("rc_formular_dsgvo", "Formular DSGVO-konform", 2, Source.MEASURED,
                      "Einwilligungs-Checkbox am Formular", buch_code="L5", buch_label="Kontaktformular",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(2, None, "Jedes gefundene Formular hat ein Einwilligungsfeld"),
                          Stufe(1, None, "Mindestens ein Formular hat ein Einwilligungsfeld, aber nicht jedes"),
                          Stufe(0, None, "Kein Formular hat ein Einwilligungsfeld"),
                      ))),
        ),
    ),
    Category(
        key="sicherheit",
        label="Sicherheit & Datenschutz",
        buch_label="Sicherheit und Datenschutz",
        buch_kapitel=6,
        criteria=(
            Criterion("si_ssl", "TLS-Zertifikat gültig", 3, Source.MEASURED,
                      "echter Handshake und gültiges Zertifikat, Abzug bei baldigem Ablauf", buch_code="S1", buch_label="Verschlüsselungszertifikat",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(3, None, "Das Zertifikat ist gültig und hat eine Restlaufzeit von 30 Tagen oder mehr"),
                          Stufe(2, None, "Das Zertifikat ist gültig, die Restlaufzeit liegt aber unter 30 Tagen"),
                          Stufe(0, None, "Es gibt kein gültiges Zertifikat"),
                      ))),
            Criterion("si_redirect", "HTTP→HTTPS erzwungen", 2, Source.MEASURED,
                      "Redirect-Test auf der http-Variante", buch_code="S2", buch_label="Erzwungene Weiterleitung auf HTTPS",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(2, None, "Der Aufruf über http wird auf https weitergeleitet"),
                          Stufe(0, None, "Der Aufruf über http wird nicht weitergeleitet"),
                      ))),
            Criterion("si_header", "Security-Header", 3, Source.MEASURED,
                      "HSTS, CSP, X-Frame-Options, X-Content-Type-Options", buch_code="S3", buch_label="Sicherheitsheader",
                      abstufung=Abstufung("ANTEIL")),
            Criterion("si_drittanbieter", "Drittanbieter ohne Einwilligung", 2, Source.MEASURED,
                      "externe Fonts, Tracking vor dem Consent", buch_code="S4", buch_label="Fremde Dienste ohne Einwilligung",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Es sind keine Schriften von fremden Servern eingebunden"),
                          Stufe(1, None, "Es läuft kein Trackingdienst ohne erkanntes Consent-Werkzeug"),
                      ))),
        ),
    ),
    Category(
        key="performance",
        label="Performance & Core Web Vitals",
        buch_label="Ladezeit und Stabilität",
        buch_kapitel=7,
        criteria=(
            Criterion("tp_lcp", "LCP (Ladezeit Hauptinhalt)", 4, Source.MEASURED,
                      "PageSpeed Insights", buch_code="P1", buch_label="Ladezeit des Hauptinhalts",
                      abstufung=Abstufung("SCHWELLE", "bis", (
                          Stufe(4, 2.5, "Der Hauptinhalt steht in weniger als 2,5 Sekunden"),
                          Stufe(2, 4.0, "Der Hauptinhalt steht in 2,5 bis unter 4,0 Sekunden"),
                          Stufe(0, None, "Der Hauptinhalt braucht 4,0 Sekunden oder länger"),
                      ))),
            Criterion("tp_cls", "CLS (Layout-Stabilität)", 3, Source.MEASURED,
                      "PageSpeed Insights", buch_code="P2", buch_label="Layoutstabilität",
                      abstufung=Abstufung("SCHWELLE", "bis", (
                          Stufe(3, 0.1, "Der Layoutverschiebungswert liegt unter 0,1"),
                          Stufe(1, 0.25, "Der Layoutverschiebungswert liegt bei 0,1 bis unter 0,25"),
                          Stufe(0, None, "Der Layoutverschiebungswert liegt bei 0,25 oder darüber"),
                      ))),
            Criterion("tp_inp", "INP (Interaktionszeit)", 2, Source.MEASURED,
                      "CrUX-Felddaten — im Labor nicht messbar", buch_code="P3", buch_label="Reaktionszeit auf Eingaben",
                      abstufung=Abstufung("SCHWELLE", "bis", (
                          Stufe(2, 200, "Die Reaktionszeit liegt unter 200 Millisekunden"),
                          Stufe(1, 500, "Die Reaktionszeit liegt bei 200 bis unter 500 Millisekunden"),
                          Stufe(0, None, "Die Reaktionszeit liegt bei 500 Millisekunden oder darüber"),
                      ))),
            Criterion("tp_mobile", "Mobile-Performance", 3, Source.MEASURED,
                      "eigener PageSpeed-Lauf mit Strategie 'mobile'", buch_code="P4", buch_label="Mobiler Gesamtwert",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(3, 90, "Mobiler Gesamtwert 90 oder höher"),
                          Stufe(2, 70, "Mobiler Gesamtwert 70 bis 89"),
                          Stufe(1, 50, "Mobiler Gesamtwert 50 bis 69"),
                          Stufe(0, None, "Mobiler Gesamtwert unter 50"),
                      ))),
            Criterion("tp_bilder", "Bildoptimierung", 3, Source.MEASURED,
                      "modernes Format, lazy loading, Größenangaben ohne überdimensionierte Bilder", buch_code="P5", buch_label="Bildoptimierung",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Mindestens die Hälfte der Bilder liegt in einem modernen Format vor"),
                          Stufe(1, None, "Mindestens die Hälfte der Bilder wird verzögert geladen"),
                          Stufe(1, None, "Mindestens vier Fünftel der Bilder tragen Größenangaben, und kein Bild ist überdimensioniert"),
                      ))),
        ),
    ),
    Category(
        key="barrierefreiheit",
        label="Barrierefreiheit (WCAG/BFSG)",
        buch_label="Barrierefreiheit",
        buch_kapitel=8,
        criteria=(
            Criterion("bf_lighthouse", "Lighthouse-Accessibility-Score", 3, Source.MEASURED,
                      "Gesamtwert der Lighthouse-Barrierefreiheitsprüfung", buch_code="B1", buch_label="Gesamtwert der Barrierefreiheitsprüfung",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(3, 90, "Der Barrierefreiheitswert liegt bei 90 oder höher"),
                          Stufe(2, 75, "Der Barrierefreiheitswert liegt bei 75 bis 89"),
                          Stufe(1, 50, "Der Barrierefreiheitswert liegt bei 50 bis 74"),
                          Stufe(0, None, "Der Barrierefreiheitswert liegt unter 50"),
                      ))),
            Criterion("bf_kontrast", "Farbkontraste (WCAG AA)", 2, Source.MEASURED,
                      "Lighthouse-Audit 'color-contrast'", buch_code="B2", buch_label="Farbkontraste",
                      abstufung=Abstufung("ANTEIL")),
            Criterion("bf_alt", "Alt-Texte der Inhaltsbilder", 2, Source.MEASURED,
                      "Anteil der Inhaltsbilder mit Alt-Text — dekorative Bilder und Zählpixel zählen nicht", buch_code="B3", buch_label="Alternativtexte für Bilder",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(2, 95, "Mindestens 95 von 100 Inhaltsbildern haben einen Alternativtext"),
                          Stufe(1, 80, "80 bis unter 95 von 100 Inhaltsbildern haben einen Alternativtext"),
                          Stufe(0, None, "Weniger als 80 von 100 Inhaltsbildern haben einen Alternativtext"),
                      ))),
            # **Gemessen, nicht abgeleitet (S2.1).** Der Katalog fuehrte
            # `DERIVED`, waehrend die Bewertung `MEASURED` schrieb. Seit dem
            # Anschluss der Lighthouse-Gruppe (S1.1) ist es zweifelsfrei
            # gemessen: DOM-Hierarchie plus `html-has-lang` und `label`.
            Criterion("bf_semantik", "Semantik & Struktur", 2, Source.MEASURED,
                      "saubere Überschriftenhierarchie, lang-Attribut, Labels", buch_code="B4", buch_label="Semantik und Struktur",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Genau eine Hauptüberschrift und eine Hierarchie ohne Sprünge"),
                          Stufe(1, None, "Sprachauszeichnung und Formularbeschriftungen sind vollständig"),
                      ))),
            Criterion("bf_tastatur", "Tastaturbedienung", 1, Source.DERIVED,
                      "Skip-Link, Fokus-Reihenfolge, keine Tastaturfallen", buch_code="B5", buch_label="Tastaturbedienung",
                      abstufung=Abstufung("ANTEIL")),
        ),
    ),
    Category(
        key="seo",
        label="SEO & Auffindbarkeit",
        buch_label="Auffindbarkeit",
        buch_kapitel=9,
        criteria=(
            Criterion("se_meta", "Title & Meta-Description", 3, Source.MEASURED,
                      "vorhanden, sinnvolle Länge, Ort und Leistung enthalten", buch_code="E1", buch_label="Seitentitel und Kurzbeschreibung",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Ein Seitentitel ist vorhanden und hat eine sinnvolle Länge"),
                          Stufe(1, None, "Eine Kurzbeschreibung ist vorhanden und hat eine sinnvolle Länge"),
                          Stufe(1, None, "Der Titel trägt, was die Branchenklasse erwartet — den Ort, sonst die Leistung"),
                      ))),
            Criterion("se_struktur", "Überschriften & Content-Tiefe", 2, Source.MEASURED,
                      "H2-Gliederung und ausreichender Textumfang", buch_code="E2", buch_label="Überschriften und Textumfang",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Genau eine Hauptüberschrift und mindestens eine Zwischenüberschrift"),
                          Stufe(1, None, "Mindestens 300 Wörter Text"),
                      ))),
            Criterion("se_index", "Indexierbarkeit", 3, Source.MEASURED,
                      "robots.txt ohne Aussperrung, sitemap.xml, Canonical", buch_code="E3", buch_label="Auffindbarkeit für Suchmaschinen",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Eine robots.txt ist vorhanden und sperrt die Seite nicht aus"),
                          Stufe(1, None, "Eine sitemap.xml ist vorhanden"),
                          Stufe(1, None, "Eine Canonical-Angabe ist gesetzt"),
                      ))),
            Criterion("se_schema", "Strukturierte Daten", 3, Source.MEASURED,
                      "JSON-LD vorhanden, passender Haupttyp, ein passender Zusatztyp", buch_code="E4", buch_label="Strukturierte Daten",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Strukturierte Daten sind überhaupt vorhanden"),
                          Stufe(1, None, "Der Haupttyp passt zur Branchenklasse"),
                          Stufe(1, None, "Mindestens ein passender Zusatztyp ist vorhanden"),
                      ))),
            Criterion("se_lokal", "Lokale Signale", 3, Source.MEASURED,
                      "Ort in Title oder H1, Telefonnummer als Link, Karte oder LocalBusiness",
                      assumes_local=True, buch_code="E5", buch_label="Lokale Signale",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Der Ort steht im Seitentitel oder in der Hauptüberschrift"),
                          Stufe(1, None, "Die Telefonnummer ist als Link hinterlegt"),
                          Stufe(1, None, "Eine Karte oder eine Betriebsauszeichnung ist vorhanden"),
                      ))),
            Criterion("se_links", "Keine defekten Links", 1, Source.MEASURED,
                      "Linkprüfung über die Startseite", buch_code="E6", buch_label="Keine defekten Verweise",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(1, None, "Kein Verweis der geprüften Seite läuft ins Leere"),
                          Stufe(0, None, "Mindestens ein Verweis läuft ins Leere"),
                      ))),
            # L-58 (a), 2026-08-21. Der Katalog hatte kein einziges Kriterium
            # für KI — kein Treffer auf ChatGPT, Perplexity oder AEO —,
            # während `audit_runner.audit_facts` die Werte seit dem 16.08.
            # bereits erhebt und das PDF sie druckt. Bewertet hat sie niemand.
            #
            # Der Name sagt **Lesbarkeit**, nicht Sichtbarkeit: Gemessen wird,
            # ob eine Maschine den Betrieb lesen *kann*. Ob sie ihn auf eine
            # Frage hin *nennt*, misst hier nichts — das ist L-58 (b), kostet
            # je Lauf Geld und ist ein eigenes Produkt.
            Criterion("se_ki_lesbar", "Lesbarkeit für KI-Systeme", 3, Source.MEASURED,
                      "KI-Crawler in robots.txt nicht ausgesperrt, llms.txt vorhanden", buch_code="E7", buch_label="Lesbarkeit für KI-Systeme",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(2, None, "Kein KI-Crawler ist in der robots.txt ausgesperrt"),
                          Stufe(1, None, "Eine llms.txt ist vorhanden"),
                      ))),
        ),
    ),
    Category(
        key="design",
        label="Design & Gestaltung",
        buch_label="Gestaltung",
        buch_kapitel=10,
        criteria=(
            Criterion("dg_aktualitaet", "Visuelle Aktualität", 3, Source.AI,
                      "Wirkt das Layout zeitgemäß oder veraltet?", buch_code="D1", buch_label="Visuelle Aktualität",
                      rubric="""3 = kein Alterungsmerkmal erkennbar; die Seite koennte diesen Monat entstanden sein.
2 = ein oder zwei Merkmale, sonst zeitgemaess.
1 = drei bis vier Merkmale; der Eindruck kippt.
0 = fuenf oder mehr, oder ein einzelnes so deutlich, dass es alles ueberlagert.
Die sechs Merkmale: feste Breite mit breiten leeren Raendern · kleine Schrift im
Fliesstext · Verlaeufe, Schlagschatten, Spiegelungen · Bildergalerien mit Rahmen
und Blaetterpfeilen · sichtbar veraltete Jahreszahl · gedraengte Anordnung ohne
Weissraum.
Nicht Teil dieses Kriteriums: die Aktualitaet der *Inhalte* (das ist I2) und die
Schriftgroesse als Messwert (das ist D2, gemessen).""",
                      abstufung=Abstufung("KI")),
            # **Gemessen statt geschätzt seit dem 24.08.2026 (S1.2).**
            # Lighthouse liefert `font-size` — die Schriftgröße wurde also
            # gemessen, während dieses Kriterium sie von einem Sprachmodell
            # schätzen ließ. Der Hinweis ist auf das gekürzt, was tatsächlich
            # geprüft wird; „Zeilenlänge" und „klare Hierarchie" versprachen
            # mehr, als eingelöst wurde (dieselbe Regel wie in S3).
            Criterion("dg_typografie", "Typografie & Lesbarkeit", 2, Source.MEASURED,
                      "Lighthouse-Audit 'font-size': lesbare Schriftgröße auf Mobilgeräten", buch_code="D2", buch_label="Typografie und Lesbarkeit",
                      abstufung=Abstufung("ANTEIL")),
            Criterion("dg_farbsystem", "Farbsystem & Konsistenz", 2, Source.AI,
                      "begrenzte Palette, erkennbare CI, ausreichender Kontrast", buch_code="D3", buch_label="Farbsystem und Konsistenz",
                      rubric="""2 = hoechstens drei tragende Farben, ueber alle Seiten gleich eingesetzt,
    erkennbare Betriebsfarbe.
1 = ein System ist erkennbar, wird aber nicht durchgehalten — abweichende
    Schaltflaechenfarben, wechselnde Flaechen.
0 = kein erkennbares System; Farben wirken einzeln gewaehlt.
Nicht Teil dieses Kriteriums: der Kontrastwert. Den misst B2 mit dem
Pruefwerkzeug.
Bewerte hier die Konsistenz, nicht die Lesbarkeit — auch dann nicht, wenn dir
ein Paar zu blass erscheint.""",
                      abstufung=Abstufung("KI")),
            Criterion("dg_bildqualitaet", "Bildqualität & Authentizität", 2, Source.AI,
                      "echte Betriebsfotos statt generischem Stockmaterial", buch_code="D4", buch_label="Bildqualität und Echtheit",
                      rubric="""2 = erkennbar eigene Aufnahmen: eigene Leute, eigene Fahrzeuge, eigene
    Baustellen, eigene Raeume.
1 = gemischt — eigene Bilder neben deutlich gekauften.
0 = durchgehend generisches Material, oder gar keine Bilder.
Anzeichen fuer gekauftes Material: freigestellte laechelnde Personen vor
weissem Grund, Werkzeug ohne Gebrauchsspuren, Innenraeume ohne jeden Bezug zum
Gewerk, dieselbe Person in mehreren Rollen.
Nicht Teil dieses Kriteriums: Dateigroesse, Format und Ladeverhalten. Das ist
P5 und wird gemessen.""",
                      abstufung=Abstufung("KI")),
            Criterion("dg_mobil", "Mobile Darstellung", 1, Source.MEASURED,
                      "Viewport-Angabe im Kopf der Seite", buch_code="D5", buch_label="Mobile Darstellung",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(1, None, "Die Darstellungsanweisung für mobile Geräte steht im Kopf der Seite"),
                          Stufe(0, None, "Es steht keine Darstellungsanweisung für mobile Geräte im Kopf der Seite"),
                      ))),
        ),
    ),
    Category(
        key="conversion",
        label="Conversion & Nutzerführung",
        buch_label="Nutzerführung und Anfragen",
        buch_kapitel=11,
        criteria=(
            Criterion("cv_klarheit", "Klarheit above the fold", 3, Source.AI,
                      "Was, für wen, in welchem Gebiet — in fünf Sekunden erfassbar",
                      assumes_business=True, buch_code="C1", buch_label="Klarheit im ersten Bildschirmausschnitt",
                      rubric="""3 = Leistung, Zielgruppe und — wo die Klasse es erwartet — das Gebiet stehen
    im ersten Bildschirmausschnitt und sind in fuenf Sekunden erfasst.
2 = zwei der drei Angaben stehen da, die dritte muss man suchen.
1 = nur eine Angabe, oder alle drei erst nach Scrollen.
0 = der erste Ausschnitt sagt nicht, worum es geht.
Massstab ist die Klasse: Ein ueberregionaler Anbieter (K4) braucht kein Gebiet,
ein Publikumsbetrieb (K3) dafuer Oeffnungszeiten oder Standort.
Nicht Teil dieses Kriteriums: ob ein Handlungsaufruf vorhanden ist (C2) und ob
das Angebot inhaltlich klar ist (C5).""",
                      abstufung=Abstufung("KI")),
            Criterion("cv_cta", "Primär-CTA", 3, Source.DERIVED,
                      "mindestens ein Handlungsaufruf, ab drei die volle Punktzahl",
                      assumes_business=True, buch_code="C2", buch_label="Die erwartete Hauptreaktion",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(3, 3, "Drei oder mehr Handlungsangebote, die in dieser Branchenklasse zählen"),
                          Stufe(2, 1, "Ein oder zwei solche Handlungsangebote"),
                          Stufe(0, None, "Kein Handlungsangebot"),
                      ))),
            Criterion("cv_kontakt", "Kontaktwege", 3, Source.MEASURED,
                      "Telefon klickbar, Formular schlank, Reaktionszeit benannt",
                      assumes_business=True, buch_code="C3", buch_label="Kontaktwege",
                      abstufung=Abstufung("SUMME", "ab", (
                          Stufe(1, None, "Das erste der drei Kontaktmerkmale dieser Branchenklasse ist erfüllt"),
                          Stufe(1, None, "Das zweite Kontaktmerkmal ist erfüllt"),
                          Stufe(1, None, "Das dritte Kontaktmerkmal ist erfüllt"),
                      ))),
            Criterion("cv_vertrauen", "Vertrauenssignale", 3, Source.DERIVED,
                      "Bewertungen, Referenzen, Qualifikations- und "
                      "Zugehörigkeitsnachweise",
                      assumes_business=True, buch_code="C4", buch_label="Vertrauenssignale",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(3, 4, "Vier oder mehr Vertrauenssignale, die in dieser Branchenklasse zählen"),
                          Stufe(2, 2, "Zwei oder drei solche Vertrauenssignale"),
                          Stufe(1, 1, "Ein Vertrauenssignal"),
                          Stufe(0, None, "Kein Vertrauenssignal"),
                      ))),
            Criterion("cv_angebot", "Angebots-Klarheit", 3, Source.AI,
                      "Leistungen konkret, Ablauf oder Preisrahmen, Risk Reversal",
                      assumes_business=True, buch_code="C5", buch_label="Klarheit des Angebots",
                      rubric="""3 = die Leistungen sind einzeln benannt, der Ablauf oder ein Preisrahmen steht
    da, und es gibt eine Zusage, die das Risiko des Kunden senkt
    (Festpreis, Garantie, kostenlose Erstbewertung).
2 = zwei der drei Teile.
1 = nur die Leistungen, ohne Ablauf, Preis oder Zusage.
0 = die Leistungen bleiben allgemein („alles rund ums Bad").
Bei Beratungs- und Gesundheitsberufen (K2) ist die fehlende Preisangabe **kein**
Mangel — dort zaehlen Ablauf und Zusage. Ziehe dafuer keinen Punkt ab.
Nicht Teil dieses Kriteriums: eigene Leistungsseiten (I1) und die
Textqualitaet (I3).""",
                      abstufung=Abstufung("KI")),
        ),
    ),
    Category(
        key="inhalt",
        label="Inhalt & Substanz",
        buch_label="Inhalt und Substanz",
        buch_kapitel=12,
        criteria=(
            Criterion("ih_leistungsseiten", "Eigene Leistungsseiten", 2, Source.MEASURED,
                      "je Hauptleistung eine Seite statt einer Sammelseite",
                      assumes_business=True, buch_code="I1", buch_label="Eigene Leistungsseiten",
                      abstufung=Abstufung("SCHWELLE", "ab", (
                          Stufe(2, 3, "Drei oder mehr eigene Leistungsseiten, die in dieser Branchenklasse zählen"),
                          Stufe(1, 1, "Eine oder zwei solche Leistungsseiten"),
                          Stufe(0, None, "Keine eigene Leistungsseite"),
                      ))),
            Criterion("ih_aktualitaet", "Aktualität", 1, Source.MEASURED,
                      "datierte Inhalte oder aktuelles Copyright", buch_code="I2", buch_label="Aktualität",
                      abstufung=Abstufung("JA_NEIN", "ab", (
                          Stufe(1, None, "Das Copyright trägt das laufende Jahr, oder es gibt datierte Inhalte"),
                          Stufe(0, None, "Weder aktuelles Copyright noch datierte Inhalte"),
                      ))),
            Criterion("ih_textqualitaet", "Textqualität", 2, Source.AI,
                      "Kundennutzen statt Selbstbeschreibung",
                      assumes_business=True, buch_code="I3", buch_label="Textqualität",
                      rubric="""2 = die Texte gehen vom Anliegen des Kunden aus, nennen Konkretes (Orte,
    Fristen, Ablaeufe, Zahlen) und sind ohne Fachjargon verstaendlich.
1 = teils kundenorientiert, teils Selbstbeschreibung; wenig Konkretes.
0 = durchgehend ueber den Betrieb statt ueber das Anliegen, austauschbar
    formuliert.
Nicht Teil dieses Kriteriums: Textlaenge und Ueberschriftenstruktur (E2,
gemessen) und die Aktualitaet der Inhalte (I2).
Zum Ton: Beschreibe, was fehlt. Abwertende Urteile ueber Texte sind untersagt —
siehe den Abschnitt TON DER TEXTE.""",
                      abstufung=Abstufung("KI")),
        ),
    ),
)


# Infrastruktur — reine Information für die Angebotskalkulation, kein Score.
# 'ho_backup' ist entfallen: von außen prinzipiell nicht prüfbar.
INFRASTRUCTURE: Tuple[Criterion, ...] = (
    Criterion("ho_anbieter", "Hosting-Anbieter identifizierbar", 0, Source.MEASURED,
              "IP-/ASN-Lookup"),
    Criterion("ho_uptime", "Erreichbarkeit", 0, Source.MEASURED,
              "HTTP-Status der Startseite"),
    Criterion("ho_cdn", "CDN aktiv", 0, Source.MEASURED,
              "CDN-Signaturen in den Response-Headern"),
    Criterion("ho_cms", "CMS / Tech-Stack erkannt", 0, Source.MEASURED,
              "Technologie-Signaturen in HTML und Headern"),
)


LEVELS: Tuple[Tuple[int, str], ...] = (
    (95, "Homepage Standard Platin"),
    (85, "Homepage Standard Gold"),
    (70, "Homepage Standard Silber"),
    (50, "Homepage Standard Bronze"),
    (0, "Nicht konform"),
)

NON_COMPLIANT = "Nicht konform"
BRONZE = "Homepage Standard Bronze"


