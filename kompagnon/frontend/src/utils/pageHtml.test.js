import { blockMarkup, fillTemplate, seitenHtml } from './pageHtml';

const BIBLIOTHEK = {
  hero: { html_template: '<section data-block="hero"><h1>{{headline}}</h1></section>' },
  cta: { html_template: '<section data-block="cta"><p>{{text}}</p></section>' },
};

describe('fillTemplate', () => {
  test('setzt die Slot-Werte ein', () => {
    expect(fillTemplate('<h1>{{headline}}</h1>', { headline: 'Wärmepumpe' }))
      .toBe('<h1>Wärmepumpe</h1>');
  });

  test('lässt einen unbefüllten Slot stehen', () => {
    // Sichtbar bleiben ist besser als spurlos verschwinden: Eine leere Stelle
    // sieht nach Absicht aus, `{{headline}}` nach Arbeit.
    expect(fillTemplate('<h1>{{headline}}</h1>', {})).toBe('<h1>{{headline}}</h1>');
  });

  test('ein leerer Wert ist ein Wert', () => {
    expect(fillTemplate('<h1>{{headline}}</h1>', { headline: '' })).toBe('<h1></h1>');
  });

  test('ein Slot-Wert ist Text, kein Markup', () => {
    expect(fillTemplate('<h1>{{headline}}</h1>',
                        { headline: '<img src=x onerror="alert(1)">' }))
      .toBe('<h1>&lt;img src=x onerror=&quot;alert(1)&quot;&gt;</h1>');
  });

  test('kaufmännisches Und bleibt lesbar', () => {
    expect(fillTemplate('<p>{{t}}</p>', { t: 'Heizung & Sanitär' }))
      .toBe('<p>Heizung &amp; Sanitär</p>');
  });
});

describe('blockMarkup', () => {
  test('folgt der Reihenfolge, nicht der Liste', () => {
    const markup = blockMarkup(
      [{ slug: 'cta', order: 2 }, { slug: 'hero', order: 1 }], BIBLIOTHEK,
    );
    expect(markup.indexOf('data-block="hero"')).toBeLessThan(markup.indexOf('data-block="cta"'));
  });

  test('ein fehlender Block wird benannt', () => {
    expect(blockMarkup([{ slug: 'weg' }], BIBLIOTHEK))
      .toBe('<!-- Block "weg" fehlt in der Bibliothek -->');
  });

  test('ohne Blöcke bleibt es leer', () => {
    expect(blockMarkup([], BIBLIOTHEK)).toBe('');
    expect(blockMarkup(null, BIBLIOTHEK)).toBe('');
  });
});

describe('seitenHtml', () => {
  const blocks = [{ slug: 'hero', order: 1, slots: { headline: 'Meisterbetrieb' } }];

  test('CSS und Markup kommen in einem Stück', () => {
    const html = seitenHtml({ blocks, library: BIBLIOTHEK, overrideCSS: '.bg-white{}' });
    expect(html).toContain('<style>.bg-white{}</style>');
    expect(html).toContain('Meisterbetrieb');
    expect(html.indexOf('<style>')).toBeLessThan(html.indexOf('<section'));
  });

  test('ohne Blöcke entsteht keine leere Seite mit CSS', () => {
    // Sonst überschriebe „Übernehmen" eine fertige Seite mit einem Stylesheet.
    expect(seitenHtml({ blocks: [], library: BIBLIOTHEK, overrideCSS: '.x{}' })).toBe('');
  });

  test('ohne Style-Guide bleibt das nackte Markup', () => {
    expect(seitenHtml({ blocks, library: BIBLIOTHEK })).not.toContain('<style>');
  });
});
