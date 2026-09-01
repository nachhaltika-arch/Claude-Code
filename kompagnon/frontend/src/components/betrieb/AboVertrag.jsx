/**
 * Welches Pflege-Abo für diesen Betrieb gilt (L-101, zweite Hälfte).
 *
 * **Warum es diesen Kasten gibt.** Bis zum 01.09.2026 stand über den
 * Pflegestunden „verbraucht" und keine Restzahl — nicht aus Versäumnis,
 * sondern weil nirgends stand, welches Abo gilt. Eine Restzahl wäre auf einer
 * Annahme gerechnet gewesen, und der Kunde läse sie als Zusage. Hier wird die
 * Annahme durch eine Angabe ersetzt.
 *
 * **Ein Wechsel ist kein Ändern.** Wer von ABO-BAS auf ABO-PRO wechselt,
 * bekommt eine neue Zeile; die alte endet im Vormonat. Deshalb gibt es hier
 * keinen „Bearbeiten"-Knopf am laufenden Vertrag: Das Produkt zu
 * überschreiben änderte rückwirkend das Kontingent jedes vergangenen Monats,
 * und eine Überschreitung von damals wäre danach keine mehr.
 *
 * **Beendete Verträge bleiben stehen.** Wer eine alte Rechnung prüft, muss
 * sehen, was damals galt.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

function monatName(wert) {
  if (!wert) return '';
  const [jahr, monat] = String(wert).split('-');
  const d = new Date(Number(jahr), Number(monat) - 1, 1);
  return Number.isNaN(d.getTime())
    ? wert
    : d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
}

function folgemonat() {
  const j = new Date();
  const d = new Date(j.getFullYear(), j.getMonth() + 1, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

function laufenderMonat() {
  const j = new Date();
  return `${j.getFullYear()}-${String(j.getMonth() + 1).padStart(2, '0')}`;
}

export default function AboVertrag({ leadId, token, onAenderung }) {
  const [daten, setDaten] = useState(null);
  const [offen, setOffen] = useState(false);
  const [produkt, setProdukt] = useState('ABO-PRO');
  const [abMonat, setAbMonat] = useState(laufenderMonat);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const kopf = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // **Der Pfad steht ausgeschrieben, statt aus einer Variablen zu wachsen.**
  // `tools/unaufgerufene-routen.py` vergleicht Aufrufe mit Routen Abschnitt
  // für Abschnitt; eine Basis, die zur Laufzeit entsteht, kann es nicht
  // zuordnen und meldet die Route als „ruft niemand auf". Genau das ist hier
  // beim ersten Entwurf passiert — und dieselbe Rüge kam am 01.09. schon
  // einmal von `test_frontend_adressen`.

  const laden = useCallback(async () => {
    if (!leadId) return;
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/leads/${leadId}/abo-vertrag`,
                                   { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setDaten(await antwort.json());
      setFehler('');
    } catch (e) {
      // Kein Rückfall auf „kein Vertrag": Das wäre eine Aussage über den
      // Bestand, wo gar nicht gelesen werden konnte — und genau die falsche,
      // weil sie die Restzahl verschwinden ließe.
      setDaten(null);
      setFehler(`Der Vertrag konnte nicht geladen werden (${e.message}).`);
    }
  }, [leadId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  // Ein Wechsel muss im Folgemonat beginnen — im selben Monat wären zwei
  // Verträge nicht unterscheidbar. Die Vorbelegung sagt das, statt den
  // Nutzer in die Fehlermeldung laufen zu lassen.
  useEffect(() => {
    if (offen) setAbMonat(daten?.laufend ? folgemonat() : laufenderMonat());
  }, [offen, daten]);

  async function speichern(e) {
    e.preventDefault();
    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/leads/${leadId}/abo-vertrag`, {
        method: 'POST', headers: kopf,
        body: JSON.stringify({ produkt, start_monat: abMonat }),
      });
      const d = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(d.detail || `Status ${antwort.status}`);
      setOffen(false);
      await laden();
      onAenderung?.();
    } catch (e2) {
      setFehler(e2.message);
    } finally {
      setLaeuft(false);
    }
  }

  async function beenden(vertragId) {
    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/abo-vertrag/${vertragId}`, {
        method: 'PATCH', headers: kopf,
        body: JSON.stringify({ end_monat: laufenderMonat() }),
      });
      const d = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(d.detail || `Status ${antwort.status}`);
      await laden();
      onAenderung?.();
    } catch (e2) {
      setFehler(e2.message);
    } finally {
      setLaeuft(false);
    }
  }

  if (!leadId) return null;

  const laufend = daten?.laufend;
  const frueher = (daten?.vertraege || []).filter((v) => !v.laeuft);

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 8,
      paddingBottom: 12, borderBottom: '1px solid var(--border-light)',
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-tertiary)' }}>
          Pflege-Abo
        </span>
        {laufend ? (
          <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
            <b>{laufend.produkt}</b>
            {' · '}{laufend.kontingent_stunden.toLocaleString('de-DE')} h/Monat
            {' · seit '}{monatName(laufend.start_monat)}
          </span>
        ) : (
          <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            keines hinterlegt
          </span>
        )}
        <button type="button" onClick={() => setOffen(!offen)} style={knopf}>
          {laufend ? 'Wechseln' : 'Abo hinterlegen'}
        </button>
        {laufend && (
          <button type="button" onClick={() => beenden(laufend.id)}
            disabled={laeuft} style={{ ...knopf, color: 'var(--text-tertiary)' }}>
            Beenden
          </button>
        )}
      </div>

      {offen && (
        <form onSubmit={speichern} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <span style={beschriftung}>Abo</span>
            <select value={produkt} onChange={(e) => setProdukt(e.target.value)}
              aria-label="Welches Pflege-Abo" style={{ ...feld, width: 'auto' }}>
              {Object.entries(daten?.abos || {}).map(([kennung, stunden]) => (
                <option key={kennung} value={kennung}>
                  {kennung} — {Number(stunden).toLocaleString('de-DE')} h/Monat
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <span style={beschriftung}>gültig ab</span>
            <input type="month" value={abMonat}
              onChange={(e) => setAbMonat(e.target.value)}
              aria-label="Ab welchem Monat gilt das Abo"
              style={{ ...feld, width: 'auto' }} />
          </label>
          <button type="submit" disabled={laeuft} style={{
            ...knopf, background: 'var(--brand-primary)',
            color: 'var(--text-on-brand)', border: 'none',
          }}>
            {laeuft ? 'Speichert …' : 'Übernehmen'}
          </button>
          {laufend && (
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)', flexBasis: '100%' }}>
              Der laufende Vertrag endet im Vormonat. Er bleibt stehen, damit
              vergangene Monate weiter mit ihrem eigenen Kontingent rechnen.
            </span>
          )}
        </form>
      )}

      {frueher.length > 0 && (
        <details>
          <summary style={{ fontSize: 12, color: 'var(--text-tertiary)', cursor: 'pointer' }}>
            {frueher.length} beendete{frueher.length === 1 ? 'r Vertrag' : ' Verträge'}
          </summary>
          <ul style={{ listStyle: 'none', margin: '6px 0 0', padding: 0, display: 'flex', flexDirection: 'column', gap: 3 }}>
            {frueher.map((v) => (
              <li key={v.id} style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                {v.produkt} · {monatName(v.start_monat)} bis {monatName(v.end_monat)}
              </li>
            ))}
          </ul>
        </details>
      )}

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, padding: '7px 10px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>
          {fehler}
        </div>
      )}
    </div>
  );
}

const beschriftung = { fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)' };

const feld = {
  padding: '7px 9px', fontSize: 12,
  borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', boxSizing: 'border-box',
};

const knopf = {
  padding: '5px 11px', fontSize: 12, fontWeight: 600,
  borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)',
  background: 'var(--bg-surface)', color: 'var(--text-primary)',
  fontFamily: 'var(--font-sans)', cursor: 'pointer',
};
