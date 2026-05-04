import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import EmptyState from '../components/ui/EmptyState';
import NewProjectModal from '../components/NewProjectModal';
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
          <div style={{ width: pNum ? `${(pNum / 7) * 100}%` : '0%', height: '100%', background: pNum && pNum > 5 ? 'var(--success)' : 'var(--kc-mid)', borderRadius: 3 }} />
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

const EMPTY_FORM = { paket: 'kompagnon', company_name: '', website_url: '', contact_name: '', email: '', phone: '' };

// ── Online Fertig Modal ───────────────────────────────────────────────────────
function OnlineFertigModal({ token, onClose, onCreated }) {
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const { isMobile } = useScreenSize();
  const h = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company_name.trim()) { toast.error('Bitte Unternehmensname eingeben'); return; }
    if (!form.website_url.trim())  { toast.error('Bitte Website / Domain eingeben'); return; }

    const websiteUrl = form.website_url.trim().startsWith('http')
      ? form.website_url.trim()
      : `https://${form.website_url.trim()}`;

    setSaving(true);
    try {
      const leadRes = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: 'POST', headers: h,
        body: JSON.stringify({
          company_name: form.company_name.trim(),
          website_url:  websiteUrl,
          contact_name: form.contact_name.trim(),
          email:        form.email.trim(),
          phone:        form.phone.trim(),
          lead_source:  'manual',
          status:       'won',
          package_type: form.paket,
        }),
      });
      if (!leadRes.ok) {
        const err = await leadRes.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${leadRes.status}`);
      }
      const lead = await leadRes.json();

      const projRes = await fetch(`${API_BASE_URL}/api/projects/from-lead/${lead.id}`, {
        method: 'POST', headers: h,
      });
      if (!projRes.ok && projRes.status !== 409) {
        throw new Error('Projekt konnte nicht angelegt werden');
      }
      const proj = await projRes.json();
      toast.success(`Projekt für ${form.company_name} angelegt`);
      onCreated(proj.project_id);
    } catch (err) {
      toast.error(err.message || 'Fehler beim Anlegen');
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
  const lbl = { display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 };

  return (
    <div onClick={e => e.target === e.currentTarget && onClose()} style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', width: '100%', maxWidth: 480, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{ padding: '18px 22px 14px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Online Fertig Projekt</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>Manuelles Projekt anlegen (ohne Stripe-Checkout)</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1, padding: '0 2px' }}>×</button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Paket */}
          <div>
            <label style={lbl}>Paket</label>
            <select value={form.paket} onChange={set('paket')} style={inp}>
              <option value="starter">Starter — 1.500 €</option>
              <option value="kompagnon">Kompagnon — 3.500 €</option>
              <option value="premium">Premium — 2.500 €</option>
            </select>
          </div>

          {/* Unternehmensname */}
          <div>
            <label style={lbl}>Unternehmensname *</label>
            <input value={form.company_name} onChange={set('company_name')} placeholder="z.B. Müller Haustechnik GmbH" style={inp} autoFocus />
          </div>

          {/* Website / Domain — Pflichtfeld */}
          <div>
            <label style={lbl}>Website / Domain *</label>
            <input value={form.website_url} onChange={set('website_url')} placeholder="z.B. mueller-haustechnik.de" style={inp} autoComplete="url" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Ohne Domain kann kein Audit und kein Website-Projekt gestartet werden.</div>
          </div>

          {/* Ansprechpartner + Telefon */}
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl}>Ansprechpartner</label>
              <input value={form.contact_name} onChange={set('contact_name')} placeholder="Vor- und Nachname" style={inp} />
            </div>
            <div>
              <label style={lbl}>Telefon</label>
              <input type="tel" value={form.phone} onChange={set('phone')} placeholder="+49 261 …" style={inp} />
            </div>
          </div>

          {/* E-Mail */}
          <div>
            <label style={lbl}>E-Mail</label>
            <input type="email" value={form.email} onChange={set('email')} placeholder="info@firma.de" style={inp} />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 4 }}>
            <button type="button" onClick={onClose} style={{ padding: '9px 18px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Abbrechen
            </button>
            <button type="submit" disabled={saving} style={{ padding: '9px 22px', background: saving ? 'var(--text-tertiary)' : 'var(--kc-dark)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Anlegen…' : '✓ Projekt anlegen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const IMPULS_EMPTY = { company_name: '', website_url: '', contact_name: '', email: '', phone: '', isb_antrag_datum: '', isb_bewilligung_datum: '', foerder_volumen: 20000, tagewerke: 20 };

// ── IMPULS-Projekt Modal ──────────────────────────────────────────────────────
function ImpulsModal({ token, onClose, onCreated }) {
  const [form, setForm] = useState({ ...IMPULS_EMPTY });
  const [saving, setSaving] = useState(false);
  const { isMobile } = useScreenSize();
  const h = token ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.company_name.trim()) { toast.error('Bitte Unternehmensname eingeben'); return; }
    if (!form.website_url.trim())  { toast.error('Bitte Website / Domain eingeben'); return; }

    const websiteUrl = form.website_url.trim().startsWith('http')
      ? form.website_url.trim()
      : `https://${form.website_url.trim()}`;

    const isbNotes = [
      form.isb_antrag_datum      ? `ISB-Antrag: ${form.isb_antrag_datum}` : '',
      form.isb_bewilligung_datum ? `ISB-Bewilligung: ${form.isb_bewilligung_datum}` : '',
      form.foerder_volumen       ? `Fördervolumen: ${form.foerder_volumen} €` : '',
      form.tagewerke             ? `Tagewerke: ${form.tagewerke}` : '',
    ].filter(Boolean).join(' | ');

    setSaving(true);
    try {
      const leadRes = await fetch(`${API_BASE_URL}/api/leads/`, {
        method: 'POST', headers: h,
        body: JSON.stringify({
          company_name: form.company_name.trim(),
          website_url:  websiteUrl,
          contact_name: form.contact_name.trim(),
          email:        form.email.trim(),
          phone:        form.phone.trim(),
          lead_source:  'isb_impuls',
          status:       'won',
          notes:        isbNotes || undefined,
        }),
      });
      if (!leadRes.ok) {
        const err = await leadRes.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${leadRes.status}`);
      }
      const lead = await leadRes.json();

      const projRes = await fetch(`${API_BASE_URL}/api/projects/from-lead/${lead.id}`, {
        method: 'POST', headers: h,
      });
      if (!projRes.ok && projRes.status !== 409) throw new Error('Projekt konnte nicht angelegt werden');
      const proj = await projRes.json();
      toast.success(`IMPULS-Projekt für ${form.company_name} angelegt`);
      onCreated(proj.project_id);
    } catch (err) {
      toast.error(err.message || 'Fehler beim Anlegen');
    } finally {
      setSaving(false);
    }
  };

  const inp = { width: '100%', boxSizing: 'border-box', padding: '9px 12px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none' };
  const lbl = { display: 'block', fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 };
  const numInp = { ...inp, width: '100%' };

  return (
    <div onClick={e => e.target === e.currentTarget && onClose()} style={{ position: 'fixed', inset: 0, zIndex: 2000, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16, overflowY: 'auto' }}>
      <div style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', width: '100%', maxWidth: 500, display: 'flex', flexDirection: 'column', margin: 'auto' }}>
        {/* Header */}
        <div style={{ padding: '18px 22px 14px', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>IMPULS-Projekt anlegen</div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>ISB-Förderprojekt (ISB-158)</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1, padding: '0 2px' }}>×</button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '18px 22px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Kontaktdaten */}
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Kontaktdaten</div>

          <div>
            <label style={lbl}>Unternehmensname *</label>
            <input value={form.company_name} onChange={set('company_name')} placeholder="Mustermann GmbH" style={inp} autoFocus />
          </div>

          <div>
            <label style={lbl}>Website / Domain *</label>
            <input value={form.website_url} onChange={set('website_url')} placeholder="mustermann-gmbh.de" style={inp} autoComplete="url" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>Für Audit und Website-Erstellung erforderlich.</div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
            <div>
              <label style={lbl}>Ansprechpartner</label>
              <input value={form.contact_name} onChange={set('contact_name')} placeholder="Vor- und Nachname" style={inp} />
            </div>
            <div>
              <label style={lbl}>Telefon</label>
              <input type="tel" value={form.phone} onChange={set('phone')} placeholder="+49 261 …" style={inp} />
            </div>
          </div>

          <div>
            <label style={lbl}>E-Mail</label>
            <input type="email" value={form.email} onChange={set('email')} placeholder="info@firma.de" style={inp} />
          </div>

          {/* ISB-Förderdaten */}
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 14 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>ISB-Förderdaten</div>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>
              <div>
                <label style={lbl}>Antragsdatum</label>
                <input type="date" value={form.isb_antrag_datum} onChange={set('isb_antrag_datum')} style={inp} />
              </div>
              <div>
                <label style={lbl}>Bewilligungsdatum</label>
                <input type="date" value={form.isb_bewilligung_datum} onChange={set('isb_bewilligung_datum')} style={inp} />
              </div>
              <div>
                <label style={lbl}>Fördervolumen (€)</label>
                <input type="number" value={form.foerder_volumen} onChange={set('foerder_volumen')} style={numInp} min={0} />
              </div>
              <div>
                <label style={lbl}>Tagewerke gesamt</label>
                <input type="number" value={form.tagewerke} onChange={set('tagewerke')} style={numInp} min={1} />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, paddingTop: 4 }}>
            <button type="button" onClick={onClose} style={{ padding: '9px 18px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', color: 'var(--text-secondary)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
              Abbrechen
            </button>
            <button type="submit" disabled={saving} style={{ padding: '9px 22px', background: saving ? 'var(--text-tertiary)' : '#7c3aed', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}>
              {saving ? 'Anlegen…' : '✓ IMPULS-Projekt anlegen'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CustomerProjects() {
  const navigate     = useNavigate();
  const { token, hasRole } = useAuth();
  const h            = token ? { Authorization: `Bearer ${token}` } : {};

  const [projects, setProjects]   = useState([]);
  const [leadsMap, setLeadsMap]   = useState({});  // lead_id → lead
  const [loading, setLoading]     = useState(true);
  const [search, setSearch]       = useState('');
  const [phaseFilter, setPhaseFilter] = useState('');
  const [showOnlineFertig, setShowOnlineFertig] = useState(false);
  const [showImpuls, setShowImpuls] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);

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

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--kc-dark)', textTransform: 'uppercase', letterSpacing: '0.02em', lineHeight: 1, margin: 0 }}>Kundenprojekte</h1>
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--text-30)', marginTop: 4, fontFamily: 'var(--font-sans)' }}>
            {loading ? 'Lädt…' : `${filtered.length} von ${projects.length} Projekten`}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={() => setShowNewProject(true)}
            style={{ padding: '9px 18px', background: 'var(--kc-yellow)', color: '#000', border: 'none', borderRadius: 'var(--r-md)', fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-sans)', textTransform: 'uppercase', letterSpacing: '0.04em' }}
          >
            + Neues Projekt
          </button>
          {hasRole('admin') && (
            <>
              <button
                onClick={() => setShowImpuls(true)}
                style={{ padding: '8px 16px', background: '#7c3aed', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                + IMPULS-PROJEKT
              </button>
              <button
                onClick={() => setShowOnlineFertig(true)}
                style={{ padding: '8px 16px', background: 'var(--kc-dark)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                + Online Fertig
              </button>
            </>
          )}
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

      {/* Neues Projekt Modal */}
      {showNewProject && (
        <NewProjectModal
          onClose={() => setShowNewProject(false)}
          onProjectCreated={(projekt) => {
            setShowNewProject(false);
            navigate(`/app/projects/${projekt.id}`);
          }}
        />
      )}

      {/* Online Fertig Modal */}
      {showOnlineFertig && (
        <OnlineFertigModal
          token={token}
          onClose={() => setShowOnlineFertig(false)}
          onCreated={(projectId) => {
            setShowOnlineFertig(false);
            navigate(`/app/projects/${projectId}`);
          }}
        />
      )}

      {/* IMPULS-Projekt Modal */}
      {showImpuls && (
        <ImpulsModal
          token={token}
          onClose={() => setShowImpuls(false)}
          onCreated={(projectId) => {
            setShowImpuls(false);
            navigate(`/app/projects/${projectId}`);
          }}
        />
      )}
    </div>
  );
}
