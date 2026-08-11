/**
 * Einbaucode für das Analyse-Widget auf einer fremden Landingpage.
 *
 * Der Code besteht bewusst aus zwei Teilen: dem iframe und einem kurzen
 * Skript, das die Höhe nachführt. Ohne dieses Skript bleibt der Rahmen auf
 * seiner Starthöhe stehen — das Formular ist kürzer als das Ergebnis, also
 * steht auf der Kundenseite entweder totes Weiß unter dem Formular oder das
 * Ergebnis wird abgeschnitten. Das Widget meldet seine Höhe bereits per
 * postMessage; hier wird nur zugehört.
 */

/** Starthöhe, bis die erste Höhenmeldung eintrifft. Entspricht dem Formular. */
export const START_HEIGHT_PX = 620;

export const FRAME_ID = 'kompagnon-audit';

/**
 * Herkunft der Widget-Adresse — der Listener nimmt nur von dort etwas an.
 *
 * @param {string} embedUrl
 * @returns {string} Origin, oder '' wenn die Adresse unbrauchbar ist
 */
export function embedOrigin(embedUrl) {
  try {
    return new URL(embedUrl).origin;
  } catch {
    return '';
  }
}

/**
 * Vollständiger Einbaucode zum Kopieren.
 *
 * @param {string} embedUrl Adresse der Widget-Seite
 * @returns {string} HTML-Schnipsel für die fremde Landingpage
 */
export function buildEmbedCode(embedUrl) {
  const origin = embedOrigin(embedUrl);

  return `<!-- KOMPAGNON Website-Analyse -->
<iframe id="${FRAME_ID}" src="${embedUrl}"
        title="KOMPAGNON Website-Analyse" loading="lazy"
        style="width:100%;max-width:680px;height:${START_HEIGHT_PX}px;border:0;
               display:block;margin:0 auto"></iframe>
<script>
(function () {
  var rahmen = document.getElementById('${FRAME_ID}');
  window.addEventListener('message', function (e) {
    if (e.origin !== '${origin}') return;
    if (!e.data || e.data.type !== 'kpg-audit-height') return;
    if (rahmen.contentWindow !== e.source) return;
    var hoehe = parseInt(e.data.height, 10);
    if (hoehe > 0) rahmen.style.height = hoehe + 'px';
  });
})();
</script>`;
}
