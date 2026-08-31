import { Children, cloneElement, isValidElement, useId } from 'react';

import {
  beschriftungsText, feldVerknuepfung, istVerknuepfbar, tail,
} from '../../utils/feldBeschriftung';

/**
 * Ein Formularfeld mit seiner Beschriftung — verknüpft, nicht nur daneben.
 *
 * Ersetzt acht gleich gebaute Kopien im Bestand (`Field` in
 * ComponentLibrary, AcademyAdminCourse, AcademyAdminLesson, ProjectDetail,
 * Settings, Profile; `Lbl` in Tickets und ProductDevelopment). Alle hatten
 * dieselbe Form — Beschriftung und Feld als Geschwister, ohne `htmlFor` — und
 * damit denselben Mangel (L-17).
 *
 * Die Kennung kommt aus `useId()`. Deshalb funktioniert das auch dort, wo
 * eine Komponente je Listenzeile mehrfach gerendert wird; von Hand vergebene
 * Kennungen würden dort kollidieren.
 *
 * **Zwei Vorsichtsmaßnahmen, beide aus einem roten CI-Lauf gelernt:**
 *
 * `Children.only` stand hier zuerst — und warf, sobald eine Hülle mehr als
 * ein Kind bekam. In `ComponentLibrary.jsx` ist das der Normalfall (ein
 * `<select>` und darunter eine Knopfreihe); die Seite stürzte ab, und vier
 * Browser-Tests fielen um. Jetzt wird das erste Kind gesucht, nicht das
 * einzige verlangt.
 *
 * Verknüpft wird nur ein echtes Formularelement. Zeigt `htmlFor` auf ein
 * `<div>`, ist die Verknüpfung ungültig — dann bleibt die Beschriftung ohne
 * `htmlFor` stehen, und das Feld darin braucht seinen eigenen Namen.
 */
export default function Feld({
  label,
  required = false,
  hint,
  error,
  children,
  labelStyle,
  style,
}) {
  const erzeugteId = useId();
  const kinder = Children.toArray(children);
  const stelle = kinder.findIndex(
    (kind) => isValidElement(kind) && istVerknuepfbar(kind.type),
  );

  const props = stelle >= 0 ? kinder[stelle].props : {};
  const { id, verknuepfen, zusatz } = feldVerknuepfung(props, erzeugteId);
  const anschliessen = stelle >= 0 && verknuepfen;

  const inhalt = anschliessen && Object.keys(zusatz).length
    ? kinder.map((kind, i) => (i === stelle ? cloneElement(kind, zusatz) : kind))
    : kinder;

  return (
    <div style={style}>
      <label
        htmlFor={anschliessen ? id : undefined}
        style={{
          display: 'block', fontSize: 10, fontWeight: 700,
          color: 'var(--text-tertiary)', textTransform: 'uppercase',
          letterSpacing: '0.05em', marginBottom: 4,
          ...labelStyle,
        }}
      >
        {beschriftungsText(label) || label}
        {/* Das Pflicht-Sternchen bleibt sichtbar und fällt trotzdem aus dem
            Namen: `aria-hidden` nimmt es aus der Namensberechnung heraus.
            Ein erster Entwurf hatte es einfach abgeschnitten — damit war es
            auch vom Bildschirm weg, und `<Field label="Kurstitel *">` sah
            plötzlich nicht mehr nach Pflichtangabe aus. */}
        {(required || tail(label)) && <span aria-hidden="true"> *</span>}
      </label>
      {inhalt}
      {hint && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
          {hint}
        </div>
      )}
      {error && (
        <div role="alert" style={{ fontSize: 12, color: 'var(--status-danger-text)', marginTop: 4 }}>
          {error}
        </div>
      )}
    </div>
  );
}
