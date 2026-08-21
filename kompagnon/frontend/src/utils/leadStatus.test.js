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
  herkunftLabel,
  herkunftVariant,
  rechtsgrundlageLabel,
  RECHTSGRUNDLAGE_OFFEN,
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

// ── L-59: Herkunft und Rechtsgrundlage ──────────────────────────────
//
// Wir prüfen bei Kunden, ob ihre Seite eine Rechtsgrundlage nennt
// (`audit_collectors.py:255` sucht nach „Art. 6"), und führten sie für die
// eigenen Leaddaten an keiner Stelle. 79 Felder am Lead, keines nannte sie.

describe('Herkunft der Daten', () => {
  test('benennt beide geführten Klassen', () => {
    expect(herkunftLabel('eingehend')).toBe('Selbst gemeldet');
    expect(herkunftLabel('kaltakquise')).toBe('Von uns erhoben');
  });

  test('eine ungeführte Quelle bleibt sichtbar ungeklärt', () => {
    // Ein Kampagnenname wie `HWK-Muenchen` bekommt keine Herkunft — das
    // Betriebsblatt soll das zeigen, nicht in eine Klasse drängen.
    expect(herkunftLabel(null)).toBe('Herkunft ungeklärt');
    expect(herkunftVariant(null)).toBe('neutral');
  });
});

describe('Rechtsgrundlage', () => {
  test('nennt Artikel und Bedeutung zusammen', () => {
    expect(rechtsgrundlageLabel('art6_1_b'))
      .toBe('Art. 6 I b — Vertrag oder vorvertragliche Maßnahme');
  });

  test('der offene Fall ist keine Leerstelle, sondern eine Aufgabe', () => {
    expect(rechtsgrundlageLabel(null)).toBe(RECHTSGRUNDLAGE_OFFEN);
    expect(rechtsgrundlageLabel(undefined)).toBe(RECHTSGRUNDLAGE_OFFEN);
  });

  test('ein unbekannter Wert wird lesbar, nie roh ausgegeben', () => {
    expect(rechtsgrundlageLabel('art9_2_a')).not.toBe('art9_2_a');
  });
});

describe('Quellen-Wortschatz', () => {
  test('kennt die Werte, die die Webhooks schreiben', () => {
    // Gemessen 21.08.2026 an routers/webhooks.py:107-162 — sie schreiben
    // facebook/linkedin/google/postkarte/telefon, nicht webhook_facebook.
    for (const quelle of ['facebook', 'linkedin', 'google', 'postkarte', 'telefon']) {
      expect(leadSourceLabel(quelle)).not.toBe(quelle);
    }
  });
});
