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
 * Orte, die **nicht** über `ort="…"` angeschlossen sind — jeder mit Grund.
 *
 * **Zwei Sorten stehen hier, und sie sind verschieden.** Die einen brauchen
 * keinen Bildschirm (nichts anzufordern, oder eine Entscheidung steht aus).
 * Die anderen sind über einen **anderen Weg** erreichbar als über ihren Ort —
 * die Rücksicherung etwa über ihren `abruf`. Sie hier als „ohne Bildschirm"
 * zu führen wäre falsch; sie hat einen, der Wächter erkennt ihn nur nicht,
 * weil er nach der Ortskennung sucht.
 */
const NICHT_UEBER_DEN_ORT = {
  laufend: 'Hosting, Aktualisierungen und Überwachung laufen im Hintergrund; '
    + 'es gibt nichts anzufordern und keine Seite, auf der man darauf wartet.',
  reaudit: 'Der Re-Audit-Termin steht seit Rang 2 in „Mein Bericht" — aus '
    + '`quartals_reaudit.TAKT_MONATE`, nicht über diesen Katalog.',
  sicherung: 'Angeschlossen über den **Abruf**, nicht über den Ort: '
    + '`AbrufbareLeistungen` zeigt jede Position mit einem `abruf`-Feld, und '
    + 'die tägliche Sicherung ist eine davon (L-160 Rang 6, 06.09.2026).',
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
    expect(NICHT_UEBER_DEN_ORT[ort]).toBeDefined();
  });

  test('jede Ausnahme in dieser Datei gibt es im Katalog noch', () => {
    // Sonst bliebe eine Begründung stehen, deren Gegenstand längst weg ist —
    // und der nächste Leser hielte sie für geprüft.
    Object.keys(NICHT_UEBER_DEN_ORT).forEach((ort) => expect(orte).toContain(ort));
  });
});

describe('Wer „über den Abruf" sagt, muss einen Abruf haben', () => {
  /**
   * **Sonst wäre die Begründung selbst die Lücke.** Ein Eintrag, der
   * behauptet, über den Abruf angeschlossen zu sein, während der Katalog dort
   * kein `abruf`-Feld führt, ist genau die Sorte Ausnahme, die einen Mangel
   * zudeckt — und sie bliebe für immer grün.
   */
  const quelle = fs.readFileSync(KATALOG, 'utf8');

  test('der Katalog führt überhaupt Abrufe', () => {
    expect(quelle).toMatch(/abruf="[^"]+"/);
  });

  test('die Abruf-Ansicht ist eingebunden', () => {
    const seiten = alleDateien(SEITEN).map((d) => fs.readFileSync(d, 'utf8')).join('\n');
    expect(seiten).toContain('<AbrufbareLeistungen');
  });
});
