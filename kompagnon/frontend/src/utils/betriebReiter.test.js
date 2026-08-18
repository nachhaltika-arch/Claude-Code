import {
  HAUPT_REITER,
  MEHR_REITER,
  aufteilung,
  istImMehr,
} from './betriebReiter';

describe('Aufteilung der Reiter', () => {
  test('sechs stehen oben', () => {
    expect(HAUPT_REITER).toHaveLength(6);
  });

  test('oben steht, was täglich gebraucht wird', () => {
    expect(HAUPT_REITER).toEqual([
      'overview', 'contact', 'audits', 'offer', 'messages', 'dateien',
    ]);
  });

  test('die übrigen vier stehen hinter „Mehr"', () => {
    expect(MEHR_REITER).toEqual(['deals', 'akademy', 'qrcode', 'emails']);
  });

  test('zusammen sind es weiterhin alle zehn', () => {
    expect([...HAUPT_REITER, ...MEHR_REITER]).toHaveLength(10);
  });

  test('kein Reiter steht an zwei Stellen', () => {
    const alle = [...HAUPT_REITER, ...MEHR_REITER];
    expect(new Set(alle).size).toBe(alle.length);
  });
});

describe('istImMehr', () => {
  test('erkennt einen untergeordneten Reiter', () => {
    expect(istImMehr('qrcode')).toBe(true);
  });

  test('erkennt einen Hauptreiter', () => {
    expect(istImMehr('audits')).toBe(false);
  });

  test('ein unbekannter Reiter gilt nicht als untergeordnet', () => {
    expect(istImMehr('gibtesnicht')).toBe(false);
  });
});

describe('aufteilung', () => {
  const REITER = [
    { id: 'overview', label: 'Übersicht' },
    { id: 'deals', label: 'Deals' },
    { id: 'messages', label: 'Nachrichten' },
    { id: 'contact', label: 'Kontakt' },
    { id: 'audits', label: 'Audits' },
    { id: 'dateien', label: 'Dateien' },
    { id: 'akademy', label: 'Akademie' },
    { id: 'offer', label: 'Angebot' },
    { id: 'qrcode', label: 'Zugang' },
    { id: 'emails', label: 'E-Mails' },
  ];

  test('teilt in oben und hinter „Mehr"', () => {
    const { haupt, mehr } = aufteilung(REITER, 'overview');

    expect(haupt.map(r => r.id)).toEqual(HAUPT_REITER);
    expect(mehr.map(r => r.id)).toEqual(MEHR_REITER);
  });

  test('behält die Reihenfolge von HAUPT_REITER, nicht die der Eingabe', () => {
    // In der Eingabe steht `deals` an zweiter Stelle. Oben soll trotzdem
    // Kontakt folgen — sonst entscheidet die alte Reihenfolge weiter.
    const { haupt } = aufteilung(REITER, 'overview');

    expect(haupt[1].id).toBe('contact');
  });

  test('ist ein untergeordneter Reiter offen, ist „Mehr" hervorgehoben', () => {
    expect(aufteilung(REITER, 'qrcode').mehrIstAktiv).toBe(true);
  });

  test('bei einem Hauptreiter ist „Mehr" nicht hervorgehoben', () => {
    expect(aufteilung(REITER, 'audits').mehrIstAktiv).toBe(false);
  });

  test('ein Reiter, den es in der Liste nicht gibt, wird nicht erfunden', () => {
    const nurZwei = [{ id: 'overview', label: 'Ü' }, { id: 'qrcode', label: 'Z' }];

    const { haupt, mehr } = aufteilung(nurZwei, 'overview');

    expect(haupt.map(r => r.id)).toEqual(['overview']);
    expect(mehr.map(r => r.id)).toEqual(['qrcode']);
  });
});
