/**
 * Aus Wireframe-Blöcken und Style-Guide eine Seite bauen.
 *
 * Dieselbe Funktion versorgt die Vorschau in der DesignView **und** das, was
 * per „Auf die Seite übernehmen" nach `sitemap_pages.mockup_html` geschrieben
 * wird. Das ist Absicht: Was übernommen wird, muss genau das sein, was vorher
 * zu sehen war — sonst gibt jemand eine Vorschau frei und liefert etwas
 * anderes aus.
 */

const ZU_MASKIEREN = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };

/** Slot-Werte sind Text, kein Markup — sonst schreibt eine Überschrift HTML. */
function maskiere(wert) {
  return String(wert).replace(/[&<>"']/g, (zeichen) => ZU_MASKIEREN[zeichen]);
}

/**
 * Ersetzt `{{slot}}`-Marker durch die Werte des Blocks.
 *
 * Ein Marker ohne Wert bleibt stehen — genau wie im Wireframe-Editor und im
 * Komponenten-Manager. Ihn zu löschen sähe nach Absicht aus; so ist zu sehen,
 * dass dort noch Text fehlt.
 */
export function fillTemplate(template, slots) {
  if (!template) return '';
  return template.replace(/\{\{(\w+)\}\}/g, (treffer, key) => {
    const wert = slots?.[key];
    if (wert === undefined || wert === null) return treffer;
    if (typeof wert !== 'string' && typeof wert !== 'number') return treffer;
    return maskiere(wert);
  });
}

/**
 * Das Markup einer Seite — die Blöcke in ihrer Reihenfolge, mit gefüllten Slots.
 *
 * @param {Array<{slug: string, order?: number, slots?: object}>} blocks
 * @param {Record<string, {html_template?: string}>} library  slug → Eintrag
 * @returns {string}
 */
export function blockMarkup(blocks, library) {
  return (blocks || [])
    .slice()
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    .map((block) => {
      const vorlage = library?.[block.slug]?.html_template;
      // Ein fehlender Block wird benannt, nicht verschwiegen: Sonst fehlt auf
      // der Seite eine Section und niemand weiß, welche.
      if (!vorlage) return `<!-- Block "${block.slug}" fehlt in der Bibliothek -->`;
      return fillTemplate(vorlage, block.slots || {});
    })
    .join('\n');
}

/**
 * Die vollständige Seite: Marken-CSS und Markup in einem Stück.
 *
 * Das CSS steht mit im Dokument, weil `mockup_html` genau so in GrapesJS
 * geladen wird — läge es woanders, käme die Seite dort grau an.
 */
export function seitenHtml({ blocks, library, overrideCSS = '' }) {
  const markup = blockMarkup(blocks, library);
  if (!markup) return '';
  return overrideCSS ? `<style>${overrideCSS}</style>\n${markup}` : markup;
}

export default seitenHtml;
