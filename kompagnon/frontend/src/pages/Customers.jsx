import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import API_BASE_URL from '../config';
import Badge from '../components/ui/Badge';
import Card from '../components/ui/Card';

const STATUS_MAP = {
  new: { label: 'Neu', variant: 'info' },
  contacted: { label: 'Kontaktiert', variant: 'neutral' },
  qualified: { label: 'Qualifiziert', variant: 'success' },
  proposal_sent: { label: 'Angebot', variant: 'warning' },
  won: { label: 'Gewonnen', variant: 'success' },
  lost: { label: 'Verloren', variant: 'danger' },
};

export default function Customers() {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [leadsRes, custRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/leads/`).catch(() => ({ data: [] })),
        axios.get(`${API_BASE_URL}/api/customers/`).catch(() => ({ data: [] })),
      ]);
      setLeads(Array.isArray(leadsRes.data) ? leadsRes.data : []);
      setCustomers(Array.isArray(custRes.data) ? custRes.data : []);
    } catch {
      toast.error('Daten konnten nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  };

  const allEntries = leads.map(l => ({
    id: l.id,
    name: l.display_name || l.company_name || 'Unbekannt',
    website: l.website_url || '',
    city: l.city || '',
    status: l.status || 'new',
    score: l.analysis_score || 0,
    type: 'lead',
  }));

  const filtered = allEntries.filter(e =>
    !search || [e.name, e.city, e.website].some(v => v.toLowerCase().includes(search.toLowerCase()))
  );

  const scoreColor = (s) => s >= 60 ? 'var(--status-success-text)' : s >= 30 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';
  const scoreBarColor = (s) => s >= 60 ? 'var(--status-success-text)' : s >= 30 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="skeleton" style={{ height: 40 }} />
        {[1, 2, 3, 4].map(i => <div key={i} className="skeleton" style={{ height: 48 }} />)}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.3s ease' }}>
      {/* Search */}
      <input
        type="text"
        placeholder="Unternehmen suchen..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{
          width: '100%', padding: '10px 14px', border: '1px solid var(--border-light)',
          borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)',
          background: 'var(--bg-surface)', color: 'var(--text-primary)',
          outline: 'none', transition: 'border-color 0.15s',
        }}
        onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
        onBlur={e => e.target.style.borderColor = 'var(--border-light)'}
      />

      {/* Table */}
      <Card padding="sm" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Unternehmen', 'Ort', 'Status', 'Homepage-Score', ''].map((h, i) => (
                <th key={i} style={{
                  padding: '10px 14px', textAlign: 'left',
                  fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em',
                  color: 'var(--text-tertiary)', borderBottom: '1px solid var(--border-light)',
                }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-tertiary)', padding: 40, fontSize: 13 }}>
                  Keine Ergebnisse
                </td>
              </tr>
            ) : (
              filtered.map((entry) => {
                const st = STATUS_MAP[entry.status] || STATUS_MAP.new;
                return (
                  <tr key={entry.id} style={{ cursor: 'pointer', transition: 'background 0.1s' }}
                    onMouseEnter={e => {
                      e.currentTarget.style.background = 'var(--bg-hover)';
                      const nameEl = e.currentTarget.querySelector('[data-name]');
                      if (nameEl) nameEl.style.color = 'var(--brand-primary)';
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.background = 'transparent';
                      const nameEl = e.currentTarget.querySelector('[data-name]');
                      if (nameEl) nameEl.style.color = 'var(--text-primary)';
                    }}
                    onClick={() => navigate(`/app/leads/${entry.id}`)}
                  >
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)' }}>
                      <div data-name style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', transition: 'color 0.1s' }}>
                        {entry.name}
                      </div>
                      {entry.website && (
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>
                          {entry.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '10px 14px', fontSize: 13, color: 'var(--text-secondary)', borderBottom: '1px solid var(--border-light)' }}>
                      {entry.city || '—'}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)' }}>
                      <Badge variant={st.variant}>{st.label}</Badge>
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)' }}>
                      {entry.score > 0 ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: 13, fontWeight: 500, color: scoreColor(entry.score), minWidth: 24 }}>
                            {entry.score}
                          </span>
                          <div style={{ flex: 1, height: 4, background: 'var(--border-light)', borderRadius: 2, maxWidth: 80 }}>
                            <div style={{ width: `${entry.score}%`, height: '100%', background: scoreBarColor(entry.score), borderRadius: 2 }} />
                          </div>
                        </div>
                      ) : (
                        <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)', textAlign: 'right' }}>
                      <span style={{ fontSize: 14, color: 'var(--text-tertiary)' }}>→</span>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
