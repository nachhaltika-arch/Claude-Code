/**
 * Die Markenfarben stehen in der Tailwind-Vorgabe (L-158).
 *
 * **Der Befund vom 04.09.2026.** `#004F59` kam an 19 Stellen im Quelltext vor,
 * `#FAE600` an 14 — und `tailwind.config.js` kannte **beide nicht**. Im
 * Werkzeug waren die Markenfarben damit Handarbeit statt Vorgabe: nicht
 * zentral änderbar, nicht prüfbar, nicht wiederverwendbar.
 *
 * **Warum die Vorgabe und nicht die Löschung.** Der Eintrag ließ beides offen:
 * „Entweder die Farben kommen als benannte Werte in die Vorgabe, oder sie
 * verschwinden aus dem Quelltext." Für `--kc-dark` und `--kc-yellow` ist die
 * Antwort keine Frage — die UI-Guidelines v1.0 machen Dark Teal zur
 * dominierenden Farbe und Gelb zum Akzent, der höchstens einmal je Bildschirm
 * vorkommt. Was eine Rolle im System hat, gehört in die Vorgabe.
 *
 * **Der eigentliche Wert liegt in der Verbindung.** `tokens.css` ist die
 * Quelle für alles, was zur Laufzeit gilt; `tailwind.config.js` für alles, was
 * beim Bauen entsteht. Zwei Orte für dieselben Farben laufen auseinander — und
 * genau das war passiert. Dieser Test hält sie zusammen.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');
const TOKENS = fs.readFileSync(path.join(WURZEL, 'styles', 'tokens.css'), 'utf8');
const CONFIG = fs.readFileSync(path.join(WURZEL, '..', 'tailwind.config.js'), 'utf8');

/** Die Palettenfarben aus dem Hellsatz — `--kc-<name>: #RRGGBB`. */
function markenfarben() {
  const wurzel = TOKENS.slice(0, TOKENS.indexOf('@media'));
  return [...wurzel.matchAll(/--kc-([a-z]+):\s*(#[0-9a-fA-F]{6})/g)]
    .map((m) => ({ name: m[1], wert: m[2].toUpperCase() }));
}

describe('Die Markenfarben sind eine Vorgabe, keine Handarbeit', () => {
  const farben = markenfarben();

  test('tokens.css führt überhaupt Markenfarben', () => {
    // Ein Wächter, der seinen Gegenstand nicht findet, ist immer grün.
    expect(farben.length).toBeGreaterThanOrEqual(3);
  });

  test.each(farben.map((f) => [f.name, f.wert]))(
    '--kc-%s (%s) steht in der Tailwind-Vorgabe', (name, wert) => {
      // Groß- und Kleinschreibung ist bei Hexwerten dieselbe Farbe — der
      // Vergleich darf daran nicht scheitern.
      expect(CONFIG.toUpperCase()).toContain(wert);
    });

  test('die Vorgabe nennt sie beim Namen, nicht nur als Zahl', () => {
    // Ein Hexwert ohne Namen ist in einer Vorgabe so wenig wiederverwendbar
    // wie im Quelltext — er wäre nur umgezogen.
    expect(CONFIG).toMatch(/dark:\s*['"]#004F59['"]/i);
    expect(CONFIG).toMatch(/(gelb|yellow):\s*['"]#FAE600['"]/i);
  });
});
