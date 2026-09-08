/**
 * Der Facebook-Pixel im Analyse-Widget (Wunsch David, 08.09.2026).
 *
 * Das Widget ist eine einzelne HTML-Datei, die eingebettet auf **fremden**
 * Seiten läuft; es gibt dort keine Bausteine, die man einzeln aufrufen könnte.
 * Geprüft wird deshalb am Text der Datei — grob, aber an genau den drei
 * Eigenschaften, deren Verlust niemandem auffiele:
 *
 *   1. Der Pixel lädt **erst beim Absenden**. Ein Pixel, der beim Anzeigen
 *      lädt, setzt Tracking ohne Einwilligung (§ 25 TTDSG) — und das Widget
 *      bringt auf einer fremden Seite keinen Cookie-Banner mit.
 *   2. Er meldet **einen** Lead, und zwar erst, wenn das Backend die Anfrage
 *      angenommen hat. Sonst laufen Metas Zahl und die Anfragenliste im
 *      Werkzeug auseinander.
 *   3. Die Adressfelder stehen in der Reihenfolge Domain → E-Mail.
 *
 * **Jede Abwesenheits-Prüfung hat hier eine positive daneben.** „Kein
 * PageView" wäre auch dann grün, wenn der ganze Pixel verschwunden ist.
 */
import fs from 'fs';
import path from 'path';

const WIDGET = fs.readFileSync(
  path.join(__dirname, '..', '..', 'public', 'embed', 'audit-widget.html'),
  'utf8',
);

describe('Reihenfolge der Formularfelder', () => {
  test('die Webseiten-Adresse steht vor der E-Mail', () => {
    const url = WIDGET.indexOf('id="kpg-url"');
    const email = WIDGET.indexOf('id="kpg-email"');
    expect(url).toBeGreaterThan(-1);
    expect(email).toBeGreaterThan(-1);
    expect(url).toBeLessThan(email);
  });

  test('beide Felder sind Pflicht geblieben', () => {
    // Die Gegenprobe zur Reihenfolge: Ein Feld, das beim Umstellen sein
    // `required` verliert, stünde weiterhin an der richtigen Stelle.
    expect(WIDGET).toMatch(/id="kpg-url" type="text" required/);
    expect(WIDGET).toMatch(/id="kpg-email" type="email" required/);
  });
});

describe('Wann der Pixel lädt', () => {
  test('das Skript von Facebook kommt genau einmal vor', () => {
    const treffer = WIDGET.match(/connect\.facebook\.net/g) || [];
    expect(treffer).toHaveLength(1);
  });

  test('es steht nicht als eigenes script-Tag im Kopf der Seite', () => {
    // Ein `<script src="…fbevents.js">` im Markup lüde beim Anzeigen — genau
    // das, was hier nicht passieren soll.
    expect(WIDGET).not.toMatch(/<script[^>]+connect\.facebook\.net/);
  });

  test('geladen wird innerhalb von meldeLead', () => {
    // Die positive Hälfte: Das Skript ist da, und es steht in der Funktion,
    // die erst beim Absenden läuft.
    const start = WIDGET.indexOf('function meldeLead()');
    const ende = WIDGET.indexOf('function loadConfig()');
    const skript = WIDGET.indexOf('connect.facebook.net');
    expect(start).toBeGreaterThan(-1);
    expect(skript).toBeGreaterThan(start);
    expect(skript).toBeLessThan(ende);
  });

  test('ohne Pixel-ID passiert nichts', () => {
    expect(WIDGET).toMatch(/if \(!FB_PIXEL_ID \|\| leadGemeldet\) return;/);
  });

  test('die ID kommt aus der Konfiguration und wird dort geprüft', () => {
    expect(WIDGET).toMatch(/cfg\.facebook_pixel_id/);
    expect(WIDGET).toMatch(/\/\^\\d\{10,20\}\$\//);
  });
});

describe('Was gemeldet wird', () => {
  test('genau ein Ereignis, und das ist Lead', () => {
    const ereignisse = [...WIDGET.matchAll(/fbq\('track', '(\w+)'\)/g)]
      .map((t) => t[1]);
    expect(ereignisse).toEqual(['Lead']);
  });

  test('kein PageView — und der Lead ist trotzdem da', () => {
    // Ohne die zweite Zusicherung wäre dieser Test auch dann grün, wenn
    // jemand den Pixel ganz entfernt hätte.
    expect(WIDGET).not.toMatch(/'PageView'/);
    expect(WIDGET).toMatch(/fbq\('track', 'Lead'\)/);
  });

  test('gemeldet wird erst, wenn das Backend die Anfrage angenommen hat', () => {
    const annahme = WIDGET.indexOf("if (!start.poll_token) throw");
    const meldung = WIDGET.indexOf('meldeLead();');
    expect(annahme).toBeGreaterThan(-1);
    expect(meldung).toBeGreaterThan(annahme);
  });

  test('gemeldet wird an genau einer Stelle', () => {
    // Zwei Aufrufe wären zwei Leads für eine Anfrage — die Sperre in der
    // Funktion fängt das zwar ab, aber der zweite Aufruf wäre trotzdem ein
    // Zeichen dafür, dass jemand die Regel nicht kannte.
    const aufrufe = WIDGET.match(/^\s*meldeLead\(\);/gm) || [];
    expect(aufrufe).toHaveLength(1);
  });
});
