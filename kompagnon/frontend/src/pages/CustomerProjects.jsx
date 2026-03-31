import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';

const N = '#0F1E3A';
const LEVEL_CFG = {
  'Homepage Standard Platin': { label: 'Platin', icon: '💎', color: '#4a90d9' },
  'Homepage Standard Gold': { label: 'Gold', icon: '🥇', color: '#b8860b' },
  'Homepage Standard Silber': { label: 'Silber', icon: '🥈', color: '#708090' },
  'Homepage Standard Bronze': { label: 'Bronze', icon: '🥉', color: '#cd7f32' },
  'Nicht konform': { label: 'N/K', icon: '⚠️', color: '#dc2626' },
};
const SRC = { stripe_checkout: 'Checkout', llm_landing: 'Landing', csv_import: 'CSV', landing_page: 'Landing' };

export default function CustomerProjects() {
  const nav = useNavigate();
  const { token } = useAuth();
  const { isMobile } = useScreenSize();
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [view, setView] = useState('grid');

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/leads/customers`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
        const data = await res.json();
        setCustomers(Array.isArray(data) ? data : []);
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line

  const filtered = customers.filter((c) => !search || [c.company_name, c.city, c.email, c.trade].some((f) => f?.toLowerCase().includes(search.toLowerCase())));

  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: '#64748b', fontSize: 14 }}>Kunden werden geladen...</div>;

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: N, margin: 0 }}>Kundenprojekte</h1>
          <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 0' }}>{filtered.length} zahlende Kunden</p>
        </div>
        <div style={{ display: 'flex', gap: 4, background: '#f1f5f9', borderRadius: 8, padding: 4 }}>
          {[{ id: 'grid', icon: '⊞' }, { id: 'list', icon: '☰' }].map((v) => (
            <button key={v.id} onClick={() => setView(v.id)} style={{
              padding: '6px 12px', borderRadius: 6, border: 'none', background: view === v.id ? '#fff' : 'transparent',
              color: view === v.id ? N : '#94a3b8', fontSize: 16, cursor: 'pointer', boxShadow: view === v.id ? '0 1px 4px rgba(0,0,0,0.1)' : 'none', minHeight: 32, minWidth: 36,
            }}>{v.icon}</button>
          ))}
        </div>
      </div>

      {/* Search */}
      <div style={{ marginBottom: 20 }}>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Suche nach Firma, Stadt, E-Mail..."
          style={{ width: '100%', maxWidth: 400, padding: '9px 12px 9px 12px', border: '1.5px solid #e2e8f0', borderRadius: 8, fontSize: 14, boxSizing: 'border-box', outline: 'none', background: '#fff' }} />
      </div>

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#94a3b8' }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🏢</div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>{customers.length === 0 ? 'Noch keine zahlenden Kunden' : 'Keine Kunden gefunden'}</div>
        </div>
      )}

      {/* Grid */}
      {view === 'grid' && filtered.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
          {filtered.map((c) => {
            const lc = LEVEL_CFG[c.audit_level] || null;
            return (
              <div key={c.id} onClick={() => nav(`/app/leads/${c.id}`)} style={{
                background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', overflow: 'hidden', cursor: 'pointer',
                transition: 'all 0.2s', boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
              }}>
                {/* Screenshot */}
                <div style={{ height: 140, background: '#f8fafc', position: 'relative', overflow: 'hidden' }}>
                  {c.website_screenshot ? (
                    <img src={c.website_screenshot} alt={c.company_name} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }} />
                  ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: 32 }}>🌐</div>
                  )}
                  {c.audit_score != null && (
                    <div style={{ position: 'absolute', bottom: 8, right: 8, background: 'rgba(15,30,58,0.85)', borderRadius: 8, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6 }}>
                      {lc && <span style={{ fontSize: 12 }}>{lc.icon}</span>}
                      <span style={{ color: lc?.color || '#fff', fontSize: 13, fontWeight: 800 }}>{c.audit_score}/100</span>
                    </div>
                  )}
                  <div style={{ position: 'absolute', top: 8, right: 8, background: 'rgba(255,255,255,0.9)', borderRadius: 6, padding: '3px 8px', fontSize: 10, fontWeight: 600, color: '#475569' }}>
                    {SRC[c.lead_source] || 'Manuell'}
                  </div>
                </div>
                {/* Body */}
                <div style={{ padding: '14px 16px' }}>
                  <div style={{ fontSize: 15, fontWeight: 800, color: N, marginBottom: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.company_name}</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 10 }}>
                    {c.contact_name && <div style={{ fontSize: 12, color: '#64748b' }}>👤 {c.contact_name}</div>}
                    {c.email && <div style={{ fontSize: 12, color: '#64748b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>✉️ {c.email}</div>}
                    {c.website_url && <div style={{ fontSize: 12, color: '#008EAA', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>🌐 {c.website_url.replace(/^https?:\/\//, '')}</div>}
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                    {c.city && <span style={{ fontSize: 11, color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: 4 }}>📍 {c.city}</span>}
                    {c.trade && <span style={{ fontSize: 11, color: '#64748b', background: '#f1f5f9', padding: '2px 8px', borderRadius: 4 }}>🔧 {c.trade}</span>}
                    {c.has_account && <span style={{ fontSize: 11, color: '#059669', background: '#d1fae5', padding: '2px 8px', borderRadius: 4 }}>✓ Login</span>}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8', paddingTop: 10, borderTop: '1px solid #f1f5f9' }}>
                    <span>Seit {c.created_at}</span>
                    {c.last_audit_date && <span>Audit: {c.last_audit_date}</span>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* List */}
      {view === 'list' && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map((c) => {
            const lc = LEVEL_CFG[c.audit_level] || null;
            return (
              <div key={c.id} onClick={() => nav(`/app/leads/${c.id}`)} style={{
                background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', padding: '14px 16px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', transition: 'border-color 0.15s',
              }}>
                <div style={{ width: 56, height: 40, borderRadius: 6, overflow: 'hidden', flexShrink: 0, background: '#f1f5f9', border: '1px solid #e2e8f0' }}>
                  {c.website_screenshot ? <img src={c.website_screenshot} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition: 'top' }} /> : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, color: '#94a3b8' }}>🌐</div>}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: N, marginBottom: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.company_name}</div>
                  <div style={{ fontSize: 12, color: '#64748b', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {c.contact_name && <span>👤 {c.contact_name}</span>}
                    {c.city && <span>📍 {c.city}</span>}
                    {c.trade && <span>🔧 {c.trade}</span>}
                  </div>
                </div>
                <div style={{ textAlign: 'center', flexShrink: 0, minWidth: 50 }}>
                  {c.audit_score != null ? <div style={{ fontSize: 16, fontWeight: 800, color: lc?.color || '#64748b' }}>{c.audit_score}</div> : <div style={{ fontSize: 11, color: '#94a3b8' }}>—</div>}
                </div>
                {c.has_account && <span style={{ fontSize: 11, color: '#059669', background: '#d1fae5', padding: '4px 8px', borderRadius: 6, flexShrink: 0 }}>✓ Login</span>}
                <span style={{ color: '#94a3b8', fontSize: 16, flexShrink: 0 }}>→</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
