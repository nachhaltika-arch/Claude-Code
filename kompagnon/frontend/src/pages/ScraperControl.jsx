import { useState, useEffect, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const STATUS_COLORS = {
  running:   { bg: '#FEF9C3', text: '#854D0E', label: 'Laeuft' },
  completed: { bg: '#dcfce7', text: '#059669', label: 'Abgeschlossen' },
  failed:    { bg: '#FDEAEA', text: '#C0392B', label: 'Fehlgeschlagen' },
  idle:      { bg: 'var(--bg-elevated)', text: 'var(--text-tertiary)', label: 'Bereit' },
};

const fmtDate = (iso) => {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' });
};

export default function ScraperControl() {
  const { token } = useAuth();
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  const [chambers, setChambers]         = useState([]);
  const [trades, setTrades]             = useState([]);
  const [selectedChamber, setChamber]   = useState('muenchen');
  const [selectedTrade, setTrade]       = useState('');
  const [citiesInput, setCitiesInput]   = useState('');
  const [status, setStatus]             = useState(null);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [triggering, setTriggering]     = useState(false);
  const pollRef                         = useRef(null);

  // ── Initial load ──────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/scraper/chambers`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (!d) return;
        setChambers(d.chambers || []);
        const tm = d.trades_muenchen || [];
        setTrades(tm);
        if (tm.length > 0) setTrade(tm[0].value);
      })
      .catch(() => toast.error('Kammern konnten nicht geladen werden'));

    fetch(`${API_BASE_URL}/api/scraper/health`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setScheduleEnabled(!!d.hwk_scraper_enabled); })
      .catch(() => {});

    loadStatus();
    // eslint-disable-next-line
  }, []);

  // ── Status polling ────────────────────────────────────────────────────────
  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/scraper/status`, { headers });
      if (!res.ok) return;
      const data = await res.json();
      setStatus(data);
    } catch { /* silent */ }
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    const isRunning = status?.current_run?.status === 'running';
    if (isRunning && !pollRef.current) {
      pollRef.current = setInterval(loadStatus, 3000);
    } else if (!isRunning && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [status?.current_run?.status, loadStatus]);

  // ── Trigger handlers ──────────────────────────────────────────────────────
  const runScrape = async () => {
    const trade = trades.find(t => t.value === selectedTrade);
    if (!trade) { toast.error('Bitte Gewerk auswaehlen'); return; }

    const cities = citiesInput.trim()
      ? citiesInput.split(',').map(c => c.trim()).filter(Boolean)
      : null;

    setTriggering(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/scraper/run`, {
        method: 'POST', headers,
        body: JSON.stringify({
          chamber: selectedChamber,
          trade_label: trade.label,
          trade_value: trade.value,
          trade_name: trade.name,
          cities,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      toast.success('Scraper gestartet');
      await loadStatus();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setTriggering(false);
    }
  };

  const runBatch = async () => {
    setTriggering(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/scraper/run-batch`, {
        method: 'POST', headers,
        body: JSON.stringify({ chamber: 'muenchen', max_trades: 5 }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      toast.success('Batch-Scraper gestartet');
      await loadStatus();
    } catch (e) {
      toast.error(e.message);
    } finally {
      setTriggering(false);
    }
  };

  const toggleSchedule = async () => {
    const next = !scheduleEnabled;
    try {
      const res = await fetch(`${API_BASE_URL}/api/scraper/schedule`, {
        method: 'POST', headers,
        body: JSON.stringify({ enabled: next }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setScheduleEnabled(!!data.hwk_scraper_enabled);
      toast.success(data.hwk_scraper_enabled ? 'Auto-Scraper aktiviert' : 'Auto-Scraper deaktiviert');
    } catch (e) {
      toast.error('Umschalten fehlgeschlagen');
    }
  };

  // ── Derived state ─────────────────────────────────────────────────────────
  const current   = status?.current_run;
  const recent    = status?.recent_runs || [];
  const statusKey = current?.status || 'idle';
  const statusCfg = STATUS_COLORS[statusKey] || STATUS_COLORS.idle;
  const result    = current?.result || {};

  // ── Styles ────────────────────────────────────────────────────────────────
  const cardStyle = {
    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
    borderRadius: 'var(--radius-lg)', padding: 20,
  };
  const labelStyle = {
    display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)',
    textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 6,
  };
  const inputStyle = {
    width: '100%', padding: '9px 12px', fontSize: 13,
    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-app)', color: 'var(--text-primary)',
    fontFamily: 'var(--font-sans)', outline: 'none', boxSizing: 'border-box',
  };
  const btnPrimary = {
    padding: '10px 22px', borderRadius: 8, border: 'none',
    background: 'linear-gradient(135deg, #008EAA, #006680)',
    color: 'white', fontSize: 13, fontWeight: 700,
    cursor: 'pointer', fontFamily: 'var(--font-sans)',
    display: 'inline-flex', alignItems: 'center', gap: 8,
    boxShadow: '0 2px 10px rgba(0,142,170,0.35)',
  };
  const btnSecondary = {
    padding: '10px 20px', borderRadius: 8,
    border: '1px solid var(--brand-primary)', background: 'transparent',
    color: 'var(--brand-primary)', fontSize: 13, fontWeight: 700,
    cursor: 'pointer', fontFamily: 'var(--font-sans)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, padding: '4px 0' }}>

      {/* Header */}
      <div>
        <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 }}>
          HWK Scraper
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Steuere und ueberwache den Lead-Scraper fuer Handwerkskammern.
        </div>
      </div>

      {/* ── Konfiguration ── */}
      <div style={cardStyle}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
          Neuer Scraper-Lauf
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={labelStyle}>Kammer</label>
            <select value={selectedChamber} onChange={e => setChamber(e.target.value)} style={inputStyle}>
              {chambers.length === 0 && <option value="muenchen">Muenchen</option>}
              {chambers.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>Gewerk</label>
            <select value={selectedTrade} onChange={e => setTrade(e.target.value)} style={inputStyle}>
              {trades.length === 0 && <option value="">Keine Gewerke geladen</option>}
              {trades.map(t => (
                <option key={t.value} value={t.value}>{t.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label style={labelStyle}>PLZ (kommagetrennt)</label>
            <input
              type="text"
              value={citiesInput}
              onChange={e => setCitiesInput(e.target.value)}
              placeholder="80331, 80333, ... (leer = Standard-PLZ)"
              style={inputStyle}
            />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button onClick={runScrape} disabled={triggering || statusKey === 'running'} style={{
            ...btnPrimary,
            opacity: (triggering || statusKey === 'running') ? 0.5 : 1,
            cursor: (triggering || statusKey === 'running') ? 'not-allowed' : 'pointer',
          }}>
            Jetzt scrapen
          </button>
          <button onClick={runBatch} disabled={triggering || statusKey === 'running'} style={{
            ...btnSecondary,
            opacity: (triggering || statusKey === 'running') ? 0.5 : 1,
            cursor: (triggering || statusKey === 'running') ? 'not-allowed' : 'pointer',
          }}>
            Batch Top 5 (Muenchen)
          </button>
        </div>
      </div>

      {/* ── Live Status ── */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
            Live-Status
          </div>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 14px', borderRadius: 99,
            background: statusCfg.bg, color: statusCfg.text,
            fontSize: 12, fontWeight: 700,
            ...(statusKey === 'running' ? { animation: 'pulse 1.5s ease-in-out infinite' } : {}),
          }}>
            {statusKey === 'running' && (
              <span style={{
                width: 8, height: 8, borderRadius: '50%',
                background: statusCfg.text, display: 'inline-block',
              }} />
            )}
            {statusCfg.label}
          </div>
        </div>

        {current && (
          <div style={{ marginBottom: 14, fontSize: 12, color: 'var(--text-secondary)' }}>
            <div><strong>Run-ID:</strong> {current.run_id}</div>
            <div><strong>Kammer:</strong> {current.chamber} · <strong>Gewerk:</strong> {current.trade}</div>
            <div><strong>Gestartet:</strong> {fmtDate(current.started_at)}</div>
            {current.error && (
              <div style={{ marginTop: 6, padding: '8px 12px', background: 'var(--status-danger-bg)', color: 'var(--status-danger-text)', borderRadius: 6 }}>
                {current.error}
              </div>
            )}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
          {[
            { label: 'Gefunden',   value: result.leads_found  ?? result.found  ?? '—', color: 'var(--brand-primary)' },
            { label: 'Gespeichert', value: result.leads_saved ?? result.saved  ?? '—', color: 'var(--status-success-text)' },
            { label: 'Fehler',      value: result.errors      ?? result.failed ?? '—', color: 'var(--status-danger-text)' },
          ].map(card => (
            <div key={card.label} style={{
              padding: 16, borderRadius: 10,
              background: 'var(--bg-app)', border: '1px solid var(--border-light)',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: card.color, lineHeight: 1 }}>
                {card.value}
              </div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', marginTop: 6, textTransform: 'uppercase', letterSpacing: '.06em' }}>
                {card.label}
              </div>
            </div>
          ))}
        </div>

        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50%      { opacity: 0.6; }
          }
        `}</style>
      </div>

      {/* ── Verlauf ── */}
      <div style={cardStyle}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>
          Verlauf (letzte 10 Laeufe)
        </div>
        {recent.length === 0 ? (
          <div style={{ padding: 24, textAlign: 'center', fontSize: 12, color: 'var(--text-tertiary)' }}>
            Noch keine Laeufe vorhanden.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-light)' }}>
                  {['Datum', 'Kammer', 'Gewerk', 'Status', 'Gefunden', 'Gespeichert', 'Fehler'].map(h => (
                    <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent.map((run, i) => {
                  const rCfg = STATUS_COLORS[run.status] || STATUS_COLORS.idle;
                  const r = run.result || {};
                  return (
                    <tr key={run.run_id || i} style={{ borderBottom: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{fmtDate(run.started_at)}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-primary)' }}>{run.chamber || '-'}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-primary)' }}>{run.trade || '-'}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{
                          padding: '3px 10px', borderRadius: 99, fontSize: 10, fontWeight: 700,
                          background: rCfg.bg, color: rCfg.text,
                        }}>
                          {rCfg.label}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{r.leads_found ?? r.found ?? '-'}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--status-success-text)', fontWeight: 600 }}>{r.leads_saved ?? r.saved ?? '-'}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--status-danger-text)' }}>{r.errors ?? r.failed ?? '-'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Auto-Scraper Footer ── */}
      <div style={{ ...cardStyle, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 3 }}>
            Woechentlicher Auto-Scraper
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Fuehrt jeden Montag um 02:00 Uhr automatisch den Batch-Lauf (Top 5 Muenchen) aus.
          </div>
        </div>
        <button onClick={toggleSchedule} style={{
          position: 'relative', width: 52, height: 28, borderRadius: 99,
          border: 'none', cursor: 'pointer',
          background: scheduleEnabled ? 'var(--status-success-text)' : 'var(--border-medium)',
          transition: 'background .2s',
          flexShrink: 0,
        }}>
          <span style={{
            position: 'absolute', top: 3, left: scheduleEnabled ? 27 : 3,
            width: 22, height: 22, borderRadius: '50%',
            background: 'white', transition: 'left .2s',
            boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
          }} />
        </button>
      </div>
    </div>
  );
}
