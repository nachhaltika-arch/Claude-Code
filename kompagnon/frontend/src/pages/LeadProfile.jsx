import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import AuditReport from '../components/AuditReport';
import API_BASE_URL from '../config';

function useScreenWidth() {
  const [width, setWidth] = useState(window.innerWidth);
  useEffect(() => {
    const h = () => setWidth(window.innerWidth);
    window.addEventListener('resize', h);
    return () => window.removeEventListener('resize', h);
  }, []);
  return width;
}

const scoreColor = (s) =>
  s >= 70 ? 'var(--status-success-text)'
  : s >= 50 ? 'var(--status-warning-text)'
  : 'var(--status-danger-text)';

const STATUS_MAP = {
  new: ['neutral', 'Neu'],
  contacted: ['info', 'Kontaktiert'],
  qualified: ['success', 'Qualifiziert'],
  proposal_sent: ['warning', 'Angebot gesendet'],
  won: ['success', 'Gewonnen'],
  lost: ['danger', 'Verloren'],
};

const LEVEL_COLORS = {
  'Homepage Standard Platin': '#4a90d9',
  'Homepage Standard Gold': '#b8860b',
  'Homepage Standard Silber': '#708090',
  'Homepage Standard Bronze': '#cd7f32',
  'Nicht konform': 'var(--status-danger-text)',
};

const TABS = [
  { id: 'overview', label: 'Übersicht', icon: '⊞' },
  { id: 'contact', label: 'Kontakt', icon: '👤' },
  { id: 'audits', label: 'Audits', icon: '✓' },
  { id: 'checklists', label: 'Checklisten', icon: '📋' },
];

export default function LeadProfile() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const width = useScreenWidth();
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1100;
  const isDesktop = width >= 1100;

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});
  const [editingName, setEditingName] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [openAudit, setOpenAudit] = useState(null);
  const [deleteAuditId, setDeleteAuditId] = useState(null);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditProgress, setAuditProgress] = useState('');
  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);

  const h = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  useEffect(() => { loadProfile(); }, [leadId]); // eslint-disable-line

  const loadProfile = async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/profile`,
        { headers: h }
      );
      const data = await res.json();
      setProfile(data);
      const lead = data.lead;
      setDisplayName(lead.display_name || lead.company_name || '');
      setEditData({
        company_name: lead.company_name || '',
        display_name: lead.display_name || '',
        contact_name: lead.contact_name || '',
        phone: lead.phone || '',
        email: lead.email || '',
        website_url: lead.website_url || '',
        street: lead.street || '',
        house_number: lead.house_number || '',
        postal_code: lead.postal_code || '',
        city: lead.city || '',
        trade: lead.trade || '',
        legal_form: lead.legal_form || '',
        vat_id: lead.vat_id || '',
        register_number: lead.register_number || '',
        register_court: lead.register_court || '',
        ceo_first_name: lead.ceo_first_name || '',
        ceo_last_name: lead.ceo_last_name || '',
        notes: lead.notes || '',
      });
      if (!lead.website_screenshot) fetchLatestScreenshot();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchLatestScreenshot = async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/latest-screenshot`,
        { headers: h }
      );
      const data = await res.json();
      if (data.screenshot_url) {
        setProfile(prev => ({
          ...prev,
          lead: { ...prev.lead, website_screenshot: data.screenshot_url },
        }));
      }
    } catch {}
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}`,
        { method: 'PATCH', headers: h, body: JSON.stringify(editData) }
      );
      if (res.ok) { setEditMode(false); await loadProfile(); }
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const saveDisplayName = async () => {
    try {
      await fetch(
        `${API_BASE_URL}/api/leads/${leadId}`,
        { method: 'PATCH', headers: h, body: JSON.stringify({ display_name: displayName }) }
      );
      setEditingName(false);
      await loadProfile();
    } catch {}
  };

  const updateStatus = async (status) => {
    try {
      await fetch(
        `${API_BASE_URL}/api/leads/${leadId}`,
        { method: 'PATCH', headers: h, body: JSON.stringify({ status }) }
      );
      await loadProfile();
    } catch {}
  };

  const startAudit = async () => {
    if (!profile?.lead?.website_url) return;
    setAuditRunning(true);
    setAuditProgress('Audit wird gestartet...');
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/audit/start`,
        {
          method: 'POST', headers: h,
          body: JSON.stringify({
            website_url: profile.lead.website_url,
            lead_id: parseInt(leadId),
            company_name: profile.lead.company_name,
            city: profile.lead.city,
            trade: profile.lead.trade,
          }),
        }
      );
      const data = await res.json();
      if (!data.audit_id) throw new Error();
      pollAudit(data.audit_id);
    } catch { setAuditRunning(false); setAuditProgress(''); }
  };

  const pollAudit = (auditId) => {
    const msgs = [
      '🔍 Website wird analysiert...',
      '⚡ Performance wird gemessen...',
      '⚖️ Rechtliches wird geprüft...',
      '📸 Screenshot wird erstellt...',
      '🤖 KI-Analyse läuft...',
    ];
    let i = 0;
    const iv = setInterval(async () => {
      i = (i + 1) % msgs.length;
      setAuditProgress(msgs[i]);
      try {
        const res = await fetch(
          `${API_BASE_URL}/api/audit/${auditId}`,
          { headers: h }
        );
        const d = await res.json();
        if (d.status === 'completed') {
          clearInterval(iv);
          setAuditProgress('✓ Audit abgeschlossen!');
          setTimeout(async () => {
            setAuditRunning(false);
            setAuditProgress('');
            await loadProfile();
            setActiveTab('audits');
          }, 1500);
        } else if (d.status === 'failed') {
          clearInterval(iv);
          setAuditRunning(false);
          setAuditProgress('');
        }
      } catch {}
    }, 4000);
    setTimeout(() => { clearInterval(iv); setAuditRunning(false); }, 180000);
  };

  const createScreenshot = async () => {
    if (!profile?.lead?.website_url) return;
    setScreenshotLoading(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/screenshot`,
        { method: 'POST', headers: h }
      );
      const data = await res.json();
      if (data.success && data.screenshot_url) {
        setProfile(prev => ({
          ...prev,
          lead: { ...prev.lead, website_screenshot: data.screenshot_url },
        }));
      }
    } catch {} finally { setScreenshotLoading(false); }
  };

  const deleteAudit = async (auditId) => {
    try {
      await fetch(
        `${API_BASE_URL}/api/audit/${auditId}`,
        { method: 'DELETE', headers: h }
      );
      setDeleteAuditId(null);
      await loadProfile();
    } catch {}
  };

  const extractFromImpressum = async () => {
    if (!profile?.lead?.website_url) return;
    setExtracting(true);
    setExtractResult(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${leadId}/extract-impressum`,
        { method: 'POST', headers: h }
      );
      const data = await res.json();
      if (!res.ok) {
        setExtractResult({ success: false, message: data.detail || 'Fehler' });
        return;
      }
      const count = Object.keys(data.updated_fields || {}).length;
      const skipped = (data.skipped_fields || []).length;
      setExtractResult({
        success: true,
        message: count > 0
          ? `${count} Felder importiert${skipped > 0 ? `, ${skipped} bereits vorhanden` : ''}`
          : 'Alle Felder bereits befüllt',
        updated: data.updated_fields,
      });
      if (count > 0) await loadProfile();
    } catch {
      setExtractResult({ success: false, message: 'Verbindungsfehler' });
    } finally {
      setExtracting(false);
    }
  };

  const inputStyle = {
    width: '100%', padding: '8px 10px',
    border: '1px solid var(--border-medium)',
    borderRadius: 'var(--radius-md)', fontSize: 13,
    fontFamily: 'var(--font-sans)',
    color: 'var(--text-primary)',
    background: 'var(--bg-surface)',
    outline: 'none', boxSizing: 'border-box',
  };

  const sectionLabel = {
    fontSize: 10, fontWeight: 600,
    color: 'var(--text-tertiary)',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    marginBottom: 8, marginTop: 16,
  };

  const fieldRow = (icon, value, label) =>
    value ? (
      <div key={label} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 14, color: 'var(--brand-primary)', flexShrink: 0, marginTop: 1, width: 18, textAlign: 'center' }}>
          {icon}
        </span>
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-primary)' }}>{value}</div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 1 }}>{label}</div>
        </div>
      </div>
    ) : null;

  // LOADING STATE
  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh', flexDirection: 'column', gap: 12 }}>
      <div style={{ width: 36, height: 36, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
      <span style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Kundenkartei wird geladen...</span>
    </div>
  );

  if (!profile) return (
    <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-tertiary)' }}>Kunde nicht gefunden</div>
  );

  const { lead, current_score, current_level, audits = [], score_history = [] } = profile;
  const latestAudit = audits[0] || null;
  const levelColor = current_level ? LEVEL_COLORS[current_level] : 'var(--text-tertiary)';
  const [statusVariant, statusLabel] = STATUS_MAP[lead.status] || ['neutral', lead.status];
  const improvement = score_history.length >= 2
    ? score_history[score_history.length - 1].score - score_history[0].score
    : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.3s ease', maxWidth: 1200, margin: '0 auto', width: '100%' }}>

      {/* HEADER */}
      <div style={{ background: 'var(--brand-primary)', borderRadius: 'var(--radius-xl)', padding: isMobile ? '20px 16px' : '24px', color: 'white', position: 'relative', overflow: 'hidden' }}>

        <button onClick={() => navigate(-1)} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 'var(--radius-md)', color: 'white', fontSize: 12, padding: '5px 10px', cursor: 'pointer', marginBottom: 14, display: 'inline-flex', alignItems: 'center', gap: 4, fontFamily: 'var(--font-sans)' }}>
          ← Zurück
        </button>

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: isMobile ? 'wrap' : 'nowrap', gap: 16 }}>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
              Kundenkartei
            </div>

            {editingName ? (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <input
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') saveDisplayName(); if (e.key === 'Escape') setEditingName(false); }}
                  autoFocus
                  style={{ ...inputStyle, background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.4)', color: 'white', fontSize: 20, fontWeight: 600, flex: 1, minWidth: 200 }}
                />
                <button onClick={saveDisplayName} style={{ background: 'white', color: 'var(--brand-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '7px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>✓</button>
                <button onClick={() => setEditingName(false)} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 'var(--radius-md)', color: 'white', padding: '7px 10px', fontSize: 12, cursor: 'pointer' }}>✕</button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <h1 style={{ fontSize: isMobile ? 20 : 24, fontWeight: 600, color: 'white', margin: 0, letterSpacing: '-0.01em' }}>
                  {lead.display_name || lead.company_name}
                </h1>
                <button onClick={() => setEditingName(true)} style={{ background: 'rgba(255,255,255,0.12)', border: 'none', borderRadius: 'var(--radius-sm)', color: 'rgba(255,255,255,0.7)', fontSize: 11, padding: '3px 7px', cursor: 'pointer' }} title="Karteiname ändern">
                  ✏️
                </button>
              </div>
            )}

            {lead.display_name && lead.display_name !== lead.company_name && (
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>{lead.company_name}</div>
            )}

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 10, alignItems: 'center' }}>
              {lead.trade && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>🔧 {lead.trade}</span>}
              {lead.city && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.75)' }}>📍 {lead.city}</span>}
              <Badge variant={statusVariant}>{statusLabel}</Badge>
              {improvement !== null && (
                <span style={{ fontSize: 11, color: improvement >= 0 ? '#86efac' : '#fca5a5', fontWeight: 500 }}>
                  {improvement >= 0 ? '↑' : '↓'}{Math.abs(improvement)} Punkte
                </span>
              )}
            </div>
          </div>

          {current_score !== null && (
            <div style={{ background: 'rgba(255,255,255,0.12)', borderRadius: 'var(--radius-lg)', padding: '16px 20px', textAlign: 'center', flexShrink: 0, backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.2)', minWidth: 90 }}>
              <div style={{ fontSize: isMobile ? 32 : 40, fontWeight: 600, color: 'white', lineHeight: 1 }}>{current_score}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>/ 100</div>
              {current_level && (
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.75)', marginTop: 6, fontWeight: 500 }}>
                  {current_level.replace('Homepage Standard ', '')}
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
          <button
            onClick={startAudit}
            disabled={auditRunning}
            style={{ background: auditRunning ? 'rgba(255,255,255,0.1)' : 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)', borderRadius: 'var(--radius-md)', color: 'white', fontSize: 12, fontWeight: 500, padding: '7px 14px', cursor: auditRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            {auditRunning ? (
              <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />{auditProgress || 'Läuft...'}</>
            ) : '🔍 Audit starten'}
          </button>

          <button onClick={() => { setActiveTab('contact'); setEditMode(true); }} style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: 'var(--radius-md)', color: 'white', fontSize: 12, fontWeight: 500, padding: '7px 14px', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ✏️ Bearbeiten
          </button>

          <select value={lead.status} onChange={e => updateStatus(e.target.value)} style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: 'var(--radius-md)', color: 'white', fontSize: 12, padding: '7px 12px', cursor: 'pointer', fontFamily: 'var(--font-sans)', outline: 'none' }}>
            <option value="new">Neu</option>
            <option value="contacted">Kontaktiert</option>
            <option value="qualified">Qualifiziert</option>
            <option value="proposal_sent">Angebot gesendet</option>
            <option value="won">Gewonnen</option>
            <option value="lost">Verloren</option>
          </select>
        </div>
      </div>

      {/* TABS */}
      <div style={{ display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 4, overflowX: 'auto' }}>
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} style={{ flex: isMobile ? '0 0 auto' : 1, padding: isMobile ? '7px 14px' : '8px 12px', borderRadius: 'var(--radius-md)', border: 'none', background: activeTab === tab.id ? 'var(--bg-active)' : 'transparent', color: activeTab === tab.id ? 'var(--brand-primary)' : 'var(--text-tertiary)', fontSize: 12, fontWeight: activeTab === tab.id ? 500 : 400, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, whiteSpace: 'nowrap', transition: 'all 0.15s' }}>
            <span>{tab.icon}</span>{tab.label}
          </button>
        ))}
      </div>

      {/* ÜBERSICHT TAB */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: isDesktop ? '340px 1fr' : isTablet ? '280px 1fr' : '1fr', gap: 16, alignItems: 'flex-start' }}>

          {/* Linke Spalte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

            {/* Screenshot */}
            <Card padding="sm">
              <div style={{ background: 'var(--bg-app)', padding: '7px 10px', display: 'flex', alignItems: 'center', gap: 5, borderBottom: '1px solid var(--border-light)', margin: '-12px -12px 0' }}>
                {['#ef4444','#f59e0b','#22c55e'].map(c => (
                  <div key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                ))}
                <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', border: '1px solid var(--border-light)' }}>
                  {lead.website_url || 'Keine Website'}
                </div>
                {lead.website_url && (
                  <a href={lead.website_url.startsWith('http') ? lead.website_url : 'https://' + lead.website_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: 'var(--text-tertiary)', flexShrink: 0 }}>↗</a>
                )}
                <button onClick={createScreenshot} disabled={screenshotLoading} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: screenshotLoading ? 'wait' : 'pointer', fontSize: 12, padding: '1px 4px', flexShrink: 0 }} title="Screenshot aktualisieren">
                  {screenshotLoading ? '⏳' : '🔄'}
                </button>
              </div>

              <div style={{ margin: '0 -12px', position: 'relative', minHeight: 160 }}>
                {screenshotLoading ? (
                  <div style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', gap: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Screenshot wird erstellt...</span>
                  </div>
                ) : lead.website_screenshot ? (
                  <>
                    <img src={lead.website_screenshot} alt="Website" style={{ width: '100%', display: 'block', maxHeight: 200, objectFit: 'cover', objectPosition: 'top' }} />
                    {current_score !== null && (
                      <div style={{ position: 'absolute', bottom: 8, right: 8, background: 'rgba(15,28,32,0.85)', backdropFilter: 'blur(6px)', borderRadius: 'var(--radius-md)', padding: '4px 10px' }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: levelColor }}>{current_score}/100</span>
                      </div>
                    )}
                  </>
                ) : (
                  <div onClick={createScreenshot} style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', cursor: lead.website_url ? 'pointer' : 'default', gap: 8 }}
                    onMouseEnter={e => { if (lead.website_url) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                    onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-app)'; }}
                  >
                    <span style={{ fontSize: 28 }}>📸</span>
                    <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>{lead.website_url ? 'Klicken für Screenshot' : 'Keine Website hinterlegt'}</span>
                  </div>
                )}
              </div>
            </Card>

            {/* Score Verlauf */}
            {score_history.length >= 2 && (
              <Card padding="sm">
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Score-Verlauf</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  {score_history.map((s, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {i > 0 && <span style={{ color: 'var(--border-medium)', fontSize: 12 }}>→</span>}
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 15, fontWeight: 600, color: scoreColor(s.score) }}>{s.score}</div>
                        <div style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>{s.date}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Kategorie Scores */}
            {latestAudit && (
              <Card padding="sm">
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Kategorien</div>
                {[
                  ['Compliance', latestAudit.rc_score, 25],
                  ['Performance', latestAudit.tp_score, 15],
                  ['Barrierefreiheit', latestAudit.bf_score, 15],
                  ['Sicherheit', latestAudit.si_score, 10],
                  ['SEO', latestAudit.se_score, 10],
                  ['UX', latestAudit.ux_score, 10],
                ].map(([label, score, max]) => {
                  const pct = Math.min(100, ((score || 0) / max) * 100);
                  const col = pct >= 70 ? 'var(--status-success-text)' : pct >= 50 ? 'var(--status-warning-text)' : 'var(--status-danger-text)';
                  return (
                    <div key={label} style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                        <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
                        <span style={{ fontWeight: 500, color: col }}>{score || 0}/{max}</span>
                      </div>
                      <div style={{ height: 4, background: 'var(--border-light)', borderRadius: 2, overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: col, borderRadius: 2, transition: 'width 0.6s ease' }} />
                      </div>
                    </div>
                  );
                })}
              </Card>
            )}
          </div>

          {/* Rechte Spalte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kontaktdaten</span>
                <button onClick={() => { setActiveTab('contact'); setEditMode(true); }} style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Bearbeiten →</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile || isTablet ? '1fr' : '1fr 1fr', gap: '0 16px' }}>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('✉️', lead.email, 'E-Mail')}
                {fieldRow('🌐', lead.website_url?.replace(/^https?:\/\//, ''), 'Website')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                {fieldRow('📍', [lead.street && `${lead.street} ${lead.house_number || ''}`.trim(), [lead.postal_code, lead.city].filter(Boolean).join(' ')].filter(Boolean).join(', '), 'Adresse')}
              </div>
              {lead.notes && (
                <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, fontStyle: 'italic' }}>
                  {lead.notes}
                </div>
              )}
            </Card>

            {latestAudit && (
              <Card padding="md">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Letzter Audit</span>
                  <button onClick={() => setActiveTab('audits')} style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Alle anzeigen →</button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: `${levelColor}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: levelColor }}>{latestAudit.total_score}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{current_level}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{new Date(latestAudit.created_at).toLocaleDateString('de-DE')}</div>
                  </div>
                </div>
                {latestAudit.ai_summary && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                    {latestAudit.ai_summary.substring(0, 200)}{latestAudit.ai_summary.length > 200 ? '...' : ''}
                  </div>
                )}
                <button onClick={() => setOpenAudit(latestAudit)} style={{ marginTop: 10, width: '100%', padding: '7px', background: 'var(--bg-active)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', color: 'var(--brand-primary)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Vollständigen Bericht anzeigen
                </button>
              </Card>
            )}

            {(lead.vat_id || lead.register_number || lead.register_court) && (
              <Card padding="md">
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>Rechtliches</div>
                {fieldRow('🏛️', lead.vat_id, 'USt-IdNr.')}
                {fieldRow('📋', lead.register_number, 'Handelsreg.-Nr.')}
                {fieldRow('⚖️', lead.register_court, 'Handelsregister')}
              </Card>
            )}
          </div>
        </div>
      )}

      {/* KONTAKT TAB */}
      {activeTab === 'contact' && (
        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)', margin: 0 }}>Kontakt & Unternehmen</h2>
            {!editMode && (
              <Button variant="secondary" size="sm" onClick={() => setEditMode(true)}>✏️ Bearbeiten</Button>
            )}
          </div>

          {!editMode && lead.website_url && (
            <div style={{ marginBottom: 16, padding: '12px 14px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>
                Automatisch aus Impressum befüllen
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 10 }}>
                Liest Firmenname, Adresse, Handelsregister u.v.m. direkt aus dem Impressum von <strong>{lead.website_url.replace(/^https?:\/\//, '')}</strong>
              </div>

              {extractResult && (
                <div style={{
                  padding: '8px 10px', borderRadius: 'var(--radius-sm)',
                  background: extractResult.success ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
                  color: extractResult.success ? 'var(--status-success-text)' : 'var(--status-danger-text)',
                  fontSize: 12, marginBottom: 8,
                }}>
                  {extractResult.success ? '✓' : '✕'} {extractResult.message}
                </div>
              )}

              <button onClick={extractFromImpressum} disabled={extracting} style={{
                padding: '7px 14px',
                background: extracting ? 'var(--bg-surface)' : 'var(--brand-primary)',
                color: extracting ? 'var(--text-tertiary)' : 'white',
                border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
                fontSize: 12, fontWeight: 500, cursor: extracting ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6,
              }}>
                {extracting ? (
                  <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid var(--border-medium)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Impressum wird gelesen...</>
                ) : '🔍 Impressum auslesen'}
              </button>
            </div>
          )}

          {editMode ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 12 }}>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Unternehmen</div>
                </div>

                {[
                  ['Firmenname', 'company_name', 'Mustermann GmbH'],
                  ['Gesellschaftsform', 'legal_form', 'GmbH, UG, GmbH & Co. KG'],
                  ['Vorname Geschäftsführer', 'ceo_first_name', 'Max'],
                  ['Nachname Geschäftsführer', 'ceo_last_name', 'Mustermann'],
                  ['Gewerk', 'trade', 'Elektriker'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Adresse</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Straße</div>
                    <input value={editData.street || ''} onChange={e => setEditData(p => ({...p, street: e.target.value}))} placeholder="Musterstraße" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Nr.</div>
                    <input value={editData.house_number || ''} onChange={e => setEditData(p => ({...p, house_number: e.target.value}))} placeholder="12a" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>PLZ</div>
                    <input value={editData.postal_code || ''} onChange={e => setEditData(p => ({...p, postal_code: e.target.value}))} placeholder="56070" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Ort</div>
                    <input value={editData.city || ''} onChange={e => setEditData(p => ({...p, city: e.target.value}))} placeholder="Koblenz" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Kontakt</div>
                </div>

                {[
                  ['Ansprechpartner', 'contact_name', 'Max Mustermann'],
                  ['Telefon', 'phone', '+49 261 123456'],
                  ['E-Mail', 'email', 'info@firma.de'],
                  ['Website', 'website_url', 'www.firma.de'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Rechtliches</div>
                </div>

                {[
                  ['USt-IdNr.', 'vat_id', 'DE123456789'],
                  ['Handelsreg.-Nr.', 'register_number', 'HRB 12345'],
                  ['Handelsregister', 'register_court', 'Amtsgericht Koblenz'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5, marginTop: 8 }}>Notizen</div>
                  <textarea value={editData.notes || ''} onChange={e => setEditData(p => ({...p, notes: e.target.value}))} placeholder="Interne Notizen..." rows={3}
                    style={{ ...inputStyle, resize: 'vertical', minHeight: 70 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary)'}
                    onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
                <Button variant="primary" onClick={saveEdit} disabled={saving}>
                  {saving ? 'Wird gespeichert...' : '✓ Speichern'}
                </Button>
                <Button variant="secondary" onClick={() => setEditMode(false)}>Abbrechen</Button>
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : isTablet ? '1fr 1fr' : '1fr 1fr 1fr', gap: 24 }}>
              <div>
                <div style={sectionLabel}>Unternehmen</div>
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🔧', lead.trade, 'Gewerk')}
              </div>
              <div>
                <div style={sectionLabel}>Kontakt</div>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('✉️', lead.email, 'E-Mail')}
                {fieldRow('🌐', lead.website_url?.replace(/^https?:\/\//, ''), 'Website')}
              </div>
              <div>
                <div style={sectionLabel}>Adresse</div>
                {fieldRow('📍', [lead.street && `${lead.street} ${lead.house_number || ''}`.trim(), [lead.postal_code, lead.city].filter(Boolean).join(' ')].filter(Boolean).join(', '), 'Anschrift')}
                {(lead.vat_id || lead.register_number) && (
                  <>
                    <div style={{ ...sectionLabel, marginTop: 16 }}>Rechtliches</div>
                    {fieldRow('🏛️', lead.vat_id, 'USt-IdNr.')}
                    {fieldRow('📋', lead.register_number, 'Handelsreg.-Nr.')}
                    {fieldRow('⚖️', lead.register_court, 'Handelsregister')}
                  </>
                )}
              </div>
            </div>
          )}
        </Card>
      )}

      {/* AUDITS TAB */}
      {activeTab === 'audits' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {auditRunning && (
            <div style={{ background: 'var(--status-info-bg)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Audit läuft...</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{auditProgress}</div>
              </div>
            </div>
          )}

          {audits.length === 0 && !auditRunning ? (
            <div style={{ textAlign: 'center', padding: '48px 20px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🔍</div>
              <div style={{ fontSize: 13 }}>Noch keine Audits vorhanden</div>
              <button onClick={startAudit} style={{ marginTop: 14, padding: '8px 18px', background: 'var(--brand-primary)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Ersten Audit starten
              </button>
            </div>
          ) : (
            audits.map((audit, i) => {
              const lc = audit.level ? LEVEL_COLORS[audit.level] : 'var(--text-tertiary)';
              const score = audit.total_score || 0;
              return (
                <div key={audit.id} style={{ background: 'var(--bg-surface)', border: `1px solid ${i === 0 ? 'var(--border-medium)' : 'var(--border-light)'}`, borderLeft: i === 0 ? '3px solid var(--brand-primary)' : '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: isMobile ? 'wrap' : 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                      <div style={{ width: 44, height: 44, borderRadius: 'var(--radius-md)', background: `${lc}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                        <span style={{ fontSize: 15, fontWeight: 700, color: lc }}>{score}</span>
                      </div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          {audit.level}
                          {i === 0 && <Badge variant="info">Aktuell</Badge>}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
                          {new Date(audit.created_at).toLocaleDateString('de-DE')}
                          {audit.website_url && ` · ${audit.website_url.replace(/^https?:\/\//, '')}`}
                        </div>
                        {audit.ai_summary && (
                          <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 380 }}>
                            {audit.ai_summary.substring(0, 100)}...
                          </div>
                        )}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexWrap: 'wrap' }}>
                      <Button variant="secondary" size="sm" onClick={() => setOpenAudit(audit)}>Details</Button>
                      <Button variant="ghost" size="sm" onClick={() => setDeleteAuditId(audit.id)}>🗑️</Button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* CHECKLISTEN TAB */}
      {activeTab === 'checklists' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <HomepageChecklist auditData={latestAudit} />
          <SecurityChecklist auditData={latestAudit} />
        </div>
      )}

      {/* AUDIT DETAIL MODAL */}
      {openAudit && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.6)', backdropFilter: 'blur(4px)', zIndex: 1000, overflowY: 'auto', padding: '20px', display: 'flex', alignItems: 'flex-start', justifyContent: 'center' }}
          onClick={e => { if (e.target === e.currentTarget) setOpenAudit(null); }}>
          <div style={{ maxWidth: 900, width: '100%', borderRadius: 'var(--radius-xl)', overflow: 'hidden', marginTop: 20 }}>
            <AuditReport auditData={openAudit} onClose={() => setOpenAudit(null)} />
          </div>
        </div>
      )}

      {/* AUDIT LÖSCHEN MODAL */}
      {deleteAuditId && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteAuditId(null)}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 380, width: '100%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--status-danger-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, margin: '0 auto 14px' }}>🗑️</div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Audit löschen?</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.5 }}>Dieser Audit-Eintrag wird dauerhaft gelöscht und kann nicht wiederhergestellt werden.</p>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button variant="secondary" fullWidth onClick={() => setDeleteAuditId(null)}>Abbrechen</Button>
              <Button variant="danger" fullWidth onClick={() => deleteAudit(deleteAuditId)}>Löschen</Button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
