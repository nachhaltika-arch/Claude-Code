/**
 * Eine Ablagefläche für Dateien braucht einen Weg ohne Maus (L-17).
 *
 * **Entstanden aus einem Verdacht, der sich nicht bestätigt hat — und der
 * Weg dorthin ist der Grund, warum es die Datei gibt.** Vier Ablageflächen
 * tragen ein `onClick`, das den Dateiauswahl-Dialog öffnet. Bei zweien — den
 * Kopien von `ProjectFilesSection.jsx` — steht das `<input type="file">` auf
 * `display: none`, was es aus der Tabulatorreihenfolge nimmt. Das sah nach
 * genau dem Mangel aus, den `portal/FileUploadSection.jsx` am 31.08. behoben
 * hat, und ich habe ihn entsprechend „repariert".
 *
 * **Die Gegenprobe hat mich widerlegt.** Der Wächter blieb grün, als ich den
 * `display: none` wieder einbaute — zu Recht: Beide Dateien haben einen
 * echten `<button>+ Datei hochladen</button>`, der die Eingabe auslöst. Sie
 * waren nie mausgebunden. Meine Änderung hätte sogar geschadet: eine
 * unsichtbare, aber fokussierbare Eingabe **neben** einem sichtbaren Knopf
 * ist ein zweiter Tabulatorhalt für dieselbe Handlung. Zurückgenommen.
 *
 * **Was bleibt, ist die Regel** — und die ist es wert, festgehalten zu
 * werden, weil sie zwei Bauarten unterscheidet, die gleich aussehen:
 *
 * * Verstecktes `<input type="file">` **mit** auslösendem `<button>`:
 *   richtig. Der Knopf ist mit der Tastatur erreichbar, die Eingabe dahinter
 *   ist bloß die Mechanik. So bauen es `ProjectFilesSection.jsx` (beide),
 *   `GrapesEditor.jsx` und `WebsiteDesigner.jsx`.
 * * Verstecktes `<input type="file">` **ohne** solchen Knopf, nur mit einer
 *   klickbaren Fläche darüber: mausgebunden, WCAG 2.1.1 Stufe A. Das war der
 *   Fall im Kundenportal, den der 31.08. behoben hat.
 *
 * Der Unterschied ist ein einziges Element und mit bloßem Auge nicht zu
 * sehen. Genau dafür ist ein Wächter da.
 */
import fs from 'fs';
import path from 'path';

const QUELLE = path.join(__dirname, '..');

function dateien(ordner = QUELLE, gesammelt = []) {
  for (const eintrag of fs.readdirSync(ordner, { withFileTypes: true })) {
    const voll = path.join(ordner, eintrag.name);
    if (eintrag.isDirectory()) dateien(voll, gesammelt);
    else if (/\.jsx?$/.test(eintrag.name) && !/\.test\./.test(eintrag.name)) gesammelt.push(voll);
  }
  return gesammelt;
}

/**
 * Dateien mit einer mausgebundenen Ablagefläche über einer versteckten
 * Eingabe.
 *
 * Gesucht wird die Kombination, nicht eines von beidem: ein `onDrop` (also
 * eine Ablagefläche), ein `<input type="file">` mit `display: none`, und
 * **kein** `<button>`, der den Dialog öffnet.
 */
function nurMitMaus() {
  const fund = [];
  for (const datei of dateien()) {
    const text = fs.readFileSync(datei, 'utf8');
    if (!/onDrop/.test(text)) continue;
    if (!/type="file"/.test(text)) continue;

    const versteckt = /type="file"[\s\S]{0,300}?display:\s*'none'/.test(text)
      || /display:\s*'none'[\s\S]{0,300}?type="file"/.test(text);
    if (!versteckt) continue;

    // Ein Knopf, der die Eingabe auslöst, macht sie erreichbar.
    const knopfLoest = /<button[\s\S]{0,400}?current\??\.?\.?click\(\)/.test(text);
    if (knopfLoest) continue;

    fund.push(path.relative(QUELLE, datei));
  }
  return fund;
}

test('der Quellbaum wird überhaupt gelesen', () => {
  // Ein Wächter, der seinen Gegenstand nicht findet, ist immer grün.
  expect(dateien().length).toBeGreaterThan(100);
});

test('es gibt überhaupt Ablageflächen zu prüfen', () => {
  // Die positive Zusicherung daneben: Fände der Ausdruck `onDrop` nichts
  // mehr — weil eine Schreibweise sich geändert hat —, wäre der Test unten
  // auch grün und hätte nichts geprüft.
  const mitAblage = dateien().filter(d => /onDrop/.test(fs.readFileSync(d, 'utf8')));
  expect(mitAblage.length).toBeGreaterThanOrEqual(4);
});

test('keine Ablagefläche ist der einzige Weg zur Datei', () => {
  expect(nurMitMaus()).toEqual([]);
});
