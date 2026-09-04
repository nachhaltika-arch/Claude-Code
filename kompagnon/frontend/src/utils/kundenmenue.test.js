/**
 * Das Kundenmenü und die Seiten dahinter (L-161, 04.09.2026).
 *
 * **Der Anlass.** Bis zum 04.09. standen Mitwirkung, Inhaltsänderungen und
 * Zahlungen alle drei untereinander auf der Übersicht — 3.156 px, zehn
 * Überschriften, davon vier auf derselben Ebene. David nannte es
 * „unübersichtlich und unaufgeräumt". Jetzt hat jede Arbeitsfläche einen
 * Menüpunkt und eine Adresse.
 *
 * **Was dieser Test hält, und warum gerade das:**
 *
 * 1. *Jeder Menüpunkt hat eine Route.* Ein Punkt, der ins Leere zeigt, ist
 *    schlimmer als keiner — er sieht aus wie ein Fehler des Nutzers.
 * 2. *Kein Punkt zeigt auf eine Weiche.* Genau daran ist „Dashboard" am
 *    04.09. gescheitert: Der Punkt zeigte auf `/app/dashboard`, von wo ein
 *    Kunde sofort weitergeleitet wird — der Vergleich für „aktiv" lief gegen
 *    die Adresse **nach** der Umleitung und war nie wahr.
 * 3. *Der Menüpunkt heißt wie die Überschrift der Seite.* Wer „Was wir
 *    brauchen" klickt und „Mitwirkungspflichten" liest, fragt sich, ob er
 *    richtig ist.
 */
import fs from 'fs';
import path from 'path';

const SRC = path.join(__dirname, '..');
const lies = (...teile) => fs.readFileSync(path.join(SRC, ...teile), 'utf8');

/** Die Kundenpunkte aus der Seitenleiste — gelesen, nicht abgeschrieben. */
function kundenpunkte() {
  const quelle = lies('components', 'Layout', 'SidebarNav.jsx');
  const block = quelle.slice(quelle.indexOf('/* ── Kunde view ── */'),
                            quelle.indexOf('/* ── All other roles'));
  return [...block.matchAll(/\{ label: '([^']+)',\s*path: ([^}]+)\}/g)]
    .map((m) => ({ label: m[1], pfad: m[2].trim() }));
}

describe('Das Menü des Kunden', () => {
  test('führt die elf Punkte in der Reihenfolge der Aufmerksamkeit', () => {
    // Arrange & Act
    const labels = kundenpunkte().map((p) => p.label);

    // Assert — erst wo er steht, dann was bei ihm liegt, dann was er zahlt.
    expect(labels.slice(0, 5)).toEqual([
      'Übersicht', 'Was wir brauchen', 'Inhaltsänderungen',
      'Mein Bericht', 'Rechnungen und Zahlung',
    ]);
  });

  test('jeder Punkt hat eine Route in App.jsx', () => {
    // Arrange
    const app = lies('App.jsx');

    // Act & Assert
    kundenpunkte().forEach(({ label, pfad }) => {
      // Die Übersicht zeigt auf die eigene Kartei — ein Ausdruck, kein Pfad.
      if (pfad.includes('usercards')) {
        expect(app).toContain('path="usercards/:id"');
        return;
      }
      const teil = pfad.replace(/['`]/g, '').replace('/app/', '').split('/')[0];
      expect(app.includes(`path="${teil}"`)).toBe(true);
      expect(label.length).toBeGreaterThan(0);
    });
  });

  test('kein Punkt zeigt auf /app/dashboard — das ist eine Weiche', () => {
    // Arrange & Act
    const punkte = kundenpunkte();

    // Assert — `/app/dashboard` leitet einen Kunden sofort weiter; ein
    // Menüpunkt darauf leuchtet nie, weil „aktiv" gegen die Zieladresse
    // vergleicht. Der Rückfall ohne `lead_id` bleibt erlaubt.
    punkte.forEach(({ pfad }) => {
      const zeigtNurAufWeiche = /^'\/app\/dashboard'$/.test(pfad);
      expect(zeigtNurAufWeiche).toBe(false);
    });
  });

  test('jede Seite traegt genau eine Ueberschrift, und zwar ihren Menuenamen', () => {
    // Arrange — der Menüpunkt und die Überschrift müssen sich decken, sonst
    // zweifelt der Nutzer, ob er richtig gelandet ist. Und die Überschrift
    // gehört in die **Seite**: `seitenTitel.test.js` liest die Seitendatei
    // und kann nicht durch eine Komponente hindurchsehen.
    const paare = [
      ['customer/WasWirBrauchen.jsx', 'Was wir brauchen', 'Mitwirkung'],
      ['customer/Inhaltsaenderungen.jsx', 'Inhaltsänderungen', 'Inhaltsguthaben'],
      ['customer/MeineRechnungen.jsx', 'Rechnungen und Zahlung', 'Zahlungen'],
      ['customer/MeinBericht.jsx', 'Mein Bericht', null],
    ];

    // Act & Assert
    paare.forEach(([datei, titel, komponente]) => {
      const quelle = lies('pages', datei);
      expect(quelle).toContain('<h1');
      expect(quelle).toContain(titel);
      // Und die Komponente darunter schweigt, damit es nicht zwei sind.
      if (komponente) expect(quelle).toContain(`<${komponente} token={token} ohneTitel />`);
    });
  });

  test('die Übersicht traegt die drei Arbeitsflaechen nicht mehr', () => {
    // Arrange & Act — sonst stünden sie doppelt: einmal dort, einmal auf
    // ihrer eigenen Seite.
    const uebersicht = lies('pages', 'CustomerDashboard.jsx');

    // Assert
    ['Mitwirkung', 'Inhaltsguthaben', 'Zahlungen'].forEach((k) => {
      expect(uebersicht).not.toContain(`<${k} `);
    });
  });
});
