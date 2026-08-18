/**
 * Die Kundenseiten stehen im selben Haus wie das Werkzeug.
 *
 * Befund UX-19 (Prüfung vom 16.08.2026): „Das Tool ist dunkel, das
 * Kundenportal ist hell." Beim Nachsehen war es kein Gestaltungsstreit,
 * sondern eine Auslassung: Die Anwendung hat **ein** Farbsystem
 * (`styles/tokens.css`) mit hellem und dunklem Modus, und die Kundenseiten
 * sind ihm nie beigetreten. Sie tragen ihre Flächen als feste Hexwerte —
 * also bleiben sie weiß, während alles andere dem System des Betrachters
 * folgt. Für den Kunden, der vom Bericht ins Portal wechselt, ist das ein
 * Hauswechsel.
 *
 * Deshalb: In den Kundenseiten steht keine feste Farbe mehr, ausser sie
 * bedeutet etwas, wofür es kein Token gibt.
 */
import fs from 'fs';
import path from 'path';

const SEITEN = [
  'PortalLogin.jsx',
  'CustomerPortal.jsx',
  'KundenPortal.jsx',
  path.join('customer', 'Freigaben.jsx'),
  path.join('customer', 'MeineRechnungen.jsx'),
  path.join('customer', 'SupportTickets.jsx'),
];

/**
 * Farben, die etwas benennen, was das Tokensystem nicht kennt.
 * Jede Ausnahme braucht einen Grund — sonst ist sie keine.
 */
const ERLAUBT = new Map([
  ['#4a90d9', 'Homepage-Standard Platin — Medaillenfarbe, kein Flächenton'],
  ['#b8860b', 'Homepage-Standard Gold'],
  ['#708090', 'Homepage-Standard Silber'],
  ['#cd7f32', 'Homepage-Standard Bronze'],
  ['#ef4444', 'Fensterknopf im Browser-Nachbau — zitiert ein Fenster, meldet keinen Zustand'],
  ['#f59e0b', 'Fensterknopf im Browser-Nachbau'],
  ['#22c55e', 'Fensterknopf im Browser-Nachbau'],
]);

function farbenIn(datei) {
  const inhalt = fs.readFileSync(path.join(__dirname, datei), 'utf8');
  const treffer = inhalt.match(/#[0-9a-fA-F]{3,8}\b/g) || [];
  return treffer.map((f) => f.toLowerCase());
}

describe('Kundenseiten folgen dem Farbsystem', () => {
  test.each(SEITEN)('%s trägt keine festen Flächen- oder Textfarben', (datei) => {
    const fremd = [...new Set(farbenIn(datei))].filter(
      (farbe) => !ERLAUBT.has(farbe),
    );

    expect(fremd).toEqual([]);
  });
});

describe('Die benutzten Töne gibt es auch', () => {
  // Eine Farbe, die auf ein Token zeigt, das niemand definiert hat, faellt
  // nicht auf: Der Browser laesst die Eigenschaft einfach weg, und die
  // Flaeche bleibt durchsichtig oder schwarz. Ein Tippfehler im Namen ist
  // deshalb schlimmer als ein Hexwert — er ist unsichtbar.
  const TOKENS = fs.readFileSync(
    path.join(__dirname, '..', 'styles', 'tokens.css'), 'utf8',
  );
  const definiert = new Set(
    (TOKENS.match(/--[a-z0-9-]+\s*:/g) || []).map((t) => t.replace(/\s*:$/, '')),
  );

  test.each(SEITEN)('%s benutzt nur Töne, die es gibt', (datei) => {
    const inhalt = fs.readFileSync(path.join(__dirname, datei), 'utf8');
    const benutzt = [...new Set(
      (inhalt.match(/var\(\s*(--[a-z0-9-]+)/g) || [])
        .map((t) => t.replace(/var\(\s*/, '')),
    )];

    expect(benutzt.filter((name) => !definiert.has(name))).toEqual([]);
  });
});

describe('Die rechtlichen Seiten sind erreichbar', () => {
  const APP = fs.readFileSync(path.join(__dirname, '..', 'App.jsx'), 'utf8');

  // Beide Seiten liegen seit jeher in `pages/`, waren aber an keine Adresse
  // gebunden — es gab also ein Impressum, zu dem kein Weg führte, während
  // der Fuss des Kundenportals auf eine dritte Domain zeigte.
  // Die Barrierefreiheitserklaerung stand im Fuss des Impressums verlinkt —
  // auf eine Adresse, die es nicht gab. Verkauft wird BFSG-Konformitaet.
  test.each(['/impressum', '/datenschutz', '/barrierefreiheit'])('%s hat eine Route', (pfad) => {
    expect(APP).toContain(`path="${pfad}"`);
  });
});
