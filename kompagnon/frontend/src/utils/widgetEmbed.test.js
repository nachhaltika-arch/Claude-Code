/**
 * Der Einbaucode landet auf einer fremden Landingpage, die niemand von uns
 * pflegt. Er muss deshalb aus sich heraus korrekt sein: richtige Herkunft,
 * Höhenmeldung nur vom eigenen Rahmen, keine offene Nachrichtenannahme.
 */
import { buildEmbedCode, embedOrigin, FRAME_ID, START_HEIGHT_PX } from './widgetEmbed';

const EMBED_URL = 'https://kompagnon-frontend.onrender.com/embed/audit-widget.html';

describe('embedOrigin', () => {
  test('nimmt die Herkunft aus der Widget-Adresse', () => {
    expect(embedOrigin(EMBED_URL)).toBe('https://kompagnon-frontend.onrender.com');
  });

  test('gibt bei unbrauchbarer Adresse einen leeren Wert zurück', () => {
    expect(embedOrigin('kein-url')).toBe('');
  });
});

describe('buildEmbedCode', () => {
  test('bettet die übergebene Widget-Adresse ein', () => {
    expect(buildEmbedCode(EMBED_URL)).toContain(`src="${EMBED_URL}"`);
  });

  test('startet mit einer Höhe, die das Formular vollständig zeigt', () => {
    expect(buildEmbedCode(EMBED_URL)).toContain(`height:${START_HEIGHT_PX}px`);
  });

  test('führt die Höhe nach, damit auf der Kundenseite kein totes Weiß steht', () => {
    const code = buildEmbedCode(EMBED_URL);

    expect(code).toContain("'kpg-audit-height'");
    expect(code).toContain("rahmen.style.height = hoehe + 'px'");
  });

  test('nimmt Nachrichten nur von der Herkunft des Widgets an', () => {
    expect(buildEmbedCode(EMBED_URL))
      .toContain("if (e.origin !== 'https://kompagnon-frontend.onrender.com') return;");
  });

  test('nimmt Nachrichten nur vom eigenen Rahmen an', () => {
    // Sonst könnte ein beliebiges anderes iframe der Seite die Höhe setzen.
    expect(buildEmbedCode(EMBED_URL)).toContain('rahmen.contentWindow !== e.source');
  });

  test('spricht den Rahmen über eine feste Kennung an', () => {
    const code = buildEmbedCode(EMBED_URL);

    expect(code).toContain(`id="${FRAME_ID}"`);
    expect(code).toContain(`getElementById('${FRAME_ID}')`);
  });
});

describe('Höhenmeldung im erzeugten Code', () => {
  /** Führt das Skript aus dem Einbaucode gegen ein nachgebautes iframe aus. */
  function setupSeite(embedUrl) {
    const rahmen = document.createElement('iframe');
    rahmen.id = FRAME_ID;
    rahmen.style.height = `${START_HEIGHT_PX}px`;
    document.body.appendChild(rahmen);

    const skript = buildEmbedCode(embedUrl).match(/<script>([\s\S]*)<\/script>/)[1];
    // eslint-disable-next-line no-new-func
    new Function(skript)();

    return rahmen;
  }

  afterEach(() => { document.body.innerHTML = ''; });

  function sendeNachricht(daten, quelle, origin = 'https://kompagnon-frontend.onrender.com') {
    const ereignis = new MessageEvent('message', { data: daten, origin });
    Object.defineProperty(ereignis, 'source', { value: quelle });
    window.dispatchEvent(ereignis);
  }

  test('übernimmt die gemeldete Höhe des eigenen Rahmens', () => {
    const rahmen = setupSeite(EMBED_URL);

    sendeNachricht({ type: 'kpg-audit-height', height: 940 }, rahmen.contentWindow);

    expect(rahmen.style.height).toBe('940px');
  });

  test('ignoriert Nachrichten fremder Herkunft', () => {
    const rahmen = setupSeite(EMBED_URL);

    sendeNachricht({ type: 'kpg-audit-height', height: 940 },
                   rahmen.contentWindow, 'https://boeser-nachbar.example');

    expect(rahmen.style.height).toBe(`${START_HEIGHT_PX}px`);
  });

  test('ignoriert Nachrichten aus einem fremden Rahmen', () => {
    const rahmen = setupSeite(EMBED_URL);
    const fremd = document.createElement('iframe');
    document.body.appendChild(fremd);

    sendeNachricht({ type: 'kpg-audit-height', height: 940 }, fremd.contentWindow);

    expect(rahmen.style.height).toBe(`${START_HEIGHT_PX}px`);
  });

  test('ignoriert Nachrichten ohne verwertbare Höhe', () => {
    const rahmen = setupSeite(EMBED_URL);

    sendeNachricht({ type: 'kpg-audit-height', height: 'hoch' }, rahmen.contentWindow);

    expect(rahmen.style.height).toBe(`${START_HEIGHT_PX}px`);
  });

  test('ignoriert fremde Nachrichtentypen', () => {
    const rahmen = setupSeite(EMBED_URL);

    sendeNachricht({ type: 'irgendwas-anderes', height: 940 }, rahmen.contentWindow);

    expect(rahmen.style.height).toBe(`${START_HEIGHT_PX}px`);
  });
});
