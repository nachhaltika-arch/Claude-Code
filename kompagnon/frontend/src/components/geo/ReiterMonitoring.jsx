/**
 * Der Reiter „Monitoring" der GEO-Ansicht (L-25).
 *
 * Am 2026-08-31 aus `GeoOptimizerStep.jsx` herausgeloest — 107 Zeilen. Er
 * zeigt unter anderem den 60-Tage-Wirkungsbericht, der bis zum 27.08. gebaut
 * war und keinen Aufrufer hatte (L-105).
 */
import { datumKurz, monatUndJahr } from '../../utils/datum';
import { SCORE_COLOR } from './geoBausteine';

export default function ReiterMonitoring({
  activeTab,
  isAdmin,
  monitoringSchalten,
  monitoring,
  wirkung,
}) {
  return (
    <div>
      {/* **Der Wirkungsbericht nach 60 Tagen.** Er steht ueber dem
          Monatsverlauf, weil er die Frage beantwortet, die der Kunde
          stellt — „hat es etwas gebracht" —, waehrend der Verlauf
          darunter die Rohdaten zeigt.

          Ist er noch nicht faellig, steht **der Grund** da und nicht
          nichts: Eine leere Stelle liest sich wie ein Fehler, und wer
          den Bericht sucht, sucht dann im Werkzeug statt im Kalender. */}
      {wirkung && (
        <div style={{ border: '1px solid #E5E7EB', borderRadius: 8,
                      padding: 14, marginBottom: 16,
                      background: wirkung.faellig ? 'var(--bg-surface)' : 'transparent' }}>
          <h4 style={{ fontSize: 14, margin: '0 0 8px' }}>
            Wirkungsbericht (60 Tage)
          </h4>

          {!wirkung.faellig ? (
            <p style={{ color: '#6B7280', fontSize: 13, margin: 0, lineHeight: 1.6 }}>
              {wirkung.grund}.
            </p>
          ) : (
            <>
              {wirkung.klartext && (
                <p style={{ fontSize: 13, margin: '0 0 10px', lineHeight: 1.7 }}>
                  {wirkung.klartext}
                </p>
              )}
              <div style={{ display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                            gap: 10 }}>
                {/* Zwei Groessen, zwei Kaesten — bewusst nicht zu einer Zahl
                    verrechnet. Den GEO-Wert stellen wir her; ob ein
                    Assistent den Betrieb nennt, entscheidet dessen
                    Anbieter. Eine gemeinsame Zahl verkaufte eine Wirkung,
                    die niemand zusichern kann. */}
                {[
                  { titel: 'GEO-Wert', daten: wirkung.geo_wert,
                    grund: wirkung.geo_wert_grund,
                    fuss: 'unser Werk' },
                  { titel: 'Nennungen', daten: wirkung.nennungen,
                    grund: wirkung.nennungen_grund,
                    fuss: 'entscheiden die Anbieter' },
                ].map(({ titel, daten, grund, fuss }) => (
                  <div key={titel} style={{ border: '1px solid #F3F4F6',
                                            borderRadius: 6, padding: '10px 12px' }}>
                    <div style={{ fontSize: 12, textTransform: 'uppercase',
                                  letterSpacing: '.07em', color: '#6B7280',
                                  fontWeight: 700 }}>{titel}</div>
                    {daten ? (
                      <div style={{ marginTop: 6, fontVariantNumeric: 'tabular-nums' }}>
                        <span style={{ fontSize: 20, fontWeight: 800 }}>
                          {daten.vorher} → {daten.heute}
                        </span>
                        <span style={{ fontSize: 13, marginLeft: 8,
                                       color: daten.veraenderung > 0 ? 'var(--status-success-text)'
                                            : daten.veraenderung < 0 ? 'var(--status-danger-text)'
                                            : '#6B7280' }}>
                          {daten.veraenderung > 0 ? '+' : ''}{daten.veraenderung}
                        </span>
                      </div>
                    ) : (
                      <p style={{ fontSize: 12, color: '#6B7280', margin: '6px 0 0',
                                  lineHeight: 1.6 }}>
                        {grund || 'Noch keine Vergleichsdaten.'}
                      </p>
                    )}
                    <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 6 }}>{fuss}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* **Der Stand des Schalters, bevor irgendetwas versprochen wird**
          (L-105, 31.08.2026). `PATCH /monitoring/toggle` war gebaut und
          ungerufen; der Satz darunter sagte „der erste Report erscheint am
          1. des naechsten Monats" — auch bei ausgeschaltetem Monitoring, wo
          nie einer kaeme. */}
      {monitoring && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, padding: '10px 12px', marginBottom: 12,
          background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
          borderRadius: 8,
        }}>
          <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
            Monatliches Monitoring:{' '}
            <strong>{monitoring.monitoring_enabled ? 'eingeschaltet' : 'ausgeschaltet'}</strong>
          </span>
          {isAdmin && (
            <button
              type="button"
              onClick={() => monitoringSchalten(!monitoring.monitoring_enabled)}
              style={{
                border: '1px solid var(--border-medium)', borderRadius: 6,
                background: 'var(--bg-app)', color: 'var(--text-primary)',
                padding: '6px 12px', fontSize: 12, fontWeight: 600,
                cursor: 'pointer', minHeight: 32,
              }}
            >
              {monitoring.monitoring_enabled ? 'Ausschalten' : 'Einschalten'}
            </button>
          )}
        </div>
      )}

      {!monitoring ? (
        <p style={{ color: '#6B7280', textAlign: 'center', padding: 24 }}>Wird geladen...</p>
      ) : monitoring.history.length === 0 ? (
        <p style={{ color: '#6B7280', textAlign: 'center', padding: 24 }}>
          {monitoring.monitoring_enabled
            ? 'Noch keine Monitoring-Daten — der erste Report erscheint am 1. des naechsten Monats.'
            : 'Noch keine Monitoring-Daten. Solange das Monitoring ausgeschaltet ist, kommt auch keiner.'}
        </p>
      ) : (
        <div>
          <p style={{ fontSize: 13, color: '#6B7280', marginBottom: 12 }}>
            Monatliche GEO-Score Entwicklung (letzter Check: {datumKurz(monitoring.last_monitored_at, 'Nie')})
          </p>
          {monitoring.history.slice().reverse().map((entry, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid #F3F4F6' }}>
              <span style={{ fontSize: 13, color: '#374151' }}>
                {monatUndJahr(entry.date)}
              </span>
              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <span style={{ fontSize: 15, fontWeight: 700, color: SCORE_COLOR(entry.score) }}>{entry.score}/100</span>
                {entry.change !== 0 && (
                  <span style={{ fontSize: 12, color: entry.change > 0 ? '#27ae60' : '#e74c3c' }}>
                    {entry.change > 0 ? `+${entry.change}` : entry.change}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
