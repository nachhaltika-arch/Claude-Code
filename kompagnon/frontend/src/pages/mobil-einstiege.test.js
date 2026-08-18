/**
 * Kein gebauter Bildschirm ohne Weg dorthin.
 *
 * UX-43: `m-leads`, `m-projekte` und `m-settings` waren geroutet, aber **von
 * nirgends verlinkt** — weder aus der Mobilleiste noch aus dem „Mehr"-Fach.
 * Wer sie doch aufrief (Lesezeichen, geteilter Link), sah auf dem Desktop
 * eine leere Seite; das ist heute Vormittag behoben worden (UX-35).
 *
 * Entfernt statt angebunden, weil sie doppeln, was es schon gibt:
 *
 * - `m-settings` gegen `SettingsLayout`, das unter `/app/settings` eine
 *   **eigene** Mobilansicht rendert (`if (isMobile)`) und im „Mehr"-Fach
 *   verlinkt ist.
 * - `m-leads` und `m-projekte` gegen die Ziele, die die Mobilleiste direkt
 *   anbietet (Projektpipeline, Alle Projekte, Betriebe, Tickets).
 *
 * Geblieben ist `MobileVertrieb`: Das ist der Einstieg, auf den die
 * Mobilleiste unter „Vertrieb" tatsächlich zeigt.
 */
import fs from 'fs';
import path from 'path';

const APP = fs.readFileSync(path.join(__dirname, '..', 'App.jsx'), 'utf8');

describe('Mobil-Einstiege', () => {
  test.each(['m-leads', 'm-projekte', 'm-settings'])(
    'die unverlinkte Adresse %s ist fort', (pfad) => {
      expect(APP).not.toMatch(new RegExp(`path="${pfad}"`));
    },
  );

  test.each(['MobileLeads.jsx', 'MobileProjekte.jsx', 'MobileSettings.jsx'])(
    '%s liegt nicht mehr herum', (datei) => {
      expect(fs.existsSync(path.join(__dirname, datei))).toBe(false);
    },
  );

  test('der Einstieg, auf den die Mobilleiste zeigt, bleibt', () => {
    expect(APP).toMatch(/path="vertrieb"/);
    expect(fs.existsSync(path.join(__dirname, 'MobileVertrieb.jsx'))).toBe(true);
  });
});
