/**
 * Kein Knopf, dessen einzige Wirkung eine Erfolgsmeldung ist.
 *
 * **Der Anlass (26.08.2026, Rest von L-18).** Unter Einstellungen →
 * Benachrichtigungen standen zwei „Speichern"-Knöpfe:
 *
 *     <Btn onClick={() => toast.success('Einstellungen gespeichert')}>
 *
 * Sechs Ankreuzfelder für Mailbenachrichtigungen und ein vollständiges
 * SMTP-Formular samt **Passwortfeld** — und beide Knöpfe meldeten grün
 * „gespeichert", ohne irgendetwas zu senden. Nichts im Backend liest die
 * sechs Schlüssel (`new_lead`, `daily_report`, …); es gab also nicht einmal
 * eine Stelle, an die sie hätten gehen können.
 *
 * **Warum das schlimmer ist als ein fehlender Knopf.** Ein fehlender Knopf
 * fällt auf. Ein Knopf, der Erfolg meldet, beendet die Suche: Wer die
 * Ankreuzfelder gesetzt und „gespeichert" gelesen hat, wundert sich Wochen
 * später, warum keine Mail kommt — und sucht überall, nur nicht hier. Es ist
 * dieselbe Familie wie die Marge, die aussah wie eine Messung, und wie das
 * PDF, das einen Beruf riet: eine Behauptung an einer Stelle, die wie ein
 * Ergebnis gelesen wird.
 *
 * **Was der Wächter prüft.** Einen Pfeilausdruck, dessen **ganzer Rumpf**
 * eine Erfolgsmeldung ist. Steht daneben ein `apiCall`, ein `fetch` oder ein
 * `setState`, ist es keine leere Behauptung, sondern eine Meldung über etwas,
 * das geschehen ist — dann schlägt er nicht an.
 *
 * Gegengeprüft: Mit der alten Zeile wieder eingesetzt wird er rot.
 */
const fs = require('fs');
const path = require('path');

const WURZEL = path.join(__dirname, '..');

/** Meldungen, die einen abgeschlossenen Vorgang behaupten. */
const BEHAUPTUNG = /toast\.success\(/;

/**
 * Kommentare ausblenden, bevor gesucht wird.
 *
 * **Der Waechter fand sich selbst (26.08.2026).** `MeldungsVorlieben.jsx`
 * erklaert in seinem Kopf, was hier frueher stand — samt der Zeile
 * `onClick={() => toast.success(...)}`. Prompt stand die Datei im Befund.
 *
 * Das ist Muster 2 der eigenen Messfehler, woertlich: Zwei Waechter haben
 * sich schon einmal in ihrer eigenen Beschreibung gefunden. Das Backend hat
 * dafuer laengst `tools/adressen.ohne_kommentare` — hier fehlte es.
 *
 * Ein Zustandsautomat statt eines Musters: `https://` enthaelt `//`, und ein
 * Muster, das darauf anspringt, zerschneidet jede Adresse in einer
 * Zeichenkette.
 */
function ohneKommentare(quelltext) {
  let raus = '';
  let i = 0;
  while (i < quelltext.length) {
    const zwei = quelltext.slice(i, i + 2);
    if (zwei === '//') {
      while (i < quelltext.length && quelltext[i] !== '\n') i += 1;
    } else if (zwei === '/*') {
      i += 2;
      while (i < quelltext.length && quelltext.slice(i, i + 2) !== '*/') i += 1;
      i += 2;
    } else if (quelltext[i] === '"' || quelltext[i] === "'" || quelltext[i] === '`') {
      const ende = quelltext[i];
      raus += quelltext[i];
      i += 1;
      while (i < quelltext.length && quelltext[i] !== ende) {
        if (quelltext[i] === '\\') { raus += quelltext[i]; i += 1; }
        raus += quelltext[i];
        i += 1;
      }
      raus += ende;
      i += 1;
    } else {
      raus += quelltext[i];
      i += 1;
    }
  }
  return raus;
}

function dateien(verzeichnis) {
  return fs.readdirSync(verzeichnis, { withFileTypes: true }).flatMap((e) => {
    const voll = path.join(verzeichnis, e.name);
    if (e.isDirectory()) return dateien(voll);
    return /\.(jsx?|tsx?)$/.test(e.name) && !/\.test\./.test(e.name) ? [voll] : [];
  });
}

/**
 * Findet `() => toast.success(…)` als vollständigen Rumpf.
 *
 * Bewusst nicht mit einem Muster über den ganzen Rumpf: Ein Ausdruck wie
 * `() => { a(); toast.success(…) }` ist erlaubt, weil `a()` etwas tut. Es
 * wird deshalb ab dem Pfeil geklammert gezählt und geprüft, ob zwischen
 * Pfeil und Ende **nur** die Meldung steht.
 */
function leereVersprechen(quelltext) {
  const funde = [];
  const pfeil = /=>\s*/g;
  let treffer;

  while ((treffer = pfeil.exec(quelltext)) !== null) {
    const start = treffer.index + treffer[0].length;
    if (!quelltext.startsWith('toast.success(', start)) continue;

    // `.then(() => toast.success(…))` ist keine leere Behauptung: Die
    // Handlung ist geschehen, sonst waere der Rueckruf nicht gelaufen.
    // Diese beiden Faelle (Einbaucode und Webhook-URL in die Zwischenablage)
    // hat die erste Fassung des Waechters mitgezaehlt.
    const davor = quelltext.slice(Math.max(0, treffer.index - 40), treffer.index);
    if (/\.(then|catch|finally)\(\s*\(?\)?\s*$/.test(davor)) continue;

    // Bis zur schliessenden Klammer der Meldung zaehlen — ein Betreff darf
    // selbst Klammern enthalten.
    let tiefe = 0;
    let i = start + 'toast.success'.length;
    for (; i < quelltext.length; i += 1) {
      if (quelltext[i] === '(') tiefe += 1;
      else if (quelltext[i] === ')') {
        tiefe -= 1;
        if (tiefe === 0) break;
      }
    }

    // Was direkt danach kommt, entscheidet: Endet der Pfeilausdruck hier,
    // war die Meldung alles, was der Knopf tut.
    const danach = quelltext.slice(i + 1, i + 3).trim();
    if (danach.startsWith('}') || danach.startsWith(')')) {
      funde.push(quelltext.slice(start, i + 1));
    }
  }
  return funde;
}

describe('Kein Knopf verspricht etwas, das nicht geschieht', () => {
  const quellen = dateien(WURZEL).map(
    (p) => [p, ohneKommentare(fs.readFileSync(p, 'utf8'))],
  );

  test('es gibt Quelldateien zu pruefen', () => {
    // Ohne diese Zusicherung waere ein leerer Suchlauf gruen — der Fehler,
    // der in diesem Bestand schon zweimal einen Waechter wertlos gemacht hat.
    expect(quellen.length).toBeGreaterThan(50);
    expect(quellen.some(([, q]) => BEHAUPTUNG.test(q))).toBe(true);
  });

  test('keine Erfolgsmeldung ohne Vorgang dahinter', () => {
    const funde = quellen.flatMap(([datei, quelltext]) =>
      leereVersprechen(quelltext).map(
        (stelle) => `${path.relative(WURZEL, datei)}: ${stelle}`,
      ),
    );

    expect(funde).toEqual([]);
  });
});
