/**
 * Welche Meldung zusätzlich per E-Mail kommt.
 *
 * **Die Vorgeschichte, die in diese Datei gehört (26.08.2026).** An dieser
 * Stelle standen sechs Ankreuzfelder und ein „Speichern"-Knopf, geschrieben
 * als `onClick={() => toast.success('Einstellungen gespeichert')}` — grün und
 * wirkungslos. Kein Backend las die sechs Schlüssel; es gab nicht einmal eine
 * Stelle, an die sie hätten gehen können. Sie wurden am Vormittag entfernt,
 * weil ein Feld, das nichts schaltet, schlimmer ist als keines: Es beendet die
 * Suche. Auf Davids Entscheidung hin sind sie am Nachmittag zurückgekommen —
 * diesmal mit einer Tabelle, einem Endpunkt und Tests an jeder Stelle, die
 * den Wert liest.
 *
 * **Was die Beschriftungen sagen, kommt vom Server.** Sie hier zu wiederholen
 * hieße, zwei Wahrheiten über dasselbe zu führen — und die zweite weicht
 * irgendwann ab. Der Server kennt die Ereignisse; diese Datei zeigt sie.
 *
 * **Gespeichert wird beim Klick, nicht bei einem „Speichern".** Ein Schalter,
 * der erst nach einem zweiten Knopf gilt, ist die Bauform, aus der der alte
 * Fehler entstand: Man sieht ihn umgelegt und weiß nicht, ob er es ist.
 */
import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../../config';

export default function MeldungsVorlieben({ token }) {
  const [stand, setStand] = useState(null);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState('');

  const kopf = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const laden = useCallback(async () => {
    setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/benachrichtigungen/vorlieben`, { headers: kopf });
      if (!antwort.ok) throw new Error(`Status ${antwort.status}`);
      setStand(await antwort.json());
    } catch (e) {
      // Kein Rückfall auf „alles an": Das wäre eine Aussage über den Bestand,
      // wo gar nicht gelesen werden konnte.
      setStand(null);
      setFehler(`Die Einstellungen konnten nicht geladen werden (${e.message}).`);
    }
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { laden(); }, [laden]);

  async function umlegen(schluessel, aktiv) {
    setLaeuft(schluessel); setFehler('');
    try {
      const antwort = await fetch(`${API_BASE_URL}/api/benachrichtigungen/vorlieben`, {
        method: 'PUT', headers: kopf,
        body: JSON.stringify({ [schluessel]: aktiv }),
      });
      if (!antwort.ok) {
        const d = await antwort.json().catch(() => ({}));
        throw new Error(d.detail || `Status ${antwort.status}`);
      }
      // Der Server antwortet mit dem neuen Stand. Ihn hier selbst zu setzen
      // wäre eine zweite Quelle für dieselbe Zahl — der Fehler, der in
      // diesem Bestand am häufigsten weh getan hat.
      setStand(await antwort.json());
    } catch (e) {
      setFehler(`Nicht gespeichert (${e.message}). Der Schalter steht, wie er stand.`);
    } finally {
      setLaeuft('');
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <p style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--text-secondary)', margin: 0 }}>
        Was von Kunden hereinkommt, meldet immer die <strong>Glocke</strong> in
        der Kopfzeile. Hier steht nur, was <em>zusätzlich</em> den Weg ins
        Postfach nimmt — abschalten schaltet also keine Meldung stumm.
      </p>

      {stand && Object.entries(stand).map(([schluessel, eintrag]) => (
        <label
          key={schluessel}
          style={{
            display: 'flex', alignItems: 'flex-start', gap: 10, padding: '9px 0',
            fontSize: 14, lineHeight: 1.5, cursor: laeuft ? 'default' : 'pointer',
            borderBottom: '1px solid var(--border-light)',
            opacity: laeuft === schluessel ? 0.5 : 1,
          }}
        >
          <input
            type="checkbox"
            checked={Boolean(eintrag.aktiv)}
            disabled={Boolean(laeuft)}
            onChange={(e) => umlegen(schluessel, e.target.checked)}
            style={{ marginTop: 3 }}
          />
          <span>{eintrag.text}</span>
        </label>
      ))}

      {stand && Object.keys(stand).length === 0 && (
        <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
          Es gibt zurzeit kein Ereignis, das sich einzeln umstellen lässt.
        </div>
      )}

      {fehler && (
        <div role="alert" style={{
          fontSize: 12, padding: '8px 11px', borderRadius: 'var(--radius-md)',
          background: 'var(--status-error-bg)', color: 'var(--status-error-text)',
        }}>
          {fehler}
        </div>
      )}
    </div>
  );
}
