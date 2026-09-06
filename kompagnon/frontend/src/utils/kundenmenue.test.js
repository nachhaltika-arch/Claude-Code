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

import { KUNDEN_MENUE, NOCH_NICHT_GEBAUT, kundenEintraege } from './menueKunde';

const SRC = path.join(__dirname, '..');
const lies = (...teile) => fs.readFileSync(path.join(SRC, ...teile), 'utf8');

/**
 * Die Kundenpunkte — seit dem 06.09.2026 aus `utils/menueKunde.js`.
 *
 * **Vorher las diese Funktion das JSX** und zog die Punkte mit einem
 * regulären Ausdruck aus `SidebarNav.jsx`. Das hielt genau so lange, bis
 * jemand die Liste anders schrieb — beim Umbau auf Gruppen brach es sofort.
 * Ein Wächter, dessen Gegenstand nur als Text vorliegt, prüft die
 * Schreibweise mit; jetzt prüft er die Sache.
 */
function kundenpunkte() {
  return kundenEintraege().map((e) => ({ label: e.label, pfad: e.path }));
}

describe('Das Menü des Kunden', () => {
  test('ist gruppiert: Übersicht, drei Gruppen, ein Ausgang', () => {
    // **Geändert am 06.09.2026** (Entwurf `kundenkonto-neu`). Hier standen
    // zwölf flache Punkte „in der Reihenfolge der Aufmerksamkeit" — eine
    // Ordnung, die nur beim Lesen von oben nach unten trägt. Zwölf
    // gleichrangige Zeilen sagen nicht, dass „Freigaben" das laufende
    // Projekt betrifft und „Rechnungen" den Vertrag.
    expect(KUNDEN_MENUE.map((g) => g.label)).toEqual([
      '', 'Mein Projekt', 'Mein Vertrag', 'Mein Konto', '',
    ]);
    KUNDEN_MENUE.forEach((g) => expect(g.eintraege.length).toBeGreaterThan(0));
  });

  test('die Gruppen stehen in der Reihenfolge der Projektphase', () => {
    // Nicht nach Häufigkeit: Vor dem Bau schaut der Kunde auf „Mein
    // Projekt", danach auf „Mein Vertrag". Eine Reise ist eine Reihenfolge.
    const mit = KUNDEN_MENUE.filter((g) => g.label).map((g) => g.label);
    expect(mit).toEqual(['Mein Projekt', 'Mein Vertrag', 'Mein Konto']);
  });

  test('jeder Punkt hat eine Route in App.jsx', () => {
    // Arrange
    const app = lies('App.jsx');

    // Act & Assert
    kundenpunkte().forEach(({ label, pfad }) => {
      if (pfad.includes('usercards')) {
        expect(app).toContain('path="usercards/:id"');
        return;
      }
      const teil = pfad.replace('/app/', '').split('/')[0];
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
      expect(pfad).not.toBe('/app/dashboard');
    });
  });

  test('jede Seite traegt genau eine Ueberschrift, und zwar ihren Menuenamen', () => {
    // Arrange — der Menüpunkt und die Überschrift müssen sich decken, sonst
    // zweifelt der Nutzer, ob er richtig gelandet ist. Und die Überschrift
    // gehört in die **Seite**: `seitenTitel.test.js` liest die Seitendatei
    // und kann nicht durch eine Komponente hindurchsehen.
    const paare = [
      ['customer/WasWirBrauchen.jsx', 'Was wir brauchen', 'Mitwirkung'],
      // **Am 06.09.2026 umbenannt** — und genau dieser Test hat verlangt, dass
      // die Seiten mitziehen. Wer „Leistungen und Guthaben" klickt und
      // „Inhaltsänderungen" liest, fragt sich, ob er richtig ist. Beide
      // Seiten zeigen inzwischen mehr, als ihr alter Name nannte.
      ['customer/Inhaltsaenderungen.jsx', 'Leistungen und Guthaben', 'Inhaltsguthaben'],
      ['customer/MeineRechnungen.jsx', 'Rechnungen und Zahlung', 'Zahlungen'],
      ['customer/MeinBericht.jsx', 'Berichte und Prüfungen', null],
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

describe('Was der Entwurf verlangt und noch fehlt', () => {
  /**
   * **Warum die vier nicht im Menü stehen.** Der Entwurf `kundenkonto-neu`
   * führt Vertragsunterlagen, Dazubuchen, Zugänge für Kollegen und
   * Nachrichten. Für keinen davon gibt es eine Seite. Sie ins Menü zu setzen
   * hieße, vier tote Klicks anzubieten — die Fehlerklasse dieses Projekts,
   * nur andersherum: nicht „gebaut, nicht angeschlossen", sondern
   * „angeschlossen, nicht gebaut". Beides führt jemanden ins Leere.
   */
  test('jeder fehlende Punkt nennt Grund und Lücke', () => {
    expect(NOCH_NICHT_GEBAUT.length).toBeGreaterThan(0);
    NOCH_NICHT_GEBAUT.forEach((p) => {
      expect(p.luecke).toMatch(/^L-\d+$/);
      expect(p.grund.length).toBeGreaterThan(20);
    });
  });

  test('kein fehlender Punkt steht gleichzeitig im Menü', () => {
    const labels = kundenpunkte().map((p) => p.label);
    NOCH_NICHT_GEBAUT.forEach((p) => expect(labels).not.toContain(p.label));
  });

  test('sobald die Seite existiert, gehört der Punkt ins Menü', () => {
    // Ein Eintrag, dessen Route es längst gibt, ist keine Lücke mehr — er ist
    // ein vergessener Anschluss.
    const app = lies('App.jsx');
    NOCH_NICHT_GEBAUT.forEach((p) => {
      expect({ label: p.label, geroutet: new RegExp(`path="${p.pfad}"`).test(app) })
        .toEqual({ label: p.label, geroutet: false });
    });
  });
});

describe('Kein Bildschirm ohne Weg dorthin', () => {
  /**
   * **Die Gegenrichtung, und sie ist die wichtigere.** Ein toter Menüpunkt
   * fällt beim ersten Klick auf; eine Seite ohne Menüpunkt fällt **nie** auf.
   */
  const KUNDENSEITEN = [
    'was-wir-brauchen', 'inhaltsaenderungen', 'mein-bericht', 'rechnungen',
    'mein-briefing', 'freigaben', 'support', 'mein-konto', 'meine-daten',
  ];

  test.each(KUNDENSEITEN)('die Seite %s steht im Menü', (stamm) => {
    expect(kundenpunkte().some((p) => p.pfad.includes(stamm))).toBe(true);
  });
});
