# -*- coding: utf-8 -*-
"""Barrierefreiheit am gerenderten Dokument messen (L-153).

**Der Anlass (04.09.2026).** Vier der fuenf Barrierefreiheitskriterien kamen
aus Lighthouse, und Lighthouse kommt ueber PageSpeed. Im Fremdlauf gegen
`neovendo.de` sind **alle acht** PageSpeed-Kriterien ausgefallen; der Kunde las
„Barrierefreiheit 0/2", weil genau ein Kriterium erhoben werden konnte.

**Was hier ersetzt wird und was nicht.** Kontrast, Schriftgroesse und
Tastaturbedienung sind am gerenderten Dokument direkt messbar — der
Browserlauf (`seitenbrowser`) laeuft seit dem 26.08. ohnehin bei jeder
Analyse. **`bf_lighthouse` bleibt aussen vor:** Das Kriterium heisst
„Lighthouse-Accessibility-Score" und **ist** dieser Wert. Ihn durch eine
eigene Zahl zu ersetzen waere keine andere Messung desselben Dings, sondern
ein anderes Kriterium — und damit eine Aenderung am Massstab, die in die
Fassung 2027.1 gehoert.

Damit wandern **5 von 20** PageSpeed-Punkten in die eigene Messung, nicht 8.
Die zuerst notierte Zahl war zu hoch, weil sie `bf_lighthouse` mitzaehlte.

**Lighthouse bleibt die erste Quelle.** Die Eigenmessung greift nur, wenn
PageSpeed nichts geliefert hat — sonst verschoeben sich Punktzahlen im
Bestand, ohne dass sich am Massstab etwas geaendert haette. Welcher Weg
gegriffen hat, steht im Ergebnis.

**Die Zahlenwerte sind bewusst die der Fachnorm**, nicht selbst gewaehlte:
4,5:1 Kontrast fuer gewoehnlichen Text und 3:1 fuer grossen (WCAG 2.1, 1.4.3),
grosser Text ab 24 px oder ab 18,66 px fett. Die Grenze von 12 px fuer die
Schriftgroesse ist die, gegen die auch Lighthouse prueft.

**Am Gegenstand geprueft, nicht am Mock (04.09.2026).** Der erste Lauf gegen
`neovendo.de` meldete **119 von 433** Textstellen mit 1,0:1 — also Weiss auf
Weiss. Das war kein Befund, sondern ein Messfehler: weisse Navigationsschrift
in einem `position: fixed`-Kopf, dessen ganze Ahnenkette durchsichtig ist. Der
Text schwebt ueber fremdem Inhalt, und der steht nicht in seiner Ahnenkette;
die Suche lief bis zum weissen Body durch und rechnete gegen eine **Annahme**.

Die Reihenfolge in `hintergrund` ist deshalb genau so gebaut: erst der eigene
deckende Grund, dann der Abbruch bei einem schwebenden Element. Ein fixierter
Kopf **mit** eigenem Grund bleibt messbar. Nach der Korrektur: 312 messbar,
**18** Verstoesse, 121 nicht bestimmbar — und dieselbe Messung liefert bei
`heise.de` 23 von 882 und bei der eigenen Anmeldeseite 2 von 11.

**Zweimal daneben gelegen, bevor es stimmte.** Der erste Erklaerungsversuch
war ein eingeklapptes Menue ohne Hoehe (Hoehenpruefung eingezogen, aenderte
nichts), der zweite ein Hintergrundbild (aenderte auch nichts). Erst der Blick
auf die tatsaechliche Ahnenkette eines gemeldeten Elements zeigte die Ursache.
"""
import logging

logger = logging.getLogger(__name__)

#: Was im Browser gemessen wird. Bewusst **eine** Auswertung in einem Durchlauf:
#: Jeder zusaetzliche `evaluate`-Aufruf kostet einen Rundlauf, und die Seite
#: soll waehrenddessen nicht weiterlaufen.
MESSSKRIPT = r"""
() => {
  const grenzeKlein = 4.5, grenzeGross = 3.0, grenzeSchrift = 12;

  const kanal = (c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  };
  const leuchtdichte = ([r, g, b]) =>
    0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b);
  const zahlen = (farbe) => {
    const m = (farbe || '').match(/[\d.]+/g);
    return m ? m.map(Number) : null;
  };
  const deckend = (farbe) => {
    const t = zahlen(farbe);
    return t && (t.length < 4 || t[3] >= 0.95) ? t.slice(0, 3) : null;
  };
  const verhaeltnis = (v, h) => {
    const a = leuchtdichte(v), b = leuchtdichte(h);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  };

  // Der Hintergrund eines Elements ist oft der seines Vorfahren. Steht auf
  // dem Weg ein Hintergrundbild, laesst sich der Kontrast aus Farben allein
  // nicht bestimmen — dann wird nicht geraten, sondern nicht gezaehlt.
  const hintergrund = (el) => {
    let n = el;
    while (n && n.nodeType === 1) {
      const s = getComputedStyle(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;
      const t = deckend(s.backgroundColor);
      if (t) return t;
      // **Erst hier, nicht frueher.** Ein schwebendes Element mit eigenem
      // deckendem Grund ist messbar — das faengt die Zeile darueber ab. Hat
      // es keinen, liegt es ueber fremdem Inhalt, und der steht nicht in
      // seiner Ahnenkette: Der weisse Body weiter oben ist dann eine Annahme
      // und kein Messwert.
      if (['fixed', 'absolute', 'sticky'].includes(s.position)) return null;
      n = n.parentElement;
    }
    return [255, 255, 255];
  };

  // Ein eingeklapptes Menue ist sichtbar im Sinne von `display`, hat aber
  // keine Hoehe — und traegt oft weisse Schrift, die erst spaeter auf dunklem
  // Grund steht. Ohne die Hoehenpruefung meldete die Messung an
  // `neovendo.de` **119 von 433** Textstellen mit 1,0:1, also Weiss auf
  // Weiss. Am 04.09.2026 an der laufenden Seite gemessen, nicht vermutet.
  const sichtbar = (el, stil) => {
    if (stil.visibility === 'hidden' || stil.display === 'none') return false;
    if (parseFloat(stil.opacity || '1') <= 0.05) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };

  let kontrastGeprueft = 0, kontrastVerstoesse = 0, kontrastOffen = 0;
  let schriftGeprueft = 0, schriftZuKlein = 0;
  const beispiele = [];

  for (const el of document.body ? document.body.querySelectorAll('*') : []) {
    // Nur Elemente mit eigenem sichtbarem Text — sonst zaehlt jeder
    // Container den Text seiner Kinder ein zweites Mal.
    const eigen = Array.from(el.childNodes)
      .filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim())
      .join(' ')
      .trim();
    if (!eigen) continue;

    const stil = getComputedStyle(el);
    if (!sichtbar(el, stil)) continue;

    const groesse = parseFloat(stil.fontSize) || 0;
    if (groesse > 0) {
      schriftGeprueft++;
      if (groesse < grenzeSchrift) schriftZuKlein++;
    }

    const vorne = deckend(stil.color);
    if (!vorne) continue;
    const hinten = hintergrund(el);
    if (!hinten) { kontrastOffen++; continue; }
    const fett = (parseInt(stil.fontWeight, 10) || 400) >= 700;
    const gross = groesse >= 24 || (fett && groesse >= 18.66);
    const wert = verhaeltnis(vorne, hinten);
    kontrastGeprueft++;
    if (wert < (gross ? grenzeGross : grenzeKlein)) {
      kontrastVerstoesse++;
      if (beispiele.length < 3) {
        beispiele.push(eigen.slice(0, 40) + ' (' + wert.toFixed(1) + ':1)');
      }
    }
  }

  // Tastatur: ein Sprungziel am Anfang und keine erzwungene Reihenfolge.
  const fokussierbar = document.querySelectorAll(
    'a[href], button, input, select, textarea, [tabindex]');
  const positiveTabindex = document.querySelectorAll('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])').length;
  let skiplink = false;
  for (const a of Array.from(document.querySelectorAll('a[href^="#"]')).slice(0, 5)) {
    const ziel = (a.getAttribute('href') || '').slice(1);
    if (ziel && document.getElementById(ziel)) { skiplink = true; break; }
  }

  return {
    kontrast_geprueft: kontrastGeprueft,
    kontrast_verstoesse: kontrastVerstoesse,
    kontrast_nicht_messbar: kontrastOffen,
    kontrast_beispiele: beispiele,
    schrift_geprueft: schriftGeprueft,
    schrift_zu_klein: schriftZuKlein,
    fokussierbar: fokussierbar.length,
    positive_tabindex: positiveTabindex,
    skiplink: skiplink,
  };
}
"""


async def messe(seite) -> dict:
    """Die Barrierefreiheitswerte der offenen Seite.

    Scheitert die Auswertung, gibt es `collected: False` — **nicht** Nullen.
    Eine misslungene Messung als „keine Verstoesse gefunden" auszugeben waere
    dieselbe Fehlerfamilie, die diesen Bestand am haeufigsten getroffen hat.
    """
    try:
        roh = await seite.evaluate(MESSSKRIPT)
    except Exception as fehler:      # noqa: BLE001
        logger.info("Barrierefreiheitsmessung im Browser fehlgeschlagen: %s: %s",
                    type(fehler).__name__, fehler)
        return {"collected": False}
    if not isinstance(roh, dict):
        return {"collected": False}
    return {"collected": True, **roh}


# ── Aus der Messung eine Punktzahl ────────────────────────────────────

#: Ab wann ein Kontrasturteil traegt.
#:
#: **Am Gegenstand entstanden (04.09.2026).** Bei `neovendo.de` liessen sich
#: 121 von 433 Textstellen nicht aus Farben bestimmen — weisse Navigation in
#: einem schwebenden Kopf ueber fremdem Inhalt. Ein „0 von 2" auf Grundlage
#: einer Handvoll messbarer Stellen waere ein Urteil ohne Messung; dieselbe
#: Regel wie in § 3.5, wo Nichterhobenes aus Zaehler und Nenner faellt.
MINDESTZAHL = 10
MINDESTANTEIL = 0.5


def kontrast_anteil(a11y: dict):
    """0 oder 1 — wie das Lighthouse-Audit, das dieses Kriterium sonst traegt.

    Lighthouse gibt `color-contrast` binaer aus: bestanden oder nicht. Eine
    feinere Abstufung hier waere kein besserer Ersatz, sondern ein anderer
    Massstab.

    `None` heisst **nicht erhoben** — zu wenige Stellen messbar (siehe
    `MINDESTZAHL`), nicht „keine Verstoesse gefunden".
    """
    if not a11y.get("collected"):
        return None
    geprueft = a11y.get("kontrast_geprueft") or 0
    offen = a11y.get("kontrast_nicht_messbar") or 0
    kandidaten = geprueft + offen
    if geprueft < MINDESTZAHL or not kandidaten:
        return None
    if geprueft / kandidaten < MINDESTANTEIL:
        return None
    return 0.0 if a11y.get("kontrast_verstoesse") else 1.0


def schrift_anteil(a11y: dict):
    """0 oder 1 für `dg_typografie` — Lighthouse prüft `font-size` ebenso binär."""
    if not a11y.get("collected") or not a11y.get("schrift_geprueft"):
        return None
    return 0.0 if a11y.get("schrift_zu_klein") else 1.0


def tastatur_anteil(a11y: dict):
    """0 oder 1 für `bf_tastatur`.

    Gemessen wird, was sich ohne Bedienung feststellen laesst: ein Sprungziel
    am Seitenanfang und keine erzwungene Reihenfolge (`tabindex` groesser 0).
    Eine echte Tastaturfalle findet man nur, indem man durchtabbt — das ist
    hier ausdruecklich **nicht** gemessen, und der Beleg sagt es.
    """
    if not a11y.get("collected") or not a11y.get("fokussierbar"):
        return None
    return 1.0 if (a11y.get("skiplink") and not a11y.get("positive_tabindex")) else 0.0
