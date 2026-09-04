/**
 * Kein Token darf auf sich selbst zeigen.
 *
 * **Der Befund vom 30.08.2026 (L-17).** Sechs Token standen so in
 * `tokens.css`:
 *
 *     --kc-mid-a-12: var(--kc-mid-a-12);
 *
 * Das ist ein Ringschluss, und CSS behandelt ihn als *invalid at
 * computed-value time*: Das Token löst zu **nichts** auf, und **jede**
 * Deklaration, die es benutzt, fällt ersatzlos weg. Im Browser gemessen
 * ergaben alle sechs `""`.
 *
 * **Warum das nicht auffiel.** Ein Schatten, der wegfällt, sieht aus wie
 * „kein Schatten vorgesehen". Nichts wird rot, nichts bricht, kein Test
 * schlug an — die Oberfläche ist nur stiller, als jemand sie gebaut hat.
 * 41 Verwendungen in 17 Dateien waren betroffen, seit dem 09.05.2026.
 *
 * **Was dadurch wirklich fehlte:** die Fokusmarke jedes Eingabefelds.
 * `input:focus, select:focus, textarea:focus` setzt `outline: none` und
 * ersetzt sie durch `box-shadow: 0 0 0 3px var(--kc-mid-a-12)`. Fällt der
 * Schatten weg, bleibt nur das `outline: none` — ein Feld, das den Fokus
 * annimmt und ihn nicht zeigt (WCAG 2.4.7, Stufe AA).
 *
 * **Warum ein Wächter und keine einmalige Korrektur.** Der Selbstbezug ist
 * beim Zusammenfassen der Alpha-Token entstanden, also bei genau der Art
 * Aufräumarbeit, die es wieder geben wird. Diese Prüfung ist billig und
 * eindeutig: Ein Token, dessen Wert seinen eigenen Namen nennt, ist immer
 * ein Fehler — es gibt keinen Fall, in dem das gemeint wäre.
 *
 * Geprüft werden **alle** `.css` unter `src/`, nicht nur `tokens.css`: Ein
 * Selbstbezug wirkt gleich, egal wo er steht.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');

function cssDateien(verzeichnis, treffer = []) {
  for (const eintrag of fs.readdirSync(verzeichnis, { withFileTypes: true })) {
    const voll = path.join(verzeichnis, eintrag.name);
    if (eintrag.isDirectory()) cssDateien(voll, treffer);
    else if (eintrag.name.endsWith('.css')) treffer.push(voll);
  }
  return treffer;
}

/**
 * Jede Deklaration `--name: wert;` einer Datei — **ohne Kommentare**.
 *
 * Der erste Lauf dieses Wächters wurde rot und hatte recht: Er fand
 * `--kc-mid-a-12: var(--kc-mid-a-12)` — im **Kommentar über der Reparatur**,
 * der den Fehler beschreibt. Dieselbe Familie wie bei den Zählwerkzeugen im
 * Backend: Wer über den Rohtext sucht, misst den Text und nicht die Sache.
 * Deshalb fallen `/* … *\/`-Blöcke vorher heraus.
 */
function ohneKommentare(css) {
  return css.replace(/\/\*[\s\S]*?\*\//g, ' ');
}

function deklarationen(css) {
  const gefunden = [];
  const muster = /(--[a-z0-9-]+)\s*:\s*([^;{}]+);/g;
  let treffer;
  while ((treffer = muster.exec(ohneKommentare(css))) !== null) {
    gefunden.push({ name: treffer[1], wert: treffer[2].trim() });
  }
  return gefunden;
}

describe('Design-Tokens zeigen nicht auf sich selbst', () => {
  const dateien = cssDateien(WURZEL);

  test('es gibt überhaupt CSS-Dateien zu prüfen', () => {
    // Eine Abwesenheits-Zusicherung ohne diese Zeile wäre auch dann grün,
    // wenn der Suchlauf nichts findet — etwa nach einem Umzug der Ordner.
    expect(dateien.length).toBeGreaterThan(0);
  });

  test('kein Token nennt seinen eigenen Namen im Wert', () => {
    const ring = [];
    for (const datei of dateien) {
      const css = fs.readFileSync(datei, 'utf8');
      for (const { name, wert } of deklarationen(css)) {
        if (wert.includes(`var(${name})`)) {
          ring.push(`${path.relative(WURZEL, datei)}: ${name}: ${wert}`);
        }
      }
    }
    expect(ring).toEqual([]);
  });

  test('die sechs Alpha-Token tragen einen echten Wert', () => {
    // Die positive Zusicherung neben der Abwesenheit: Der Test oben bliebe
    // auch grün, wenn jemand die Token ersatzlos löscht — und dann wäre
    // die Fokusmarke wieder weg, nur auf einem anderen Weg.
    const tokens = fs.readFileSync(path.join(WURZEL, 'styles', 'tokens.css'), 'utf8');
    const karte = new Map(deklarationen(tokens).map(d => [d.name, d.wert]));

    for (const stufe of ['08', '12', '20', '25', '30', '50']) {
      const name = `--kc-mid-a-${stufe}`;
      expect(karte.has(name)).toBe(true);
      expect(karte.get(name)).toMatch(/^rgba\(0,\s*142,\s*170,\s*0\.\d+\)$/);
    }
  });

  test('die Fokusmarke der Eingabefelder hängt an einem dieser Token', () => {
    // Warum diese Prüfung hier steht und nicht bei den Tastaturtests: Sie
    // hält den **Grund** fest, aus dem die Token einen Wert brauchen. Wer
    // die Regel eines Tages umschreibt, soll hier vorbeikommen.
    const index = fs.readFileSync(path.join(WURZEL, 'index.css'), 'utf8');
    const regel = index.match(
      /input:focus,\s*select:focus,\s*textarea:focus\s*\{[^}]*\}/,
    );
    expect(regel).not.toBeNull();
    expect(regel[0]).toContain('outline: none');
    expect(regel[0]).toMatch(/box-shadow:[^;]*var\(--kc-mid-a-\d+\)/);
  });
});
