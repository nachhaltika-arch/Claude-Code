import { Children, cloneElement, isValidElement, useId } from 'react';

import { beschriftungsText, feldVerknuepfung } from '../../utils/feldBeschriftung';

/**
 * Ein Formularfeld mit seiner Beschriftung — verknüpft, nicht nur daneben.
 *
 * Ersetzt acht gleich gebaute Kopien im Bestand (`Field` in
 * ComponentLibrary, AcademyAdminCourse, AcademyAdminLesson, ProjectDetail,
 * BriefingWizard, LeistungsseitenWizard; `Lbl` in Tickets und
 * ProductDevelopment). Alle hatten dieselbe Form — Beschriftung und Feld als
 * Geschwister, ohne `htmlFor` — und damit denselben Mangel (L-17).
 *
 * Die Kennung kommt aus `useId()`. Deshalb funktioniert das auch dort, wo
 * eine Komponente je Listenzeile mehrfach gerendert wird; von Hand vergebene
 * Kennungen würden dort kollidieren.
 *
 * Trägt das Kind schon einen eigenen Namen (`aria-label`), bleibt der stehen:
 * Zwei Namen, die auseinanderlaufen, sind schlimmer als einer.
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
  const kind = Children.only(children);
  const props = isValidElement(kind) ? kind.props : {};
  const { id, verknuepfen, zusatz } = feldVerknuepfung(props, erzeugteId);

  const feld = isValidElement(kind) && Object.keys(zusatz).length
    ? cloneElement(kind, zusatz)
    : kind;

  return (
    <div style={style}>
      <label
        htmlFor={verknuepfen ? id : undefined}
        style={{
          display: 'block', fontSize: 10, fontWeight: 700,
          color: 'var(--text-tertiary)', textTransform: 'uppercase',
          letterSpacing: '0.05em', marginBottom: 4,
          ...labelStyle,
        }}
      >
        {beschriftungsText(label) || label}
        {required && <span aria-hidden="true"> *</span>}
      </label>
      {feld}
      {hint && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
          {hint}
        </div>
      )}
      {error && (
        <div role="alert" style={{ fontSize: 11, color: 'var(--status-danger-text)', marginTop: 4 }}>
          {error}
        </div>
      )}
    </div>
  );
}
