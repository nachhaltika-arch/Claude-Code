/**
 * Kleine Helfer am Block-Markup.
 *
 * Vertragsregel R2 verlangt, dass das Wurzelelement `data-block="<slug>"`
 * traegt. Wer einen Block in der Oberflaeche umbenennt, muss die Markierung
 * mitziehen — sonst faellt ein eben noch sauberer Block beim Speichern auf
 * Entwurf zurueck, und der Grund steht in keinem Feld, das der Nutzer angefasst
 * hat.
 */

/**
 * Setzt `data-block` auf den Slug — nur die erste Fundstelle, denn genau die
 * ist das Wurzelelement. Fehlt die Markierung ganz, bleibt das Markup
 * unveraendert: sie zu erfinden waere geraten, und der Vertrag meldet den
 * Verstoss ohnehin im Klartext.
 *
 * @param {string} html
 * @param {string} slug
 * @returns {string}
 */
export function mitBlockMarkierung(html, slug) {
  if (!html || !slug) return html;
  return html.replace(/data-block\s*=\s*"[^"]*"/, `data-block="${slug}"`);
}

export default mitBlockMarkierung;
