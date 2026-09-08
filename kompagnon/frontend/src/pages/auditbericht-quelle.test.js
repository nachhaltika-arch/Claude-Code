/**
 * Der Auditbericht zeigt den vollständigen Audit, nicht die Listenzeile.
 *
 * **Der Befund vom 08.09.2026** (gemeldet an Betrieb 87): Unter „Audits"
 * fehlte das vollständige Ergebnis. `AuditReport` bekam das Objekt aus der
 * Liste — Punktzahl, Stufe, Datum. Kriterien, Belege, Kategorien, Deckung
 * und K.-o.-Punkte waren nie dabei.
 *
 * Das Bittere daran: `AuditReport` ist auf die richtige Form längst gebaut
 * (`r.items`, `buildViewCategories` aus dem mitgelieferten Katalog), und
 * `GET /api/audit/{id}` liefert sie durch `_format_audit`. Beide Seiten
 * waren fertig; es fehlte der Aufruf dazwischen — die achte Auflage von
 * „gebaut, nicht angeschlossen".
 *
 * Geprüft wird am Quelltext, weil die Seite `react-router-dom` hereinzieht
 * und sich im Testlauf nicht rendern lässt. Beide Richtungen: Der Aufruf
 * muss da sein, **und** die Abkürzung darf nicht zurückkehren.
 */
import fs from 'fs';
import path from 'path';

const SEITE = fs.readFileSync(
  path.join(__dirname, 'LeadProfile.jsx'), 'utf8',
);

describe('Woher der Auditbericht seine Daten bekommt', () => {
  test('der vollständige Audit wird nachgeladen', () => {
    expect(SEITE).toMatch(/\/api\/audit\/\$\{audit\.id\}/);
  });

  test('der Details-Knopf ruft den Lader, nicht den Zustand direkt', () => {
    // Die Abkürzung, die den Fehler gemacht hat: das Listenobjekt ohne
    // Umweg in den Dialog stellen.
    expect(SEITE).not.toMatch(/onClick=\{\(\) => setOpenAudit\(audit\)\}/);
    expect(SEITE).toMatch(/onClick=\{\(\) => auditOeffnen\(audit\)\}/);
  });

  test('ein Ladefehler öffnet den Bericht trotzdem', () => {
    // Weniger zu zeigen ist besser, als einen Klick wortlos verpuffen zu
    // lassen — der Rückfall auf das Listenobjekt muss stehen bleiben.
    expect(SEITE).toMatch(/setOpenAudit\(voll \|\| audit\)/);
  });

  test('der Knopf sagt, dass geladen wird', () => {
    expect(SEITE).toMatch(/Wird geladen/);
  });
});
