/**
 * Eine Statusfarbe als Text gehört an ein Token, nicht an einen Hex-Wert.
 *
 * **Der Befund (31.08.2026, L-17).** Die Browsermessung meldete acht Zeichen
 * unter AA-Kontrast. Gesucht wurde die Ursache zuerst in `tokens.css` — dort
 * war sie nicht: `--success`, `--warn`, `--error` und `--info` bestehen AA in
 * **beiden** Modi, mit 4,69 bis 9,12. Falsch war, dass die Oberfläche sie an
 * **89 Stellen in 28 Dateien** gar nicht benutzt hat, sondern feste
 * Tailwind-Hex-Werte:
 *
 *     Smaragd #059669   3,40      Grün      #16a34a   2,98
 *     Cyan    #0891b2   3,33      Bernstein #d97706   2,88
 *
 * **Zwei Mängel in einem.** Der Kontrast ist der sichtbare; der zweite ist,
 * dass ein fester Wert sich im Dunkelmodus **nicht umstellen kann**. Zwei der
 * acht Farben fallen auch dort durch (4,49 und 4,39).
 *
 * **Warum als Fläche trotzdem erlaubt.** Ein Balken, ein Punkt, der Grund
 * einer Plakette — dort ist die kräftige Farbe richtig und AA für Text gilt
 * nicht. Deshalb prüft dieser Test **je Vorkommen**, welche Eigenschaft links
 * davon steht, und nicht die ganze Zeile: `{ background: '#16a34a', color:
 * '#fff' }` enthält `color:` und ist trotzdem in Ordnung.
 */
import fs from 'fs';
import path from 'path';

const QUELLE = path.join(__dirname, '..');

/** Die Werte, die am 31.08.2026 als Schriftfarbe durchgefallen sind. */
const STATUSFARBEN = [
  '#0891b2', '#059669', '#16a34a', '#d97706',
  '#ca8a04', '#f59e0b', '#10b981', '#22c55e',
];

/** Eigenschaften, deren Wert als Text gerendert wird. */
const FAERBT_TEXT = new Set(['color', 'WebkitTextFillColor', 'caretColor']);

/**
 * **`color:` ist nicht immer ein CSS-Attribut.**
 *
 * In einer Farbtabelle — `{ id: 'phase_5', label: 'QA', color: '#dc7226' }` —
 * ist es ein **Feldname**. Der Wert wandert von dort in Flächen, Ränder und
 * Schatten, oft über Verkettungen wie `${ph.color}20`; an ein `var(…)` lässt
 * sich kein Alpha-Suffix anhängen, das ergäbe ungültiges CSS.
 *
 * Genau daran ist die erste Fassung dieser Umstellung gescheitert: Sie hat
 * 22 Tabellenzeilen mitgenommen und dabei fünf Flächentönungen stillgelegt.
 * Der Test hier hätte das nicht gemerkt — er hätte es beklatscht.
 *
 * Erkannt wird eine Tabellenzeile daran, dass sie einen Schlüssel neben der
 * Farbe trägt und **nicht** in einem `style={{…}}` steht.
 */
const TABELLE = /\b(id|name|key|slug)\s*:/;

const farbe = new RegExp(STATUSFARBEN.join('|'), 'gi');
//: Ein Eigenschaftsname — aber kein `https:`, deshalb darf kein `/` folgen.
const eigenschaft = /([A-Za-z][A-Za-z0-9]*)\s*:(?!\/)/g;

function dateien(verzeichnis) {
  const heraus = [];
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) heraus.push(...dateien(voll));
    else if (/\.(js|jsx)$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) {
      heraus.push(voll);
    }
  }
  return heraus;
}

/** Jedes Vorkommen einer Statusfarbe, mit der Eigenschaft, die sie steuert. */
function vorkommen() {
  const heraus = [];
  for (const datei of dateien(QUELLE)) {
    const zeilen = fs.readFileSync(datei, 'utf8').split('\n');
    zeilen.forEach((zeile, i) => {
      for (const treffer of zeile.matchAll(farbe)) {
        const namen = [...zeile.matchAll(eigenschaft)]
          .filter(e => e.index + e[0].length <= treffer.index);
        heraus.push({
          ort: `${path.relative(QUELLE, datei)}:${i + 1}`,
          wert: treffer[0].toLowerCase(),
          name: namen.length ? namen[namen.length - 1][1] : null,
          istTabelle: TABELLE.test(zeile) && !zeile.includes('style={{'),
        });
      }
    });
  }
  return heraus;
}

describe('Statusfarben als Schriftfarbe', () => {
  const alle = vorkommen();

  test('der Ausdruck findet überhaupt noch etwas', () => {
    // Ohne diese Zusicherung wäre der Test darunter auch dann grün, wenn die
    // Farbwerte umbenannt würden und nichts mehr trifft. Genau so war der
    // Kontrast-Wächter am 30.08. grün: Er las eine Form, die es nicht mehr
    // gab, und übersprang alles.
    expect(alle.length).toBeGreaterThan(50);
  });

  test('keine Statusfarbe steht fest eingetragen als Schriftfarbe da', () => {
    const alsText = alle
      .filter(v => FAERBT_TEXT.has(v.name) && !v.istTabelle)
      .map(v => `${v.ort}  ${v.name}: ${v.wert}`);

    expect(alsText).toEqual([]);
  });

  test('die Farbtabellen sind gezählt und wachsen nicht unbemerkt', () => {
    // **Kein Freibrief, sondern ein Merkzettel.** Eine Tabellenfarbe kann
    // sehr wohl als Text erscheinen — im Zählabzeichen der Projektpipeline
    // tut sie es, und genau dort stand die orange „0" aus der Messung. Die
    // Lösung dort ist ein **zweites Feld** neben `color`, nicht ein Token an
    // seiner Stelle: Der Balken darf kräftig sein, die Ziffer muss lesbar
    // sein.
    //
    // Solange nicht jede Tabelle das hat, hält diese Zahl den Rest fest.
    const tabellen = alle.filter(v => v.istTabelle);

    expect(tabellen.length).toBe(19);
  });

  test('als Fläche kommen sie weiter vor — sonst hätte der Test oben nichts geprüft', () => {
    // Die positive Gegenprobe zur Absenz. Wären auch die Flächen migriert,
    // stünde hier 0, und „keine als Text" wäre eine Aussage über eine leere
    // Menge.
    const alsFlaeche = alle.filter(
      v => v.name && (/ackground/.test(v.name) || v.name === 'fill'),
    );

    expect(alsFlaeche.length).toBeGreaterThan(20);
  });
});
