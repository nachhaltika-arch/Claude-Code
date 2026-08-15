/**
 * Die Eigenprüfung: der eigene Katalog gegen die selbst gebaute Seite.
 *
 * Schritt 8 des Design-Konzepts. Das Backend deployt die Seite als Vorschau
 * und lässt denselben Audit darüber laufen, den ein Kunde bekommt — inklusive
 * Bericht. Hier steht nur, was das Frontend davon deuten muss.
 *
 * Gemessen wird der Stand in der Datenbank, nicht der im Browser. Der Knopf
 * speichert deshalb, bevor er prüft; sonst bezöge der Nutzer eine Bewertung
 * auf Änderungen, die nie beim Server ankamen.
 */
import { stufeAnzeige } from './homepageStandard';

export const MELDUNGEN = {
  leer: 'Diese Seite hat noch keinen Inhalt — erst bauen, dann prüfen.',
  nichtEingerichtet:
    'Für die Prüfung fehlt eine eigene Vorschau-Site bei Netlify '
    + '(NETLIFY_VORSCHAU_SITE_ID). Ohne sie wird nichts deployt.',
  deploy: 'Die Vorschau konnte nicht bereitgestellt werden — Netlify hat abgelehnt.',
  unbekannt: 'Die Prüfung konnte nicht gestartet werden.',
};

// Zustände, die das Backend beim Audit führt.
const LAEUFT_NOCH = ['pending', 'running'];

// Ab dieser Punktzahl gilt eine Seite als gut genug für den Kunden.
const SCHWELLE_GUT = 85;
const SCHWELLE_MITTEL = 50;

/** Was dem Nutzer zu einem fehlgeschlagenen Start gesagt wird. */
export function fehlermeldung(status, detail = '') {
  if (status === 400) return MELDUNGEN.leer;
  if (status === 503) return MELDUNGEN.nichtEingerichtet;
  if (status === 502) return MELDUNGEN.deploy;
  return detail && status !== 500 ? detail : MELDUNGEN.unbekannt;
}

/**
 * Ob nicht weiter nachgefragt werden muss.
 *
 * Ein unbekannter Zustand zählt als Ende: Lieber einmal zu früh aufhören als
 * den Server endlos fragen, weil eine Antwort anders aussieht als erwartet.
 */
export function istEndzustand(status) {
  return !LAEUFT_NOCH.includes(status);
}

/** Ob die Prüfung durchlief — `failed` ist ein Ende, aber kein Ergebnis. */
export function pruefungAbgeschlossen(audit) {
  return (audit || {}).status === 'completed';
}

/** Das Ergebnis in der Form, in der die Anzeige es braucht. */
export function zusammenfassung(audit) {
  const daten = audit || {};
  const punkte = Number(daten.total_score) || 0;

  let ampel = 'schwach';
  if (punkte >= SCHWELLE_GUT) ampel = 'gut';
  else if (punkte >= SCHWELLE_MITTEL) ampel = 'mittel';

  return {
    punkte,
    // Die Stufe kommt vom Server, wenn er eine liefert: Nur er kennt die
    // K.-o.-Regeln, die eine Seite unabhängig vom Punktestand deckeln.
    stufe: stufeAnzeige(punkte, daten.level || ''),
    abdeckung: Number(daten.coverage) || 0,
    ampel,
    vorschauUrl: daten.website_url || '',
    auditId: daten.id || daten.audit_id || null,
  };
}
