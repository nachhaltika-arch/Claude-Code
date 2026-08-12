"""
Die KOMPAGNON-Marke für serverseitig gerendertes HTML.

Bericht und E-Mails werden im Backend gebaut und können deshalb nicht auf
`tokens.css` zugreifen. Die Werte hier sind die Gegenstücke dazu und müssen
mit `kompagnon/frontend/src/styles/tokens.css` übereinstimmen — dort steht
die Quelle der Wahrheit, hier die Kopie für alles, was ohne die React-
Anwendung ausgeliefert wird.

Vorher standen zwei frei erfundene Hex-Werte in `widget_report.py`
(``#0F2E2B`` und ``#F5C518``). Beide sind nirgends in der CI belegt: der
erste ist ein Grünton, das offizielle Dunkelblau ist ``#004F59``, und das
Gelb war ein Goldton statt ``#FAE600``. Bericht und E-Mail sahen damit nach
einer anderen Marke aus als das Tool.

**Schriften:** Ausgeliefert wird ein Stapel, keine Webschrift. Die
Berichtsseite öffnet ein Dritter, und das Widget läuft auf fremden
Landingpages — ein Google-Fonts-Aufruf überträgt dessen IP-Adresse an
Google, ohne Einwilligung. In E-Mails greifen Webschriften ohnehin nicht.
Wer Noto Sans installiert hat, sieht Noto Sans; sonst die Systemschrift.
"""

# ── Primärfarben (Pantone) ───────────────────────────────────────────
DARK = "#004F59"     # Pantone 3165 — Primär, Flächen und Überschriften
MID = "#008EAA"      # Pantone 3135 — Links, sekundäre Kategorien
YELLOW = "#FAE600"   # Pantone 3945 — Akzent, genau eine Aktion je Seite
BLACK = "#000000"

# ── Flächen und Linien ───────────────────────────────────────────────
PAPER = "#FAFAFA"
SURFACE = "#F0F4F5"
BORDER = "#D5E0E2"
WHITE = "#FFFFFF"

# ── Text ─────────────────────────────────────────────────────────────
TEXT = "#000000"
TEXT_60 = "#4A5A5C"
TEXT_30 = "#9AACAE"
TEXT_INVERSE = "#FFFFFF"

# ── Status ───────────────────────────────────────────────────────────
SUCCESS = "#00875A"
SUCCESS_BG = "#E3F6EF"
WARN = "#A86800"
WARN_BG = "#FFF4E0"
ERROR = "#C0392B"
ERROR_BG = "#FDECEA"
INFO = "#008EAA"
INFO_BG = "#E0F4F8"

# ── Schrift ──────────────────────────────────────────────────────────
FONT_SANS = ("'Noto Sans',system-ui,-apple-system,'Segoe UI',Roboto,"
             "Helvetica,Arial,sans-serif")
FONT_MONO = "'DM Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def score_colour(score: int) -> str:
    """Die Ampel hinter einer Punktzahl.

    Dieselben Schwellen wie im Widget, damit der Besucher auf der
    Berichtsseite nicht plötzlich eine andere Farbe für dieselbe Zahl sieht.
    """
    if score >= 70:
        return SUCCESS
    if score >= 50:
        return WARN
    return ERROR
