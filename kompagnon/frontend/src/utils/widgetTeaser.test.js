/**
 * Der Teaser im Analyse-Widget (Entwurf David, 10.09.2026).
 *
 * Der Entwurf „Teaser Audit + Check PLUS" ändert den Trichter an zwei
 * Stellen: Die Mängelliste verschwindet, und an die Stelle des Terminknopfs
 * tritt ein bezahltes Angebot — Check PLUS, 249 € netto, mit Anrechnung auf
 * einen Websprint.
 *
 * **Geprüft werden Eigenschaften, nicht Wortlaut** — wie in
 * `widgetPixel.test.js`. Der Text darf umformuliert, die Reihenfolge geändert
 * werden. Was nicht wanken darf, sind vier Zusicherungen:
 *
 *   1. **Kein Preis im Widget.** Er kommt aus der Katalogzeile über
 *      `/api/widget/config`. Eine Zahl im Quelltext wäre eine zweite
 *      Preisquelle (L-29) an der Stelle mit der geringsten Sichtbarkeit:
 *      eingebettet auf fremden Seiten, wo sie niemandem auffällt.
 *   2. **Kein Knopf ohne Ziel.** Ist das Produkt Entwurf oder fehlt die
 *      Kaufadresse, zeigt der Block keinen Kaufknopf. Ein Knopf in eine 404
 *      ist schlimmer als keiner — er wird nicht gemeldet.
 *   3. **Netto und brutto stehen beide da.** Der Entwurf zeigt netto, die
 *      Kasse bucht brutto ab. Genau diese Lücke war L-61.
 *   4. **Die Mängelliste ist fort** — und der Punktestand ist es nicht.
 *      Ohne die zweite Hälfte wäre die Prüfung auch dann grün, wenn das
 *      ganze Ergebnis verschwindet.
 */
import fs from 'fs';
import path from 'path';

const WIDGET = fs.readFileSync(
  path.join(__dirname, '..', '..', 'public', 'embed', 'audit-widget.html'),
  'utf8',
);

/** Der Rumpf einer Funktion — unabhängig von ihrer Unterschrift. */
function rumpf(name) {
  const start = WIDGET.indexOf('function ' + name);
  if (start < 0) return '';
  const naechste = WIDGET.indexOf('\n  function ', start + 10);
  return WIDGET.slice(start, naechste > 0 ? naechste : start + 6000);
}

const ERGEBNIS = rumpf('renderResult');

/**
 * Der Angebotsblock steht in einer **eigenen** Funktion, nicht in
 * `renderResult`. Der erste Anlauf dieser Datei suchte ihn dort und wurde
 * rot, obwohl alles gebaut war — ein Wächter, der auf die falsche Stelle
 * zeigt, meldet einen Fehler, den es nicht gibt. Damit beide nicht
 * auseinanderlaufen, prüft `ruft den Angebotsblock auf` unten, dass
 * `renderResult` ihn tatsächlich einsetzt.
 */
const ANGEBOT = rumpf('checkPlusHtml');

describe('Der Teaser baut auf dem Ergebnis auf', () => {
  test('renderResult ist auffindbar', () => {
    // Positive Probe zuerst: ohne sie sind alle Abwesenheits-Prüfungen
    // unten auch dann grün, wenn die Funktion verschwindet.
    expect(ERGEBNIS.length).toBeGreaterThan(400);
  });

  test('der Punktestand wird weiterhin gezeigt', () => {
    expect(ERGEBNIS).toMatch(/total_score/);
    expect(ERGEBNIS).toMatch(/kpg-balken/);
  });

  test('die Mängelliste wird nicht mehr gebaut', () => {
    // Der Teaser liefert top_issues weiterhin — der Entwurf zeigt sie nicht
    // mehr, weil sie den Befund verschenkt, der verkauft werden soll.
    expect(ERGEBNIS).not.toMatch(/top_issues/);
  });

  test('die Ausschlussgründe bleiben', () => {
    // Sie sind kein Befund, sondern eine Einschränkung der Bewertung.
    expect(ERGEBNIS).toMatch(/blocker_count/);
  });
});

describe('Das Check-PLUS-Angebot', () => {
  test('kommt aus der Konfiguration', () => {
    expect(WIDGET).toMatch(/check_plus/);
    expect(ANGEBOT).toMatch(/preis_netto/);
    expect(ANGEBOT).toMatch(/preis_brutto/);
  });

  test('renderResult ruft den Angebotsblock auf', () => {
    // Die Klammer zwischen beiden Prüfbereichen: Ohne sie wäre alles oben
    // grün, auch wenn der Block nirgends eingesetzt wird.
    expect(ERGEBNIS).toMatch(/checkPlusHtml\(\)/);
  });

  test('trägt keinen Preis im Quelltext', () => {
    // Die eigentliche Zusicherung. 249 ist der heutige Wert; jede feste
    // Zahl neben einem Euro-Zeichen wäre dieselbe Falle.
    expect(WIDGET).not.toMatch(/249/);
    expect(WIDGET).not.toMatch(/\d+[.,]?\d*\s*&euro;/);
  });

  test('zeigt keinen Kaufknopf ohne Verfügbarkeit', () => {
    expect(ANGEBOT).toMatch(/verfuegbar/);
  });

  test('nennt die Leistungen aus dem Katalog', () => {
    expect(ANGEBOT).toMatch(/leistungen/);
  });

  test('nennt die Anrechnung', () => {
    expect(ANGEBOT).toMatch(/anrechnung_monate/);
  });

  test('fehlt das Angebot, fehlt der Block', () => {
    // `check_plus` ist null, solange es das Produkt nicht gibt — dann darf
    // kein leerer Kasten stehenbleiben.
    expect(ANGEBOT).toMatch(/CHECK_PLUS\s*&&|if\s*\(\s*!\s*CHECK_PLUS/);
  });
});

describe('Die Fußzeile', () => {
  test('trägt den Datenschutzlink', () => {
    expect(WIDGET).toMatch(/kpg-privacy/);
    expect(WIDGET).toMatch(/privacy_url/);
  });
});
