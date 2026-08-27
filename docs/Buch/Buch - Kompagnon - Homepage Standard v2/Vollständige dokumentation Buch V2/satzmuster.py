#!/usr/bin/env python3
"""Satzmuster „Der Homepage Standard" — 170 x 240 mm.

Setzt den Satzspiegel aus dem Buchkonzept (Teil 1.2) exakt um und zeigt ihn
an echten Inhalten aus dem Manuskript.

SCHRIFTEN: Platzhalter. Die KOMPAGNON-Hausschrift liegt hier nicht vor.
DejaVu Serif steht fuer die Textschrift, DejaVu Sans fuer die Hausschrift.
Beim Satz zu ersetzen — Lizenz fuer Print UND EPUB vorher pruefen.

FARBE: Innenteil einfarbig (Variante B des Buchkonzepts). Umschlag vierfarbig.
"""
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# ── Format ───────────────────────────────────────────────────────────────
PB, PH = 170 * mm, 240 * mm
BUND, HAUPT, STEG, MARG, AUSSEN = 20 * mm, 95 * mm, 5 * mm, 35 * mm, 15 * mm
KOPF, SATZ, FUSS = 20 * mm, 190 * mm, 30 * mm
RASTER = 13
X_HAUPT = BUND
X_MARG = BUND + HAUPT + STEG
Y_OBEN = PH - KOPF

# ── Farbe ────────────────────────────────────────────────────────────────
TEAL = HexColor("#004F59")
TEAL_HELL = HexColor("#008EAA")
GELB = HexColor("#FAE600")
G15 = Color(.88, .88, .88)
G30 = Color(.72, .72, .72)
G60 = Color(.42, .42, .42)
G80 = Color(.22, .22, .22)

# ── Schriften ────────────────────────────────────────────────────────────
D = "/usr/share/fonts/truetype/dejavu/"
for name, datei in [("Haus", "DejaVuSans.ttf"), ("Haus-B", "DejaVuSans-Bold.ttf"),
                    ("Text", "DejaVuSerif.ttf"), ("Text-B", "DejaVuSerif-Bold.ttf"),
                    ("Text-I", "DejaVuSerif-Italic.ttf")]:
    pdfmetrics.registerFont(TTFont(name, D + datei))

c = canvas.Canvas("Satzmuster-Homepage-Standard.pdf", pagesize=(PB, PH))
c.setTitle("Der Homepage Standard — Satzmuster")
c.setAuthor("Manuel Potter")


# ── Werkzeuge ────────────────────────────────────────────────────────────
def zeilen(text, font, groesse, breite):
    """Blocksatzfreier Umbruch auf eine gegebene Breite."""
    aus, zeile = [], ""
    for wort in text.split():
        probe = (zeile + " " + wort).strip()
        if pdfmetrics.stringWidth(probe, font, groesse) <= breite:
            zeile = probe
        else:
            aus.append(zeile)
            zeile = wort
    if zeile:
        aus.append(zeile)
    return aus


def fliess(y, text, font="Text", gr=10, lead=RASTER, x=X_HAUPT, br=HAUPT,
           farbe=black, abstand=0):
    c.setFont(font, gr)
    c.setFillColor(farbe)
    for z in zeilen(text, font, gr, br):
        c.drawString(x, y, z)
        y -= lead
    return y - abstand


def marginalie(y, kopf, text, extra=None):
    c.setFont("Haus-B", 7.5)
    c.setFillColor(black)
    c.drawString(X_MARG, y, kopf)
    y -= 10
    c.setFont("Haus", 7.5)
    c.setFillColor(G80)
    for z in zeilen(text, "Haus", 7.5, MARG):
        c.drawString(X_MARG, y, z)
        y -= 9.5
    if extra:
        y -= 3
        c.setFont("Haus", 7.5)
        c.setFillColor(G60)
        for z in zeilen(extra, "Haus", 7.5, MARG):
            c.drawString(X_MARG, y, z)
            y -= 9.5
    return y


def stufenmarke(x, y, gefuellt=0, gr=6, luecke=1.6):
    """Vier Segmente. Unterscheidung nur ueber Fuellung — nie ueber Farbe."""
    for i in range(4):
        xi = x + i * (gr + luecke)
        if i < gefuellt:
            c.setFillColor(black)
            c.rect(xi, y, gr, gr, stroke=0, fill=1)
        else:
            c.setStrokeColor(G30)
            c.setLineWidth(.5)
            c.rect(xi, y, gr, gr, stroke=1, fill=0)


def tabelle(y, kopf, reihen, spalten, gr=8.5, lead=RASTER, x=X_HAUPT):
    br_ges = sum(spalten)
    c.setFont("Haus-B", gr)
    c.setFillColor(black)
    xs = x
    for i, z in enumerate(kopf):
        c.drawString(xs, y, z)
        xs += spalten[i]
    y -= 4
    c.setStrokeColor(black)
    c.setLineWidth(.8)
    c.line(x, y, x + br_ges, y)
    y -= lead - 4
    for r, reihe in enumerate(reihen):
        fett = any(str(z).startswith("*") for z in reihe)
        f = "Haus-B" if fett else "Haus"
        c.setFont(f, gr)
        c.setFillColor(black)
        xs = x
        for i, z in enumerate(reihe):
            c.drawString(xs, y, str(z).lstrip("*"))
            xs += spalten[i]
        y -= 3
        c.setStrokeColor(black if fett else G15)
        c.setLineWidth(.8 if fett else .4)
        c.line(x, y, x + br_ges, y)
        y -= lead - 3
    return y


def fuss(seite, kolumne):
    if seite % 2 == 0:
        px, ax = BUND, "left"
    else:
        px, ax = PB - AUSSEN, "right"
    c.setFont("Haus", 8)
    c.setFillColor(G60)
    if ax == "left":
        c.drawString(px, FUSS - 12 * mm, str(seite))
        c.drawString(px + 12, FUSS - 12 * mm, kolumne)
    else:
        c.drawRightString(px, FUSS - 12 * mm, str(seite))
        c.drawRightString(px - 12, FUSS - 12 * mm, kolumne)


def hinweis(text):
    """Roter Randvermerk — nur im Muster, nicht im Buch."""
    c.saveState()
    c.setFont("Haus", 6.5)
    c.setFillColor(HexColor("#B00020"))
    c.drawRightString(PB - 6 * mm, 6 * mm, "SATZMUSTER · " + text)
    c.restoreState()


# ═════════════════════════════════════════════════════════════════════════
# 1 · UMSCHLAG
# ═════════════════════════════════════════════════════════════════════════
c.setFillColor(TEAL)
c.rect(0, 0, PB, PH, stroke=0, fill=1)
c.setFillColor(GELB)
c.rect(0, PH - 118 * mm, PB, 8 * mm, stroke=0, fill=1)

c.setFillColor(white)
c.setFont("Haus-B", 15)
c.drawString(BUND, PH - 42 * mm, "DER")
c.setFont("Haus-B", 34)
c.drawString(BUND, PH - 58 * mm, "HOMEPAGE")
c.drawString(BUND, PH - 74 * mm, "STANDARD")

c.setFont("Haus", 10.5)
c.setFillColor(white)
for i, z in enumerate(["Der Selbsttest für Unternehmenswebsites",
                       "39 Kriterien · 8 Kategorien · 103 Punkte"]):
    c.drawString(BUND, PH - 92 * mm - i * 15, z)

# Stufenleiste als Gestaltungselement
for i in range(5):
    x = BUND + i * 22 * mm
    c.setFillColor(white if i < 3 else Color(1, 1, 1, .35))
    c.rect(x, 62 * mm, 18 * mm, 3 * mm, stroke=0, fill=1)
c.setFont("Haus", 7)
c.setFillColor(Color(1, 1, 1, .8))
c.drawString(BUND, 56 * mm, "NICHT KONFORM   BRONZE   SILBER   GOLD   PLATIN")

c.setFont("Haus-B", 11)
c.setFillColor(GELB)
c.drawString(BUND, 34 * mm, "MANUEL POTTER")
c.setFont("Haus", 8.5)
c.setFillColor(Color(1, 1, 1, .75))
c.drawString(BUND, 27 * mm, "Herausgegeben von KOMPAGNON communications BP GmbH")
hinweis("Umschlag · Farben laut CD, Hausschrift ersetzen")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 2 · HAUPTTITEL
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN - 60 * mm
c.setFillColor(black)
c.setFont("Haus-B", 11)
c.drawString(X_HAUPT, y, "DER")
c.setFont("Haus-B", 27)
c.drawString(X_HAUPT, y - 14 * mm, "HOMEPAGE")
c.drawString(X_HAUPT, y - 26 * mm, "STANDARD")
c.setStrokeColor(black)
c.setLineWidth(1.2)
c.line(X_HAUPT, y - 34 * mm, X_HAUPT + HAUPT, y - 34 * mm)
fliess(y - 42 * mm, "Der Selbsttest für Unternehmenswebsites:", "Text", 11)
fliess(y - 42 * mm - RASTER, "39 Kriterien, 8 Kategorien, 103 Punkte", "Text-B", 11)
c.setFont("Haus-B", 10)
c.drawString(X_HAUPT, 62 * mm, "MANUEL POTTER")
c.setFont("Haus", 8.5)
c.setFillColor(G60)
c.drawString(X_HAUPT, 55 * mm, "Herausgegeben von KOMPAGNON communications BP GmbH")
hinweis("Haupttitel · Untertitel nach ISBN-Meldung eingefroren")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 3 · IMPRESSUMSSEITE
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 8.5)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "DER HOMEPAGE STANDARD")
y -= RASTER
y = fliess(y, "Der Selbsttest für Unternehmenswebsites: 39 Kriterien, "
              "8 Kategorien, 103 Punkte", "Haus", 8.5, abstand=RASTER)
for block in [
    ("Autor", "Manuel Potter"),
    ("Herausgeber", "KOMPAGNON communications BP GmbH, Marienfelder Straße 52, "
                    "56070 Koblenz"),
    ("Fassung des Standards", "2026.2"),
    ("Rechtsstand", "[bei Drucklegung einzutragen]"),
    ("ISBN Print", "[noch zu beantragen]"),
    ("ISBN E-Book", "[noch zu beantragen]"),
    ("Herstellung", "Books on Demand"),
]:
    c.setFont("Haus-B", 7.5)
    c.setFillColor(black)
    c.drawString(X_HAUPT, y, block[0])
    y -= 10
    y = fliess(y, block[1], "Haus", 8.5, lead=11, abstand=6)

y -= 6
c.setStrokeColor(G30)
c.setLineWidth(.5)
c.line(X_HAUPT, y, X_HAUPT + HAUPT, y)
y -= RASTER
y = fliess(y, "Prüfliste und Vorlagen zum Ausfüllen sowie der kostenlose "
              "Online-Check:", "Haus", 8, lead=11)
c.setFont("Haus-B", 9)
c.setFillColor(black)
c.drawString(X_HAUPT, y - 2, "[eigene Domain — noch festzulegen]")
y -= RASTER + 8
y = fliess(y, "Alle Zahlen dieses Buchs stammen aus dem Prüfkatalog der "
              "Software und sind nicht von Hand eingetragen. Wenn eine "
              "Rechnung nicht aufgeht, ist das ein Fehler — bitte melden Sie "
              "ihn über die Adresse oben.", "Haus", 8, lead=11)

marginalie(Y_OBEN, "🔴 OFFEN",
           "Zwei Adressen auf dieser Seite sind nach dem Druck nicht mehr "
           "änderbar. Beide brauchen eine eigene Domain mit serverseitiger "
           "Weiterleitung.")
hinweis("Impressumsseite · zwei unumkehrbare Entscheidungen")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 4 · INHALT (Auszug)
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 16)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "INHALT")
y -= 22

inhalt = [
    ("T", "TEIL I — WARUM EIN STANDARD", ""),
    ("K", "1  Die Website ist ein Betriebsmittel", "11"),
    ("K", "2  Warum es einen Standard braucht", "23"),
    ("K", "3  Das Bewertungssystem", "33"),
    ("K", "4  Ihre Branchenklasse", "49"),
    ("T", "TEIL II — DIE ACHT KATEGORIEN", ""),
    ("K", "5  Recht und Compliance · 20 Punkte", "63"),
    ("K", "6  Sicherheit und Datenschutz · 10 Punkte", "85"),
    ("K", "7  Ladezeit und Stabilität · 15 Punkte", "97"),
    ("K", "8  Barrierefreiheit · 10 Punkte", "113"),
    ("K", "9  Auffindbarkeit · 18 Punkte", "127"),
    ("K", "10  Gestaltung · 10 Punkte", "145"),
    ("K", "11  Nutzerführung und Anfragen · 15 Punkte", "159"),
    ("K", "12  Inhalt und Substanz · 5 Punkte", "175"),
    ("T", "TEIL III — ANWENDUNG", ""),
    ("K", "13  Der Selbsttest in 120 Minuten", "187"),
    ("K", "14  Zwanzig Befunde, die wiederkehren", "203"),
    ("K", "15  Der 30-Tage-Plan", "215"),
    ("T", "TEIL IV — GRENZEN", ""),
    ("K", "16  Was von außen nicht messbar ist", "229"),
    ("K", "17  Grenzen des Selbermachens", "237"),
    ("T", "ANHANG", ""),
    ("K", "A  Glossar", "247"),
    ("K", "B  Der Katalog auf einen Blick", "252"),
    ("K", "C  Fünf Vorlagen", "258"),
    ("K", "D  Rechtsquellen und Fundstellen", "263"),
]
for art, titel, seite in inhalt:
    if art == "T":
        y -= 8
        c.setFont("Haus-B", 8)
        c.setFillColor(black)
        c.drawString(X_HAUPT, y, titel)
        y -= 5
        c.setStrokeColor(black)
        c.setLineWidth(.8)
        c.line(X_HAUPT, y, X_HAUPT + HAUPT, y)
        y -= 11
    else:
        c.setFont("Text", 9.5)
        c.setFillColor(black)
        c.drawString(X_HAUPT, y, titel)
        c.setFont("Haus", 8.5)
        c.setFillColor(G60)
        c.drawRightString(X_HAUPT + HAUPT, y, seite)
        y -= RASTER

marginalie(Y_OBEN - 30, "SEITENZAHLEN",
           "Vorläufig. Der Entwurf liegt bei rund 260 Seiten statt der "
           "geplanten 208 — Entscheidung offen.")
hinweis("Inhaltsverzeichnis · Umfang 25 % über Ziel")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 5 · TEIL-TRENNSEITE
# ═════════════════════════════════════════════════════════════════════════
c.setFillColor(G15)
c.rect(0, 0, PB, PH, stroke=0, fill=1)
c.setFillColor(black)
c.setFont("Haus-B", 9)
c.drawString(X_HAUPT, PH / 2 + 30, "TEIL I")
c.setFont("Haus-B", 24)
c.drawString(X_HAUPT, PH / 2, "WARUM EIN")
c.drawString(X_HAUPT, PH / 2 - 26, "STANDARD")
c.setStrokeColor(black)
c.setLineWidth(1)
c.line(X_HAUPT, PH / 2 - 42, X_HAUPT + 60 * mm, PH / 2 - 42)
c.setFont("Haus", 8.5)
c.setFillColor(G80)
c.drawString(X_HAUPT, PH / 2 - 58, "Kapitel 1 bis 4")
hinweis("Teil-Trennseite · Fläche in Variante B als Grauton")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 6 · KAPITELÖFFNER
# ═════════════════════════════════════════════════════════════════════════
c.setFillColor(G15)
c.setFont("Haus-B", 130)
c.drawString(X_HAUPT - 4, PH - 108 * mm, "3")
c.setFillColor(black)
c.setFont("Haus-B", 22)
c.drawString(X_HAUPT, PH - 122 * mm, "DAS")
c.drawString(X_HAUPT, PH - 132 * mm, "BEWERTUNGSSYSTEM")
c.setStrokeColor(black)
c.setLineWidth(1)
c.line(X_HAUPT, PH - 140 * mm, X_HAUPT + HAUPT, PH - 140 * mm)
y = PH - 152 * mm
y = fliess(y, "Acht Kategorien, 39 Kriterien, 103 Punkte. Was davon zählt, "
              "was nicht zählt und warum am Ende trotzdem eine Zahl zwischen "
              "0 und 100 steht.", "Text-I", 11, lead=16)
c.setFont("Haus", 7.5)
c.setFillColor(G60)
c.drawString(X_MARG, PH - 122 * mm, "TEIL I")
hinweis("Kapitelöffner · rechte Seite, Rückseite bleibt frei")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 7 · TEXTSEITE MIT TABELLE
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 12)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "3.2  Die acht Kategorien")
y -= 22
y = fliess(y, "Der Standard prüft 39 Kriterien in acht Kategorien. Zusammen "
              "ergeben sie 103 Punkte.", abstand=8)
y = tabelle(y, ["Kategorie", "P", "Krit."],
            [["Recht und Compliance", "20", "5"],
             ["Sicherheit und Datenschutz", "10", "4"],
             ["Ladezeit und Stabilität", "15", "5"],
             ["Barrierefreiheit", "10", "5"],
             ["Auffindbarkeit", "18", "7"],
             ["Gestaltung", "10", "5"],
             ["Nutzerführung und Anfragen", "15", "5"],
             ["Inhalt und Substanz", "5", "3"],
             ["*Summe", "*103", "*39"]],
            [62 * mm, 18 * mm, 15 * mm])
y -= 8
c.setFont("Text-B", 10)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "Warum 103 und nicht 100.")
y = fliess(y - RASTER,
           "Die Kategorien ergeben zusammen 103 Punkte. Ihr Ergebnis wird "
           "trotzdem als Wert zwischen 0 und 100 ausgewiesen. Der Grund steht "
           "in Abschnitt 3.6 und ist wichtiger, als er zunächst klingt: Je "
           "nach Branche gelten nicht alle Kriterien für Sie, und ein Maßstab, "
           "dessen Höchstwert von der Branche abhängt, wäre nicht vergleichbar.",
           abstand=10)
y -= 2
c.setFont("Text-B", 10)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "Zwei Kategorien, die Sie selten finden.")
fliess(y - RASTER,
       "Gestaltung und Nutzerführung stehen in vergleichbaren Checklisten "
       "selten. Genau das sind aber die beiden Dinge, die Sie selbst auf Ihrer "
       "Seite sehen und über die Sie mit einem Dienstleister diskutieren. Sie "
       "unbewertet zu lassen, weil sie unbequem zu messen sind, hieße, die "
       "Hälfte des Gesprächs auszulassen.")

my = marginalie(Y_OBEN + 4, "ERZEUGT",
                "Diese Tabelle stammt aus dem Prüfkatalog der Software und "
                "ist nicht von Hand eingetragen.")
marginalie(my - 16, "103 ≠ 100",
           "103 ist die Summe des Katalogs. 0–100 ist die Skala Ihres "
           "Ergebnisses.", "→ Abschnitt 3.6")
fuss(36, "Das Bewertungssystem")
hinweis("Textseite · Hauptspalte 95 mm ≈ 62 Zeichen")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 8 · STUFENSEITE MIT MARKEN
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 12)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "3.7  Die fünf Stufen")
y -= 22
y = fliess(y, "Aus Ihrem Wert ergibt sich eine von fünf Stufen.", abstand=8)

stufen = [(4, "Homepage Standard Platin", "95–100"),
          (3, "Homepage Standard Gold", "85–94"),
          (2, "Homepage Standard Silber", "70–84"),
          (1, "Homepage Standard Bronze", "50–69"),
          (0, "Nicht konform", "0–49")]
c.setStrokeColor(black)
c.setLineWidth(.8)
c.line(X_HAUPT, y + 4, X_HAUPT + HAUPT, y + 4)
y -= 6
for gef, name, wert in stufen:
    stufenmarke(X_HAUPT, y - 1)
    stufenmarke(X_HAUPT, y - 1, gef)
    c.setFont("Haus-B" if gef >= 3 else "Haus", 9)
    c.setFillColor(black)
    c.drawString(X_HAUPT + 36, y, name)
    c.setFont("Haus", 9)
    c.drawRightString(X_HAUPT + HAUPT, y, wert)
    y -= 6
    c.setStrokeColor(G15)
    c.setLineWidth(.4)
    c.line(X_HAUPT, y, X_HAUPT + HAUPT, y)
    y -= RASTER - 6

y -= 8
c.setFont("Text-B", 10)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "Gold ist das Ziel, nicht Platin.")
y = fliess(y - RASTER,
           "Das ist keine Bescheidenheit, sondern Wirtschaftlichkeit. Die "
           "letzten Punkte zwischen 85 und 100 kosten überproportional viel "
           "Aufwand und bringen für die Kundengewinnung fast nichts mehr. Wer "
           "von Bronze auf Silber kommt, verändert seine Außenwirkung spürbar. "
           "Wer von Gold auf Platin geht, verändert vor allem seine Rechnung.")

marginalie(Y_OBEN + 4, "KEINE METALLFARBEN",
           "Die Stufen werden über Füllung unterschieden, nicht über Farbe. "
           "Gold und Silber in CMYK gedruckt sehen billig aus — und Kapitel 8 "
           "bewertet Farbkontraste.")
fuss(45, "Das Bewertungssystem")
hinweis("Stufenmarken · schwarzweißfest, Variante B")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 9 · KRITERIENSEITE
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 12)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "5.4  L1 — Impressum · 6 Punkte")
y -= 20
c.setFont("Haus-B", 8.5)
c.drawString(X_HAUPT, y, "Worum es geht")
y -= RASTER
y = fliess(y, "Wer geschäftsmäßig eine Website betreibt, muss bestimmte "
              "Angaben leicht erkennbar, unmittelbar erreichbar und ständig "
              "verfügbar halten. Die Pflicht steht seit Mai 2024 in § 5 des "
              "Digitale-Dienste-Gesetzes. Ältere Vorlagen nennen § 5 TMG — "
              "das Telemediengesetz gibt es nicht mehr.", abstand=8)
c.setFont("Haus-B", 8.5)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "Punktvergabe")
y -= RASTER
y = tabelle(y, ["P", "Bedingung"],
            [["6", "erreichbar und alle vier Angaben gefunden"],
             ["3", "erreichbar, mindestens eine Angabe fehlt"],
             ["0", "keine erreichbare Impressumsseite"]],
            [12 * mm, 83 * mm])
y -= 8
y = fliess(y, "Es gibt keinen Zwischenwert zwischen 3 und 6. Ob eine oder "
              "drei Angaben fehlen, macht keinen Unterschied — die Pflicht ist "
              "nicht teilbar.", "Text-I", 9.5, abstand=8)
c.setFont("Haus-B", 8.5)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "So beheben Sie es")
y -= RASTER
fliess(y, "Der Sprung von 0 auf 3 ist eine Verlinkung. Der Sprung von 3 auf 6 "
          "ist ein Textblock. Beides ist an einem Vormittag erledigt.")

my = marginalie(Y_OBEN + 4, "L1 · 6 PUNKTE",
                "gemessen\n§ 5 DDG", "AUSSCHLUSSKRITERIUM")
my = marginalie(my - 16, "ERZEUGT",
                "Punktetabelle aus dem Prüfkatalog.")
marginalie(my - 16, "🔴 ANWALTLICH ZU PRÜFEN",
           "Die Aussage zur Telefonnummer gehört zu den dreizehn Punkten der "
           "Rechtsprüfung.")
fuss(70, "Recht und Compliance")
hinweis("Kriterienseite · Marginalspalte trägt Code, Punkte, Rechtsquelle")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 10 · SELBSTTEST
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 12)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "13.7  Die Umrechnung")
y -= 20
y = fliess(y, "Drei Zeilen. Rechnen Sie sie mit einem Taschenrechner nach.",
           abstand=10)

c.setStrokeColor(black)
c.setLineWidth(.8)
kasten_y = y
zeilen_rech = [("①", "Ihr anwendbares Maximum", ""),
               ("②", "Minus Ihre U-Punkte", "−"),
               ("③", "Ihr tatsächlicher Nenner", "="),
               ("④", "Ihre erreichten Punkte", ""),
               ("⑤", "④ ÷ ③ × 100", ""),
               ("⑥", "Kaufmännisch gerundet", "")]
h = len(zeilen_rech) * 18 + 12
c.rect(X_HAUPT, kasten_y - h + 8, HAUPT, h, stroke=1, fill=0)
yy = kasten_y - 8
for nr, txt, op in zeilen_rech:
    fett = nr == "⑥"
    c.setFont("Haus-B" if fett else "Haus", 9)
    c.setFillColor(black)
    c.drawString(X_HAUPT + 5, yy, nr)
    c.drawString(X_HAUPT + 18, yy, txt)
    c.drawRightString(X_HAUPT + 62 * mm, yy, op)
    c.setStrokeColor(black if fett else G60)
    c.setLineWidth(1 if fett else .5)
    c.line(X_HAUPT + 64 * mm, yy - 2, X_HAUPT + HAUPT - 5, yy - 2)
    yy -= 18
y = kasten_y - h - 4

y = fliess(y, "Ein Betrieb der Klasse K1, der den Selbsttest ohne Messung "
              "durchgeführt hat:", "Text-I", 9.5, abstand=6)
y = tabelle(y, ["", "Wert"],
            [["Anwendbares Maximum (K1)", "103"],
             ["U-Punkte: S3, E4, P1, P3, P4, B1", "− 18"],
             ["*Tatsächlicher Nenner", "*85"],
             ["Erreichte Punkte", "64"],
             ["64 ÷ 85 × 100", "75,3"],
             ["*Gerundet — Silber", "*75"]],
            [72 * mm, 23 * mm])

marginalie(Y_OBEN + 4, "WARUM SCHRITT ②",
           "Was Sie nicht prüfen konnten, zählt weder für noch gegen Sie. Es "
           "verschwindet aus der Rechnung — nicht in die Null.",
           "→ Abschnitt 3.5")
fuss(195, "Der Selbsttest")
hinweis("Selbsttest · Ausfüllfelder, PDF-Fassung zwingend")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 11 · VORLAGE 1 — ERGEBNISBLATT
# ═════════════════════════════════════════════════════════════════════════
y = Y_OBEN
c.setFont("Haus-B", 8)
c.setFillColor(G60)
c.drawString(X_HAUPT, y, "ANHANG C · VORLAGE 1")
y -= 16
c.setFont("Haus-B", 16)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "IHR ERGEBNISBLATT")
y -= 20

br = HAUPT + STEG + MARG
for feld in ["Betrieb", "Website", "Geprüft am", "Branchenklasse"]:
    c.setFont("Haus", 8)
    c.setFillColor(G60)
    c.drawString(X_HAUPT, y, feld)
    c.setStrokeColor(G60)
    c.setLineWidth(.5)
    c.line(X_HAUPT + 28 * mm, y - 2, X_HAUPT + br, y - 2)
    y -= 17
y -= 4

y = tabelle(y, ["Kap.", "Kategorie", "Max", "Erreicht", "davon U"],
            [["5", "Recht und Compliance", "20", "", ""],
             ["6", "Sicherheit und Datenschutz", "10", "", ""],
             ["7", "Ladezeit und Stabilität", "15", "", ""],
             ["8", "Barrierefreiheit", "10", "", ""],
             ["9", "Auffindbarkeit", "18", "", ""],
             ["10", "Gestaltung", "10", "", ""],
             ["11", "Nutzerführung und Anfragen", "15", "", ""],
             ["12", "Inhalt und Substanz", "5", "", ""],
             ["", "*Summe", "*103", "", ""]],
            [12 * mm, 62 * mm, 14 * mm, 24 * mm, 20 * mm], gr=8.5)
y -= 10

c.setFont("Haus-B", 9)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "IHRE STUFE")
y -= 16
for gef, name, wert in stufen:
    c.setStrokeColor(black)
    c.setLineWidth(.7)
    c.rect(X_HAUPT, y - 1, 7, 7, stroke=1, fill=0)
    stufenmarke(X_HAUPT + 14, y - 1)
    stufenmarke(X_HAUPT + 14, y - 1, gef)
    c.setFont("Haus", 9)
    c.setFillColor(black)
    c.drawString(X_HAUPT + 50, y, name)
    c.setFont("Haus", 8.5)
    c.setFillColor(G60)
    c.drawRightString(X_HAUPT + br, y, wert)
    y -= 16

y -= 6
c.setFont("Haus-B", 8.5)
c.setFillColor(black)
c.drawString(X_HAUPT, y, "NÄCHSTER PRÜFTERMIN")
c.setStrokeColor(black)
c.setLineWidth(.8)
c.line(X_HAUPT + 46 * mm, y - 2, X_HAUPT + br, y - 2)
hinweis("Vorlage 1 · Kandidat für die Umschlaginnenseite")
c.showPage()

# ═════════════════════════════════════════════════════════════════════════
# 12 · SATZSPIEGEL (technische Seite für Manuel)
# ═════════════════════════════════════════════════════════════════════════
c.setFillColor(Color(.97, .97, .97))
c.rect(X_HAUPT, FUSS, HAUPT, SATZ, stroke=0, fill=1)
c.setFillColor(Color(.92, .92, .92))
c.rect(X_MARG, FUSS, MARG, SATZ, stroke=0, fill=1)
c.setStrokeColor(G60)
c.setLineWidth(.5)
c.rect(X_HAUPT, FUSS, HAUPT, SATZ, stroke=1, fill=0)
c.rect(X_MARG, FUSS, MARG, SATZ, stroke=1, fill=0)

c.setStrokeColor(Color(.85, .85, .85))
c.setLineWidth(.25)
yy = FUSS + SATZ
while yy > FUSS:
    c.line(X_HAUPT, yy, X_MARG + MARG, yy)
    yy -= RASTER

c.setFont("Haus-B", 8)
c.setFillColor(black)
c.drawString(X_HAUPT + 4, FUSS + SATZ - 14, "HAUPTSPALTE 95 mm")
c.setFont("Haus", 7)
c.drawString(X_HAUPT + 4, FUSS + SATZ - 25, "10/13 pt · ca. 62 Zeichen")
c.setFont("Haus-B", 7)
c.drawString(X_MARG + 3, FUSS + SATZ - 14, "MARGINAL 35 mm")
c.setFont("Haus", 6.5)
c.drawString(X_MARG + 3, FUSS + SATZ - 24, "8/11 pt")

c.setFont("Haus", 7)
c.setFillColor(G60)
c.drawString(6 * mm, PH / 2, "20")
c.drawString(BUND + HAUPT + 1, PH / 2, "5")
c.drawString(PB - 11 * mm, PH / 2, "15")
c.drawCentredString(PB / 2, PH - 11 * mm, "Kopfsteg 20 mm")
c.drawCentredString(PB / 2, 14 * mm, "Fußsteg 30 mm · Pagina außen")
c.drawCentredString(PB / 2, 6 * mm, "Format 170 × 240 mm · Grundlinienraster 13 pt")
hinweis("Satzspiegel · Vorlage für den Satz")
c.showPage()

c.save()
print("Satzmuster-Homepage-Standard.pdf geschrieben — 12 Seiten")
