/**
 * Der E-Mail-Reiter des Betriebsblatts (L-25).
 *
 * Am 2026-08-31 aus `LeadProfile.jsx` herausgeloest — 222 Zeilen, der
 * groesste der verbliebenen Reiter. Er zeigt die Sequenzsteuerung und beide
 * Mailprotokolle nebeneinander; dass es **zwei** gibt, die einander nicht
 * kennen, ist ein eigener Befund und aelter als dieser Schnitt.
 */


export default function ReiterMails({
  emailLoading,
  emailLogs,
  seqAction,
  seqStatus,
}) {
  return (
        <div style={{ padding: '20px 0' }}>

          {/* SEQUENZ-STEUERUNG */}
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 12,
            border: '0.5px solid var(--border-light)',
            padding: '16px 20px', marginBottom: 16,
          }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em',
              marginBottom: 12,
            }}>
              E-Mail-Sequenz (Tag 1 · 3 · 7)
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{
                padding: '3px 10px', borderRadius: 10, fontSize: 12, fontWeight: 600,
                background: seqStatus?.active && !seqStatus?.paused
                  ? '#E1F5EE' : seqStatus?.paused ? '#FAEEDA' : '#F1EFE8',
                color: seqStatus?.active && !seqStatus?.paused
                  ? '#085041' : seqStatus?.paused ? '#633806' : '#444441',
              }}>
                {seqStatus?.active && !seqStatus?.paused
                  ? `Aktiv — Schritt ${seqStatus.step} von 3`
                  : seqStatus?.paused ? 'Pausiert'
                  : 'Inaktiv'}
              </span>
              {seqStatus?.last_sent && (
                <span style={{ fontSize: 11, color: '#94a3b8' }}>
                  Letzter Versand: {new Date(seqStatus.last_sent).toLocaleDateString('de-DE')}
                </span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {!seqStatus?.active && (
                <button
                  onClick={() => seqAction('start')}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: 'none',
                    background: 'var(--success)', color: 'var(--text-on-brand)',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>
                  Sequenz starten
                </button>
              )}
              {seqStatus?.active && !seqStatus?.paused && (
                <button
                  onClick={() => seqAction('pause')}
                  style={{
                    padding: '8px 14px', borderRadius: 8,
                    border: '1px solid #e2e8f0', background: 'transparent',
                    color: '#64748b', fontSize: 12, cursor: 'pointer',
                  }}>
                  Pausieren
                </button>
              )}
              {seqStatus?.paused && (
                <button
                  onClick={() => seqAction('start')}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: 'none',
                    background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>
                  Fortsetzen
                </button>
              )}
              {seqStatus?.active && (
                <button
                  onClick={() => seqAction('stop')}
                  style={{
                    padding: '8px 14px', borderRadius: 8,
                    border: '1px solid #FECACA', background: '#FFF1F1',
                    color: '#A32D2D', fontSize: 12, cursor: 'pointer',
                  }}>
                  Stoppen
                </button>
              )}
            </div>
          </div>

          {/* E-MAIL-PROTOKOLL */}
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 12,
            border: '0.5px solid var(--border-light)',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '12px 16px',
              borderBottom: '0.5px solid var(--border-light)',
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              Gesendete E-Mails ({emailLogs.length})
            </div>

            {emailLoading ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Lädt...
              </div>
            ) : emailLogs.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Noch keine E-Mails gesendet.
              </div>
            ) : emailLogs.map((log, i) => (
              <div key={i} style={{
                padding: '10px 16px',
                borderBottom: i < emailLogs.length - 1 ? '0.5px solid var(--border-light)' : 'none',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: '2px 7px',
                  borderRadius: 8,
                  background: log.status === 'sent' ? '#EAF3DE' : '#FFF1F1',
                  color: log.status === 'sent' ? '#27500A' : '#A32D2D',
                  flexShrink: 0,
                }}>
                  {log.status === 'sent' ? '✓ Gesendet' : '✗ Fehler'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 13, color: 'var(--text-primary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {log.subject}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>
                    {log.template_key} ·{' '}
                    {log.sent_at
                      ? new Date(log.sent_at).toLocaleDateString('de-DE', {
                          day: '2-digit', month: '2-digit', year: 'numeric',
                          hour: '2-digit', minute: '2-digit',
                        })
                      : '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
  );
}
