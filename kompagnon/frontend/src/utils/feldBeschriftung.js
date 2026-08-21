/**
 * Wie eine Beschriftung an ihr Feld kommt — die Entscheidung, ohne React.
 *
 * Lücke L-17. Gemessen am 21.08.2026: 399 Formularsteuerelemente, **18** mit
 * einem programmatisch lesbaren Namen — bei **209 `<label>`-Elementen** im
 * Quellbaum. Sichtbar war fast alles beschriftet, verknüpft fast nichts.
 *
 * Ein Teil davon steckte in Hüllkomponenten, die es acht Mal gab — `Field`,
 * `Lbl`, `Label` — und die alle dieselbe Form hatten:
 *
 *     <label>{label}</label>
 *     {children}
 *
 * Optisch eine Beschriftung, im Baum zwei Geschwister ohne Verbindung.
 *
 * `htmlFor` ist hier der richtige Weg und nicht `aria-label`: Es macht die
 * Beschriftung zugleich anklickbar, und der zugängliche Name ist derselbe
 * Text, der dasteht — er kann nicht davon abweichen. Möglich wird das durch
 * `useId()`: Auch wenn eine Komponente je Listenzeile mehrfach gerendert
 * wird, bleiben die Kennungen eindeutig. Von Hand vergebene Kennungen
 * würden dort kollidieren, und doppelte `id`s sind ein eigener Fehler.
 *
 * Diese Datei enthält nur die Entscheidung, damit sie ohne Rendern prüfbar
 * ist — der Baustein daneben (`components/ui/Feld.jsx`) wendet sie an.
 */

/**
 * Was mit einem Feld zu geschehen hat, damit die Beschriftung greift.
 *
 * @param {object} props     die Eigenschaften, die das Feld schon trägt
 * @param {string} erzeugteId  eine eindeutige Kennung (aus `useId()`)
 * @returns {{id: string|undefined, verknuepfen: boolean, zusatz: object}}
 */
/** Was `htmlFor` überhaupt verknüpfen darf. Zeigt es auf ein `<div>`, ist die
 *  Verknüpfung ungültig — dann lieber keine. */
const VERKNUEPFBAR = new Set(['input', 'select', 'textarea']);

export function istVerknuepfbar(typ) {
  return typeof typ === 'string' && VERKNUEPFBAR.has(typ);
}

export function feldVerknuepfung(props = {}, erzeugteId = '') {
  // Ein Feld, das bereits einen Namen trägt, bekommt keinen zweiten:
  // `aria-label` sticht die Beschriftung, und zwei Namen, die auseinander-
  // laufen, sind schlimmer als einer.
  const traegtSchonEinenNamen = Boolean(
    props['aria-label'] || props['aria-labelledby'],
  );

  if (traegtSchonEinenNamen) {
    return { id: props.id, verknuepfen: false, zusatz: {} };
  }

  const id = props.id || erzeugteId;
  return {
    id,
    verknuepfen: Boolean(id),
    zusatz: props.id ? {} : { id },
  };
}

/**
 * Der sichtbare Text einer Beschriftung als zugänglicher Name.
 *
 * Das Sternchen der Pflichtangabe ist Dekoration — ein Screenreader liest
 * daraus „Stern". Es bleibt sichtbar stehen und fällt nur aus dem Namen.
 */
export function beschriftungsText(label) {
  if (typeof label !== 'string') return '';
  return label.replace(/\s*[*:]+\s*$/, '').trim();
}

/**
 * Trug die Beschriftung ein Pflicht-Sternchen?
 *
 * `beschriftungsText` nimmt es heraus, damit ein Screenreader nicht „Stern"
 * vorliest. Sichtbar bleiben muss es trotzdem — sonst sieht ein Pflichtfeld
 * aus wie ein freiwilliges.
 */
export function tail(label) {
  return typeof label === 'string' && /\s*\*\s*$/.test(label);
}
