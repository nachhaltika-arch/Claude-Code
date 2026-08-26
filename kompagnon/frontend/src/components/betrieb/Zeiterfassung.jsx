/**
 * Erfasste Zeit eines Projekts — und damit der Boden, auf dem die Marge steht.
 *
 * **Der Anlass (26.08.2026, Entscheidung David).** `actual_hours` war an
 * jedem Projekt 0, `time_tracking` leer, und keine Oberfläche rief
 * `POST /api/projects/{id}/time`. Die Marge rechnete damit Festpreis minus
 * Werkzeugkosten und kam überall auf ~97,5 % — eine Zahl, die aussieht wie
 * eine Messung und keine ist. Seit demselben Tag sagt die Kanban-Karte
 * „Marge: keine Zeiten"; hier bekommt sie etwas zu zeigen.
 *
 * **Wer eingetragen hat, kommt aus der Anmeldung.** Das Feld dafür gibt es
 * bewusst nicht: Ein Textfeld „wer hat gearbeitet" beantwortet die Frage
 * nicht, es lässt sie beantworten. Dieselbe Überlegung wie bei der Abnahme.
 *
 * **Die Summe kommt vom Server.** Sie hier auszurechnen wäre eine zweite
 * Quelle für dieselbe Zahl — der Fehler, der in diesem Bestand am häufigsten
 * weh getan hat.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

const LEER = { hours: '', activity_description: '' };

function zeitpunkt(roh) {
  if (!roh) return '';
  const d = new Date(roh);
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

export default function Zeiterfassung({ projectId, phase, token }) {
  const [daten, setDaten] = useState(null);
  const [formular, setFormular] = useState(LEER);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const kopf = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const laden = useCallback(async () => {
    if (!projectId) return;
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/projects/${projectId}/time`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setDaten(await antwort.json());
    } catch (e) {
      // Kein Rückfall auf „keine Zeiten": Das wäre eine Aussage über den
      // Bestand, wo gar nicht gelesen werden konnte.
      setDaten(null);
      setFehler(`Die Zeiten konnten nicht geladen werden (${e.message}).`);
    }
  }, [projectId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function eintragen(e) {
    e.preventDefault();
    const stunden = parseFloat(String(formular.hours).replace(',', '.'));
    if (!Number.isFinite(stunden) || stunden <= 0) {
      setFehler('Bitte eine Stundenzahl größer als 0 angeben.');
      return;
    }

    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/projects/${projectId}/time`, {
        method: 'POST', headers: kopf,
        body: JSON.stringify({
          hours: stunden,
          phase: phase ?? null,
          activity_description: formular.activity_description.trim(),
        }),
      });
      const d = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(d.detail || `Status ${antwort.status}`);
      setFormular(LEER);
      await laden();
    } catch (e2) {
      // Die Eingabe bleibt stehen — sie noch einmal abzutippen wäre der
      // zweite Schaden nach dem ersten.
      setFehler(`Nicht gespeichert (${e2.message}). Ihre Eingabe steht noch da.`);
    } finally {
      setLaeuft(false);
    }
  }

  if (!projectId) return null;

  return (
    <section style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-xl)', padding: '16px 18px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
          Zeiterfassung
        </h2>
        {daten && (
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            {daten.summe.toLocaleString('de-DE')} h erfasst
          </span>
        )}
      </div>

      <form onSubmit={eintragen} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)' }}>Stunden</span>
          <input
            value={formular.hours}
            onChange={(e) => setFormular({ ...formular, hours: e.target.value })}
            inputMode="decimal"
            placeholder="1,5"
            aria-label="Erfasste Stunden"
            style={{ ...feld, width: 76 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: '1 1 200px' }}>
          <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)' }}>Woran?</span>
          <input
            value={formular.activity_description}
            onChange={(e) => setFormular({ ...formular, activity_description: e.target.value })}
            placeholder="z. B. Texte eingepflegt"
            aria-label="Woran wurde gearbeitet"
            style={feld}
          />
        </label>
        <button type="submit" disabled={laeuft} style={{
          padding: '8px 16px', border: 'none', borderRadius: 'var(--radius-md)',
          background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
          fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-sans)',
          cursor: laeuft ? 'default' : 'pointer', opacity: laeuft ? 0.6 : 1,
        }}>
          {laeuft ? 'Speichert …' : 'Eintragen'}
        </button>
      </form>

      {daten?.eintraege?.length > 0 && (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 160, overflowY: 'auto' }}>
          {daten.eintraege.map((e) => (
            <li key={e.id} style={{ display: 'flex', gap: 10, fontSize: 12, color: 'var(--text-secondary, var(--text-primary))' }}>
              <span style={{ fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                {e.hours.toLocaleString('de-DE')} h
              </span>
              <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {e.activity_description || '—'}
              </span>
              <span style={{ fontSize: 10, color: 'var(--text-tertiary)', flexShrink: 0 }}>
                {e.logged_by} · {zeitpunkt(e.logged_at)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {daten?.eintraege?.length === 0 && (
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
          Noch nichts erfasst. Solange hier nichts steht, zeigt die
          Projektpipeline „Marge: keine Zeiten" — und das ist richtig so.
        </div>
      )}

      {fehler && (
        <div role="alert" style={{
          fontSize: 11, padding: '7px 10px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>
          {fehler}
        </div>
      )}
    </section>
  );
}

const feld = {
  padding: '7px 9px', fontSize: 12,
  borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', width: '100%', boxSizing: 'border-box',
};
