import { useCallback, useEffect, useState } from 'react';
import API_BASE_URL from '../config';
import { datumKurz } from '../utils/datum';

/**
 * Die zugesagte Bauzeit eines Betriebs — und der Knopf, der sie ruhen lässt.
 *
 * **Der Befund (L-166, K3, 06.09.2026).** Der Angebotsfuß sagt zu: „Die
 * vereinbarte Bauzeit beginnt an dem Werktag, an dem sämtliche
 * Mitwirkungsleistungen vollständig vorliegen. Verzögert sich eine Freigabe
 * nach M7 oder M8, ruht die Frist für die Dauer der Verzögerung."
 *
 * Die erste Hälfte trug seit dem 03.09. Die zweite gar nicht: Es gab **kein
 * Feld für den Vorlagezeitpunkt**. Wann ein Bauplan zur Freigabe vorlag, wann
 * der Kunde freigab und wie viele Werktage dazwischen die Frist ruhte, stand
 * nirgends — und damit war das zugesagte Ende nicht berechenbar, sondern nur
 * behauptbar. Von beiden Seiten.
 *
 * **Warum der Knopf hier steht und nicht im Kundenkonto.** Die Freigabe
 * erteilt der Kunde; die **Vorlage** kommt von uns. Wer sein eigenes
 * Vorlagedatum setzen könnte, könnte sich die Ruhezeit wegrechnen, die er
 * selbst verursacht hat.
 *
 * **Und warum es ihn überhaupt gibt.** Ein Endpunkt ohne Aufrufer ist die
 * häufigste Fehlerklasse dieses Projekts — sechsmal allein zwischen dem 4.
 * und 6. September. Ein Vorlagedatum, das niemand eintragen kann, wäre eine
 * leere Spalte mit einer schönen Rechnung dahinter.
 *
 * **Gerechnet wird im Backend.** Alle Zahlen hier kommen aus der Antwort;
 * eine zweite Rechnung in JavaScript wäre der zweite Ort, an dem die
 * Auslegung des Angebotstexts gepflegt werden müsste.
 */
export default function BauzeitFrist({ leadId, token }) {
  const [daten, setDaten] = useState(null);
  const [fehler, setFehler] = useState('');
  const [laeuft, setLaeuft] = useState('');

  const laden = useCallback(async () => {
    if (!leadId) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/bauzeit/${leadId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Bauzeit nicht ladbar (${res.status})`);
      setDaten(await res.json());
      setFehler('');
    } catch (e) {
      setFehler(e.message);
    }
  }, [leadId, token]);

  useEffect(() => { laden(); }, [laden]);

  const vorlegen = async (kennung) => {
    setLaeuft(kennung);
    try {
      const res = await fetch(`${API_BASE_URL}/api/bauzeit/${leadId}/vorlage/${kennung}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: '{}',
      });
      if (!res.ok) throw new Error('Vorlage nicht gespeichert — bitte noch einmal.');
      await laden();
    } catch (e) {
      setFehler(e.message);
    } finally {
      setLaeuft('');
    }
  };

  if (fehler) return <p style={S.fehler}>{fehler}</p>;
  if (!daten) return null;
  /* Ein Betrieb ohne Projekt ist kein Fehler, sondern der Normalfall vor dem
     Kauf — dann steht hier nichts statt eines leeren Kastens. */
  if (!daten.frist) return null;

  const f = daten.frist;

  return (
    <section style={S.rahmen}>
      <h3 style={S.h3}>Bauzeit und Fristen</h3>

      <div style={S.zahlen}>
        <Zahl beschriftung="Frist beginnt"
              wert={f.beginn ? datumKurz(f.beginn) : 'läuft noch nicht'} />
        <Zahl beschriftung="Bauzeit laut Paket" wert={`${f.bauzeit_werktage} Werktage`} />
        <Zahl beschriftung="Ruhezeit"
              wert={f.pause_werktage === 0 ? 'keine' : `${f.pause_werktage} Werktage`}
              warnen={f.pause_werktage > 0} />
        <Zahl beschriftung="Zugesagt fertig"
              wert={f.ende ? datumKurz(f.ende) : '—'} betont />
      </div>

      {!f.beginn && (
        /* **Warum die offenen Punkte hier stehen.** „läuft noch nicht" ohne
           den Grund zwingt den Innendienst, in einem zweiten Fenster
           nachzusehen, was fehlt. */
        <p style={S.hinweis}>
          Die Frist läuft noch nicht — offen: {f.offene_punkte.join(', ') || '—'}.
        </p>
      )}

      {f.ende && f.pause_werktage > 0 && (
        <p style={S.hinweis}>
          Ohne die Ruhezeit wäre der zugesagte Tag {datumKurz(f.ende_ohne_pause)} gewesen.
        </p>
      )}

      <table style={S.tabelle}>
        <thead>
          <tr>
            <th style={S.kopf}>Freigabe</th>
            <th style={S.kopf}>vorgelegt</th>
            <th style={S.kopf}>Frist bis</th>
            <th style={S.kopf}>freigegeben</th>
            <th style={S.kopf}>ruht</th>
            <th style={S.kopf} />
          </tr>
        </thead>
        <tbody>
          {f.freigaben.map(g => (
            <tr key={g.kennung}>
              <td style={S.zelle}>{g.kennung} — {g.titel}</td>
              <td style={S.zelle}>{g.vorgelegt_am ? datumKurz(g.vorgelegt_am) : '—'}</td>
              <td style={S.zelle}>{g.frist_bis ? datumKurz(g.frist_bis) : '—'}</td>
              <td style={S.zelle}>{g.freigegeben_am ? datumKurz(g.freigegeben_am) : '—'}</td>
              <td style={{ ...S.zelle, ...(g.werktage > 0 ? S.warn : {}) }}>
                {g.werktage > 0
                  ? `${g.werktage} Werktage${g.laeuft_noch ? ' und länger' : ''}`
                  : '—'}
              </td>
              <td style={S.zelle}>
                {g.vorgelegt_am ? (
                  <span style={S.leise}>eingetragen</span>
                ) : (
                  <button style={S.knopf} onClick={() => vorlegen(g.kennung)}
                          disabled={laeuft === g.kennung}>
                    {laeuft === g.kennung ? 'Wird gespeichert …' : 'Heute vorgelegt'}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p style={S.leise}>
        Der Kunde hat je Freigabe {f.freigabefrist_werktage} Werktage. Was darüber
        hinausgeht, lässt die Bauzeit ruhen — so steht es im Angebotsfuß.
      </p>
    </section>
  );
}

function Zahl({ beschriftung, wert, betont, warnen }) {
  return (
    <div style={S.kachel}>
      <span style={S.kachelText}>{beschriftung}</span>
      <span style={{ ...S.kachelWert, ...(betont ? S.betont : {}), ...(warnen ? S.warn : {}) }}>
        {wert}
      </span>
    </div>
  );
}

/* Tool-CI: Dark Teal dominiert, Status immer Farbe UND Text. */
const S = {
  rahmen: { background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: 24, marginTop: 20 },
  h3: { fontWeight: 900, letterSpacing: '-0.025em', fontSize: 14, textTransform: 'uppercase', margin: '0 0 16px', color: 'var(--text-secondary)' },
  zahlen: { display: 'flex', flexWrap: 'wrap', gap: 12, marginBottom: 16 },
  kachel: { flex: '1 1 140px', background: 'var(--bg-app)', borderRadius: 6, padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 4 },
  kachelText: { fontSize: 12, color: 'var(--text-tertiary)' },
  kachelWert: { fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' },
  betont: { color: 'var(--brand-primary)' },
  warn: { color: 'var(--status-warning-text)' },
  hinweis: { fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 16px', maxWidth: '64ch' },
  tabelle: { width: '100%', borderCollapse: 'collapse', fontSize: 13, marginBottom: 12 },
  kopf: { textAlign: 'left', fontWeight: 700, color: 'var(--text-tertiary)', padding: '6px 8px', borderBottom: '1px solid var(--border-subtle)' },
  zelle: { padding: '10px 8px', borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-primary)', verticalAlign: 'top' },
  knopf: { fontWeight: 700, fontSize: 12, padding: '7px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', background: 'var(--brand-primary)', color: 'var(--text-on-brand)' },
  leise: { color: 'var(--text-tertiary)', fontSize: 12 },
  fehler: { color: 'var(--status-danger-text)', fontSize: 13 },
};
