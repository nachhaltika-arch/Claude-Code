/**
 * Die Überschrift, die eine Seite zur Seite macht.
 *
 * Lücke L-17, zweite Hälfte. Gemessen am 21.08.2026: **27 von 66 Seiten ohne
 * jedes `<h1>`**, 13 davon ganz ohne Überschrift. Ein Screenreader-Nutzer
 * springt über Überschriften — auf diesen Seiten gibt es nichts, wohin.
 *
 * Wo ein sichtbarer Titel steht, wird er befördert. Wo keiner steht, steht
 * er hier: sichtbar für Hilfsmittel, unsichtbar auf dem Bildschirm. Das ist
 * kein Ersatz für einen echten Titel im Entwurf — es ist die Aussage, dass
 * der Entwurf keinen hat, an der richtigen Stelle hinterlegt.
 *
 * `clip-path` statt `display: none`: Verstecktes mit `display: none` oder
 * `visibility: hidden` liest ein Screenreader **nicht** vor. Die Fassung hier
 * nimmt der Überschrift jede Fläche, ohne sie aus dem Baum zu nehmen.
 */
export default function SeitenTitel({ children }) {
  return (
    <h1
      style={{
        position: 'absolute',
        width: 1,
        height: 1,
        margin: -1,
        padding: 0,
        overflow: 'hidden',
        clipPath: 'inset(50%)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
    >
      {children}
    </h1>
  );
}
