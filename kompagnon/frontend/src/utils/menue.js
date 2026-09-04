// Die Gruppen der Seitenleiste — einmal, und die Adressen kommen daraus.
//
// **Warum eigene Datei.** Die Zuordnung Adresse → Gruppe stand zweimal: in der
// Menuedefinition und noch einmal als Pfadliste in `getDefaultOpen`. Wer einen
// Eintrag verschob und die zweite Liste vergass, bekam eine Seitenleiste, die
// nicht mehr zeigt, wo man ist — genau der Fehler vom 16.08.2026, nur an einer
// anderen Stelle. Jetzt wird die Zuordnung aus den Eintraegen abgeleitet.
//
// **Was sich am 17.08.2026 geaendert hat** (UX-16, UX-17):
//
// Die Gruppe hiess **„Kompagnon"** und enthielt sieben unverwandte Eintraege —
// Tickets, Templates, Produkt-Editor, Produkte, Produktentwicklung,
// QR-Generator, Retainer. Der eigene Firmenname sagt nicht, was darin liegt;
// er ist der Name fuer „alles Uebrige".
//
// Beim Nachsehen, was die Eintraege wirklich sind:
//
//   QR-Generator      erzeugt Codes fuer Kampagnen (Platzhalter
//                     `postkarte-koblenz-mai-2025`) → gehoert zu Akquise
//   Templates         verwaltet Verkaufsseiten fuer Pakete
//                     (`/paket/mein-produkt`) → gehoert zum Angebot
//   Produkte          der Katalog (`api/products/`)
//   Produkt-Editor    bearbeitet **denselben** Katalog und ist von „Produkte"
//                     aus erreichbar → kein eigener Menueeintrag
//   Produktentwicklung  ein Ideen-Board (Idee → Geplant → In Entwicklung →
//                     Testing → Fertig), also keine Produktpflege → „Roadmap"
//   Tickets, Retainer   beides Betreuung nach dem Verkauf

/** Die Gruppen in der Reihenfolge, in der sie stehen. */
export const MENUE_GRUPPEN = [
  {
    key: 'akquise',
    label: 'Akquise',
    icon: '🎯',
    eintraege: [
      { label: 'Kaltakquise',     path: '/app/scraper',       adminOnly: true },
      { label: 'Domain-Import',   path: '/app/import' },
      { label: 'Audit-Tool',      path: '/app/audit' },
      { label: 'Analyse-Widget',  path: '/app/widget',        adminOnly: true },
      { label: 'Webhooks',        path: '/app/webhooks',      adminOnly: true },
    ],
  },
  {
    key: 'werbung',
    label: 'Werbung',
    icon: '📣',
    eintraege: [
      { label: 'Newsletter',      path: '/app/newsletter' },
      { label: 'Kampagnen',       path: '/app/campaigns',     adminOnly: true },
      { label: 'QR-Codes',        path: '/app/qr-generator',  adminOnly: true },
    ],
  },
  {
    key: 'vertrieb',
    label: 'Vertrieb',
    icon: '💼',
    eintraege: [
      { label: 'Deals',           path: '/app/deals' },
      { label: 'Betriebe',        path: '/app/betriebe' },
      { label: 'Export',          path: '/app/export' },
      // Die Druckwarteschlange des Buchs (BUCH-07). Sie steht unter
      // Vertrieb, weil sie eingehende Bestellungen abarbeitet — nicht
      // unter „Angebot", wo beschrieben wird, was wir verkaufen.
      { label: 'Buchbestellungen', path: '/app/buchbestellungen', adminOnly: true },
    ],
  },
  {
    key: 'projekte',
    label: 'Projekte',
    icon: '📁',
    eintraege: [
      { label: 'Alle Projekte',   path: '/app/projects' },
      { label: 'Projektpipeline', path: '/app/projektpipeline' },
      { label: 'Prozess-Ansicht', path: '/app/checklists' },
    ],
  },
  {
    key: 'angebot',
    label: 'Angebot',
    icon: '🏷️',
    eintraege: [
      { label: 'Pakete',          path: '/app/products',      adminOnly: true },
      { label: 'Verkaufsseiten',  path: '/app/pages',         adminOnly: true },
      { label: 'Roadmap',         path: '/app/product',       adminOnly: true },
    ],
  },
  {
    key: 'betreuung',
    label: 'Betreuung',
    icon: '🤝',
    eintraege: [
      { label: 'Tickets',         path: '/app/tickets' },
      // Die Akademie stand in keiner Gruppe: fünf Kurse, eine Verwaltung und
      // Urkunden für Kunden, auf dem Desktop ohne jeden Weg dorthin — nur die
      // Mobilleiste kannte sie unter „Mehr". Gefunden von David am
      // 18.08.2026. Sie liegt hier, weil Betreuung das ist, was nach dem
      // Verkauf mit dem Kunden passiert; die internen Kurse gehören ins
      // selbe Regal.
      { label: 'Akademie',        path: '/app/academy' },
      { label: 'Kurse verwalten', path: '/app/academy/admin', adminOnly: true },
      { label: 'Abrechnung',      path: '/app/retainer',      adminOnly: true },
    ],
  },
  {
    key: 'einstellungen',
    label: 'Einstellungen',
    icon: '⚙️',
    eintraege: [
      { label: 'Profil',            path: '/app/profile' },
      { label: 'Sicherheit',        path: '/app/2fa-setup' },
      // **Zeigte bis zum 27.08.2026 auf `/app/settings`** — und das leitet
      // auf `/app/settings/profile` um. Wer „System" anklickte, landete auf
      // dem Profil. Ein Menuepunkt, der woanders hinfuehrt, als er sagt,
      // ist schlimmer als einer, der fehlt.
      { label: 'System',            path: '/app/settings/system' },
      // Aus der Einstellungs-Seitenleiste hierher geholt (Bitte David,
      // 27.08.2026). Sie stand neben dem Hauptmenue und wiederholte es zur
      // Haelfte; diese drei gab es **nur** dort.
      { label: 'Benachrichtigungen', path: '/app/settings/notifications' },
    ],
  },
  {
    key: 'verwaltung',
    label: 'Verwaltung',
    icon: '🔧',
    eintraege: [
      { label: 'Benutzer',          path: '/app/admin/users', adminOnly: true },
      // **Zeigte bis zum 27.08.2026 auf `/app/admin/roles` — den Pfad gibt
      // es nicht.** Die Rollenverwaltung liegt unter
      // `/app/settings/roles`, innerhalb der Einstellungen mit ihrer
      // Seitenleiste. Wer den Menuepunkt anklickte, landete im Auffang;
      // bis heute hiess das: auf der Anmeldemaske. David hat es gemeldet.
      //
      // `menueZiele.test.js` haelt seither jeden Eintrag gegen die
      // Routen — ein Menuepunkt, der nirgendwohin fuehrt, ist die
      // teuerste Sorte Knopf.
      { label: 'Rollen',            path: '/app/settings/roles', adminOnly: true },
      // Heisst wie die Seite, zu der er fuehrt. Hier stand kurz „Bausteine" —
      // kuerzer und besseres Deutsch, aber die Seite traegt weiter die
      // Ueberschrift „Komponenten-Bibliothek". Menue und Titel auseinander
      // laufen zu lassen ist genau UX-01, der erste Befund dieser Pruefung.
      // Wer umbenennen will, benennt beides um.
      { label: 'Komponenten-Bibliothek', path: '/app/settings/component-library', adminOnly: true },
      // Ebenfalls aus der Seitenleiste. „KAS Website" gehoert hierher und
      // nicht unter „Einstellungen": Es ist die eigene Agenturseite mit
      // eigenem Deploy — ein Arbeitsbereich, keine Einstellung.
      { label: 'KAS Website',       path: '/app/settings/kas-website', adminOnly: true },
      { label: 'Vorlagen',          path: '/app/settings/templates', adminOnly: true },
      // Ein Fehlerprotokoll, das niemand findet, ist so gut wie keines (L-10).
      { label: 'Fehlerprotokoll', path: '/app/fehler', adminOnly: true },
    ],
  },
];

/** Alle Einträge über alle Gruppen hinweg. */
export function alleEintraege() {
  return MENUE_GRUPPEN.flatMap(g => g.eintraege);
}

/** Zu welcher Gruppe gehört diese Adresse? `null`, wenn zu keiner. */
export function gruppeVon(pfad = '') {
  for (const gruppe of MENUE_GRUPPEN) {
    const treffer = gruppe.eintraege.some(
      e => pfad === e.path || pfad.startsWith(e.path + '/'),
    );
    if (treffer) return gruppe.key;
  }
  return null;
}

/**
 * Welche Gruppen zu dieser Adresse offen stehen sollen.
 *
 * Abgeleitet aus den Einträgen — nicht aus einer zweiten Liste, die
 * hinterherhinken kann.
 */
export function offeneGruppen(pfad = '') {
  const offen = gruppeVon(pfad);
  return Object.fromEntries(MENUE_GRUPPEN.map(g => [g.key, g.key === offen]));
}
