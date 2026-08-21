// Listenlogik der Betriebsliste — Suche, Filter, Sortierung, Kennzahlen.
//
// Warum eigene Datei: Diese Logik lag doppelt vor, in „Unternehmen" und in
// „Kunden", und sie lief auseinander. Sie gehoert an eine Stelle und ist als
// reine Funktion pruefbar — die Seite selbst ist es nicht.
//
// Alle Funktionen geben neue Listen zurueck und fassen die Eingabe nicht an.

import { LEAD_PHASE, LEAD_STATUS, leadPhaseLabel, leadSourceLabel, leadStatusLabel } from './leadStatus';

/** Sortierungen der Liste. `key` steht im Auswahlfeld. */
export const BETRIEB_SORTIERUNGEN = [
  { key: 'name',  label: 'A → Z' },
  { key: 'score', label: 'Score ↓' },
  { key: 'date',  label: 'Neueste' },
  { key: 'city',  label: 'Ort' },
];

/**
 * Die Quellen, die in den Daten **wirklich vorkommen** — nach Haeufigkeit.
 *
 * Vorher stand im Auswahlfeld eine feste Liste aus drei Eintraegen. Quellen
 * sind aber Freitext (Kampagnennamen), und so fehlten alle uebrigen: Man
 * konnte nach ihnen nicht filtern und sah nicht, dass es sie gibt. Ein Feld,
 * das nur einen Ausschnitt anbietet, behauptet, das sei alles.
 *
 * Datensaetze ohne Quelle laufen unter `manual` — sie sind von Hand angelegt
 * worden, bevor das Feld gesetzt wurde.
 */
export function quellenAusBetrieben(betriebe = []) {
  const zaehler = new Map();
  for (const betrieb of betriebe) {
    const key = betrieb.lead_source || 'manual';
    zaehler.set(key, (zaehler.get(key) || 0) + 1);
  }

  const gefunden = [...zaehler.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([key, anzahl]) => ({ key, label: leadSourceLabel(key), anzahl }));

  return [{ key: 'alle', label: 'Alle Quellen', anzahl: betriebe.length }, ...gefunden];
}

const kleingeschrieben = (wert) => (wert || '').toLowerCase();

/** Durchsucht Name, Ort, Gewerk, E-Mail, Website und Status. */
export function sucheBetriebe(betriebe, suchbegriff) {
  const q = kleingeschrieben(suchbegriff).trim();
  if (!q) return [...betriebe];

  return betriebe.filter((b) =>
    kleingeschrieben(b.display_name).includes(q) ||
    kleingeschrieben(b.company_name).includes(q) ||
    kleingeschrieben(b.city).includes(q) ||
    kleingeschrieben(b.trade).includes(q) ||
    kleingeschrieben(b.email).includes(q) ||
    kleingeschrieben(b.website_url).includes(q)
  );
}

export function filterNachStatus(betriebe, status) {
  if (!status || status === 'alle') return [...betriebe];
  return betriebe.filter((b) => b.status === status);
}

/**
 * Nach Lebenszyklus-Phase filtern.
 *
 * `offen` trifft die Betriebe **ohne** Phase — die mit einem Status, den die
 * Zuordnung nicht kennt. Sie bekommen bewusst eine eigene Schaltfläche: Ein
 * unbekannter Wert soll sich zeigen, nicht verschwinden (dieselbe Lehre wie
 * bei `statusAusBetrieben` weiter unten).
 */
export function filterNachPhase(betriebe, phase) {
  if (!phase || phase === 'alle') return [...betriebe];
  if (phase === 'offen') return betriebe.filter((b) => !b.lifecycle_phase);
  return betriebe.filter((b) => b.lifecycle_phase === phase);
}

export function filterNachQuelle(betriebe, quelle) {
  if (!quelle || quelle === 'alle') return [...betriebe];
  if (quelle === 'manual') {
    return betriebe.filter((b) => !b.lead_source || b.lead_source === 'manual');
  }
  return betriebe.filter((b) => b.lead_source === quelle);
}

const zeitwert = (wert) => {
  const zeit = new Date(wert || 0).getTime();
  return Number.isNaN(zeit) ? 0 : zeit;
};

/** Sortiert eine Kopie — die Eingabeliste bleibt unberuehrt. */
export function sortiereBetriebe(betriebe, sortierung) {
  const kopie = [...betriebe];
  const name = (b) => b.display_name || b.company_name || '';

  if (sortierung === 'score') {
    return kopie.sort((a, b) => (b.analysis_score || 0) - (a.analysis_score || 0));
  }
  if (sortierung === 'date') {
    return kopie.sort((a, b) => zeitwert(b.created_at) - zeitwert(a.created_at));
  }
  if (sortierung === 'city') {
    return kopie.sort((a, b) => (a.city || '').localeCompare(b.city || ''));
  }
  return kopie.sort((a, b) => name(a).localeCompare(name(b)));
}

/**
 * Suche, beide Filter und Sortierung in einem Durchgang.
 * @returns {Array} neue Liste
 */
export function betriebeAufbereiten({ betriebe = [], suche = '', status = 'alle', quelle = 'alle', phase = 'alle', sortierung = 'name' } = {}) {
  const gesucht  = sucheBetriebe(betriebe, suche);
  const gefiltert = filterNachPhase(
    filterNachQuelle(filterNachStatus(gesucht, status), quelle),
    phase,
  );
  return sortiereBetriebe(gefiltert, sortierung);
}

/**
 * Die Phasen, die in den Daten vorkommen — samt derer **ohne** Phase.
 *
 * Anders als bei den Status ist die Menge hier bekannt und klein; trotzdem
 * wird gezaehlt und nicht aufgezaehlt, damit die Summe der Schaltflaechen der
 * Zahl der Betriebe entspricht. Genau daran ist es beim Status aufgefallen.
 */
export function phasenAusBetrieben(betriebe = []) {
  const zaehler = new Map();
  for (const betrieb of betriebe) {
    const key = betrieb.lifecycle_phase || 'offen';
    zaehler.set(key, (zaehler.get(key) || 0) + 1);
  }

  const reihenfolge = [...Object.keys(LEAD_PHASE), 'offen'];
  const rang = (key) => {
    const platz = reihenfolge.indexOf(key);
    return platz === -1 ? reihenfolge.length : platz;
  };

  return [...zaehler.entries()]
    .map(([key, anzahl]) => ({
      key,
      label: key === 'offen' ? 'Phase offen' : leadPhaseLabel(key),
      anzahl,
    }))
    .sort((a, b) => rang(a.key) - rang(b.key));
}

/**
 * Die Statuswerte, die in den Daten **wirklich vorkommen**.
 *
 * Bekannte zuerst, in der Reihenfolge des Vertriebswegs (neu → gewonnen);
 * unbekannte dahinter, lesbar gemacht.
 *
 * Warum aus den Daten und nicht aus `LEAD_STATUS`: Auf Staging steht ein
 * Betrieb mit dem Status `opt_in`. Er kommt in `LEAD_STATUS` nicht vor, bekam
 * darum keine Filterschaltflaeche — und die Kacheln zaehlten 27 Neu + 2
 * Gewonnen bei 30 Betrieben. **Der dreissigste war weder zu sehen noch zu
 * finden.** Ein unbekannter Wert soll sich zeigen, nicht verschwinden.
 */
export function statusAusBetrieben(betriebe = []) {
  const zaehler = new Map();
  for (const betrieb of betriebe) {
    const key = betrieb.status || 'new';
    zaehler.set(key, (zaehler.get(key) || 0) + 1);
  }

  const bekannt = Object.keys(LEAD_STATUS);
  const rang = (key) => {
    const platz = bekannt.indexOf(key);
    return platz === -1 ? bekannt.length : platz;
  };

  return [...zaehler.entries()]
    .sort((a, b) => rang(a[0]) - rang(b[0]) || a[0].localeCompare(b[0]))
    .map(([key, anzahl]) => ({ key, label: leadStatusLabel(key), anzahl }));
}

/**
 * Kennzahlen ueber der Liste.
 *
 * Wichtig: Diese Zahlen gelten fuer die **uebergebene** Liste. Wer sie ueber
 * eine abgeschnittene Liste rechnet, druckt falsche Zahlen — genau das war der
 * Fehler in „Kunden", wo nur die ersten 50 Datensaetze geladen wurden.
 */
export function betriebeStatistik(betriebe = []) {
  const mitScore = betriebe.filter((b) => b.analysis_score > 0);
  const summe = mitScore.reduce((s, b) => s + b.analysis_score, 0);

  return {
    gesamt: betriebe.length,
    mitScore: mitScore.length,
    durchschnittsScore: mitScore.length ? Math.round(summe / mitScore.length) : 0,
    statusZaehler: statusAusBetrieben(betriebe),
    phasenZaehler: phasenAusBetrieben(betriebe),
  };
}
