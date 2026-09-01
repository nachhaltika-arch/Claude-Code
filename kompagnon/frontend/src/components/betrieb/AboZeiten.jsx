/**
 * Pflegestunden eines Betriebs — die zweite Achse der Zeiterfassung (L-101).
 *
 * **Warum neben und nicht in `Zeiterfassung.jsx`.** Die zählt je Projekt und
 * Bauphase und speist die Marge. Diese hier zählt je **Monat und Betrieb**
 * und speist das Abo-Kontingent. Dieselbe Tabelle, zwei Fragen — und wer sie
 * in einen Kasten legt, lädt dazu ein, Herstellung als Pflege zu buchen.
 *
 * **Sie steht am Betrieb und nicht am Projekt**, weil ein Abo gar kein
 * Projekt hat. Genau daran ist L-101 hängengeblieben: Das Werkzeug war da,
 * die Achse fehlte.
 *
 * **Die Restzahl kam am 01.09.2026 dazu — unter einer Bedingung.** Bis dahin
 * stand hier „verbraucht" und sonst nichts, weil nirgends hinterlegt war,
 * welches Abo gilt; eine Restzahl wäre auf einer Annahme gerechnet gewesen,
 * und der Kunde läse sie als Zusage. Jetzt steht der Vertrag darüber
 * (`AboVertrag.jsx`), und **solange einer für den gewählten Monat gilt**,
 * steht auch die Restzahl da. Ohne Vertrag bleibt es beim Verbrauch samt
 * Hinweis — die Zurückhaltung ist nicht weggefallen, sie hat einen Ausweg.
 *
 * **Eine Überschreitung wird gezeigt, nicht auf null gekappt.** „0 h übrig"
 * sähe aus wie „gerade aufgebraucht"; −1,5 h ist die Auskunft, für die das
 * Kontingent gebaut ist.
 *
 * **Der Monat ist wählbar, nicht abgeleitet.** Wer am 2. September
 * Augustarbeit einträgt, bucht sie auf den August — abgeleitet aus dem
 * Zeitpunkt verfiele das Kontingent des Vormonats still.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';
import AboVertrag from './AboVertrag';

const LEER = { stunden: '', taetigkeit: '' };

/** Der laufende Monat als `JJJJ-MM` — die Vorbelegung, nicht die Vorschrift. */
function laufenderMonat() {
  const jetzt = new Date();
  return `${jetzt.getFullYear()}-${String(jetzt.getMonth() + 1).padStart(2, '0')}`;
}

function monatName(wert) {
  const [jahr, monat] = String(wert).split('-');
  const d = new Date(Number(jahr), Number(monat) - 1, 1);
  return Number.isNaN(d.getTime())
    ? wert
    : d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
}

function zeitpunkt(roh) {
  if (!roh) return '';
  const d = new Date(roh);
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' });
}

export default function AboZeiten({ leadId, token }) {
  const [monat, setMonat] = useState(laufenderMonat);
  const [daten, setDaten] = useState(null);
  const [formular, setFormular] = useState(LEER);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState(false);

  const kopf = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const laden = useCallback(async () => {
    if (!leadId) return;
    setFehler('');
    try {
      const antwort = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/abo-zeiten?monat=${monat}`,
        { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setDaten(await antwort.json());
    } catch (e) {
      // Kein Rückfall auf „nichts erfasst": Das wäre eine Aussage über den
      // Bestand, wo gar nicht gelesen werden konnte.
      setDaten(null);
      setFehler(`Die Pflegestunden konnten nicht geladen werden (${e.message}).`);
    }
  }, [leadId, monat, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function eintragen(e) {
    e.preventDefault();
    const stunden = parseFloat(String(formular.stunden).replace(',', '.'));
    if (!Number.isFinite(stunden) || stunden <= 0) {
      setFehler('Bitte eine Stundenzahl größer als 0 angeben.');
      return;
    }

    setLaeuft(true); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/leads/${leadId}/abo-zeiten`, {
        method: 'POST', headers: kopf,
        body: JSON.stringify({
          stunden,
          taetigkeit: formular.taetigkeit.trim(),
          monat,
        }),
      });
      const d = await antwort.json().catch(() => ({}));
      if (!antwort.ok) throw new Error(d.detail || `Status ${antwort.status}`);
      setFormular(LEER);
      // Der Server schickt den neuen Stand mit — kein zweiter Aufruf, der
      // einen anderen Augenblick sähe.
      setDaten(d);
    } catch (e2) {
      setFehler(`Nicht gespeichert (${e2.message}). Ihre Eingabe steht noch da.`);
    } finally {
      setLaeuft(false);
    }
  }

  if (!leadId) return null;

  return (
    <section style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
      borderRadius: 'var(--radius-xl)', padding: '16px 18px',
      display: 'flex', flexDirection: 'column', gap: 12,
    }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
          Pflegestunden
        </h2>
        {daten && (
          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            {daten.verbraucht.toLocaleString('de-DE')} h im {monatName(daten.monat)}
            {daten.abo && (
              <>
                {' von '}
                {daten.kontingent_stunden.toLocaleString('de-DE')} h
                {' · '}
                <b style={{ color: daten.ueberzogen ? 'var(--status-error-text)' : 'var(--text-secondary)' }}>
                  {daten.verbleibend_stunden.toLocaleString('de-DE')} h übrig
                </b>
              </>
            )}
          </span>
        )}
      </div>

      <AboVertrag leadId={leadId} token={token} onAenderung={laden} />

      <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)' }}>Monat</span>
        <input
          type="month"
          value={monat}
          onChange={(e) => setMonat(e.target.value || laufenderMonat())}
          aria-label="Abrechnungsmonat"
          style={{ ...feld, width: 'auto' }}
        />
      </label>

      <form onSubmit={eintragen} style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)' }}>Stunden</span>
          <input
            value={formular.stunden}
            onChange={(e) => setFormular({ ...formular, stunden: e.target.value })}
            inputMode="decimal"
            placeholder="0,5"
            aria-label="Erfasste Pflegestunden"
            style={{ ...feld, width: 76 }}
          />
        </label>
        <label style={{ display: 'flex', flexDirection: 'column', gap: 3, flex: '1 1 200px' }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)' }}>Woran?</span>
          <input
            value={formular.taetigkeit}
            onChange={(e) => setFormular({ ...formular, taetigkeit: e.target.value })}
            placeholder="z. B. Öffnungszeiten geändert"
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
                {e.stunden.toLocaleString('de-DE')} h
              </span>
              <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {e.taetigkeit || '—'}
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)', flexShrink: 0 }}>
                {e.wer} · {zeitpunkt(e.erfasst_am)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {daten?.eintraege?.length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
          Für {monatName(monat)} ist nichts erfasst.
        </div>
      )}

      {daten?.hinweis && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
          {daten.hinweis}
        </div>
      )}

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, padding: '7px 10px', borderRadius: 'var(--radius-md)',
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
