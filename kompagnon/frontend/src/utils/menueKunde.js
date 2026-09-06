// Das Kundenmenü — gruppiert, an einer Stelle (06.09.2026).
//
// **Der Anlass.** Der Entwurf `kundenkonto-neu` (David, 06.09.2026) legt zwölf
// flache Punkte in eine Übersicht, drei Gruppen und zwei Ausgänge. Zwölf
// gleichrangige Zeilen sind keine Ordnung: „Mein Bericht" stand darin neben
// „Akademie" wie „Freigaben" neben „Einstellungen" — das eine betrifft den
// Vertrag, das andere das Konto, das dritte das laufende Projekt.
//
// **Warum als Daten und nicht als Feld im Bauteil.** Für den Innendienst gibt
// es `utils/menue.js` seit dem 17.08.2026 aus genau diesem Grund. Das
// Kundenmenü stand bis heute inline in `SidebarNav.jsx`: nicht prüfbar, und
// die Mobilansicht musste es ein zweites Mal führen.
//
// **Die Reihenfolge der Gruppen folgt der Projektphase.** Vor dem Bau ist
// „Mein Projekt" das, worauf der Kunde schaut; nach dem Go-live „Mein
// Vertrag". Die Gruppen stehen deshalb in dieser Reihenfolge und nicht nach
// Häufigkeit — eine Reise ist eine Reihenfolge.

/**
 * Die Gruppen in der Reihenfolge, in der sie stehen.
 *
 * Eine Gruppe ohne `label` ist keine Gruppe, sondern ein einzelner Punkt ohne
 * Überschrift: oben die Übersicht, unten die Ausgänge.
 */
export const KUNDEN_MENUE = [
  {
    key: 'start',
    label: '',
    eintraege: [
      // **Direkt auf die eigene Karte** (04.09.2026). Der Punkt zeigte auf
      // `/app/dashboard`; `DashboardRoute` wirft einen Kunden von dort sofort
      // weiter. Der Klick landete richtig — aber die Aktiv-Erkennung verglich
      // mit der Adresse **nach** der Umleitung und war nie wahr. Ein
      // Menüpunkt soll benennen, wohin er wirklich führt.
      { label: 'Übersicht', path: '/app/usercards/:leadId', ohneLead: '/app/dashboard' },
    ],
  },
  {
    key: 'projekt',
    label: 'Mein Projekt',
    eintraege: [
      { label: 'Was wir brauchen', path: '/app/was-wir-brauchen' },
      { label: 'Freigaben',        path: '/app/freigaben' },
      { label: 'Mein Briefing',    path: '/app/mein-briefing' },
    ],
  },
  {
    key: 'vertrag',
    label: 'Mein Vertrag',
    eintraege: [
      // **„Leistungen und Guthaben" statt „Inhaltsänderungen"** — die Seite
      // zeigt seit L-160 Rang 3 beides: den Kontostand in Minuten **und**
      // was im Pflege-Abo steckt, im Wortlaut des Vertrags. Der alte Name
      // nannte nur die Hälfte.
      { label: 'Leistungen und Guthaben', path: '/app/inhaltsaenderungen' },
      // „Berichte und Prüfungen": Die Seite führt den Monatsbericht **und**
      // den Re-Audit-Termin. „Mein Bericht" nannte den zweiten nicht.
      { label: 'Berichte und Prüfungen',  path: '/app/mein-bericht' },
      { label: 'Rechnungen und Zahlung',  path: '/app/rechnungen' },
    ],
  },
  {
    key: 'konto',
    label: 'Mein Konto',
    eintraege: [
      { label: 'Meine Daten',   path: '/app/meine-daten' },
      { label: 'Akademie',      path: '/app/academy' },
      // **`/app/mein-konto`, nicht `/app/settings`.** Beide gab es
      // nebeneinander: `settings/profile|security|notifications` ist die
      // gemeinsame Seite für alle Rollen, `mein-konto` die seit dem
      // 06.09.2026 für Kunden gebaute mit sechs Reitern (Profil,
      // Abo/Zahlung, Rechnung, Geräte, Sicherheit, Benachrichtigungen,
      // Downloads). Zwei Wege zum selben Ziel sind zwei, die auseinander
      // laufen; der Kunde bekommt seinen.
      { label: 'Einstellungen', path: '/app/mein-konto' },
    ],
  },
  {
    key: 'ausgaenge',
    label: '',
    eintraege: [
      { label: 'Support', path: '/app/support' },
    ],
  },
];

/**
 * Was der Entwurf führt und wofür es keine Seite gibt.
 *
 * **Warum sie nicht im Menü stehen.** Vier tote Klicks wären die Fehlerklasse
 * dieses Projekts, nur andersherum: nicht „gebaut, nicht angeschlossen",
 * sondern „angeschlossen, nicht gebaut". Beides führt jemanden ins Leere.
 *
 * Sie stehen hier mit ihrer Nummer, und ein Test verlangt, dass der Eintrag
 * ins Menü wandert, sobald seine Route existiert.
 */
export const NOCH_NICHT_GEBAUT = [
  { label: 'Vertragsunterlagen', pfad: 'vertragsunterlagen', luecke: 'L-160',
    grund: 'Rang 7 der Ordnung: Angebot, AGB-Fassung und Auftragsbestätigung '
      + 'liegen im System, der Kunde kommt nicht heran.' },
  { label: 'Dazubuchen', pfad: 'dazubuchen', luecke: 'L-160',
    grund: 'Der Bestellweg für Zusatzleistungen aus dem laufenden Konto — im '
      + 'Entwurf mit Bestätigungsschritt, ohne Check PLUS und Workbook.' },
  { label: 'Zugänge für Kollegen', pfad: 'zugaenge', luecke: 'L-160',
    grund: 'Rang 4 und zugleich K7 der Reibungskarte: Ein Betrieb ist keine '
      + 'Person. Die Routen verlangen manage_users, also Innendienst.' },
  { label: 'Nachrichten', pfad: 'nachrichten', luecke: 'L-160',
    grund: 'Der Verlauf mit dem Betreuer steht heute auf der Übersicht und '
      + 'macht sie lang; als eigene Seite wäre er auffindbar.' },
];

/** Alle Einträge quer über die Gruppen — für Prüfungen und die Mobilansicht. */
export function kundenEintraege() {
  return KUNDEN_MENUE.flatMap(g => g.eintraege);
}

/**
 * Der Pfad eines Eintrags für einen konkreten Betrieb.
 *
 * Nur die Übersicht trägt eine Kennung. Fehlt sie, greift `ohneLead` — sonst
 * stünde `/app/usercards/undefined` im Menü.
 */
export function pfadFuer(eintrag, leadId) {
  if (!eintrag.path.includes(':leadId')) return eintrag.path;
  return leadId ? eintrag.path.replace(':leadId', leadId) : eintrag.ohneLead;
}
