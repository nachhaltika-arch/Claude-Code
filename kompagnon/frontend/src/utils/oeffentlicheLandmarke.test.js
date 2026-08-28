/**
 * Jede öffentliche Seite trägt eine Landmarke (L-17, Gruppe Tastatur).
 *
 * **Was Lighthouse unter `bypass` prüft** — eine der vier Prüfungen der
 * Gruppe „tastatur" in `audit_pagespeed.A11Y_AUDIT_GROUPS`, die unser eigenes
 * Audit bei Kunden anwendet: Kann eine Tastaturbedienung die Navigation
 * überspringen? Erfüllt ist das durch einen Sprunglink **oder** eine
 * Landmarke.
 *
 * **Der Stand am 28.08.2026.** `AppLayout` hatte seit jeher ein `<main>` —
 * alles unter `/app` war also in Ordnung. **Sechzehn öffentliche Seiten hatten
 * keins:** Login, Registrierung, Passwort zurücksetzen, Mailbestätigung, Shop
 * und Dankeseite, Portalanmeldung, Kundenportal, Impressum, Datenschutz,
 * Bestellweg, Freigabeseite, Zertifikat — und `Barrierefreiheit.jsx`, die
 * Erklärung selbst.
 *
 * **Die drei anderen Prüfungen der Gruppe waren schon sauber**, und das ist
 * nachgemessen statt angenommen: kein `tabIndex` grösser als 0 (null Treffer),
 * kein `accesskey` (null), kein `meta http-equiv="refresh"` (null). Sie stehen
 * unten trotzdem als Test — eine Klasse, die heute leer ist, bleibt es nur,
 * wenn jemand hinsieht. Dieselbe Überlegung wie bei `image-alt` am 26.08.
 *
 * **Warum am Routenbaum geprüft wird und nicht an den Seiten.** Eine Seite
 * kann ein `<main>` haben und trotzdem nie gerendert werden; und eine neue
 * Seite entsteht als Route, nicht als Datei. Der Routenbaum ist die Stelle, an
 * der die Lücke entsteht.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..');
const APP = path.join(WURZEL, 'App.jsx');
const quelle = fs.readFileSync(APP, 'utf8');

/**
 * Routen mit absolutem Pfad ausserhalb von `/app`. Kindrouten (`path="deals"`)
 * liegen in der App-Hülle und sind durch deren `<main>` gedeckt.
 */
function oeffentlicheRouten() {
  const gefunden = [];
  const muster = /<Route\s+path="(\/[^"]*)"\s+element=\{([\s\S]*?)\}\s*\/>/g;
  let treffer;
  while ((treffer = muster.exec(quelle)) !== null) {
    const [, pfad, element] = treffer;
    if (pfad.startsWith('/app')) continue;
    gefunden.push({ pfad, element: element.trim() });
  }
  return gefunden;
}

/** Reine Umleitungen rendern nichts, was jemand mit der Tastatur bedient. */
function istUmleitung(element) {
  return /^<Navigate\b/.test(element);
}

describe('bypass — Landmarke auf öffentlichen Seiten', () => {
  const routen = oeffentlicheRouten();

  test('der Routenbaum wird überhaupt gelesen', () => {
    // Ohne das wäre alles Folgende auch dann grün, wenn das Muster nicht mehr
    // passt und die Liste leer bleibt — der häufigste Weg, wie ein Wächter
    // still wirkungslos wird.
    expect(routen.length).toBeGreaterThanOrEqual(15);
  });

  test('jede öffentliche Route trägt OeffentlicheSeite', () => {
    const ohne = routen
      .filter(r => !istUmleitung(r.element))
      .filter(r => !r.element.includes('<OeffentlicheSeite>'))
      .map(r => r.pfad);

    expect(ohne).toEqual([]);
  });

  test('die Hülle rendert wirklich ein main', () => {
    const huelle = fs.readFileSync(
      path.join(WURZEL, 'components', 'ui', 'OeffentlicheSeite.jsx'), 'utf8');
    expect(huelle).toMatch(/<main[\s>]/);
  });
});

describe('tabindex, accesskeys, meta-refresh', () => {
  const dateien = [];
  (function sammle(ordner) {
    fs.readdirSync(ordner, { withFileTypes: true }).forEach(e => {
      const voll = path.join(ordner, e.name);
      if (e.isDirectory()) {
        if (e.name !== 'node_modules') sammle(voll);
      } else if (/\.(jsx?|html)$/.test(e.name) && !/\.test\./.test(e.name)) {
        dateien.push(voll);
      }
    });
  })(WURZEL);

  const suche = muster => dateien
    .map(d => ({ datei: path.relative(WURZEL, d), text: fs.readFileSync(d, 'utf8') }))
    .filter(({ text }) => muster.test(text))
    .map(({ datei }) => datei);

  test('kein tabIndex grösser als 0 — er zerreisst die Tab-Reihenfolge', () => {
    expect(suche(/tabIndex\s*[=:]\s*[{"']?\s*[1-9]\d*/)).toEqual([]);
  });

  test('kein accesskey — er kollidiert mit den Kürzeln der Hilfsmittel', () => {
    expect(suche(/\baccess[Kk]ey\s*=/)).toEqual([]);
  });

  test('kein meta-refresh — es reisst den Fokus weg', () => {
    expect(suche(/http-equiv\s*=\s*["']refresh/i)).toEqual([]);
  });

  test('die Suche findet überhaupt Dateien', () => {
    expect(dateien.length).toBeGreaterThan(50);
  });
});

describe('meta-viewport — Zoomen bleibt erlaubt', () => {
  const html = fs.readFileSync(
    path.join(WURZEL, '..', 'public', 'index.html'), 'utf8');

  test('es gibt überhaupt ein viewport-meta', () => {
    expect(html).toMatch(/<meta\s+name="viewport"/);
  });

  test('das Zoomen ist nicht gesperrt', () => {
    // `user-scalable=no` und `maximum-scale=1` sind die beiden Wege, einer
    // Sehbehinderung das Vergrössern zu verbieten. Beide sind schnell
    // eingefügt, weil sie auf dem Telefon „ordentlicher" aussehen — und
    // genau deshalb steht hier ein Test und kein Kommentar.
    expect(html).not.toMatch(/user-scalable\s*=\s*no/i);
    expect(html).not.toMatch(/maximum-scale\s*=\s*1\b/i);
  });
});
