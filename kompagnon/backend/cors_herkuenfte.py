# -*- coding: utf-8 -*-
"""Wer das Backend im Browser ansprechen darf (BUCH-09).

**Warum eine eigene Datei fuer eine Liste.** Sie hat jetzt zwei Leser: die
Middleware in `main.py` und die Diagnose `GET /api/health/cors`. Zwei Leser
derselben Daten, die ihre eigene Fassung bauen, sind zwei Wahrheiten — und die
Diagnose waere ausgerechnet dann falsch, wenn man sie braucht.

**Warum CORS ueberhaupt eine eigene Aufgabe ist.** Es ist der einzige Fehler
in diesem Bestand, der **nirgends** ein Protokoll erzeugt: Der Browser haelt
die Anfrage an, bevor sie ankommt. Im Render-Log steht nichts, in Stripe
nichts, in der Datenbank nichts — nur in der Browserkonsole steht
`blocked by CORS policy`. Ein Kaufknopf ohne Wirkung, und kein Alarm.

**Was hier bewusst nicht passiert: Werte verwerfen.** Eine Herkunft mit
Schraegstrich am Ende oder mit `http://` wirkt nicht, und die stille Wirkung
ist genau das Problem. Sie wird deshalb **beanstandet und trotzdem
uebernommen** — wer sie eingetragen hat, soll sie in der Liste wiederfinden
und den Grund danebenstehen sehen. Wegzuwerfen hiesse, denselben unsichtbaren
Fehler mit umgekehrtem Vorzeichen zu bauen.
"""
import os
import re

#: Der Name der Variablen an den Render-Diensten. **`CORS_ALLOWED_ORIGINS`,
#: nicht `ALLOWED_ORIGINS`** — der Auftrag BUCH-09 nennt den zweiten Namen,
#: gesetzt ist seit Langem der erste. Den Namen zu wechseln hiesse, eine
#: gesetzte Variable an einem laufenden Dienst wirkungslos zu machen.
UMGEBUNGSVARIABLE = "CORS_ALLOWED_ORIGINS"

#: Herkuenfte, die auch ohne Variable gelten.
#:
#: **Sie stehen bewusst zusaetzlich hier.** Geht die Variable am Dienst
#: verloren, laedt die Oberflaeche sonst und scheitert an jeder Anfrage, ohne
#: dass irgendwo „CORS" stuende.
VORGABE = (
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "https://kas.kompagnon.group",
    "https://kompagnon-frontend.onrender.com",   # alte Adresse, bleibt gueltig
    "https://websprint.kompagnon.eu",            # WebSprint-Landingpage
)

#: Jede Netlify-Adresse. **Das ist Absicht und keine Nachlaessigkeit:** Die
#: erzeugten Kundenseiten liegen dort, jede unter eigener Subdomain, und ihre
#: Zahl aendert sich mit jedem Projekt. Sie einzeln zu pflegen hiesse, jede
#: neue Kundenseite mit einem Deploy des Backends zu bezahlen.
#:
#: **Was das nicht oeffnet.** Die Anmeldung laeuft ueber ein `Bearer`-Token aus
#: dem Speicher der Anwendung, nicht ueber ein Cookie — eine fremde Seite kann
#: es nicht lesen und bekommt deshalb 401. Sobald hier je ein Cookie gesetzt
#: wird, ist dieser Ausdruck neu zu bewerten.
#: **Der Ausdruck beschreibt einen Hostnamen, nicht „irgendwas".** Bis zum
#: 01.09.2026 stand hier `https://.*\.netlify\.app`, und `.*` schliesst den
#: Schraegstrich ein: `https://fremde.example/pfad.netlify.app` passte darauf.
#: Ueber den Browser ist das folgenlos — ein `Origin`-Kopf traegt nie einen
#: Pfad —, aber ein Ausdruck, der mehr erlaubt als er soll, ist eine Zusage,
#: die niemand geprueft hat. Deploy-Vorschauen (`deploy-preview-3--seite`)
#: bleiben erfasst.
NETLIFY_MUSTER = r"https://[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.netlify\.app"

#: `fullmatch`, weil Starlette es auch so macht
#: (`starlette/middleware/cors.py`). Eine Diagnose, die anders rechnet als die
#: Middleware, ist eine zweite Wahrheit.
_NETLIFY = re.compile(NETLIFY_MUSTER)


def herkuenfte() -> list:
    """Die geltende Liste — Variable zuerst, Vorgaben ergaenzt."""
    roh = os.getenv(UMGEBUNGSVARIABLE, "")
    aus_variable = [w.strip() for w in roh.split(",") if w.strip()]
    liste = list(aus_variable)
    for vorgabe in VORGABE:
        if vorgabe not in liste:
            liste.append(vorgabe)
    return liste


def beanstandungen(liste=None) -> list:
    """Eintraege, die nicht wirken werden — mit Grund, in Klartext.

    Die drei Faelle stammen aus BUCH-09 und sind alle drei still: Der Browser
    vergleicht die Herkunft zeichengenau, und keiner davon erzeugt eine
    Fehlermeldung auf unserer Seite.
    """
    liste = herkuenfte() if liste is None else liste
    funde = []
    for eintrag in liste:
        if eintrag.endswith("/"):
            funde.append(f"{eintrag}: Schraegstrich am Ende — der Browser "
                         f"vergleicht zeichengenau und trifft nie")
        if eintrag == "*":
            funde.append("*: zusammen mit allow_credentials=True nach "
                         "Spezifikation ungueltig; Browser ignorieren es "
                         "kommentarlos")
        if eintrag.startswith("http://") and not eintrag.startswith(
                ("http://localhost", "http://127.0.0.1")):
            funde.append(f"{eintrag}: unverschluesselt — von einer "
                         f"https-Seite aus nie erlaubt")
    return funde


def ist_erlaubt(herkunft: str, liste=None) -> bool:
    """Duerfte dieser Aufrufer? Dieselbe Rechnung wie in der Middleware."""
    if not herkunft:
        return False
    liste = herkuenfte() if liste is None else liste
    return herkunft in liste or bool(_NETLIFY.fullmatch(herkunft))


def fassung() -> str:
    """Welcher Stand laeuft — fuer die Diagnose, damit „ich habe doch
    deployt" nachpruefbar wird.

    Render setzt `RENDER_GIT_COMMIT`. Fehlt sie, wird **nicht** geraten: Ein
    erfundener Stand ist schlimmer als ein zugegebener Unbekannter.
    """
    return os.getenv("RENDER_GIT_COMMIT", "")[:12]
