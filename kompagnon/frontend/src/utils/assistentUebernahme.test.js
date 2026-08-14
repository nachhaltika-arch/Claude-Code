import { textUebernehmen, hinweisSchluessel, zeigeHinweis } from './assistentUebernahme';

describe('textUebernehmen', () => {
  test('setzt den Vorschlag ein, wenn das Feld leer ist', () => {
    expect(textUebernehmen('', 'Wärmepumpen-Einbau')).toBe('Wärmepumpen-Einbau');
  });

  test('behält vorhandenen Text und hängt den Vorschlag darunter', () => {
    const ergebnis = textUebernehmen('Heizung', 'Wärmepumpen-Einbau');

    expect(ergebnis).toBe('Heizung\nWärmepumpen-Einbau');
  });

  test('hängt einen bereits enthaltenen Vorschlag nicht zweimal an', () => {
    const vorhanden = 'Heizung\nWärmepumpen-Einbau';

    expect(textUebernehmen(vorhanden, 'Wärmepumpen-Einbau')).toBe(vorhanden);
  });

  test('lässt das Feld unverändert, wenn der Vorschlag leer ist', () => {
    expect(textUebernehmen('Heizung', '   ')).toBe('Heizung');
  });

  test('kommt mit fehlenden Werten zurecht', () => {
    expect(textUebernehmen(undefined, undefined)).toBe('');
  });
});

describe('zeigeHinweis', () => {
  const befund = { brauchbar: false, hinweise: ['Zu allgemein.', 'Nennen Sie eine Zahl.'] };

  test('zeigt den Hinweis, wenn die Antwort nicht brauchbar ist', () => {
    expect(zeigeHinweis('usp', befund, new Set())).toBe('Zu allgemein. Nennen Sie eine Zahl.');
  });

  test('schweigt, wenn die Antwort brauchbar ist', () => {
    expect(zeigeHinweis('usp', { brauchbar: true, hinweise: ['egal'] }, new Set())).toBe('');
  });

  test('wiederholt denselben Hinweis zum selben Feld nicht', () => {
    const gesehen = new Set([hinweisSchluessel('usp', befund.hinweise)]);

    expect(zeigeHinweis('usp', befund, gesehen)).toBe('');
  });

  test('zeigt einen anderen Hinweis zum selben Feld trotzdem', () => {
    const gesehen = new Set([hinweisSchluessel('usp', befund.hinweise)]);

    expect(zeigeHinweis('usp', { brauchbar: false, hinweise: ['Zu kurz.'] }, gesehen))
      .toBe('Zu kurz.');
  });

  test('zeigt denselben Hinweistext zu einem anderen Feld erneut', () => {
    const gesehen = new Set([hinweisSchluessel('usp', befund.hinweise)]);

    expect(zeigeHinweis('leistungen', befund, gesehen)).not.toBe('');
  });

  test('schweigt bei leerem Befund', () => {
    expect(zeigeHinweis('usp', null, new Set())).toBe('');
    expect(zeigeHinweis('usp', { brauchbar: false, hinweise: [] }, new Set())).toBe('');
  });
});
