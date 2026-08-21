import { meldung, schreibe } from './schreiben';

const antwortMit = (status, text = '') => ({
  ok: status >= 200 && status < 300,
  status,
  text: async () => text,
});

describe('schreibe', () => {
  test('eine gelungene Antwort kommt durch', async () => {
    const ergebnis = await schreibe(async () => antwortMit(200));

    expect(ergebnis.ok).toBe(true);
    expect(ergebnis.fehler).toBeUndefined();
  });

  test('ein Serverfehler wird zur Meldung, nicht zur Stille', async () => {
    // Genau der Fall aus der Akademie: 500, und die Oberfläche zeigte nichts.
    const ergebnis = await schreibe(
      async () => antwortMit(500, '{"detail":"Internal server error"}'),
      'Die Lektion',
    );

    expect(ergebnis.ok).toBe(false);
    expect(ergebnis.fehler).toContain('Die Lektion');
    expect(ergebnis.fehler).toContain('500');
  });

  test('eine abgebrochene Verbindung wird zur Meldung', async () => {
    const ergebnis = await schreibe(async () => { throw new Error('Failed to fetch'); });

    expect(ergebnis.ok).toBe(false);
    expect(ergebnis.fehler).toMatch(/keine Verbindung/i);
  });

  test('403 sagt, woran es liegt', async () => {
    const ergebnis = await schreibe(async () => antwortMit(403), 'Die Freigabe');

    expect(ergebnis.fehler).toBe('Die Freigabe nicht gespeichert. Dafür fehlt die Berechtigung.');
  });

  test('401 verweist auf die Anmeldung', async () => {
    expect(meldung('Der Kurs', 401)).toMatch(/neu anmelden/);
  });

  test('ein unbekannter Status bleibt trotzdem lesbar', () => {
    expect(meldung('Der Kurs', 418)).toBe('Der Kurs nicht gespeichert (Status 418).');
  });
});
