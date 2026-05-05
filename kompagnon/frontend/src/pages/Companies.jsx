import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const TRADE_OPTIONS = [
  'Heizung', 'Sanitär', 'Elektriker', 'Klempner',
  'Dachdecker', 'Maler', 'Schreiner', 'Fliesenleger', 'Sonstiges',
];

const STATUS_COLORS = {
  new:      { bg: '#EAF4E0', text: '#3B6D11' },
  contacted:{ bg: '#FEF3DC', text: '#BA7517' },
  qualified:{ bg: '#E6F1FB', text: '#185FA5' },
  won:      { bg: '#EAF4E0', text: '#1D9E75' },
  lost:     { bg: '#FDEAEA', text: '#E24B4A' },
  customer: { bg: '#F0E8FF', text: '#7c3aed' },
};

function statusColor(s) {
  return STATUS_COLORS[(s || '').toLowerCase()] || { bg: 'var(--bg-muted)', text: 'var(--text-secondary)' };
}

function scoreBar(score) {
  const pct  = Math.min(100, Math.max(0, score || 0));
  const color = pct >= 70 ? '#1D9E75' : pct >= 40 ? '#BA7517' : '#E24B4A';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden', minWidth: 48 }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 12, color: 'var(--text-secondary)', flexShrink: 0, minWidth: 28, textAlign: 'right' }}>{pct}</span>
    </div>
  );
}

const SORT_KEYS = ['company_name', 'city', 'status', 'analysis_score'];

function sourceBadge(source) {
  const map = {
    'HWK-Muenchen':    { bg: '#EAF4E0', text: '#3B6D11', label: 'HWK München' },
    'HWK-Rheinhessen': { bg: '#E6F1FB', text: '#185FA5', label: 'HWK Rheinhessen' },
  };
  const style = map[source] || { bg: 'var(--bg-muted)', text: 'var(--text-tertiary)', label: source || 'Manuell' };
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 500,
      background: style.bg,
      color: style.text,
      whiteSpace: 'nowrap',
    }}>
      {style.label}
    </span>
  );
}

export default function Companies() {
  const navigate         = useNavigate();
  const { token }        = useAuth();
  const headers          = token ? { Authorization: `Bearer ${token}` } : {};

  const [rows, setRows]         = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [search, setSearch]     = useState('');
  const [sourceFilter, setSourceFilter] = useState('Alle');
  const [sortKey, setSortKey]   = useState('company_name');
  const [sortAsc, setSortAsc]   = useState(true);
  const [showNewCompany, setShowNewCompany] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/?limit=1000`, { headers });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []); // eslint-disable-line

  useEffect(() => { load(); }, []); // eslint-disable-line

  const handleSort = (key) => {
    if (sortKey === key) setSortAsc(a => !a);
    else { setSortKey(key); setSortAsc(true); }
  };

  const filtered = rows
    .filter(r => {
      const q = search.toLowerCase();
      const matchSearch = !q
        || (r.company_name || '').toLowerCase().includes(q)
        || (r.city         || '').toLowerCase().includes(q)
        || (r.website_url  || '').toLowerCase().includes(q)
        || (r.status       || '').toLowerCase().includes(q);

      const matchSource =
        sourceFilter === 'Alle'
        || (sourceFilter === 'manual' && (!r.lead_source || r.lead_source === 'manual'))
        || r.lead_source === sourceFilter;

      return matchSearch && matchSource;
    })
    .sort((a, b) => {
      let av = a[sortKey] ?? '';
      let bv = b[sortKey] ?? '';
      if (typeof av === 'string') av = av.toLowerCase();
      if (typeof bv === 'string') bv = bv.toLowerCase();
      if (av < bv) return sortAsc ? -1 : 1;
      if (av > bv) return sortAsc ?  1 : -1;
      return 0;
    });

  // ── styles ────────────────────────────────────────────────────────────────
  const thStyle = (key) => ({
    padding: '10px 14px', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)',
    textTransform: 'uppercase', letterSpacing: '0.06em', textAlign: 'left',
    background: 'var(--bg-surface)', borderBottom: '1px solid var(--border-light)',
    cursor: SORT_KEYS.includes(key) ? 'pointer' : 'default',
    userSelect: 'none', whiteSpace: 'nowrap',
    color: sortKey === key ? 'var(--brand-primary)' : 'var(--text-tertiary)',
  });

  const SortIcon = ({ k }) => sortKey !== k ? null : (
    <span style={{ marginLeft: 4 }}>{sortAsc ? '↑' : '↓'}</span>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* ── Page header ────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Unternehmen</h1>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '2px 0 0' }}>
            {loading ? 'Lädt…' : `${filtered.length} von ${rows.length} Einträgen`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="search"
            placeholder="Suche nach Name, Stadt, URL …"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{
              padding: '8px 12px', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-medium)', background: 'var(--bg-surface)',
              color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)',
              outline: 'none', width: 260,
            }}
          />
          <select
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              background: 'var(--bg-surface)',
              color: 'var(--text-primary)',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            <option value="Alle">Alle Quellen</option>
            <option value="HWK-Muenchen">HWK München</option>
            <option value="HWK-Rheinhessen">HWK Rheinhessen</option>
            <option value="manual">Manuell</option>
          </select>
          <button
            type="button"
            onClick={() => setShowNewCompany(true)}
            style={{
              padding: '8px 16px',
              background: 'var(--brand-primary)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 13,
              fontWeight: 700,
              cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              whiteSpace: 'nowrap',
            }}
          >
            + Neues Unternehmen
          </button>
        </div>
      </div>

      {/* ── Error ──────────────────────────────────────────────────────────── */}
      {error && (
        <div style={{ padding: '12px 16px', background: '#FDEAEA', border: '1px solid #E24B4A', borderRadius: 'var(--radius-md)', fontSize: 13, color: '#E24B4A' }}>
          Fehler beim Laden: {error}
        </div>
      )}

      {/* ── Loading ────────────────────────────────────────────────────────── */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}

      {/* ── Table ──────────────────────────────────────────────────────────── */}
      {!loading && (
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={thStyle('company_name')} onClick={() => handleSort('company_name')}>
                    Firmenname <SortIcon k="company_name" />
                  </th>
                  <th style={thStyle('city')} onClick={() => handleSort('city')}>
                    Stadt <SortIcon k="city" />
                  </th>
                  <th style={thStyle('website_url')}>Website</th>
                  <th style={thStyle('status')} onClick={() => handleSort('status')}>
                    Status <SortIcon k="status" />
                  </th>
                  <th style={thStyle('lead_source')}>Quelle</th>
                  <th style={{ ...thStyle('analysis_score'), textAlign: 'right' }} onClick={() => handleSort('analysis_score')}>
                    Score <SortIcon k="analysis_score" />
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ padding: '32px 16px', textAlign: 'center', fontSize: 13, color: 'var(--text-tertiary)' }}>
                      Keine Einträge gefunden.
                    </td>
                  </tr>
                )}
                {filtered.map((row, i) => {
                  const sc = statusColor(row.status);
                  return (
                    <tr
                      key={row.id}
                      onClick={() => navigate(`/app/leads/${row.id}`)}
                      style={{
                        cursor: 'pointer',
                        background: i % 2 === 0 ? 'transparent' : 'var(--bg-app)',
                        borderTop: '1px solid var(--border-light)',
                        transition: 'background 0.1s',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                      onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'transparent' : 'var(--bg-app)'}
                    >
                      {/* Firmenname */}
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          {row.favicon_url ? (
                            <img
                              src={row.favicon_url}
                              alt=""
                              style={{ width: 24, height: 24, borderRadius: 4, objectFit: 'contain', background: '#fff', padding: 2, border: '1px solid var(--border-light)', flexShrink: 0 }}
                              onError={e => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
                            />
                          ) : null}
                          <div
                            style={{
                              width: 24, height: 24, borderRadius: 4,
                              background: 'var(--brand-primary)', color: '#fff',
                              fontSize: 11, fontWeight: 700,
                              display: row.favicon_url ? 'none' : 'flex',
                              alignItems: 'center', justifyContent: 'center',
                              flexShrink: 0,
                            }}
                          >
                            {(row.company_name || '?')[0].toUpperCase()}
                          </div>
                          <div>
                            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                              {row.company_name || `Lead #${row.id}`}
                            </div>
                            {row.trade && (
                              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{row.trade}</div>
                            )}
                          </div>
                        </div>
                      </td>
                      {/* Stadt */}
                      <td style={{ padding: '12px 14px', fontSize: 13, color: 'var(--text-secondary)' }}>
                        {row.city || '–'}
                      </td>
                      {/* Website */}
                      <td style={{ padding: '12px 14px', maxWidth: 200 }}>
                        {row.website_url ? (
                          <a
                            href={row.website_url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={e => e.stopPropagation()}
                            style={{ fontSize: 12, color: 'var(--brand-primary)', textDecoration: 'none', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          >
                            {row.website_url.replace(/^https?:\/\//, '')}
                          </a>
                        ) : (
                          <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>–</span>
                        )}
                      </td>
                      {/* Status */}
                      <td style={{ padding: '12px 14px' }}>
                        <span style={{
                          display: 'inline-flex', alignItems: 'center',
                          padding: '2px 8px', borderRadius: 20,
                          fontSize: 11, fontWeight: 600,
                          background: sc.bg, color: sc.text,
                        }}>
                          {row.status || '–'}
                        </span>
                      </td>
                      {/* Quelle */}
                      <td style={{ padding: '12px 14px' }}>
                        {sourceBadge(row.lead_source)}
                      </td>
                      {/* Score */}
                      <td style={{ padding: '12px 14px', minWidth: 100 }}>
                        {scoreBar(row.analysis_score)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showNewCompany && (
        <NewCompanyModal
          token={token}
          onClose={() => setShowNewCompany(false)}
          onCreated={(lead) => {
            setShowNewCompany(false);
            load();
            // Optional: direkt zur neuen Lead-Profile-Page
            if (lead?.id) navigate(`/app/leads/${lead.id}`);
          }}
        />
      )}
    </div>
  );
}

// ── Modal: Neues Unternehmen ──────────────────────────────────────────────────

function NewCompanyModal({ token, onClose, onCreated }) {
  const [form, setForm] = useState({
    company_name: '',
    website_url:  '',
    contact_name: '',
    email:        '',
    phone:        '',
    city:         '',
    trade:        '',
  });
  const [saving, setSaving] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (saving) return;
    if (!form.company_name.trim()) {
      toast.error('Firmenname ist Pflichtfeld');
      return;
    }
    let websiteUrl = form.website_url.trim();
    if (websiteUrl && !websiteUrl.startsWith('http')) {
      websiteUrl = `https://${websiteUrl}`;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          company_name: form.company_name.trim(),
          website_url:  websiteUrl || undefined,
          contact_name: form.contact_name.trim() || undefined,
          email:        form.email.trim() || undefined,
          phone:        form.phone.trim() || undefined,
          city:         form.city.trim() || undefined,
          trade:        form.trade || undefined,
          status:       'new',
          lead_source:  'manual',
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = body?.detail;
        const msg = typeof detail === 'string' ? detail : detail?.message || `Fehler ${res.status}`;
        throw new Error(msg);
      }
      toast.success(`„${form.company_name}" angelegt`);
      onCreated(body);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  const inp = {
    width: '100%', boxSizing: 'border-box', padding: '9px 12px',
    border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
    background: 'var(--bg-surface)', color: 'var(--text-primary)',
    fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none',
  };
  const lbl = {
    display: 'block', fontSize: 11, fontWeight: 600,
    color: 'var(--text-tertiary)', textTransform: 'uppercase',
    letterSpacing: '0.06em', marginBottom: 4,
  };

  return createPortal(
    <div
      onClick={(e) => e.target === e.currentTarget && onClose()}
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(0,0,0,0.55)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 16,
      }}
    >
      <form
        onSubmit={handleSubmit}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          width: '100%', maxWidth: 520,
          maxHeight: 'calc(100vh - 32px)', overflowY: 'auto',
          display: 'flex', flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '18px 22px 14px',
          borderBottom: '1px solid var(--border-light)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
              Neues Unternehmen anlegen
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
              Manueller Lead — kann später für Audit / Projekt genutzt werden
            </div>
          </div>
          <button
            type="button" onClick={onClose}
            style={{
              background: 'none', border: 'none', fontSize: 20,
              cursor: 'pointer', color: 'var(--text-tertiary)',
              lineHeight: 1, padding: '0 2px',
            }}
            aria-label="Schließen"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={lbl}>Firmenname *</label>
            <input
              value={form.company_name} onChange={set('company_name')}
              placeholder="z.B. Müller Haustechnik GmbH"
              style={inp} autoFocus
            />
          </div>
          <div>
            <label style={lbl}>Website / Domain</label>
            <input
              value={form.website_url} onChange={set('website_url')}
              placeholder="z.B. mueller-haustechnik.de"
              style={inp} autoComplete="url"
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl}>Ansprechpartner</label>
              <input
                value={form.contact_name} onChange={set('contact_name')}
                placeholder="Vor- und Nachname" style={inp}
              />
            </div>
            <div>
              <label style={lbl}>Telefon</label>
              <input
                type="tel" value={form.phone} onChange={set('phone')}
                placeholder="+49 …" style={inp}
              />
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl}>E-Mail</label>
              <input
                type="email" value={form.email} onChange={set('email')}
                placeholder="info@firma.de" style={inp}
              />
            </div>
            <div>
              <label style={lbl}>Stadt</label>
              <input
                value={form.city} onChange={set('city')}
                placeholder="Boppard" style={inp}
              />
            </div>
          </div>
          <div>
            <label style={lbl}>Gewerk</label>
            <select value={form.trade} onChange={set('trade')} style={{ ...inp, cursor: 'pointer' }}>
              <option value="">Bitte wählen…</option>
              {TRADE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 22px',
          borderTop: '1px solid var(--border-light)',
          display: 'flex', justifyContent: 'flex-end', gap: 10,
        }}>
          <button
            type="button" onClick={onClose}
            style={{
              padding: '9px 18px',
              background: 'var(--bg-app)',
              border: '1px solid var(--border-light)',
              color: 'var(--text-secondary)',
              borderRadius: 'var(--radius-md)',
              fontSize: 13, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
            }}
          >
            Abbrechen
          </button>
          <button
            type="submit" disabled={saving}
            style={{
              padding: '9px 22px',
              background: saving ? 'var(--text-tertiary)' : 'var(--brand-primary)',
              color: '#fff', border: 'none',
              borderRadius: 'var(--radius-md)',
              fontSize: 13, fontWeight: 600,
              cursor: saving ? 'wait' : 'pointer',
              fontFamily: 'var(--font-sans)',
              opacity: saving ? 0.6 : 1,
            }}
          >
            {saving ? 'Anlegen…' : '✓ Unternehmen anlegen'}
          </button>
        </div>
      </form>
    </div>,
    document.body,
  );
}
