/**
 * Der Ladekreisel der Schritt-Ansichten.
 *
 * Acht Zeilen in einer eigenen Datei — weil ihn `SchrittInhalt` **und** die
 * Technik-Einbettungen brauchen. Ihn zu kopieren waere die billigere
 * Loesung und die schlechtere: Zwei Fassungen desselben Bausteins laufen
 * auseinander, und genau das ist am 22.08.2026 an zwei Stellen passiert
 * (`_serialize` in den Briefing-Routern, `PHASEN` hier).
 */
export default function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}>
      <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin .8s linear infinite' }} />
    </div>
  );
}
