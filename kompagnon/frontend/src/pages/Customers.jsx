import { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';

const STATUS = {
  new:           { label: 'Neu',         variant: 'neutral' },
  contacted:     { label: 'Kontaktiert', variant: 'info' },
  qualified:     { label: 'Qualifiziert',variant: 'success' },
  proposal_sent: { label: 'Angebot',     variant: 'warning' },
  won:           { label: 'Gewonnen',    variant: 'success' },
  lost:          { label: 'Verloren',    variant: 'danger' },
};

const CERT = (score) =>
  score >= 85 ? { label: 'Platin', short: 'Pt', bg: 'var(--brand-primary-light)', fg: 'var(--brand-primary)' }
  : score >= 70 ? { label: 'Gold',   short: 'Go', bg: 'var(--status-warning-bg)',  fg: 'var(--status-warning-text)' }
  : score >= 50 ? { label: 'Silber', short: 'Si', bg: 'var(--status-neutral-bg)',  fg: 'var(--text-secondary)' }
  : score >= 30 ? { label: 'Bronze', short: 'Br', bg: '#fdf0e0',                  fg: '#a06820' }
  :               { label: 'N/K',    short: 'NC', bg: 'var(--status-danger-bg)',   fg: 'var(--status-danger-text)' };

export default function Customers() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name'); // name | score | date | city

  const h = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/leads/`, { headers: h })
      .then(r => r.json())
      .then(d => setLeads(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line

  // ── Derived data ──

  const filtered = useMemo(() => {
    let list = leads;

    // Search
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(l =>
        (l.company_name || '').toLowerCase().includes(q) ||
        (l.city || '').toLowerCase().includes(q) ||
        (l.trade || '').toLowerCase().includes(q) ||
        (l.email || '').toLowerCase().includes(q) ||
        (l.website_url || '').toLowerCase().includes(q)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      list = list.filter(l => l.status === statusFilter);
    }

    // Sort
    list = [...list].sort((a, b) => {
      if (sortBy === 'score') return (b.analysis_score || 0) - (a.analysis_score || 0);
      if (sortBy === 'date')  return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      if (sortBy === 'city')  return (a.city || '').localeCompare(b.city || '');
      return (a.company_name || '').localeCompare(b.company_name || '');
    });

    return list;
  }, [leads, search, statusFilter, sortBy]);

  // Stats
  const stats = useMemo(() => ({
    total: leads.length,
    withScore: leads.filter(l => l.analysis_score > 0).length,
    avgScore: leads.filter(l => l.analysis_score > 0).length
      ? Math.round(leads.filter(l => l.analysis_score > 0).reduce((s, l) => s + l.analysis_score, 0) / leads.filter(l => l.analysis_score > 0).length)
      : 0,
    statusCounts: Object.entries(STATUS).map(([k, v]) => ({
      key: k, ...v, count: leads.filter(l => l.status === k).length,
    })).filter(s => s.count > 0),
  }), [leads]);

  const domain = (url) => {
    if (!url) return '';
    try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); } catch { return url; }
  };

  // ── Loading ──

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="skeleton" style={{ height: 44 }} />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton" style={{ height: 64 }} />)}
        </div>
        {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 56 }} />)}
      </div>
    );
  }

  // ── Render ──

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Stats Row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr 1fr' : 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10 }}>
        <MiniStat label="Gesamt" value={stats.total} />
        <MiniStat label="Mit Score" value={stats.withScore} />
        <MiniStat label="Ø Score" value={stats.avgScore || '—'} color={stats.avgScore >= 70 ? 'var(--status-success-text)' : stats.avgScore >= 50 ? 'var(--status-warning-text)' : undefined} />
        {stats.statusCounts.slice(0, 3).map(s => (
          <MiniStat key={s.key} label={s.label} value={s.count}
            onClick={() => setStatusFilter(statusFilter === s.key ? 'all' : s.key)}
            active={statusFilter === s.key} />
        ))}
      </div>

      {/* ── Search + Filter Bar ── */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        {/* Search */}
        <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}>
            <circle cx="7" cy="7" r="5"/><path d="M11 11l3.5 3.5"/>
          </svg>
          <input
            type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Suchen nach Name, Ort, Gewerk, E-Mail..."
            style={{
              width: '100%', padding: '9px 12px 9px 34px',
              border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
              fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)',
              color: 'var(--text-primary)', outline: 'none', transition: 'border-color 0.15s',
            }}
            onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
            onBlur={e => e.target.style.borderColor = 'var(--border-light)'}
          />
        </div>

        {/* Status filter pills */}
        <div style={{ display: 'flex', gap: 4 }}>
          {['all', ...Object.keys(STATUS)].map(key => {
            const active = statusFilter === key;
            const label = key === 'all' ? 'Alle' : STATUS[key].label;
            const count = key === 'all' ? leads.length : leads.filter(l => l.status === key).length;
            if (key !== 'all' && count === 0) return null;
            return (
              <button key={key} onClick={() => setStatusFilter(key)} style={{
                padding: '5px 10px', borderRadius: 'var(--radius-full)',
                border: active ? '1px solid var(--border-medium)' : '1px solid var(--border-light)',
                background: active ? 'var(--bg-active)' : 'transparent',
                color: active ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                fontSize: 11, fontWeight: active ? 500 : 400, cursor: 'pointer',
                fontFamily: 'var(--font-sans)', transition: 'all 0.1s', whiteSpace: 'nowrap',
              }}>
                {label}
                {count > 0 && <span style={{ marginLeft: 4, opacity: 0.6 }}>{count}</span>}
              </button>
            );
          })}
        </div>

        {/* Sort */}
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
          padding: '7px 10px', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)', fontSize: 12, fontFamily: 'var(--font-sans)',
          background: 'var(--bg-surface)', color: 'var(--text-secondary)', cursor: 'pointer', outline: 'none',
        }}>
          <option value="name">A → Z</option>
          <option value="score">Score ↓</option>
          <option value="date">Neueste</option>
          <option value="city">Ort</option>
        </select>
      </div>

      {/* ── Results count ── */}
      <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
        {filtered.length} {filtered.length === 1 ? 'Ergebnis' : 'Ergebnisse'}
        {search && ` für „${search}"`}
        {statusFilter !== 'all' && ` · Filter: ${STATUS[statusFilter]?.label}`}
      </div>

      {/* ── Customer List ── */}
      {filtered.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '48px 20px' }}>
          <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>🔍</div>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>
            Keine Ergebnisse
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
            Passen Sie Ihre Suche oder Filter an
          </div>
        </Card>
      ) : (
        <Card padding="sm" style={{ padding: 0, overflow: 'hidden' }}>
          {/* Table header — desktop only */}
          {!isMobile && (
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 120px 100px 100px 40px',
              gap: 12, padding: '10px 16px', borderBottom: '1px solid var(--border-light)',
              background: 'var(--bg-app)',
            }}>
              {['Unternehmen', 'Ort', 'Status', 'Score', ''].map((h, i) => (
                <span key={i} style={{
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: '0.04em', color: 'var(--text-tertiary)',
                }}>{h}</span>
              ))}
            </div>
          )}

          {/* Rows */}
          {filtered.map((lead, idx) => {
            const st = STATUS[lead.status] || STATUS.new;
            const score = lead.analysis_score || 0;
            const cert = score > 0 ? CERT(score) : null;

            return (
              <div
                key={lead.id}
                onClick={() => navigate(`/app/leads/${lead.id}`)}
                style={{
                  display: isMobile ? 'flex' : 'grid',
                  gridTemplateColumns: isMobile ? undefined : '1fr 120px 100px 100px 40px',
                  flexDirection: isMobile ? 'column' : undefined,
                  gap: isMobile ? 6 : 12,
                  alignItems: isMobile ? 'stretch' : 'center',
                  padding: isMobile ? '12px 16px' : '10px 16px',
                  borderBottom: idx < filtered.length - 1 ? '1px solid var(--border-light)' : 'none',
                  cursor: 'pointer', transition: 'background 0.1s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {/* Company */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                  {/* Avatar */}
                  <div style={{
                    width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                    background: cert ? cert.bg : 'var(--brand-primary-light)',
                    color: cert ? cert.fg : 'var(--brand-primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: cert ? 10 : 13, fontWeight: 600,
                  }}>
                    {cert ? cert.short : (lead.company_name?.[0] || '?')}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{
                      fontSize: 13, fontWeight: 500, color: 'var(--text-primary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {lead.display_name || lead.company_name || 'Unbekannt'}
                    </div>
                    <div style={{
                      fontSize: 11, color: 'var(--text-tertiary)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    }}>
                      {lead.trade ? `${lead.trade}` : ''}{lead.trade && lead.website_url ? ' · ' : ''}{domain(lead.website_url)}
                    </div>
                  </div>
                </div>

                {/* City */}
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', display: isMobile ? 'none' : 'block' }}>
                  {lead.city || '—'}
                </div>

                {/* Status */}
                <div style={isMobile ? { display: 'flex', justifyContent: 'space-between', alignItems: 'center' } : {}}>
                  {isMobile && <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{lead.city}</span>}
                  <Badge variant={st.variant}>{st.label}</Badge>
                </div>

                {/* Score */}
                <div>
                  {score > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{
                        fontSize: 13, fontWeight: 600, fontFamily: 'var(--font-mono)',
                        color: cert.fg, minWidth: 22,
                      }}>
                        {score}
                      </span>
                      <div style={{ flex: 1, height: 4, background: 'var(--border-light)', borderRadius: 2, maxWidth: 50 }}>
                        <div style={{
                          width: `${score}%`, height: '100%', borderRadius: 2,
                          background: score >= 60 ? 'var(--status-success-text)' : score >= 30 ? 'var(--status-warning-text)' : 'var(--status-danger-text)',
                        }} />
                      </div>
                    </div>
                  ) : (
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>—</span>
                  )}
                </div>

                {/* Arrow */}
                <div style={{ display: isMobile ? 'none' : 'flex', justifyContent: 'flex-end' }}>
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5" strokeLinecap="round">
                    <path d="M6 4l4 4-4 4"/>
                  </svg>
                </div>
              </div>
            );
          })}
        </Card>
      )}
    </div>
  );
}

// ── Mini Stat Card ──

function MiniStat({ label, value, color, onClick, active }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: active ? 'var(--bg-active)' : 'var(--bg-surface)',
        border: `1px solid ${active ? 'var(--border-medium)' : 'var(--border-light)'}`,
        borderRadius: 'var(--radius-md)', padding: '10px 12px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.15s',
      }}
    >
      <div style={{
        fontSize: 20, fontWeight: 500, fontFamily: 'var(--font-sans)',
        color: color || (active ? 'var(--brand-primary)' : 'var(--text-primary)'),
        lineHeight: 1, marginBottom: 3,
      }}>
        {value}
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
        {label}
      </div>
    </div>
  );
}
