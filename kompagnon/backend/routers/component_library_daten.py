"""Die Datenblöcke der Bausteinbibliothek (L-25).

**Warum eigene Datei, 22.08.2026.** In `routers/component_library.py` standen
398 Zeilen **reine Daten** zwischen den Routen: 289 davon allein
`_LAYOUT_PRESETS`, dazu der Branchenkatalog, die Elementbeschriftungen und
die Vertragsregeln fuer Wireframes.

Daten sind keine Logik. Sie in einer Routendatei zu halten heisst, beim Lesen
der Routen an ihnen vorbeizuscrollen — und beim Aendern der Daten eine Datei
anzufassen, in der Routen stehen. Beides ist vermeidbar.

Kein Verhalten aendert sich: Die Bloecke sind unveraendert uebernommen und
werden von `component_library.py` importiert.
"""

_LAYOUT_PRESETS = {
    # ── HERO / Header ───────────────────────────────────────────────────────
    "hero_centered": {
        "category": "HERO",
        "label":    "Hero · Zentriert",
        "guidance": "Zentrierter Hero — eine Spalte, max-w-3xl. Kicker (Eyebrow) ueber der Headline, Headline gross (text-4xl/5xl), Subtext mittig 1-2 Saetze, primaerer + sekundaerer CTA-Button nebeneinander. Kein Hero-Bild, viel Whitespace.",
    },
    "hero_split_image": {
        "category": "HERO",
        "label":    "Hero · Split (Bild rechts)",
        "guidance": "Zwei-Spalten-Layout 50/50 auf Desktop, gestapelt auf Mobile. Links: Headline + Subtext + 2 CTAs + 3 Bullet-Points. Rechts: Bild-Placeholder (aspect-video oder aspect-[4/3]).",
    },
    "hero_split_reverse": {
        "category": "HERO",
        "label":    "Hero · Split (Bild links)",
        "guidance": "Spiegelung von hero_split_image: Bild-Placeholder links, Text-Block rechts.",
    },
    "hero_with_form": {
        "category": "HERO",
        "label":    "Hero · mit Lead-Form",
        "guidance": "Zwei-Spalten-Layout. Links: Headline + Subtext + Trust-Bullets. Rechts: Karte mit Mini-Lead-Formular (Name, E-Mail, Telefon, Submit-Button). Form als Card mit border + shadow-sm.",
    },
    "hero_off_grid": {
        "category": "HERO",
        "label":    "Hero · Off-Grid",
        "guidance": "Asymmetrisches Layout: Text-Block links oben, ueberlappende Bild-Placeholder rechts mit leichtem Versatz (translate). Wirkt redaktionell. Nutze grid + col-span fuer den Versatz.",
    },
    "hero_grid_cards": {
        "category": "HERO",
        "label":    "Hero · mit Karten-Grid",
        "guidance": "Hero-Headline oben zentriert, darunter ein 3-Spalten-Grid mit Service-/Feature-Cards. Jede Card: Icon (SVG) + Titel + 1-Satz-Text. Karten sind die primaeren CTAs.",
    },
    "hero_minimal": {
        "category": "HERO",
        "label":    "Hero · Minimal",
        "guidance": "Kompakt fuer Sub-Pages: Breadcrumb + Headline + 1-Satz-Subtext. Padding sparsamer (py-12 statt py-24). Kein Bild, kein CTA.",
    },
    "hero_video": {
        "category": "HERO",
        "label":    "Hero · mit Video",
        "guidance": "Hero mit Video-Placeholder rechts (aspect-video, Play-Icon zentriert in einem dunklen Overlay-Div). Links: Text-Block wie bei split-image.",
    },

    # ── NAV / Navbar ─────────────────────────────────────────────────────────
    "nav_standard": {
        "category": "NAV",
        "label":    "Nav · Logo-Links",
        "guidance": "Klassisch: Logo links, Nav-Links zentriert, primaerer CTA-Button rechts. Mobile-Burger als alleiniges sichtbares Mobile-Element. Sticky-friendly mit border-bottom.",
    },
    "nav_centered_logo": {
        "category": "NAV",
        "label":    "Nav · Zentriertes Logo",
        "guidance": "Logo zentriert, je 2-3 Nav-Links links und rechts vom Logo. CTA als Button ganz rechts. Mobile: Logo bleibt zentriert, Burger links.",
    },
    "nav_minimal": {
        "category": "NAV",
        "label":    "Nav · Minimal",
        "guidance": "Nur Logo links + 1 primaerer CTA rechts. Keine Nav-Links. Fuer Landing-Pages mit klarer Single-Conversion.",
    },
    "nav_with_search": {
        "category": "NAV",
        "label":    "Nav · mit Suche",
        "guidance": "Logo links, Nav-Links + Such-Feld inline rechts daneben, CTA-Button rechts. Such-Feld mit Icon (lupe) als input.",
    },
    "nav_sidebar": {
        "category": "NAV",
        "label":    "Nav · Sidebar (vertikal)",
        "guidance": "Vertikale Sidebar-Nav: Logo oben, Nav-Links untereinander, CTA unten. Width fixed (w-60), full-height. Fuer App-Layouts.",
    },

    # ── LEIST / Feature-Sections ────────────────────────────────────────────
    "leist_split_left": {
        "category": "LEIST",
        "label":    "Leistung · Bild links + Text rechts",
        "guidance": "Zwei-Spalten 50/50: Bild-Placeholder links, rechts Headline + Subtext + Bullet-Liste mit Check-Icons (4-6 Punkte) + sekundaerer CTA.",
    },
    "leist_split_right": {
        "category": "LEIST",
        "label":    "Leistung · Bild rechts + Text links",
        "guidance": "Spiegelung von leist_split_left.",
    },
    "leist_3_col": {
        "category": "LEIST",
        "label":    "Leistung · 3-Spalten-Cards",
        "guidance": "Section-Headline zentriert. Darunter 3 Karten nebeneinander: jede Karte = Icon (SVG) + Titel + Beschreibung (2-3 Saetze) + 'Mehr erfahren'-Link. Mobile: gestapelt.",
    },
    "leist_4_col": {
        "category": "LEIST",
        "label":    "Leistung · 4-Spalten-Cards",
        "guidance": "Wie leist_3_col, aber 4 Karten nebeneinander. Mobile: 2x2 Grid, dann Single-Column.",
    },
    "leist_grid_cards_with_image": {
        "category": "LEIST",
        "label":    "Leistung · Grid mit Bild-Cards",
        "guidance": "3-Spalten-Grid, jede Karte hat oben einen Bild-Placeholder (aspect-video) und darunter Titel + Kurztext + Pfeil-Link.",
    },
    "leist_tabs": {
        "category": "LEIST",
        "label":    "Leistung · Tabs",
        "guidance": "Section mit Tab-Navigation oben (3-5 Tabs). Aktiver Tab unterstrichen. Darunter Tab-Inhalt (statisch im Wireframe — zeige nur den ersten Tab als ausgewaehlt). Tab-Inhalt: 50/50-Layout Text + Bild.",
    },
    "leist_overlapping": {
        "category": "LEIST",
        "label":    "Leistung · Overlapping Images",
        "guidance": "Zwei ueberlappende Bild-Placeholder (eines absolut positioniert, leicht versetzt). Rechts daneben Text-Block. Editorial-Look.",
    },
    "leist_alternating": {
        "category": "LEIST",
        "label":    "Leistung · Wechselnde Reihen",
        "guidance": "Drei aufeinanderfolgende Feature-Reihen: 1. Bild links/Text rechts, 2. Text links/Bild rechts, 3. Bild links/Text rechts. Jede Reihe hat eigene Headline + Subtext + Bullets.",
    },

    # ── TRUST / Social Proof ─────────────────────────────────────────────────
    "trust_testimonial_single": {
        "category": "TRUST",
        "label":    "Trust · Einzel-Testimonial",
        "guidance": "Eine grosse Testimonial-Karte zentriert. Zitat in serif-Font (text-2xl), darunter Avatar + Name + Position. Optional 5-Sterne-Rating ueber dem Zitat.",
    },
    "trust_testimonial_grid": {
        "category": "TRUST",
        "label":    "Trust · Testimonial-Grid (3)",
        "guidance": "Drei Testimonial-Karten nebeneinander. Jede: Zitat (kurz, 2-3 Saetze), Avatar, Name + Funktion, Sternchen-Rating.",
    },
    "trust_stats_row": {
        "category": "TRUST",
        "label":    "Trust · Zahlen-Reihe",
        "guidance": "4 Zahlen-Counter horizontal. Jede: grosse Zahl (text-5xl, fett), kurzes Label darunter (z.B. '500+ zufriedene Kunden'). Border zwischen Counters.",
    },
    "trust_logo_strip": {
        "category": "TRUST",
        "label":    "Trust · Logo-Streifen",
        "guidance": "Section mit kleiner Headline ('Wir arbeiten mit:'), darunter horizontale Reihe mit 6-8 Logo-Placeholdern (graue Rechtecke). Mobile: 2 Reihen a 3-4.",
    },
    "trust_team_grid": {
        "category": "TRUST",
        "label":    "Trust · Team-Grid",
        "guidance": "3-4 Team-Mitglieder als Karten: Avatar (rund) + Name + Position + 1-Satz-Bio. Optional Social-Links (Mail/LinkedIn) als Icons.",
    },
    "trust_fallstudien_3": {
        "category": "TRUST",
        "label":    "Trust · 3 Fallstudien",
        "guidance": "Drei Case-Study-Karten: jede mit Vorher/Nachher-Bild-Placeholder, Kunden-Name, kurzer Problem→Loesung-Text, Kennzahl als Highlight.",
    },
    "trust_comparison": {
        "category": "TRUST",
        "label":    "Trust · Vergleichstabelle",
        "guidance": "Tabelle mit 2-3 Spalten: 'Wir' vs 'Wettbewerb 1' vs 'Wettbewerb 2'. Zeilen sind Feature-Punkte mit Check/X-Icons.",
    },

    # ── SEO / Content ────────────────────────────────────────────────────────
    "seo_long_form": {
        "category": "SEO",
        "label":    "SEO · Lang-Text",
        "guidance": "Reine Text-Section, max-w-prose zentriert. H2-Headline, dann Paragraphen, H3-Subheadlines, mehr Paragraphen, Bullet-Liste, Inline-CTA-Box am Ende.",
    },
    "seo_with_toc": {
        "category": "SEO",
        "label":    "SEO · mit Inhaltsverzeichnis",
        "guidance": "Zwei-Spalten: links sticky Inhaltsverzeichnis (5-7 Anker-Links), rechts Long-Form-Content mit H2/H3-Struktur.",
    },
    "seo_blog_grid": {
        "category": "SEO",
        "label":    "SEO · Blog-Karten-Grid",
        "guidance": "Section-Headline + 3-Spalten-Grid mit Blog-Karten: Bild-Placeholder oben, Kategorie-Badge, Titel, Excerpt (2 Saetze), Datum + Autor.",
    },
    "seo_faq_simple": {
        "category": "SEO",
        "label":    "SEO · FAQ Akkordeon",
        "guidance": "Section-Headline zentriert. Darunter 8-10 FAQ-Items als statische Akkordeons (kein JS): Frage als button-styled-summary, Antwort darunter. Erstes Item geoeffnet.",
    },
    "seo_faq_categorized": {
        "category": "SEO",
        "label":    "SEO · FAQ kategorisiert",
        "guidance": "FAQ in 2-3 Spalten gruppiert nach Themen-Kategorien. Jede Spalte hat eigene Sub-Headline + 3-4 FAQ-Items.",
    },

    # ── CTA / Call-to-Action ─────────────────────────────────────────────────
    "cta_inline_strip": {
        "category": "CTA",
        "label":    "CTA · Inline-Streifen",
        "guidance": "Kompakter horizontaler Streifen: Headline links, primaerer Button rechts. Background gray-100, py-8.",
    },
    "cta_final_large": {
        "category": "CTA",
        "label":    "CTA · Grosse End-CTA",
        "guidance": "Volle Section py-20: zentrierte grosse Headline (text-4xl/5xl), 1-2 Saetze Subtext, zwei Buttons (primaer + sekundaer). Background bg-gray-900 mit text-white.",
    },
    "cta_urgency": {
        "category": "CTA",
        "label":    "CTA · Urgency / Stichtag",
        "guidance": "CTA mit prominentem Datum/Counter: 'Nur noch bis 31.12.' als Headline, Untertitel mit Foerder-Hinweis (z.B. BAFA), grosser CTA-Button.",
    },
    "cta_with_form": {
        "category": "CTA",
        "label":    "CTA · mit Mini-Formular",
        "guidance": "Headline + Subtext zentriert, darunter horizontales Mini-Formular: nur E-Mail-Feld + Submit-Button nebeneinander. Trust-Badges darunter klein.",
    },
    "cta_split_contact": {
        "category": "CTA",
        "label":    "CTA · Split (Form + Kontakt-Daten)",
        "guidance": "Zwei-Spalten: links Kontakt-Formular (4-5 Felder), rechts Kontakt-Daten (Adresse, Telefon, E-Mail) + Map-Placeholder.",
    },

    # ── HW / Hardware / Pricing ──────────────────────────────────────────────
    "hw_pricing_3_tier": {
        "category": "HW",
        "label":    "HW · 3-Pakete-Pricing",
        "guidance": "Drei Pricing-Karten nebeneinander. Mittlere ist hervorgehoben (border-2, shadow). Jede Karte: Paket-Name, Preis (gross), Feature-Liste mit Check-Icons (5-7 Items), CTA-Button.",
    },
    "hw_pricing_comparison": {
        "category": "HW",
        "label":    "HW · Pricing-Vergleichstabelle",
        "guidance": "Tabelle mit 3 Tier-Spalten + Feature-Zeilen. Erste Zeile zeigt Tier-Namen + Preise. Folgezeilen: Feature-Name + Check/X-Icons pro Tier.",
    },
    "hw_product_grid": {
        "category": "HW",
        "label":    "HW · Produkt-Grid",
        "guidance": "3-Spalten-Grid mit Produkt-Karten: Bild-Placeholder, Produkt-Name, Kurz-Spec, Preis, CTA-Button.",
    },
    "hw_product_detail": {
        "category": "HW",
        "label":    "HW · Produkt-Detail",
        "guidance": "Zwei-Spalten: links Produkt-Bild gross, rechts Produkt-Name + Preis + Feature-Liste + CTA-Button + Spec-Tabelle.",
    },

    # ── FOOT / Footer ────────────────────────────────────────────────────────
    "foot_4_col": {
        "category": "FOOT",
        "label":    "Footer · 4-Spalten",
        "guidance": "Klassischer Footer: Spalte 1 Logo + Tagline, Spalten 2-4 mit Link-Listen (Sitemap / Service / Rechtliches). Bottom-Bar mit Copyright + Social-Icons.",
    },
    "foot_compact": {
        "category": "FOOT",
        "label":    "Footer · Kompakt",
        "guidance": "Schmaler Footer: nur eine Reihe mit Logo links, ein paar wichtige Links zentriert, Social-Icons rechts. py-6.",
    },
    "foot_with_newsletter": {
        "category": "FOOT",
        "label":    "Footer · mit Newsletter",
        "guidance": "Top-Section: Newsletter-Anmeldung (Headline + E-Mail-Input + Submit). Bottom-Section: 4-Spalten-Layout wie foot_4_col.",
    },
    "foot_with_map": {
        "category": "FOOT",
        "label":    "Footer · mit Mini-Map",
        "guidance": "Zwei-Bereiche: oben links Map-Placeholder + Adresse, oben rechts Link-Liste. Bottom-Bar mit Copyright.",
    },

    # ── CUSTOM / Misc ────────────────────────────────────────────────────────
    "custom_banner_top": {
        "category": "CUSTOM",
        "label":    "Banner · Top-Streifen",
        "guidance": "Schmaler Banner ueber Nav: Text + Inline-CTA-Link, Schliessen-X rechts. Background bg-gray-900 text-white. py-2.",
    },
    "custom_cookie_consent": {
        "category": "CUSTOM",
        "label":    "Cookie-Consent",
        "guidance": "Sticky-Bottom-Card: Text-Block + 3 Buttons (Akzeptieren / Ablehnen / Einstellungen). Mit shadow-lg, border, rounded.",
    },
    "custom_breadcrumb": {
        "category": "CUSTOM",
        "label":    "Breadcrumb-Pfad",
        "guidance": "Horizontale Breadcrumb mit 3-4 Items, getrennt durch '>' oder '/'. Letztes Item ist die aktuelle Seite (text-gray-900), die anderen sind links.",
    },
    "custom_progress_steps": {
        "category": "CUSTOM",
        "label":    "Progress-Steps",
        "guidance": "Mehrstufiger Form-Indicator: 4-5 Schritte horizontal, jeder mit Nummer-Bubble + Label. Aktive Schritte gefuellt, kommende leer.",
    },
    "custom_timeline": {
        "category": "CUSTOM",
        "label":    "Timeline · Vertikal",
        "guidance": "Vertikale Timeline mit 5-6 Eintraegen. Linker Rand: Datum + Bullet-Marker auf vertikaler Linie. Rechts: Titel + Beschreibung pro Eintrag.",
    },
    "custom_gallery": {
        "category": "CUSTOM",
        "label":    "Galerie · Bild-Grid",
        "guidance": "3- oder 4-Spalten-Grid mit Bild-Placeholdern unterschiedlicher Aspect-Ratios (Masonry-aehnlich). Hover-Effekt auf Karten.",
    },
    "custom_404": {
        "category": "CUSTOM",
        "label":    "404 · Fehlerseite",
        "guidance": "Volle Section, zentriert: '404'-Heading sehr gross, 'Seite nicht gefunden'-Subhead, kurzer Text, zwei Buttons (Zur Startseite / Kontakt).",
    },
    "custom_coming_soon": {
        "category": "CUSTOM",
        "label":    "Coming Soon",
        "guidance": "Zentriertes Layout: 'Bald verfuegbar'-Headline, kurzer Subtext, Newsletter-Mini-Form, Countdown-Placeholder (statisch).",
    },
}


# Branchen-Kontexte. Tuple (label, topic-list). Topic-Liste wird in den Prompt
# eingebaut, damit Sonnet branchen-spezifische Default-Werte schreibt.
_INDUSTRIES = {
    "shk": (
        "SHK (Heizung/Sanitaer/Elektrik)",
        "Waermepumpe-Beratung/-Installation/-Foerderung (BAFA, KfW), Wallbox-Installation mit THG-Quote, "
        "Heizungstausch/Modernisierung (GEG), Notdienst 24/7, Wartungsvertrag, Beratungstermin/Kostenvoranschlag, "
        "Innung/Meisterbetrieb, lokale Verankerung."
    ),
    "bauhandwerk": (
        "Bauhandwerk (Maurer, Dachdecker, Trockenbau, Zimmerei)",
        "Sanierung, Neubau, Dachdaemmung/Energetische Sanierung, Gewerk-Koordination, Festpreis-Angebot, "
        "Termintreue, Innung, Bauleitung, Referenzobjekte."
    ),
    "gala": (
        "Garten- und Landschaftsbau",
        "Aussenanlagen-Gestaltung, Pflasterung/Wegebau, Gartendesign, Bewaesserung, Hecken-/Baumschnitt, "
        "Teich/Pool, Saisonpflege, Gartenplanung mit 3D-Visualisierung."
    ),
    "maler": (
        "Maler & Stuckateur",
        "Innen-/Aussenanstrich, Fassadenrenovierung, Stuckarbeiten, Daemmsysteme (WDVS), Schimmelsanierung, "
        "Tapezierarbeiten, Sonderwuensche/Dekorputz, Farbberatung."
    ),
    "kfz": (
        "KFZ-Werkstatt / Auto-Service",
        "Inspektion, TUEV/AU, Reifenwechsel, Klimaservice, E-Auto-Service inkl. Hochvolt-Zertifizierung, "
        "Unfallinstandsetzung, Hol-/Bring-Service, Hersteller-Zertifizierungen."
    ),
    "steuer-anwalt": (
        "Steuerberater / Rechtsanwalt / Versicherungsmakler",
        "Erstberatung, Mandant-Onboarding, digitale Aktenuebergabe, Spezialisierungen (z.B. Erbrecht, "
        "Existenzgruendung, IT-Recht), Honorar-Transparenz, Vertraulichkeit, persoenliche Erreichbarkeit."
    ),
    "medizin": (
        "Arzt / Zahnarzt / Praxis / Therapie",
        "Termin-Buchung online, Sprechzeiten, Notdienst-Hinweis, Spezialisierungen, Vorsorge/Praeventiv, "
        "barrierefreier Zugang, Privat/Kassen, Patienten-Komfort."
    ),
    "gastro": (
        "Gastronomie / Hotel / Restaurant",
        "Reservierung, Speisekarte, Events/Catering, Oeffnungszeiten, regionale Kueche/Bio-Zutaten, "
        "Wein-/Getraenkekarte, Atmosphaere, Gutscheine, Gaeste-Bewertungen."
    ),
    "kosmetik": (
        "Friseur / Kosmetik / Wellness / Spa",
        "Online-Termin, Behandlungs-Menue, Produkt-Linien, Preisstaffel (Damen/Herren), "
        "Specials/Saison-Aktionen, Geschenkgutscheine, Ambiente/Studio-Tour."
    ),
    "fitness": (
        "Fitness-Studio / Sport / Yoga / Personal Training",
        "Probetraining, Mitgliedschaft (Tarife), Kursplan, Trainer-Profile, Geraete/Equipment, "
        "Ernaehrungs-/Reha-Coaching, Online-Kurse, Family-/Studenten-Tarife."
    ),
}


_ELEMENT_LABELS = {
    "headline":    "Headlines (H1/H2/H3)",
    "subtext":     "Subtexte / Paragraphen",
    "buttons":     "Buttons / CTAs",
    "links":       "Links / Nav-Links",
    "images":      "Bilder",
    "icons":       "Icons (SVG inline)",
    "cards":       "Karten / Feature-Items / Service-Items",
    "avatars":     "Avatare / Personen-Bilder",
    "stats":       "Statistik-Counter / Zahlen-Badges",
    "form_fields": "Formular-Felder",
    "logo":        "Logo (als Text-Slot oder Image-Placeholder)",
    "dropdown":    "Dropdown / Select-Menue",
    "search":      "Such-Feld",
    "rating":      "Star-Rating-Anzeige",
    # Kein iframe: eine YouTube-Einbettung laedt beim Seitenaufruf und schickt
    # die Besucher-IP an Google, bevor jemand auf Play geklickt hat.
    "video":       "Video-Platzhalter mit Play-Icon (KEIN iframe, keine Einbettung)",
    "list":        "Liste (bullet oder numbered)",
}


# Wireframe-Stil-Constraints — gilt fuer ALLE Generierungen, unabhaengig vom
# Style-Vibe. Komponenten kommen in eine Wireframe-Bibliothek; das eigentliche
# CI-Design (Brand-Farben, Schriften, Akzente) wird spaeter im Projekt-Prozess
# pro Kunde appliziert. Hier zaehlt nur Struktur + Hierarchie.
_WIREFRAME_CONSTRAINTS = """
WIREFRAME-STIL (PFLICHT — KEINE Brand-Farben, KEINE bunten Akzente):

Farb-Palette — NUR diese Tailwind-Klassen:
- Hintergruende: bg-white, bg-gray-50, bg-gray-100
- Borders: border-gray-200, border-gray-300
- Text: text-gray-900 (Headlines), text-gray-700 (Body), text-gray-500 (Subtext/Mutiert)
- Primary-Button: bg-gray-900 text-white
- Secondary-Button: bg-white border border-gray-300 text-gray-900
- Inverted-Section (sparsam): bg-gray-900 text-white

VERBOTEN: bg-blue-*, bg-indigo-*, bg-amber-*, bg-emerald-*, bg-rose-*, bg-purple-*,
text-blue-*, text-indigo-* etc. Keine bunten Tailwind-Farben.
VERBOTEN: Gradients (bg-gradient-*), starke Schatten (shadow-xl, shadow-2xl).
VERBOTEN: Custom-Hex (#FF...).
ERLAUBT: shadow-sm, shadow (subtle, einsetzen wenn Layout-relevant).

Bilder/Logos/Avatare als neutrale Placeholder:
- Statt <img src="..."> immer ein Tailwind-Placeholder-Block:
  <div class="bg-gray-200 aspect-video flex items-center justify-center text-gray-500">
    <svg ...>Bild-Icon</svg>
  </div>
  Aspect-Ratios: aspect-video (16:9), aspect-square (1:1), aspect-[4/3] etc.
- Logos werden zu Text-Slots ({{logo_text}}) — KEIN Image.
- Avatare als runde Placeholder: <div class="size-12 rounded-full bg-gray-300">

Icons:
- Inline-SVG mit fill="none" stroke="currentColor". Klassen: text-gray-700, size-5 oder size-6.
- Keine Emojis, keine externen Icon-Libraries (kein lucide-react, kein heroicons-cdn).
- Generic genug halten: heart, check, arrow-right, plus, search, menu, x, mail, phone.

Hintergrund-Hinweis fuer Sonnet: Diese Section kommt in eine Wireframe-Bibliothek.
Das eigentliche Brand-Design (CI-Farben, Schriften, dekorative Akzente) wird
spaeter im Projekt-Prozess pro Kunde appliziert. Wireframe = Struktur + Hierarchie +
Semantik. Es ist NICHT das finale Design.
"""
