import { naechsterSchritt } from './naechsterSchritt';

describe('naechsterSchritt', () => {
  test('ohne Audit ist der Audit dran', () => {
    expect(naechsterSchritt({ hatAudit: false, hatProjekt: false, hatEmail: true, status: 'new' }))
      .toBe('audit');
  });

  test('mit Audit und E-Mail ist die Kaltakquise dran', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: false, hatEmail: true, status: 'new' }))
      .toBe('kaltakquise');
  });

  test('ohne E-Mail gibt es nichts zu schicken — dann die Stammdaten', () => {
    // Der Knopf für die Kaltakquise wird ohne Adresse gar nicht erst gezeigt.
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: false, hatEmail: false, status: 'new' }))
      .toBe('stammdaten');
  });

  test('gewonnen und noch kein Projekt: das Projekt anlegen', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: false, hatEmail: true, status: 'won' }))
      .toBe('projekt');
  });

  test('gibt es das Projekt schon, führt der Weg dorthin', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: true, hatEmail: true, status: 'won' }))
      .toBe('zum_projekt');
  });

  test('das Projekt schlägt den Status', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: true, hatEmail: true, status: 'new' }))
      .toBe('zum_projekt');
  });

  test('verloren: kein Schritt drängt sich auf', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: false, hatEmail: true, status: 'lost' }))
      .toBe(null);
  });

  test('nach dem Angebot wartet man auf Antwort, nicht auf einen Knopf', () => {
    expect(naechsterSchritt({ hatAudit: true, hatProjekt: false, hatEmail: true, status: 'proposal_sent' }))
      .toBe(null);
  });

  test('ohne Angaben wird nichts hervorgehoben', () => {
    expect(naechsterSchritt()).toBe('audit');
  });
});
