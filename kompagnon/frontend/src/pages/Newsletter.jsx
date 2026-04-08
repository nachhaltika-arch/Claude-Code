import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';
import NewsletterAnalytics from '../components/newsletter/NewsletterAnalytics';

export default function Newsletter() {
  const navigate = useNavigate();
  const { token } = useAuth();
  const fetchedRef = useRef(false);

  const [activeTab, setActiveTab] = useState('campaigns');
  const [campaigns, setCampaigns] = useState([]);
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [showNewList, setShowNewList] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [importListId, setImportListId] = useState(null);
  const [newListForm, setNewListForm] = useState({ name: '', description: '' });
  const [csvText, setCsvText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Analytics modal
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);

  const mkH = () => ({
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  });

  // ── Fetch data ──────────────────────────────────────────────────

  const fetchCampaigns = () =>
    fetch(`${API_BASE_URL}/api/newsletter/campaigns`, { headers: mkH() })
      .then(r => r.json())
      .then(d => setCampaigns(Array.isArray(d) ? d : []))
      .catch(() => toast.error('Kampagnen konnten nicht geladen werden'));

  const fetchLists = () =>
    fetch(`${API_BASE_URL}/api/newsletter/lists`, { headers: mkH() })
      .then(r => r.json())
      .then(d => setLists(Array.isArray(d) ? d : []))
      .catch(() => toast.error('Listen konnten nicht geladen werden'));

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    Promise.all([fetchCampaigns(), fetchLists()]).finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Stats ───────────────────────────────────────────────────────

  const totalSent = campaigns.filter(c => c.status === 'sent').length;
  const activeLists = lists.length;

  const openStats = (id) => setSelectedCampaignId(id);

  // ── Delete ──────────────────────────────────────────────────────

  const deleteCampaign = async (id) => {
    if (!window.confirm('Kampagne wirklich loeschen?')) return;
    try {
      const r = await fetch(`${API_BASE_URL}/api/newsletter/campaigns/${id}`, { method: 'DELETE', headers: mkH() });
      if (r.ok) { toast.success('Geloescht'); setCampaigns(prev => prev.filter(c => c.id !== id)); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Loeschen fehlgeschlagen'); }
  };

  // ── Create list ─────────────────────────────────────────────────

  const createList = async () => {
    if (!newListForm.name.trim()) { toast.error('Name erforderlich'); return; }
    setSubmitting(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/newsletter/lists`, {
        method: 'POST', headers: mkH(), body: JSON.stringify(newListForm),
      });
      if (r.ok) { toast.success('Liste erstellt'); setShowNewList(false); setNewListForm({ name: '', description: '' }); fetchLists(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Erstellen fehlgeschlagen'); }
    setSubmitting(false);
  };

  // ── Sync CRM ────────────────────────────────────────────────────

  const syncCrm = async (listId) => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/newsletter/lists/${listId}/sync-crm`, { method: 'POST', headers: mkH() });
      if (r.ok) { const d = await r.json(); toast.success(`${d.synced_count} Kontakte synchronisiert`); fetchLists(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Sync fehlgeschlagen'); }
  };

  // ── Import CSV ──────────────────────────────────────────────────

  const importContacts = async () => {
    const lines = csvText.trim().split('\n').filter(l => l.trim());
    if (!lines.length) { toast.error('Keine Kontakte eingegeben'); return; }
    const contacts = lines.map(line => {
      const [email, first_name, last_name] = line.split(',').map(s => s.trim());
      return { email, first_name: first_name || null, last_name: last_name || null };
    }).filter(c => c.email);
    if (!contacts.length) { toast.error('Keine gueltigen E-Mails gefunden'); return; }
    setSubmitting(true);
    try {
      const r = await fetch(`${API_BASE_URL}/api/newsletter/lists/${importListId}/import`, {
        method: 'POST', headers: mkH(), body: JSON.stringify({ contacts }),
      });
      if (r.ok) { const d = await r.json(); toast.success(`${d.imported_count} Kontakte importiert`); setShowImport(false); setCsvText(''); fetchLists(); }
      else toast.error((await r.json()).detail || 'Fehler');
    } catch { toast.error('Import fehlgeschlagen'); }
    setSubmitting(false);
  };

  // ── Helpers ─────────────────────────────────────────────────────

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '-';

  const statusBadge = (status) => {
    const map = {
      draft:     { label: 'Entwurf',   bg: 'var(--bg-app)',            color: 'var(--text-secondary)' },
      scheduled: { label: 'Geplant',   bg: '#e8f4fd',                  color: '#0369a1' },
      sent:      { label: 'Versendet', bg: 'var(--status-success-bg)', color: 'var(--status-success-text)' },
    };
    const s = map[status] || map.draft;
    return (
      <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 999, fontSize: 12, fontWeight: 500, background: s.bg, color: s.color }}>
        {s.label}
      </span>
    );
  };

  const sourceBadge = (source) => {
    const isManual = source === 'manual';
    return (
      <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 500, background: isManual ? 'var(--bg-app)' : 'var(--brand-primary-light)', color: isManual ? 'var(--text-secondary)' : 'var(--brand-primary)' }}>
        {isManual ? 'Manuell' : source}
      </span>
    );
  };

  // ── Styles ──────────────────────────────────────────────────────

  const card = { background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' };
  const btnPrimary = { background: 'var(--brand-primary)', color: '#fff', border: 'none', padding: '8px 16px', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const btnSecondary = { background: 'transparent', color: 'var(--brand-primary)', border: '1px solid var(--brand-primary)', padding: '6px 14px', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' };
  const overlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center' };
  const modal = { background: 'var(--bg-surface)', borderRadius: 12, padding: 28, width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column', gap: 16 };
  const input = { width: '100%', padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' };
  const iconBtn = { background: 'none', border: 'none', cursor: 'pointer', padding: 4, display: 'flex', color: 'var(--text-tertiary)' };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '40vh', color: 'var(--text-tertiary)', fontSize: 14 }}>
        Laden...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* ── Header ───────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Newsletter</h1>
        <button style={btnPrimary} onClick={() => navigate('/app/newsletter/editor/new')}>+ Neue Kampagne</button>
      </div>

      {/* ── Stat tiles ───────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12 }}>
        {[
          { label: 'Gesamt verschickt', value: totalSent },
          { label: 'Ø Oeffnungsrate', value: '-' },
          { label: 'Ø Klickrate', value: '-' },
          { label: 'Aktive Listen', value: activeLists },
        ].map((s, i) => (
          <div key={i} style={{ ...card, padding: '16px 20px' }}>
            <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--brand-primary)' }}>{s.value}</div>
          </div>
        ))}
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--border-light)' }}>
        {[
          { key: 'campaigns', label: 'Kampagnen' },
          { key: 'lists', label: 'Kontaktlisten' },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              background: 'none', border: 'none', padding: '10px 20px', cursor: 'pointer',
              fontSize: 13, fontWeight: activeTab === tab.key ? 600 : 400,
              color: activeTab === tab.key ? 'var(--brand-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab.key ? '2px solid var(--brand-primary)' : '2px solid transparent',
              fontFamily: 'var(--font-sans)', transition: 'color var(--transition-fast)',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Campaigns ───────────────────────────────────────── */}
      {activeTab === 'campaigns' && (
        <div style={card}>
          {/* Table header */}
          <div style={{
            display: 'grid', gridTemplateColumns: '2fr 100px 100px 100px 100px',
            gap: 12, padding: '10px 20px', borderBottom: '1px solid var(--border-light)', background: 'var(--bg-app)',
            borderRadius: '8px 8px 0 0',
          }}>
            {['Betreff', 'Status', 'Erstellt', 'Versendet', 'Aktionen'].map(h => (
              <span key={h} style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-tertiary)' }}>{h}</span>
            ))}
          </div>

          {campaigns.length === 0 && (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Noch keine Kampagnen vorhanden.
            </div>
          )}

          {campaigns.map((c, idx) => (
            <div
              key={c.id}
              style={{
                display: 'grid', gridTemplateColumns: '2fr 100px 100px 100px 100px',
                gap: 12, padding: '12px 20px', alignItems: 'center',
                borderBottom: idx < campaigns.length - 1 ? '1px solid var(--border-light)' : 'none',
                transition: 'background 0.1s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{c.subject}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{c.title}</div>
              </div>
              <div>{statusBadge(c.status)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(c.created_at)}</div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{fmtDate(c.sent_at)}</div>
              <div style={{ display: 'flex', gap: 4 }}>
                {/* Edit */}
                <button style={iconBtn} title="Bearbeiten" onClick={() => navigate(`/app/newsletter/editor/${c.id}`)}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M11.5 2.5l2 2L5 13H3v-2l8.5-8.5z"/>
                  </svg>
                </button>
                {/* Stats */}
                <button style={iconBtn} title="Statistiken" onClick={() => openStats(c.id)}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="8" width="3" height="6" rx="0.5"/><rect x="6.5" y="4" width="3" height="10" rx="0.5"/><rect x="11" y="2" width="3" height="12" rx="0.5"/>
                  </svg>
                </button>
                {/* Delete */}
                <button style={iconBtn} title="Loeschen" onClick={() => deleteCampaign(c.id)}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 4h10M6 4V3a1 1 0 011-1h2a1 1 0 011 1v1M5 4v8.5a1 1 0 001 1h4a1 1 0 001-1V4"/>
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Tab: Lists ───────────────────────────────────────────── */}
      {activeTab === 'lists' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button style={btnPrimary} onClick={() => setShowNewList(true)}>+ Neue Liste</button>
          </div>

          {lists.length === 0 && (
            <div style={{ ...card, padding: 40, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
              Noch keine Listen vorhanden.
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {lists.map(l => (
              <div key={l.id} style={{ ...card, padding: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>{l.name}</div>
                    <div style={{ marginTop: 4 }}>{sourceBadge(l.source)}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--brand-primary)' }}>{l.contact_count}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Kontakte</div>
                  </div>
                </div>
                {l.description && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{l.description}</div>}
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 'auto' }}>
                  <button style={btnSecondary} onClick={() => syncCrm(l.id)}>CRM synchronisieren</button>
                  <button style={btnSecondary} onClick={() => { setImportListId(l.id); setShowImport(true); }}>Kontakte importieren</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Modal: New List ──────────────────────────────────────── */}
      {showNewList && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowNewList(false)}>
          <div style={modal}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Neue Liste erstellen</h3>
            <div>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Name</label>
              <input style={input} value={newListForm.name} onChange={e => setNewListForm(f => ({ ...f, name: e.target.value }))} placeholder="z.B. Bestandskunden" />
            </div>
            <div>
              <label style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-secondary)', display: 'block', marginBottom: 4 }}>Beschreibung</label>
              <textarea style={{ ...input, minHeight: 80, resize: 'vertical' }} value={newListForm.description} onChange={e => setNewListForm(f => ({ ...f, description: e.target.value }))} placeholder="Optionale Beschreibung" />
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={{ ...btnSecondary, color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }} onClick={() => setShowNewList(false)}>Abbrechen</button>
              <button style={btnPrimary} onClick={createList} disabled={submitting}>{submitting ? 'Erstellen...' : 'Erstellen'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Import CSV ────────────────────────────────────── */}
      {showImport && (
        <div style={overlay} onClick={e => e.target === e.currentTarget && setShowImport(false)}>
          <div style={modal}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Kontakte importieren</h3>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0 }}>
              Eine Zeile pro Kontakt: <code style={{ background: 'var(--bg-app)', padding: '1px 4px', borderRadius: 4, fontSize: 11 }}>email, vorname, nachname</code>
            </p>
            <textarea
              style={{ ...input, minHeight: 140, resize: 'vertical', fontFamily: 'var(--font-mono)', fontSize: 12 }}
              value={csvText}
              onChange={e => setCsvText(e.target.value)}
              placeholder={'max@beispiel.de, Max, Mustermann\nlisa@firma.de, Lisa, Mueller'}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button style={{ ...btnSecondary, color: 'var(--text-secondary)', borderColor: 'var(--border-light)' }} onClick={() => { setShowImport(false); setCsvText(''); }}>Abbrechen</button>
              <button style={btnPrimary} onClick={importContacts} disabled={submitting}>{submitting ? 'Importieren...' : 'Importieren'}</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Analytics ─────────────────────────────────────── */}
      {selectedCampaignId != null && (
        <NewsletterAnalytics campaignId={selectedCampaignId} onClose={() => setSelectedCampaignId(null)} />
      )}
    </div>
  );
}
