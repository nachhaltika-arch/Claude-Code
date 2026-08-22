import { BETRIEB_ANSICHTEN, ansichtFinden } from '../utils/betriebAnsichten';

/**
 * Das Reiterband über der Betriebsliste (L-83).
 *
 * Es steht über den Filtern, nicht zwischen ihnen: Ein Reiter ist der Blick,
 * mit dem man anfängt; die Filter darunter sind das, was man danach noch
 * verstellt. Deshalb ist er auch optisch lauter als die Filterpillen.
 *
 * Passt der Zustand zu keinem Reiter, leuchtet keiner — und daneben steht,
 * dass es eine eigene Auswahl ist. Ein Reiter, der leuchtet, während die
 * Liste etwas anderes zeigt, wäre eine Falschaussage.
 */
export default function AnsichtReiter({ zustand, onWaehlen }) {
  const aktiv = ansichtFinden(zustand);

  return (
    <div
      role="tablist"
      aria-label="Ansicht der Betriebsliste"
      style={{
        display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center',
        borderBottom: '1px solid var(--border-light)',
      }}
    >
      {BETRIEB_ANSICHTEN.map((ansicht) => {
        const istAktiv = ansicht.id === aktiv;
        return (
          <button
            key={ansicht.id}
            type="button"
            role="tab"
            aria-selected={istAktiv}
            title={ansicht.hinweis}
            onClick={() => onWaehlen(ansicht.id)}
            style={{
              padding: '8px 14px', border: 'none', background: 'transparent',
              // Der aktive Reiter traegt die Linie, die das Band abschliesst —
              // daher der negative Versatz auf die Rahmenlinie.
              borderBottom: `2px solid ${istAktiv ? 'var(--brand-primary)' : 'transparent'}`,
              marginBottom: -1,
              color: istAktiv ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              fontSize: 13, fontWeight: istAktiv ? 700 : 400,
              cursor: 'pointer', fontFamily: 'var(--font-sans)',
              whiteSpace: 'nowrap', transition: 'color 0.1s',
            }}
          >
            {ansicht.label}
          </button>
        );
      })}

      {aktiv === null && (
        <span style={{
          marginLeft: 8, fontSize: 11, color: 'var(--text-tertiary)',
          fontFamily: 'var(--font-sans)',
        }}>
          Eigene Auswahl
        </span>
      )}
    </div>
  );
}
