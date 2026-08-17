// Auswahl und Loeschvorschau in der Projektliste.
//
// Warum eigene Datei: Die Seite selbst ist nicht pruefbar, diese Logik schon.
// Und es geht hier um ein Loeschen — der Teil, der entscheidet, was in der
// Rueckfrage steht, sollte nicht in einer 600-Zeilen-Seite mitlaufen.
//
// Alle Funktionen geben neue Listen zurueck und fassen die Eingabe nicht an.

/** Beschriftungen der abhaengigen Tabellen. Wer die Liste liest, ist Admin —
 *  aber „project_scraped_pages" ist auch fuer den kein Wort. */
const TABELLEN_BESCHRIFTUNG = {
  project_checklists:    'Checklisten',
  communications:        'Nachrichtenverlauf',
  automation_logs:       'Automatik-Protokoll',
  time_tracking:         'Zeiterfassung',
  project_scraped_pages: 'Ausgelesene Seiten',
  project_scrape_jobs:   'Auslese-Auftraege',
  project_credentials:   'Zugangsdaten',
  geo_analyses:          'GEO-Analysen',
  website_versions:      'Website-Versionen',
  invoices:              'Rechnungen',
  retainer_contracts:    'Vertraege',
  customers:             'Kundendaten',
  email_logs:            'Versandprotokoll',
  briefings:             'Briefings',
  assistant_conversations: 'Assistenz-Gespraeche',
};

/** Nimmt eine Nummer auf oder entfernt sie. */
export function umschalten(auswahl = [], id) {
  return auswahl.includes(id)
    ? auswahl.filter(vorhanden => vorhanden !== id)
    : [...auswahl, id];
}

/** Ob jede gerade sichtbare Nummer gewaehlt ist. */
export function alleGewaehlt(auswahl = [], sichtbare = []) {
  if (sichtbare.length === 0) return false;
  return sichtbare.every(id => auswahl.includes(id));
}

/**
 * Haken bei „alle" — bezogen auf das, was gerade zu sehen ist.
 *
 * Was hinter einem Filter liegt, bleibt gewaehlt: Sonst faellt es beim
 * Umschalten still aus der Auswahl, und geloescht wird weniger als angezeigt.
 */
export function alleUmschalten(auswahl = [], sichtbare = []) {
  if (sichtbare.length === 0) return [...auswahl];
  if (alleGewaehlt(auswahl, sichtbare)) {
    return auswahl.filter(id => !sichtbare.includes(id));
  }
  const fehlende = sichtbare.filter(id => !auswahl.includes(id));
  return [...auswahl, ...fehlende];
}

function zeilen(zaehlung = {}) {
  return Object.entries(zaehlung)
    .filter(([, anzahl]) => anzahl > 0)
    .map(([tabelle, anzahl]) => ({
      tabelle,
      beschriftung: TABELLEN_BESCHRIFTUNG[tabelle] || tabelle,
      anzahl,
    }));
}

/**
 * Der Bericht des Servers, lesbar gemacht.
 *
 * Tabellen mit 0 Zeilen fallen raus — eine Rueckfrage, die zwoelf Nullen
 * auflistet, wird nicht gelesen.
 */
export function vorschauZeilen(bericht) {
  if (!bericht) return { geloescht: [], bleibt: [] };
  return {
    geloescht: zeilen(bericht.wird_geloescht),
    bleibt:    zeilen(bericht.bleibt_erhalten),
  };
}

/** Die Frage ueber der Rueckfrage. Bei einem Projekt beim Namen genannt. */
export function loeschFrage(namen = []) {
  if (namen.length === 0) return '';
  if (namen.length === 1) return `„${namen[0]}" löschen?`;
  return `${namen.length} Projekte löschen?`;
}
