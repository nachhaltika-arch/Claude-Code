import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API_BASE_URL from '../config';

const PHASES = [
  { id: 'phase_1', label: 'Onboarding',  color: '#008EAA' },
  { id: 'phase_2', label: 'Briefing',    color: '#7c3aed' },
  { id: 'phase_3', label: 'Content',     color: '#d97706' },
  { id: 'phase_4', label: 'Technik',     color: '#0891b2' },
  { id: 'phase_5', label: 'QA',          color: '#dc7226' },
  { id: 'phase_6', label: 'Go-Live',     color: '#059669' },
  { id: 'phase_7', label: 'Post-Launch', color: '#16a34a' },
];

const CERT_STYLES = {
  bronze:  { bg: '#F5E6D3', text: '#7D4A1A' },
  silber:  { bg: '#EFEFEF', text: '#5A5A5A' },
  gold:    { bg: '#FEF3DC', text: '#BA7517' },
  platin:  { bg: '#E6F1FB', text: '#185FA5' },
  diamant: { bg: '#EAF4E0', text: '#1D9E75' },
};

function speedColor(s) {
  if (s === null || s === undefined) return null;
  if (s >= 90) return { bg: '#EAF4E0', text: '#3B6D11' };
  if (s >= 50) return { bg: '#FEF3DC', text: '#BA7517' };
  return { bg: '#FDEAEA', text: '#E24B4A' };
}

function getDomain(url) {
  if (!url) return null;
  try { return new URL(url.startsWith('http') ? url : 'https://' + url).hostname.replace('www.', ''); }
  catch { return url; }
}

function phaseInfo(status) {
  return PHASES.find(p => p.id === status) || null;
}

function phaseNum(status) {
  const idx = PHASES.findIndex(p => p.id === status);
  return idx === -1 ? null : idx + 1;
}

// ── Project list card ─────────────────────────────────────────────────────────
function ProjectListCard({ project, lead, onClick }) {
  const ph      = phaseInfo(project.status);
  const pNum    = phaseNum(project.status);
  const domain  = getDomain(lead?.website_url || project.website_url);
  const scM     = project.pagespeed_mobile;
  const scStyle = speedColor(scM);
  const certKey = (project.audit_level || '').toLowerCase();
  const certSt  = CERT_STYLES[certKey];

  return (
    <div
      className="kc-list-row--card"
      onClick={onClick}
      style={{
        flexWrap: 'wrap', gap: 16,
        borderLeft: ph ? `4px solid ${ph.color}` : undefined,
      }}
    >
      {/* Avatar */}
      <div style={{
        width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
        background: ph?.color || '#185FA5', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 13, fontWeight: 700,
      }}>
        {((lead?.company_name || project.company_name || '?')[0]).toUpperCase()}
      </div>

      {/* Name + domain */}
      <div style={{ flex: '1 1 160px', minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {lead?.company_name || project.company_name || `Projekt #${project.id}`}
        </div>
        {domain && (
          <div style={{ fontSize: 11, color: 'var(--brand-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
            {domain}
          </div>
        )}
      </div>

      {/* Phase + progress */}
      <div style={{ flex: '1 1 140px', minWidth: 120 }}>
        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>
          {pNum ? `Phase ${pNum} von 7 · ${ph?.label}` : project.status || '–'}
        </div>
        <div style={{ height: 5, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ width: pNum ? `${(pNum / 7) * 100}%` : '0%', height: '100%', background: '#0d6efd', borderRadius: 3 }} />
        </div>
      </div>

      {/* Badges */}
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center', flexShrink: 0 }}>
        {scStyle && scM !== null && scM !== undefined && (
          <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 7px', borderRadius: 10, background: scStyle.bg, color: scStyle.text }}>
            📱 {scM}
          </span>
        )}
        {certSt && (
          <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 7px', borderRadius: 10, background: certSt.bg, color: certSt.text }}>
            🏅 {project.audit_level}
          </span>
        )}
      </div>

      <span style={{ color: 'var(--text-tertiary)', fontSize: 16, flexShrink: 0 }}>→</span>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CustomerProjects() {
  const navigate     = useNavigate();
  const { token }    = useAuth();
  const h            = token ? { Authorization: `Bearer ${token}` } : {};

  const [projects, setProjects]   = useState([]);
  const [leadsMap, setLeadsMap]   = useState({});  // lead_id → lead
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [phaseFilter, setPhaseFilter] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [projRes, leadsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers: h }),
          fetch(`${API_BASE_URL}/api/leads/?limit=500`,    { headers: h }),
        ]);
        const projData  = await projRes.json();
        const leadsData = await leadsRes.json();

        setProjects(Array.isArray(projData) ? projData : []);

        const map = {};
        if (Array.isArray(leadsData)) leadsData.forEach(l => { map[l.id] = l; });
        setLeadsMap(map);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []); // eslint-disable-line

  const filtered = projects.filter(p => {
    const lead = leadsMap[p.lead_id];
    const name = (lead?.company_name || p.company_name || '').toLowerCase();
    const domain = (lead?.website_url || p.website_url || '').toLowerCase();
    const q = search.toLowerCase();
    if (q && !name.includes(q) && !domain.includes(q)) return false;
    if (phaseFilter && p.status !== phaseFilter) return false;
    return true;
  }).sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>Kundenprojekte</h1>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: '2px 0 0' }}>
            {loading ? 'Lädt…' : `${filtered.length} von ${projects.length} Projekten`}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 200px' }}>
          <span style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-tertiary)', fontSize: 13 }}>🔍</span>
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Firma oder Domain suchen…"
            style={{ width: '100%', padding: '8px 12px 8px 30px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', background: 'var(--bg-surface)', color: 'var(--text-primary)', boxSizing: 'border-box' }}
          />
        </div>
        <select
          value={phaseFilter} onChange={e => setPhaseFilter(e.target.value)}
          style={{ padding: '8px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-surface)', color: 'var(--text-primary)', cursor: 'pointer', outline: 'none' }}
        >
          <option value="">Alle Phasen</option>
          {PHASES.map(ph => <option key={ph.id} value={ph.id}>Phase {PHASES.indexOf(ph)+1} · {ph.label}</option>)}
        </select>
        {(search || phaseFilter) && (
          <button onClick={() => { setSearch(''); setPhaseFilter(''); }}
            style={{ padding: '8px 12px', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--status-danger-text)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ✕ Filter
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-tertiary)' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📋</div>
          <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>{projects.length === 0 ? 'Noch keine Projekte' : 'Keine Treffer'}</div>
          <div style={{ fontSize: 13 }}>Suche anpassen oder Filter zurücksetzen.</div>
        </div>
      )}

      {/* List */}
      {!loading && filtered.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(p => (
            <ProjectListCard
              key={p.id}
              project={p}
              lead={leadsMap[p.lead_id]}
              onClick={() => navigate(`/app/projects/${p.id}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
