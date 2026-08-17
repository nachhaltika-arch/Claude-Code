import {
  sucheBetriebe,
  filterNachStatus,
  filterNachQuelle,
  sortiereBetriebe,
  betriebeAufbereiten,
  betriebeStatistik,
  quellenAusBetrieben,
  statusAusBetrieben,
  BETRIEB_SORTIERUNGEN,
} from './betriebeListe';

const betrieb = (ueberschreiben = {}) => ({
  id: 1,
  company_name: 'Müller Haustechnik',
  display_name: null,
  city: 'Boppard',
  trade: 'Heizung',
  email: 'info@mueller.de',
  website_url: 'https://mueller-haustechnik.de',
  status: 'new',
  lead_source: 'manual',
  analysis_score: 0,
  created_at: '2026-01-01T10:00:00Z',
  ...ueberschreiben,
});

// ── Suche ──────────────────────────────────────────────────────────────

describe('sucheBetriebe', () => {
  test('gibt bei leerem Suchbegriff alle Betriebe zurück', () => {
    const liste = [betrieb({ id: 1 }), betrieb({ id: 2 })];

    const treffer = sucheBetriebe(liste, '');

    expect(treffer).toHaveLength(2);
  });

  test('findet unabhängig von Groß- und Kleinschreibung', () => {
    const liste = [betrieb({ company_name: 'Müller Haustechnik' })];

    expect(sucheBetriebe(liste, 'MÜLLER')).toHaveLength(1);
  });

  test('durchsucht auch Ort, Gewerk, E-Mail und Website', () => {
    const liste = [betrieb()];

    expect(sucheBetriebe(liste, 'boppard')).toHaveLength(1);
    expect(sucheBetriebe(liste, 'heizung')).toHaveLength(1);
    expect(sucheBetriebe(liste, 'info@mueller')).toHaveLength(1);
    expect(sucheBetriebe(liste, 'haustechnik.de')).toHaveLength(1);
  });

  test('findet auch über den Anzeigenamen, wenn der Firmenname abweicht', () => {
    const liste = [betrieb({ company_name: 'adrian-vidak.de', display_name: 'Adrian Vidak' })];

    expect(sucheBetriebe(liste, 'adrian vidak')).toHaveLength(1);
  });

  test('gibt eine leere Liste zurück, wenn nichts passt', () => {
    expect(sucheBetriebe([betrieb()], 'zzz')).toEqual([]);
  });

  test('fasst die Eingabeliste nicht an', () => {
    const liste = [betrieb({ id: 1 }), betrieb({ id: 2, company_name: 'Andere' })];

    sucheBetriebe(liste, 'andere');

    expect(liste).toHaveLength(2);
  });

  test('kommt mit fehlenden Feldern zurecht', () => {
    const liste = [{ id: 9 }];

    expect(() => sucheBetriebe(liste, 'irgendwas')).not.toThrow();
    expect(sucheBetriebe(liste, 'irgendwas')).toEqual([]);
  });
});

// ── Filter ─────────────────────────────────────────────────────────────

describe('filterNachStatus', () => {
  test('gibt bei „alle" die ganze Liste zurück', () => {
    const liste = [betrieb({ status: 'new' }), betrieb({ status: 'won' })];

    expect(filterNachStatus(liste, 'alle')).toHaveLength(2);
  });

  test('filtert auf genau einen Status', () => {
    const liste = [betrieb({ id: 1, status: 'new' }), betrieb({ id: 2, status: 'won' })];

    const treffer = filterNachStatus(liste, 'won');

    expect(treffer).toHaveLength(1);
    expect(treffer[0].id).toBe(2);
  });
});

describe('filterNachQuelle', () => {
  test('zählt Betriebe ohne Quelle zu „manual"', () => {
    const liste = [
      betrieb({ id: 1, lead_source: null }),
      betrieb({ id: 2, lead_source: 'manual' }),
      betrieb({ id: 3, lead_source: 'HWK-Muenchen' }),
    ];

    expect(filterNachQuelle(liste, 'manual')).toHaveLength(2);
  });

  test('filtert auf eine benannte Quelle', () => {
    const liste = [
      betrieb({ id: 1, lead_source: 'embed_audit' }),
      betrieb({ id: 2, lead_source: 'manual' }),
    ];

    const treffer = filterNachQuelle(liste, 'embed_audit');

    expect(treffer).toHaveLength(1);
    expect(treffer[0].id).toBe(1);
  });
});

// ── Sortierung ─────────────────────────────────────────────────────────

describe('sortiereBetriebe', () => {
  test('sortiert nach Namen von A nach Z', () => {
    const liste = [betrieb({ company_name: 'Zimmermann' }), betrieb({ company_name: 'Ackermann' })];

    const sortiert = sortiereBetriebe(liste, 'name');

    expect(sortiert.map(b => b.company_name)).toEqual(['Ackermann', 'Zimmermann']);
  });

  test('sortiert nach Score absteigend', () => {
    const liste = [betrieb({ analysis_score: 20 }), betrieb({ analysis_score: 80 })];

    expect(sortiereBetriebe(liste, 'score').map(b => b.analysis_score)).toEqual([80, 20]);
  });

  test('sortiert nach Datum, das Neueste zuerst', () => {
    const liste = [
      betrieb({ id: 1, created_at: '2026-01-01T00:00:00Z' }),
      betrieb({ id: 2, created_at: '2026-06-01T00:00:00Z' }),
    ];

    expect(sortiereBetriebe(liste, 'date').map(b => b.id)).toEqual([2, 1]);
  });

  test('behandelt ein ungültiges Datum als ältesten Eintrag statt zu stolpern', () => {
    const liste = [
      betrieb({ id: 1, created_at: 'kein-datum' }),
      betrieb({ id: 2, created_at: '2026-06-01T00:00:00Z' }),
    ];

    expect(sortiereBetriebe(liste, 'date').map(b => b.id)).toEqual([2, 1]);
  });

  test('sortiert eine Kopie und lässt die Eingabe unverändert', () => {
    const liste = [betrieb({ company_name: 'Zimmermann' }), betrieb({ company_name: 'Ackermann' })];

    sortiereBetriebe(liste, 'name');

    expect(liste[0].company_name).toBe('Zimmermann');
  });

  test('jede angebotene Sortierung liefert eine vollständige Liste', () => {
    const liste = [betrieb({ id: 1 }), betrieb({ id: 2, city: 'Koblenz' })];

    for (const { key } of BETRIEB_SORTIERUNGEN) {
      expect(sortiereBetriebe(liste, key)).toHaveLength(2);
    }
  });
});

// ── Zusammenspiel ──────────────────────────────────────────────────────

describe('betriebeAufbereiten', () => {
  test('wendet Suche, beide Filter und Sortierung zusammen an', () => {
    const liste = [
      betrieb({ id: 1, company_name: 'Zeta Heizung',  status: 'won', lead_source: 'manual' }),
      betrieb({ id: 2, company_name: 'Alpha Heizung', status: 'won', lead_source: 'manual' }),
      betrieb({ id: 3, company_name: 'Beta Heizung',  status: 'new', lead_source: 'manual' }),
      betrieb({ id: 4, company_name: 'Gamma Heizung', status: 'won', lead_source: 'embed_audit' }),
    ];

    const ergebnis = betriebeAufbereiten({
      betriebe: liste, suche: 'heizung', status: 'won', quelle: 'manual', sortierung: 'name',
    });

    expect(ergebnis.map(b => b.company_name)).toEqual(['Alpha Heizung', 'Zeta Heizung']);
  });

  test('ohne Argumente eine leere Liste statt eines Fehlers', () => {
    expect(betriebeAufbereiten()).toEqual([]);
  });
});

// ── Kennzahlen ─────────────────────────────────────────────────────────

describe('betriebeStatistik', () => {
  test('zählt Gesamt und Betriebe mit Score', () => {
    const liste = [
      betrieb({ analysis_score: 0 }),
      betrieb({ analysis_score: 40 }),
      betrieb({ analysis_score: 60 }),
    ];

    const stat = betriebeStatistik(liste);

    expect(stat.gesamt).toBe(3);
    expect(stat.mitScore).toBe(2);
  });

  test('mittelt nur über Betriebe, die einen Score haben', () => {
    const liste = [
      betrieb({ analysis_score: 0 }),
      betrieb({ analysis_score: 40 }),
      betrieb({ analysis_score: 60 }),
    ];

    expect(betriebeStatistik(liste).durchschnittsScore).toBe(50);
  });

  test('gibt 0 als Durchschnitt zurück, wenn kein Betrieb einen Score hat', () => {
    expect(betriebeStatistik([betrieb({ analysis_score: 0 })]).durchschnittsScore).toBe(0);
  });

  test('führt nur Statuswerte auf, die vorkommen', () => {
    const liste = [betrieb({ status: 'new' }), betrieb({ status: 'won' }), betrieb({ status: 'won' })];

    const zaehler = betriebeStatistik(liste).statusZaehler;

    expect(zaehler).toEqual([
      { key: 'new', label: 'Neu',      anzahl: 1 },
      { key: 'won', label: 'Gewonnen', anzahl: 2 },
    ]);
  });

  test('die Statuszähler summieren sich auf die Gesamtzahl, auch bei unbekanntem Status', () => {
    // Der Fund vom laufenden System: 27 Neu + 2 Gewonnen bei 30 Betrieben.
    // Der dreissigste stand auf `opt_in` und fiel aus jeder Zaehlung.
    const liste = [
      ...Array.from({ length: 27 }, (_, i) => betrieb({ id: i, status: 'new' })),
      betrieb({ id: 28, status: 'won' }),
      betrieb({ id: 29, status: 'won' }),
      betrieb({ id: 30, status: 'opt_in' }),
    ];

    const stat = betriebeStatistik(liste);
    const summe = stat.statusZaehler.reduce((s, z) => s + z.anzahl, 0);

    expect(summe).toBe(stat.gesamt);
  });

  test('eine leere Liste ergibt Nullen statt eines Fehlers', () => {
    expect(betriebeStatistik([])).toEqual({
      gesamt: 0, mitScore: 0, durchschnittsScore: 0, statusZaehler: [],
    });
  });

  test('die Zahlen gelten für genau die übergebene Liste', () => {
    // Der Fehler, der Paket 2 ausgeloest hat: „Kunden" lud nur 50 von 61
    // Datensaetzen und rechnete die Kennzahlen darueber. Die Zahl war nicht
    // gefiltert, sondern abgeschnitten — und behauptete trotzdem „Gesamt".
    const alle = Array.from({ length: 61 }, (_, i) => betrieb({ id: i, analysis_score: 50 }));

    expect(betriebeStatistik(alle).gesamt).toBe(61);
    expect(betriebeStatistik(alle.slice(0, 50)).gesamt).toBe(50);
  });
});

// ── Statuswerte ────────────────────────────────────────────────────────

describe('statusAusBetrieben', () => {
  test('führt nur Statuswerte auf, die vorkommen', () => {
    const liste = [betrieb({ status: 'new' }), betrieb({ status: 'won' })];

    expect(statusAusBetrieben(liste).map(s => s.key)).toEqual(['new', 'won']);
  });

  test('bietet auch einen unbekannten Status als Filter an', () => {
    const liste = [betrieb({ status: 'new' }), betrieb({ status: 'opt_in' })];

    expect(statusAusBetrieben(liste).map(s => s.key)).toContain('opt_in');
  });

  test('macht den unbekannten Status lesbar, statt ihn roh zu zeigen', () => {
    const eintrag = statusAusBetrieben([betrieb({ status: 'opt_in' })])[0];

    expect(eintrag.label).toBe('Opt in');
  });

  test('sortiert bekannte Werte nach dem Vertriebsweg, unbekannte dahinter', () => {
    const liste = [
      betrieb({ status: 'opt_in' }),
      betrieb({ status: 'won' }),
      betrieb({ status: 'new' }),
    ];

    expect(statusAusBetrieben(liste).map(s => s.key)).toEqual(['new', 'won', 'opt_in']);
  });

  test('zählt einen fehlenden Status als „new" — so liefert ihn der Server', () => {
    const liste = [betrieb({ status: null }), betrieb({ status: 'new' })];

    const neu = statusAusBetrieben(liste).find(s => s.key === 'new');

    expect(neu.anzahl).toBe(2);
  });

  test('eine leere Liste ergibt keine Filter', () => {
    expect(statusAusBetrieben([])).toEqual([]);
  });
});

// ── Quellen ────────────────────────────────────────────────────────────

describe('quellenAusBetrieben', () => {
  test('bietet nur Quellen an, die wirklich vorkommen', () => {
    const liste = [
      betrieb({ lead_source: 'manual' }),
      betrieb({ lead_source: 'embed_audit' }),
    ];

    const keys = quellenAusBetrieben(liste).map(q => q.key);

    expect(keys).toEqual(['alle', 'embed_audit', 'manual']);
  });

  test('führt die häufigste Quelle zuerst', () => {
    const liste = [
      betrieb({ lead_source: 'manual' }),
      betrieb({ lead_source: 'embed_audit' }),
      betrieb({ lead_source: 'embed_audit' }),
    ];

    expect(quellenAusBetrieben(liste)[1].key).toBe('embed_audit');
  });

  test('übersetzt die Quelle in ein lesbares Wort', () => {
    const eintrag = quellenAusBetrieben([betrieb({ lead_source: 'embed_audit' })])[1];

    expect(eintrag.label).toBe('Analyse-Widget');
  });

  test('macht auch einen unbekannten Kampagnennamen lesbar', () => {
    const eintrag = quellenAusBetrieben([betrieb({ lead_source: 'postkarte-koblenz-mai-2026' })])[1];

    expect(eintrag.label).toBe('Postkarte koblenz mai 2026');
  });

  test('zählt Betriebe ohne Quelle unter „manual"', () => {
    const liste = [betrieb({ lead_source: null }), betrieb({ lead_source: 'manual' })];

    const manual = quellenAusBetrieben(liste).find(q => q.key === 'manual');

    expect(manual.anzahl).toBe(2);
  });

  test('„Alle Quellen" trägt die Gesamtzahl', () => {
    const liste = [betrieb({ lead_source: 'manual' }), betrieb({ lead_source: 'embed_audit' })];

    expect(quellenAusBetrieben(liste)[0].anzahl).toBe(2);
  });

  test('eine leere Liste ergibt nur „Alle Quellen"', () => {
    expect(quellenAusBetrieben([])).toEqual([{ key: 'alle', label: 'Alle Quellen', anzahl: 0 }]);
  });
});
