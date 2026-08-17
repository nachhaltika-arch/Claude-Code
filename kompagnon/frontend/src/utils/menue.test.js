import { MENUE_GRUPPEN, alleEintraege, offeneGruppen, gruppeVon } from './menue';

describe('Aufbau des Menüs', () => {
  test('jede Gruppe lässt sich mit einem Wort benennen', () => {
    // Die Prüffrage aus UX-16. „Kompagnon" bestand sie nicht: Der eigene
    // Firmenname sagt nicht, was in der Gruppe liegt.
    MENUE_GRUPPEN.forEach(g => {
      expect(g.label.split(/\s/)).toHaveLength(1);
      expect(g.label).not.toMatch(/kompagnon/i);
    });
  });

  test('jeder Eintrag hat eine Adresse', () => {
    alleEintraege().forEach(e => {
      expect(e.path).toMatch(/^\/app\//);
    });
  });

  test('keine Adresse steht in zwei Gruppen', () => {
    const pfade = alleEintraege().map(e => e.path);
    expect(new Set(pfade).size).toBe(pfade.length);
  });

  test('keine Gruppe steht allein da', () => {
    // Eine Gruppe mit einem Eintrag ist keine Gruppe, sondern ein Eintrag mit
    // Überschrift.
    MENUE_GRUPPEN.forEach(g => {
      expect(g.eintraege.length).toBeGreaterThanOrEqual(2);
    });
  });

  test('keine Gruppe wird zum Sammelbecken', () => {
    // Nicht die Größe war der Befund, sondern das Vermischen — „Kompagnon"
    // hatte sieben unverwandte Einträge. Das lässt sich nicht messen. Diese
    // Grenze ist nur ein Wächter gegen unbemerktes Anwachsen; wer sie reißt,
    // soll kurz innehalten, nicht automatisch umbauen.
    MENUE_GRUPPEN.forEach(g => {
      expect(g.eintraege.length).toBeLessThanOrEqual(7);
    });
  });

  test('keine zwei Einträge heißen fast gleich', () => {
    // UX-17: „Produkt-Editor", „Produkte" und „Produktentwicklung" standen
    // nebeneinander. Aus den Namen war nicht ableitbar, welcher wofür ist.
    const wortstamm = (s) => s.toLowerCase().replace(/[^a-zäöüß]/g, '').slice(0, 7);
    const staemme = alleEintraege().map(e => wortstamm(e.label));
    expect(new Set(staemme).size).toBe(staemme.length);
  });
});

describe('offeneGruppen', () => {
  test('öffnet die Gruppe, in der die Adresse liegt', () => {
    const offen = offeneGruppen('/app/betriebe');

    expect(offen.vertrieb).toBe(true);
    expect(offen.akquise).toBe(false);
  });

  test('auch bei einer Unteradresse', () => {
    expect(offeneGruppen('/app/betriebe/17').vertrieb).toBe(true);
  });

  test('eine fremde Adresse öffnet nichts', () => {
    const offen = offeneGruppen('/app/gibtesnicht');

    expect(Object.values(offen).every(v => v === false)).toBe(true);
  });

  test('die Zuordnung kommt aus den Einträgen selbst', () => {
    // Vorher stand die Pfadliste ein zweites Mal in `getDefaultOpen`. Wer
    // einen Eintrag verschob und die zweite Liste vergaß, bekam eine
    // Seitenleiste, die nicht zeigt, wo man ist.
    alleEintraege().forEach(e => {
      expect(gruppeVon(e.path)).not.toBeNull();
    });
  });
});

describe('Wo die früheren Sammelbecken-Einträge gelandet sind', () => {
  test.each([
    ['/app/qr-generator', 'werbung'],
    ['/app/products',     'angebot'],
    ['/app/pages',        'angebot'],
    ['/app/product',      'angebot'],
    ['/app/tickets',      'betreuung'],
    ['/app/retainer',     'betreuung'],
  ])('%s liegt unter %s', (pfad, gruppe) => {
    expect(gruppeVon(pfad)).toBe(gruppe);
  });

  test('der Produkt-Editor steht nicht mehr im Menü', () => {
    // Er bearbeitet denselben Bestand wie „Produkte" (api/products/) und ist
    // von dort erreichbar. Zwei Menüeinträge für ein Objekt sind einer zu viel.
    expect(alleEintraege().map(e => e.path)).not.toContain('/app/product-editor');
  });
});
