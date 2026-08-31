/**
 * Der Reiter „KI-Nennung" der GEO-Ansicht (L-25).
 *
 * Am 2026-08-31 aus `GeoOptimizerStep.jsx` herausgeloest — 109 Zeilen.
 */
import { datumKurz } from '../../utils/datum';
import { SCORE_COLOR } from './geoBausteine';

export default function ReiterNennung({
  activeTab,
  nennung,
  nennungFehler,
  nennungLaeuft,
  pruefeNennung,
  verlauf,
}) {
  return (
    <div>
      <div style={{
        background: '#F9FAFB', border: '1px solid #E5E7EB', borderRadius: 8,
        padding: '14px 16px', marginBottom: 16, fontSize: 13, color: '#374151',
      }}>
        <strong>Zwei verschiedene Fragen.</strong> Die Analyse nebenan misst, ob eine
        Maschine den Betrieb <em>lesen</em> kann. Hier wird gefragt, ob sie ihn auch
        <em> nennt</em> — mit denselben Fragen, die ein Kunde stellt.
        {' '}Jeder Lauf kostet Geld und fliesst deshalb in keinen Score ein.
      </div>

      <button
        onClick={pruefeNennung}
        disabled={nennungLaeuft}
        style={{
          background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
          border: 'none', padding: '10px 20px', borderRadius: 8, fontSize: 14,
          fontWeight: 600, cursor: nennungLaeuft ? 'not-allowed' : 'pointer',
          opacity: nennungLaeuft ? 0.7 : 1, marginBottom: 16,
        }}
      >
        {nennungLaeuft ? 'Wird gefragt … (bis zu einer Minute)' : 'Nennung jetzt pruefen'}
      </button>

      {nennungFehler && (
        <div style={{
          background: '#FEF3C7', border: '1px solid #FCD34D', borderRadius: 8,
          padding: '12px 16px', marginBottom: 16, fontSize: 13, color: '#78350F',
        }}>
          <strong>Nicht gemessen.</strong> {nennungFehler}
          <div style={{ marginTop: 6 }}>
            Das ist <strong>keine</strong> Aussage ueber den Betrieb — es wurde nicht gefragt.
          </div>
        </div>
      )}

      {nennung && (
        <div style={{ display: 'grid', gap: 10, marginBottom: 20 }}>
          {Object.entries(nennung.anbieter || {}).map(([schluessel, block]) => (
            <div key={schluessel} style={{
              border: '1px solid #E5E7EB', borderRadius: 8, padding: '12px 16px',
              background: block.collected ? '#fff' : '#F9FAFB',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between',
                            alignItems: 'baseline', gap: 12, flexWrap: 'wrap' }}>
                <strong style={{ fontSize: 14 }}>{block.anzeige || schluessel}</strong>
                {block.collected ? (
                  <span style={{ fontSize: 14, fontWeight: 700,
                                 color: SCORE_COLOR((block.quote || 0) * 100) }}>
                    {block.genannt_bei} von {block.beantwortet} Fragen
                  </span>
                ) : (
                  <span style={{ fontSize: 12, color: '#6B7280' }}>nicht erhoben</span>
                )}
              </div>
              {block.collected ? (
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
                  Modell {block.modell}
                  {block.fehler > 0 && ` · ${block.fehler} Frage(n) ohne Antwort`}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: '#6B7280', marginTop: 4 }}>
                  {block.grund}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {verlauf?.verlauf?.length > 0 && (
        <div>
          <h4 style={{ fontSize: 14, margin: '0 0 8px' }}>Verlauf</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13,
                            fontVariantNumeric: 'tabular-nums' }}>
              <thead>
                <tr style={{ textAlign: 'left', color: '#6B7280' }}>
                  <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Lauf</th>
                  <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Genannt bei</th>
                  <th style={{ padding: '6px 8px', borderBottom: '1px solid #E5E7EB' }}>Nicht erhoben</th>
                </tr>
              </thead>
              <tbody>
                {[...verlauf.verlauf].reverse().map((eintrag, i) => (
                  <tr key={eintrag.am || i}>
                    <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6' }}>
                      {datumKurz(eintrag.am)}
                    </td>
                    <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6' }}>
                      {Object.entries(eintrag.anbieter || {})
                        .map(([k, w]) => `${k}: ${w.genannt_bei}/${w.von}`)
                        .join(' · ') || '—'}
                    </td>
                    <td style={{ padding: '6px 8px', borderBottom: '1px solid #F3F4F6',
                                 color: '#6B7280' }}>
                      {(eintrag.nicht_erhoben || []).join(', ') || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
