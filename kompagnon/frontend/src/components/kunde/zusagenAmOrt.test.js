/**
 * Jede Zusage aus dem Leistungsverzeichnis hat einen Bildschirm (L-160, Rang 3).
 *
 * **Warum dieser Wächter.** Der Katalog `services/leistungsverzeichnis.py`
 * gibt jeder Abo-Position einen `ort` — die Zusage soll dort stehen, wo sie
 * gilt. Ein Ort, den keine Seite abfragt, ist eine Zusage, die niemand liest:
 * genau die Fehlerklasse, die zwischen dem 4. und 6. September sechsmal
 * vorkam. Gebaut, nicht angeschlossen.
 *
 * **Der Test liest beide Seiten.** Die Orte kommen aus der Python-Quelle, die
 * Verwendungen aus dem JSX-Baum. Eine Liste, die hier von Hand stünde, wäre
 * der zweite Ort zum Pflegen — und würde grün bleiben, während der Katalog
 * weiterwächst.
 */
import fs from 'fs';
import path from 'path';

const WURZEL = path.join(__dirname, '..', '..', '..', '..');
const KATALOG = path.join(WURZEL, 'backend', 'services', 'leistungsverzeichnis.py');
const SEITEN = path.join(__dirname, '..', '..', 'pages');

/**
 * Orte ohne eigenen Bildschirm — jeder braucht einen Grund, sonst wird die
 * Liste zum Ablagefach.
 */
const OHNE_BILDSCHIRM = {
  laufend: 'Hosting, Aktualisierungen und Überwachung laufen im Hintergrund; '
    + 'es gibt nichts anzufordern und keine Seite, auf der man darauf wartet.',
  sicherung: 'Die Rücksicherung anzufordern ist Rang 6 der Ordnung und noch '
    + 'nicht gebaut. Bis dahin hat diese Zusage bewusst keinen Ort.',
  reaudit: 'Der Re-Audit-Termin steht seit Rang 2 in „Mein Bericht" — aus '
    + '`quartals_reaudit.TAKT_MONATE`, nicht über diesen Katalog.',
  bericht: 'Bewusst offen gelassen, und das ist K5 der Reibungskarte: Das '
    + 'Datenblatt sagt für ABO-PRO einen Bericht über Aufrufe, Anfragen, '
    + 'Auffindbarkeit und Ladezeit zu — gemessen wird die Ladezeit, eine von '
    + 'vier. Diesen Vertragstext im Konto anzuzeigen, solange er nicht '
    + 'stimmt, hieße eine Zusage zu bewerben, die wir nicht halten. Der Block '
    + 'in „Mein Bericht" sagt seit Rang 2 ausdrücklich, was er zeigt. Der Ort '
    + 'bekommt seinen Bildschirm, sobald K5 entschieden ist — entweder die '
    + 'drei anderen Zahlen entstehen, oder die Zusage wird zusammengestrichen.',
};

function orteAusDemKatalog() {
  const quelle = fs.readFileSync(KATALOG, 'utf8');
  const treffer = [...quelle.matchAll(/^ORT_[A-Z]+ = "([a-z]+)"/gm)];
  return treffer.map((m) => m[1]);
}

function alleDateien(verzeichnis) {
  return fs.readdirSync(verzeichnis, { withFileTypes: true }).flatMap((e) => {
    const voll = path.join(verzeichnis, e.name);
    if (e.isDirectory()) return alleDateien(voll);
    return e.name.endsWith('.jsx') ? [voll] : [];
  });
}

describe('das Leistungsverzeichnis ist an den Bildschirmen angeschlossen', () => {
  const orte = orteAusDemKatalog();
  const quelltext = alleDateien(SEITEN).map((d) => fs.readFileSync(d, 'utf8')).join('\n');

  test('der Katalog wird überhaupt gefunden', () => {
    expect(orte.length).toBeGreaterThan(0);
  });

  test.each(orte)('der Ort „%s" hat einen Bildschirm oder einen Grund', (ort) => {
    const verwendet = quelltext.includes(`ort="${ort}"`);
    if (verwendet) return;
    expect(OHNE_BILDSCHIRM[ort]).toBeDefined();
  });

  test('jede Ausnahme in dieser Datei gibt es im Katalog noch', () => {
    // Sonst bliebe eine Begründung stehen, deren Gegenstand längst weg ist —
    // und der nächste Leser hielte sie für geprüft.
    Object.keys(OHNE_BILDSCHIRM).forEach((ort) => expect(orte).toContain(ort));
  });
});
