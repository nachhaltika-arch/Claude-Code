import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import EmptyState from '../components/ui/EmptyState';
import toast from 'react-hot-toast';

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
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: 15, fontWeight: 700,
          color: 'var(--kc-dark)',
          textTransform: 'uppercase',
          letterSpacing: '0.04em',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {lead?.company_name || project.company_name || `Projekt #${project.id}`}
        </div>
        {domain && (
          <div style={{ fontSize: 11, color: 'var(--kc-mid)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>
            {domain}
          </div>
        )}
      </div>

      {/* Phase + progress (oder IMPULS-Badge) */}
      <div style={{ flex: '1 1 140px', minWidth: 120 }}>
        {project.project_type === 'impuls' ? (
          <span style={{
            display: 'inline-block',
            fontSize: 10, fontWeight: 900, padding: '3px 10px', borderRadius: 20,
            background: '#004F5920', color: '#004F59',
            letterSpacing: '0.08em', textTransform: 'uppercase',
            border: '1px solid #004F5940',
          }}>
            IMPULS
          </span>
        ) : (
          <>
            <div style={{
              fontSize: 11, fontWeight: 700,
              color: 'var(--text-60)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
              marginBottom: 4,
            }}>
              {pNum ? `Phase ${pNum} von 7 · ${ph?.label}` : project.status || '–'}
            </div>
            <div style={{ height: 5, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{
                width: pNum ? `${(pNum / 7) * 100}%` : '0%',
                height: '100%',
                background: pNum && (pNum / 7) > 0.8 ? 'var(--success)' : 'var(--kc-mid)',
                borderRadius: 3,
                transition: 'width 0.5s ease',
              }} />
            </div>
          </>
        )}
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
  const { isMobile } = useScreenSize();
  const h            = token ? { Authorization: `Bearer ${token}` } : {};

  const [projects, setProjects]   = useState([]);
  const [leadsMap, setLeadsMap]   = useState({});  // lead_id → lead
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [phaseFilter, setPhaseFilter] = useState('');

  // ── IMPULS-Projekt anlegen ──
  const emptyImpulsForm = {
    company_name:          '',
    contact_name:          '',
    contact_email:         '',
    contact_phone:         '',
    isb_antrag_datum:      '',
    isb_bewilligung_datum: '',
    isb_foerdersumme:      20000,
    tagewerke_gesamt:      20,
  };
  const [showImpulsModal, setShowImpulsModal] = useState(false);
  const [impulsForm, setImpulsForm] = useState(emptyImpulsForm);
  const [impulsLoading, setImpulsLoading] = useState(false);
  const setImpuls = (field) => (e) =>
    setImpulsForm(prev => ({ ...prev, [field]: e.target.value }));

  const [showOnlineFertigModal, setShowOnlineFertigModal] = useState(false);
  const [onlineFertigForm, setOnlineFertigForm] = useState({
    company_name: '', contact_name: '', contact_email: '', contact_phone: '', paket: 'kompagnon',
  });
  const [onlineFertigLoading, setOnlineFertigLoading] = useState(false);
  const setOF = (field) => (e) =>
    setOnlineFertigForm(prev => ({ ...prev, [field]: e.target.value }));

  const createImpulsProjekt = async () => {
    if (!impulsForm.company_name.trim()) {
      toast.error('Unternehmensname ist Pflichtfeld');
      return;
    }
    setImpulsLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/impuls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify(impulsForm),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Fehler');
      toast.success('IMPULS-Projekt angelegt');
      setShowImpulsModal(false);
      setImpulsForm(emptyImpulsForm);
      navigate(`/app/projects/${data.id}`);
    } catch (err) {
      toast.error(err.message || 'Fehler beim Anlegen');
    }
    setImpulsLoading(false);
  };

  const createOnlineFertigProjekt = async () => {
    if (!onlineFertigForm.company_name.trim()) {
      toast.error('Unternehmensname ist Pflichtfeld');
      return;
    }
    setOnlineFertigLoading(true);
    const PREISE = { starter: 1500, kompagnon: 2000, premium: 2800 };
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
        body: JSON.stringify({
          company_name:  onlineFertigForm.company_name,
          contact_name:  onlineFertigForm.contact_name,
          contact_email: onlineFertigForm.contact_email,
          contact_phone: onlineFertigForm.contact_phone,
          project_type:  'website',
          status:        'phase_1',
          fixed_price:   PREISE[onlineFertigForm.paket] ?? 2000,
          package_type:  onlineFertigForm.paket,
        }),
      });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(d.detail || 'Fehler beim Anlegen');
      }
      const data = await res.json();
      toast.success('Online Fertig Projekt angelegt');
      setShowOnlineFertigModal(false);
      setOnlineFertigForm({ company_name: '', contact_name: '', contact_email: '', contact_phone: '', paket: 'kompagnon' });
      navigate(`/app/projects/${data.id}`);
    } catch (err) {
      toast.error(err.message || 'Fehler beim Anlegen');
    }
    setOnlineFertigLoading(false);
  };

  const MOBILE_PROJEKTE_PILLS = [
    { id: 'alle',    label: 'Alle Projekte' },
    { id: 'tickets', label: '🎫 Tickets',    path: '/app/tickets' },
    { id: 'check',   label: '✅ Checklisten', path: '/app/checklists' },
  ];

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

  // Pull-to-refresh support
  useEffect(() => {
    const onRefresh = () => window.location.reload();
    window.addEventListener('kompagnon:refresh', onRefresh);
    return () => window.removeEventListener('kompagnon:refresh', onRefresh);
  }, []);

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

      {/* Mobile: Pill-Navigation */}
      {isMobile && (
        <div style={{
          display: 'flex', gap: 8,
          padding: '10px 14px 4px',
          overflowX: 'auto',
          scrollbarWidth: 'none',
          msOverflowStyle: 'none',
          background: '#fff',
          borderBottom: '0.5px solid var(--border-light)',
          marginLeft: -16, marginRight: -16,
        }}>
          {MOBILE_PROJEKTE_PILLS.map(p => {
            const active = p.id === 'alle' && !p.path;
            return (
              <button
                key={p.id}
                onClick={() => { if (p.path) navigate(p.path); }}
                style={{
                  padding: '7px 14px',
                  borderRadius: 20,
                  fontSize: 11, fontWeight: 700,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  border: active ? 'none' : '1.5px solid var(--border-medium, #D5E0E2)',
                  background: active ? '#004F59' : '#fff',
                  color: active ? '#fff' : 'var(--text-secondary, #4A5A5C)',
                  textTransform: 'uppercase',
                  letterSpacing: '.04em',
                  fontFamily: 'var(--font-sans)',
                  transition: 'all .12s',
                  flexShrink: 0,
                }}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: 28, fontWeight: 700,
            color: 'var(--kc-dark)',
            textTransform: 'uppercase',
            letterSpacing: '0.02em', lineHeight: 1,
            margin: 0,
          }}>
            Kundenprojekte
          </h1>
          <div style={{
            fontSize: 10, fontWeight: 700,
            letterSpacing: '0.1em', textTransform: 'uppercase',
            color: 'var(--text-30)', marginTop: 4,
            fontFamily: 'var(--font-sans)',
          }}>
            {loading ? 'Lädt…' : `${filtered.length} von ${projects.length} Projekten`}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setShowOnlineFertigModal(true)}
            style={{
              padding: '8px 16px', borderRadius: 8, border: 'none',
              background: 'var(--brand-primary)', color: '#fff',
              fontSize: 12, fontWeight: 900, cursor: 'pointer',
              letterSpacing: '0.04em', fontFamily: 'inherit',
              textTransform: 'uppercase',
            }}
          >
            + Online Fertig
          </button>
          <button
            onClick={() => setShowImpulsModal(true)}
            style={{
              padding: '8px 16px', borderRadius: 8, border: 'none',
              background: '#004F59', color: '#FAE600',
              fontSize: 12, fontWeight: 900, cursor: 'pointer',
              letterSpacing: '0.04em', fontFamily: 'inherit',
              textTransform: 'uppercase',
            }}
          >
            + IMPULS-Projekt
          </button>
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

      {/* Loading Skeleton */}
      {loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="skeleton" style={{ height: 40, borderRadius: 'var(--radius-md)' }} />
          {[1,2,3,4,5].map(i => (
            <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12, minHeight: 64 }}>
              <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%', flexShrink: 0 }} />
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <div className="skeleton" style={{ height: 13, width: '55%', borderRadius: 4 }} />
                <div className="skeleton" style={{ height: 10, width: '35%', borderRadius: 4 }} />
              </div>
              <div className="skeleton" style={{ height: 22, width: 80, borderRadius: 20 }} />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && filtered.length === 0 && (
        <EmptyState
          icon="📋"
          title={search ? `Keine Projekte für „${search}"` : 'Noch keine Projekte'}
          description={search ? 'Passe den Suchbegriff an oder entferne den Filter.' : 'Wenn ein Lead als „Gewonnen" markiert wird, erscheint hier automatisch ein Projekt.'}
          action={!search ? { label: '→ Zur Lead-Pipeline', onClick: () => navigate('/app/leads') } : undefined}
          secondaryAction={search ? { label: 'Filter zurücksetzen', onClick: () => setSearch('') } : undefined}
        />
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

      {/* IMPULS-Projekt anlegen — Modal */}
      {showImpulsModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 16, padding: 32, width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto' }}>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 900, color: '#004F59' }}>IMPULS-Projekt anlegen</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>Nach ISB-Antragsbewilligung ausführen</div>
              </div>
              <button onClick={() => setShowImpulsModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--text-tertiary)' }}>✕</button>
            </div>

            {[
              { field: 'company_name',  label: 'Unternehmensname *', placeholder: 'Mustermann GmbH',   type: 'text' },
              { field: 'contact_name',  label: 'Ansprechpartner',    placeholder: 'Max Mustermann',    type: 'text' },
              { field: 'contact_email', label: 'E-Mail',             placeholder: 'max@mustermann.de', type: 'email' },
              { field: 'contact_phone', label: 'Telefon',            placeholder: '+49 261 ...',       type: 'tel' },
            ].map(f => (
              <div key={f.field} style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>
                  {f.label}
                </label>
                <input
                  type={f.type}
                  placeholder={f.placeholder}
                  value={impulsForm[f.field]}
                  onChange={setImpuls(f.field)}
                  style={{ width: '100%', padding: '10px 12px', border: '1.5px solid var(--border-light)', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', background: 'var(--bg-app)', color: 'var(--text-primary)' }}
                />
              </div>
            ))}

            <div style={{ background: 'var(--bg-app)', borderRadius: 8, padding: '14px 16px', marginBottom: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 12 }}>ISB-Förderdaten</div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
                {[
                  { field: 'isb_antrag_datum',      label: 'Antragsdatum',      type: 'date' },
                  { field: 'isb_bewilligung_datum', label: 'Bewilligungsdatum', type: 'date' },
                ].map(f => (
                  <div key={f.field}>
                    <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{f.label}</label>
                    <input
                      type={f.type}
                      value={impulsForm[f.field]}
                      onChange={setImpuls(f.field)}
                      style={{ width: '100%', padding: '9px 10px', border: '1.5px solid var(--border-light)', borderRadius: 8, fontSize: 13, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                    />
                  </div>
                ))}
                <div>
                  <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Fördervolumen (€)</label>
                  <input
                    type="number"
                    value={impulsForm.isb_foerdersumme}
                    onChange={setImpuls('isb_foerdersumme')}
                    style={{ width: '100%', padding: '9px 10px', border: '1.5px solid var(--border-light)', borderRadius: 8, fontSize: 13, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Tagewerke gesamt</label>
                  <input
                    type="number"
                    value={impulsForm.tagewerke_gesamt}
                    onChange={setImpuls('tagewerke_gesamt')}
                    style={{ width: '100%', padding: '9px 10px', border: '1.5px solid var(--border-light)', borderRadius: 8, fontSize: 13, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', background: 'var(--bg-surface)', color: 'var(--text-primary)' }}
                  />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button onClick={() => setShowImpulsModal(false)} style={{ padding: '10px 20px', border: '1px solid var(--border-light)', borderRadius: 8, background: 'transparent', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', color: 'var(--text-primary)' }}>
                Abbrechen
              </button>
              <button
                onClick={createImpulsProjekt}
                disabled={impulsLoading}
                style={{ padding: '10px 24px', border: 'none', borderRadius: 8, background: impulsLoading ? '#94a3b8' : '#004F59', color: impulsLoading ? '#fff' : '#FAE600', cursor: impulsLoading ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 900, fontFamily: 'inherit', letterSpacing: '0.04em' }}
              >
                {impulsLoading ? '⏳ Anlegen...' : '✓ IMPULS-Projekt anlegen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Online Fertig Projekt anlegen — Modal */}
      {showOnlineFertigModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div style={{ background: 'var(--bg-surface)', borderRadius: 16, padding: 32, width: '100%', maxWidth: 480, maxHeight: '90vh', overflowY: 'auto' }}>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <div>
                <div style={{ fontSize: 18, fontWeight: 900, color: 'var(--brand-primary)' }}>Online Fertig Projekt</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>Website-Projekt manuell anlegen</div>
              </div>
              <button onClick={() => setShowOnlineFertigModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 20, color: 'var(--text-tertiary)' }}>✕</button>
            </div>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Paket</label>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 8 }}>
                {[
                  { value: 'starter',   label: 'Starter',   preis: '1.500 €' },
                  { value: 'kompagnon', label: 'Kompagnon', preis: '2.000 €' },
                  { value: 'premium',   label: 'Premium',   preis: '2.800 €' },
                ].map(p => (
                  <div
                    key={p.value}
                    onClick={() => setOF('paket')({ target: { value: p.value } })}
                    style={{
                      padding: '10px 8px', borderRadius: 8, cursor: 'pointer', textAlign: 'center',
                      border: `2px solid ${onlineFertigForm.paket === p.value ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                      background: onlineFertigForm.paket === p.value ? 'var(--bg-active)' : 'var(--bg-surface)',
                    }}
                  >
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>{p.label}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{p.preis}</div>
                  </div>
                ))}
              </div>
            </div>

            {[
              { field: 'company_name',  label: 'Unternehmensname *', placeholder: 'Mustermann GmbH',  type: 'text' },
              { field: 'contact_name',  label: 'Ansprechpartner',    placeholder: 'Max Mustermann',   type: 'text' },
              { field: 'contact_email', label: 'E-Mail',             placeholder: 'max@beispiel.de',  type: 'email' },
              { field: 'contact_phone', label: 'Telefon',            placeholder: '+49 261 ...',      type: 'tel' },
            ].map(f => (
              <div key={f.field} style={{ marginBottom: 14 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{f.label}</label>
                <input
                  type={f.type}
                  placeholder={f.placeholder}
                  value={onlineFertigForm[f.field]}
                  onChange={setOF(f.field)}
                  style={{ width: '100%', padding: '10px 12px', border: '1.5px solid var(--border-light)', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', background: 'var(--bg-app)', color: 'var(--text-primary)' }}
                />
              </div>
            ))}

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
              <button onClick={() => setShowOnlineFertigModal(false)} style={{ padding: '10px 20px', border: '1px solid var(--border-light)', borderRadius: 8, background: 'transparent', cursor: 'pointer', fontSize: 13, fontFamily: 'inherit', color: 'var(--text-primary)' }}>
                Abbrechen
              </button>
              <button
                onClick={createOnlineFertigProjekt}
                disabled={onlineFertigLoading}
                style={{ padding: '10px 24px', border: 'none', borderRadius: 8, background: onlineFertigLoading ? '#94a3b8' : 'var(--brand-primary)', color: '#fff', cursor: onlineFertigLoading ? 'not-allowed' : 'pointer', fontSize: 13, fontWeight: 900, fontFamily: 'inherit' }}
              >
                {onlineFertigLoading ? '⏳ Anlegen...' : '✓ Projekt anlegen'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
