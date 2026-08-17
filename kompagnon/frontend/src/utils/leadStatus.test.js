/**
 * Ein unbekannter Wert darf nie roh in der Oberfläche landen.
 *
 * Genau das ist passiert: `Companies.jsx` hatte eine Farbabbildung ohne
 * Labels, also stand dort `proposal_sent` — englisch, mit Unterstrich, in
 * einer deutschen Liste. Und weil der Schlüssel in der Farbabbildung fehlte,
 * fiel es nicht einmal auf: Der Rückfall lieferte eine neutrale Farbe.
 */
import {
  LEAD_STATUS,
  leadStatusLabel,
  leadStatusVariant,
  leadSourceLabel,
} from './leadStatus';

// ── Die Werte, die produktiv in der Datenbank stehen ──────────────────
// Am 2026-08-16 in der Produktiv-DB gezählt.
const ECHTE_STATUS = ['new', 'contacted', 'qualified', 'proposal_sent', 'won', 'lost'];
const ECHTE_QUELLEN = ['domain_import', 'landing_audit', 'stripe_checkout', 'embed_audit'];

describe('Status', () => {
  test('jeder produktiv vorkommende Status hat ein deutsches Wort', () => {
    // Arrange / Act / Assert
    ECHTE_STATUS.forEach(status => {
      expect(LEAD_STATUS[status]).toBeDefined();
      expect(leadStatusLabel(status)).not.toBe(status);
    });
  });

  test('proposal_sent hat ein Wort — der Status, der ohne Rahmen dastand', () => {
    expect(leadStatusLabel('proposal_sent')).toBe('Angebot');
    expect(leadStatusVariant('proposal_sent')).toBe('warning');
  });

  test('kein Label enthält einen Unterstrich', () => {
    Object.values(LEAD_STATUS).forEach(({ label }) => {
      expect(label).not.toMatch(/_/);
    });
  });

  test('ein unbekannter Status wird lesbar gemacht, nicht roh gezeigt', () => {
    // Arrange — ein Wert, den niemand vorhergesehen hat
    const unbekannt = 'awaiting_signature';

    // Act
    const label = leadStatusLabel(unbekannt);

    // Assert — lesbar, und nicht als bekannter Status getarnt
    expect(label).toBe('Awaiting signature');
    expect(leadStatusVariant(unbekannt)).toBe('neutral');
  });

  test('ein unbekannter Status wird NICHT als „Neu" ausgegeben', () => {
    // Der stille Fehlgriff in Customers.jsx: `STATUS[x] || STATUS.new`
    expect(leadStatusLabel('irgendwas')).not.toBe('Neu');
  });

  test('leer bleibt leer, nicht erfunden', () => {
    expect(leadStatusLabel('')).toBe('Unbekannt');
    expect(leadStatusLabel(null)).toBe('Unbekannt');
    expect(leadStatusLabel(undefined)).toBe('Unbekannt');
  });

  test('Groß- und Kleinschreibung ist egal', () => {
    expect(leadStatusLabel('WON')).toBe('Gewonnen');
  });
});

describe('Herkunft', () => {
  test('jede produktiv vorkommende Quelle hat ein deutsches Wort', () => {
    ECHTE_QUELLEN.forEach(quelle => {
      expect(leadSourceLabel(quelle)).not.toBe(quelle);
    });
  });

  test('ein Kampagnenname bleibt erhalten, nur lesbar', () => {
    // Freitext ist hier normal — er wird beim Import vergeben.
    expect(leadSourceLabel('postkarte-koblenz-mai-2025'))
      .toBe('Postkarte koblenz mai 2025');
  });

  test('embed_audit heisst Analyse-Widget, nicht „Embed audit"', () => {
    // Der Rückfall hatte den Wert nur lesbar gemacht — halb englisch. Er hat
    // sich damit verraten, wie gebaut; nachgetragen gehörte er trotzdem.
    expect(leadSourceLabel('embed_audit')).toBe('Analyse-Widget');
  });

  test('ohne Quelle wird nichts behauptet', () => {
    expect(leadSourceLabel('')).toBe('Unbekannt');
  });
});
