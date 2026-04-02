import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import AuditReport from '../components/AuditReport';
import BriefingTab from '../components/BriefingTab';
import OfferTab from '../components/OfferTab';
import ProjectFilesSection from '../components/ProjectFilesSection';
import AcademyCustomerSection from '../components/AcademyCustomerSection';
import PageSpeedSection from '../components/PageSpeedSection';
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
  { id: 'overview',   label: 'Übersicht',   icon: '⊞' },
  { id: 'briefing',   label: 'Briefing',    icon: '📋' },
  { id: 'contact',    label: 'Kontakt',     icon: '👤' },
  { id: 'audits',     label: 'Audits',      icon: '✓' },
  { id: 'dateien',    label: 'Dateien',     icon: '📎' },
  { id: 'pagespeed',  label: 'PageSpeed',   icon: '⚡' },
  { id: 'akademy',    label: 'Akademy',     icon: '🎓' },
  { id: 'checklists', label: 'Checklisten', icon: '📋' },
  { id: 'offer',      label: 'Angebot',     icon: '📄' },
  { id: 'qrcode',     label: 'Zugang',      icon: '📲' },
  { id: 'crawler',    label: 'Crawler',     icon: '🕷️' },
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
  const [qrData, setQrData] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [qrRefreshing, setQrRefreshing] = useState(false);
  // Crawler
  const [crawlJob, setCrawlJob] = useState(null);
  const [crawlResults, setCrawlResults] = useState([]);
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlSort, setCrawlSort] = useState({ col: 'crawled_at', asc: true });
  const [crawlExpandedRow, setCrawlExpandedRow] = useState(null);

  const h = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  useEffect(() => { loadProfile(); loadQrCode(); }, [leadId]); // eslint-disable-line

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

  const loadQrCode = async () => {
    setQrLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${leadId}/qr-code`, { headers: h });
      const data = await res.json();
      setQrData(data);
    } catch (e) { console.error(e); }
    finally { setQrLoading(false); }
  };

  const refreshQrCode = async () => {
    if (!window.confirm('Alten QR-Code ungültig machen und neuen erstellen?')) return;
    setQrRefreshing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${leadId}/qr-code/refresh`, { method: 'POST', headers: h });
      const data = await res.json();
      setQrData(data);
    } catch (e) { console.error(e); }
    finally { setQrRefreshing(false); }
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

            {/* QR-Code */}
            <Card padding="md">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kunden-Zugang</span>
                <button onClick={() => setActiveTab('qrcode')} style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Details →</button>
              </div>
              {qrLoading ? (
                <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                </div>
              ) : qrData ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ background: 'white', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: 8, flexShrink: 0, cursor: 'pointer' }}
                    onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                    title="Klicken zum Herunterladen">
                    <img src={`data:image/png;base64,${qrData.qr_code_base64}`} alt="QR-Code" style={{ width: 90, height: 90, display: 'block' }} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    {lead.email && (
                      <div style={{ background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 'var(--radius-sm)', padding: '3px 8px', fontSize: 11, fontWeight: 500, marginBottom: 8, display: 'inline-block' }}>
                        🔐 @{lead.email.split('@')[1]}
                      </div>
                    )}
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: 10 }}>
                      {qrData.portal_url.replace('https://', '')}
                    </div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <button onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                        style={{ padding: '5px 10px', background: 'var(--brand-primary)', color: 'white', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        ⬇ PNG
                      </button>
                      <button onClick={() => navigator.clipboard.writeText(qrData.portal_url)}
                        style={{ padding: '5px 10px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        📋 Link
                      </button>
                      {lead.email && (
                        <a href={`mailto:${lead.email}?subject=Ihr persönlicher Zugang&body=Ihr Zugangslink:%0D%0A${qrData.portal_url}`}
                          style={{ padding: '5px 10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)', fontSize: 11, textDecoration: 'none', fontFamily: 'var(--font-sans)' }}>
                          ✉️
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <button onClick={loadQrCode} style={{ padding: '8px 16px', background: 'var(--bg-active)', color: 'var(--brand-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    QR-Code generieren
                  </button>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* BRIEFING TAB */}
      {activeTab === 'briefing' && (
        <BriefingTab lead={lead} isMobile={isMobile} />
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

      {/* DATEIEN TAB */}
      {activeTab === 'dateien' && <ProjectFilesSection leadId={lead.id} />}

      {/* PAGESPEED TAB */}
      {activeTab === 'pagespeed' && <PageSpeedSection leadId={lead.id} />}

      {/* AKADEMY TAB */}
      {activeTab === 'akademy' && <AcademyCustomerSection leadId={lead.id} />}

      {/* ANGEBOT TAB */}
      {activeTab === 'offer' && (
        <OfferTab lead={lead} currentScore={current_score} currentLevel={current_level} isMobile={isMobile} />
      )}

      {/* QR-CODE TAB */}
      {activeTab === 'qrcode' && (() => {
        if (!qrData && !qrLoading) { loadQrCode(); }
        return (
          <div style={{ display: 'grid', gridTemplateColumns: isDesktop ? '320px 1fr' : '1fr', gap: 16, alignItems: 'flex-start' }}>
            <Card padding="md">
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4 }}>Kunden-Zugang QR-Code</div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 16, lineHeight: 1.5 }}>
                Der Kunde scannt diesen Code und gelangt direkt zu seinen Daten.
              </div>
              {qrLoading ? (
                <div style={{ height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                </div>
              ) : qrData ? (
                <>
                  <div style={{ background: 'white', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16, textAlign: 'center', marginBottom: 12 }}>
                    <img src={`data:image/png;base64,${qrData.qr_code_base64}`} alt="QR-Code" style={{ width: '100%', maxWidth: 220, height: 'auto', display: 'block', margin: '0 auto' }} />
                    <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, letterSpacing: '0.05em' }}>{lead.company_name?.toUpperCase()}</div>
                  </div>
                  <div style={{ background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', padding: '8px 10px', marginBottom: 12 }}>
                    <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Portal-Link</div>
                    <div style={{ fontSize: 10, color: 'var(--brand-primary)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all', lineHeight: 1.4 }}>{qrData.portal_url}</div>
                  </div>
                  {lead.email && (
                    <div style={{ background: 'var(--status-info-bg)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: '8px 10px', marginBottom: 12, fontSize: 11, color: 'var(--status-info-text)', lineHeight: 1.5 }}>
                      🔐 Zugang via Domain <strong>@{lead.email.split('@')[1]}</strong>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                      style={{ flex: 1, padding: 8, background: 'var(--brand-primary)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      ⬇ PNG laden
                    </button>
                    <button onClick={() => navigator.clipboard.writeText(qrData.portal_url)}
                      style={{ flex: 1, padding: 8, background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      📋 Link kopieren
                    </button>
                    <button onClick={refreshQrCode} disabled={qrRefreshing}
                      style={{ padding: '8px 10px', background: 'var(--bg-surface)', color: 'var(--status-danger-text)', border: '1px solid var(--status-danger-bg)', borderRadius: 'var(--radius-md)', fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                      title="Neuen Code generieren">🔄</button>
                  </div>
                  <div style={{ marginTop: 8, fontSize: 10, color: 'var(--text-tertiary)', textAlign: 'center' }}>Erstellt: {qrData.created_at}</div>
                </>
              ) : (
                <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-tertiary)', fontSize: 12 }}>QR-Code konnte nicht geladen werden</div>
              )}
            </Card>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Card padding="md">
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>So funktioniert der Kunden-Zugang</div>
                {[
                  { icon: '📲', title: 'QR-Code scannen', desc: 'Kunde scannt den Code mit dem Smartphone — kein Login nötig.' },
                  { icon: '✉️', title: 'E-Mail-Domain eingeben', desc: `Verifikation über @${lead.email?.split('@')[1] || 'ihredomain.de'}.` },
                  { icon: '📊', title: 'Zugang zu Daten', desc: 'Audit-Ergebnisse, Scores und Handlungsempfehlungen.' },
                  { icon: '🔒', title: 'Sicher & eindeutig', desc: 'Jeder Code ist einmalig — bei Bedarf neuen erstellen.' },
                ].map(item => (
                  <div key={item.icon} style={{ display: 'flex', gap: 12, marginBottom: 14, alignItems: 'flex-start' }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-active)', color: 'var(--brand-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>{item.icon}</div>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{item.title}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{item.desc}</div>
                    </div>
                  </div>
                ))}
              </Card>
              <Card padding="md">
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>QR-Code versenden</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.6, marginBottom: 12 }}>
                  Den QR-Code als PNG herunterladen und dem Kunden per E-Mail oder Brief zusenden.
                </div>
                {lead.email && qrData && (
                  <a href={`mailto:${lead.email}?subject=Ihr persönlicher Zugang — KOMPAGNON&body=Sehr geehrte Damen und Herren,%0D%0A%0D%0AIhr persönlicher Kundenlink:%0D%0A${qrData.portal_url}`}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', background: 'var(--brand-primary)', color: 'white', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, textDecoration: 'none' }}>
                    ✉️ Per E-Mail senden
                  </a>
                )}
              </Card>
            </div>
          </div>
        );
      })()}

      {/* CRAWLER TAB */}
      {activeTab === 'crawler' && (() => {
        const loadCrawlStatus = () => {
          fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers: h })
            .then(r => r.json()).then(d => {
              setCrawlJob(d);
              if (d.status === 'completed') {
                fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers: h })
                  .then(r => r.json()).then(res => setCrawlResults(res.results || []));
              }
            }).catch(console.error);
        };
        const startCrawl = () => {
          const url = lead?.website_url;
          if (!url) return;
          setCrawlLoading(true);
          fetch(`${API_BASE_URL}/api/crawler/start/${leadId}`, {
            method: 'POST', headers: h,
            body: JSON.stringify({ url, max_pages: 50 }),
          }).then(r => r.json()).then(d => {
            setCrawlJob(d);
            setCrawlResults([]);
            // Poll while running
            const interval = setInterval(() => {
              fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers: h })
                .then(r => r.json()).then(status => {
                  setCrawlJob(status);
                  if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(interval);
                    setCrawlLoading(false);
                    if (status.status === 'completed') {
                      fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers: h })
                        .then(r => r.json()).then(res => setCrawlResults(res.results || []));
                    }
                  }
                });
            }, 3000);
          }).catch(e => { console.error(e); setCrawlLoading(false); });
        };

        if (!crawlJob && !crawlLoading) loadCrawlStatus();

        const statusColor = { running: '#f59e0b', completed: '#16a34a', failed: '#dc2626', pending: '#64748b', none: '#94a3b8' };
        const statusLabel = { running: 'Läuft', completed: 'Abgeschlossen', failed: 'Fehler', pending: 'Wartend', none: 'Kein Job' };

        const sorted = [...crawlResults].sort((a, b) => {
          const va = a[crawlSort.col] ?? '';
          const vb = b[crawlSort.col] ?? '';
          return crawlSort.asc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
        });

        const statusGroups = { '2xx': 0, '3xx': 0, '4xx+': 0 };
        crawlResults.forEach(r => {
          if (!r.status_code) return;
          if (r.status_code < 300) statusGroups['2xx']++;
          else if (r.status_code < 400) statusGroups['3xx']++;
          else statusGroups['4xx+']++;
        });
        const totalForBar = Object.values(statusGroups).reduce((a, b) => a + b, 0) || 1;

        const ThSort = ({ col, label }) => (
          <th onClick={() => setCrawlSort(p => ({ col, asc: p.col === col ? !p.asc : true }))} style={{ padding: '8px 12px', fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'left', cursor: 'pointer', borderBottom: '1px solid var(--border-light)', userSelect: 'none', whiteSpace: 'nowrap' }}>
            {label} {crawlSort.col === col ? (crawlSort.asc ? '↑' : '↓') : ''}
          </th>
        );

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>🕷️ Website-Crawler</div>
              <button onClick={startCrawl} disabled={crawlLoading || crawlJob?.status === 'running'} style={{
                padding: '8px 18px', background: '#16a34a', color: 'white',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 700,
                cursor: crawlLoading || crawlJob?.status === 'running' ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', opacity: crawlLoading || crawlJob?.status === 'running' ? 0.7 : 1,
              }}>
                {crawlJob?.status === 'running' ? '⏳ Läuft…' : '▶ Crawler starten'}
              </button>
            </div>

            {/* Status cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Status', value: statusLabel[crawlJob?.status || 'none'], color: statusColor[crawlJob?.status || 'none'] },
                { label: 'Laufzeit', value: crawlJob?.duration_seconds != null ? `${Math.floor(crawlJob.duration_seconds / 60)}m ${crawlJob.duration_seconds % 60}s` : '—' },
                { label: 'Gecrawlte URLs', value: crawlJob?.total_urls || crawlResults.length || 0 },
                { label: 'URL-Limit', value: 50 },
              ].map(c => (
                <div key={c.label} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{c.label}</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: c.color || 'var(--text-primary)' }}>{c.value}</div>
                </div>
              ))}
            </div>

            {/* Status bar chart */}
            {crawlResults.length > 0 && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>URLs nach Status-Code</div>
                <div style={{ display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', marginBottom: 10 }}>
                  {statusGroups['2xx'] > 0 && <div style={{ flex: statusGroups['2xx'], background: '#16a34a', minWidth: 2 }} title={`${statusGroups['2xx']} × 2xx`} />}
                  {statusGroups['3xx'] > 0 && <div style={{ flex: statusGroups['3xx'], background: '#f59e0b', minWidth: 2 }} title={`${statusGroups['3xx']} × 3xx`} />}
                  {statusGroups['4xx+'] > 0 && <div style={{ flex: statusGroups['4xx+'], background: '#dc2626', minWidth: 2 }} title={`${statusGroups['4xx+']} × 4xx+`} />}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 11, color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#16a34a', display: 'inline-block' }} />{statusGroups['2xx']} OK</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#f59e0b', display: 'inline-block' }} />{statusGroups['3xx']} Redirect</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#dc2626', display: 'inline-block' }} />{statusGroups['4xx+']} Fehler</span>
                </div>
              </div>
            )}

            {/* Results table */}
            {sorted.length > 0 ? (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden', overflowX: 'auto' }}>
                <table style={{ width: '100%', minWidth: 480, borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-app)' }}>
                      <ThSort col="crawled_at" label="Zeitpunkt" />
                      <ThSort col="status_code" label="Status" />
                      <ThSort col="load_time" label="Ladezeit" />
                      <ThSort col="url" label="URL" />
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((r, i) => {
                      const sc = r.status_code;
                      const scColor = !sc ? '#94a3b8' : sc < 300 ? '#16a34a' : sc < 400 ? '#f59e0b' : '#dc2626';
                      const scBg = !sc ? 'var(--bg-app)' : sc < 300 ? 'var(--status-success-bg)' : sc < 400 ? 'var(--status-warning-bg)' : 'var(--status-danger-bg)';
                      const lt = r.load_time;
                      const rowKey = r.url + '_' + i;
                      const isExpanded = crawlExpandedRow === rowKey;

                      // ── Build hints ──────────────────────────────
                      const hints = [];
                      if (sc === 301 || sc === 302) {
                        hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '⚠️ Weiterleitung erkannt. Prüfe ob die Ziel-URL direkt verlinkt werden kann, um Ladezeit zu sparen.' });
                      } else if (sc === 404) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht gefunden. Dieser Link sollte entfernt oder korrigiert werden.' });
                      } else if (sc === 500) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Serverfehler. Diese Seite hat ein technisches Problem und muss geprüft werden.' });
                      } else if (!sc || sc === 0) {
                        hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht erreichbar. Timeout nach 10 Sekunden.' });
                      }
                      if (lt != null && lt > 3.0) {
                        hints.push({ bg: '#fff7ed', border: '#fed7aa', text: '🟠 Ladezeit über 3 Sekunden. Bilder komprimieren oder Caching aktivieren.' });
                      } else if (lt != null && lt > 1.5) {
                        hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '🟡 Ladezeit erhöht. Performance-Optimierung empfohlen.' });
                      }
                      if (hints.length === 0 && sc >= 200 && sc < 300 && lt != null && lt <= 1.5) {
                        hints.push({ bg: 'var(--status-success-bg)', border: '#bbf7d0', text: '✅ Alles in Ordnung.' });
                      }

                      return (
                        <>
                          <tr
                            key={rowKey}
                            onClick={() => setCrawlExpandedRow(isExpanded ? null : rowKey)}
                            style={{
                              borderTop: '1px solid var(--border-light)',
                              cursor: 'pointer',
                              background: isExpanded ? 'var(--bg-app)' : 'transparent',
                              transition: 'background 0.15s',
                            }}
                            onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                            onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = 'transparent'; }}
                          >
                            <td style={{ padding: '7px 12px', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{r.crawled_at || '—'}</td>
                            <td style={{ padding: '7px 12px' }}>
                              <span style={{ background: scBg, color: scColor, fontWeight: 700, borderRadius: 4, padding: '2px 7px' }}>{sc || '—'}</span>
                            </td>
                            <td style={{ padding: '7px 12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                              {lt != null ? `${lt}s` : '—'}
                            </td>
                            <td style={{ padding: '7px 12px', maxWidth: 400 }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                <a href={r.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--brand-primary)', textDecoration: 'none', fontSize: 11, wordBreak: 'break-all' }}>{r.url}</a>
                                <span style={{ flexShrink: 0, fontSize: 10, color: 'var(--text-tertiary)', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
                              </div>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr key={rowKey + '_hint'} style={{ background: 'var(--bg-app)' }}>
                              <td colSpan={4} style={{ padding: '0 12px 10px 12px' }}>
                                <div style={{
                                  display: 'flex', flexDirection: 'column', gap: 6,
                                  animation: 'crawlHintIn 0.18s ease',
                                }}>
                                  {hints.length === 0 ? (
                                    <div style={{ padding: '8px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)' }}>
                                      Keine Empfehlung verfügbar.
                                    </div>
                                  ) : hints.map((hint, hi) => (
                                    <div key={hi} style={{
                                      padding: '9px 13px',
                                      background: hint.bg,
                                      border: `1px solid ${hint.border}`,
                                      borderRadius: 'var(--radius-md)',
                                      fontSize: 12, lineHeight: 1.5,
                                      color: 'var(--text-primary)',
                                    }}>
                                      {hint.text}
                                    </div>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : crawlJob?.status !== 'running' && (
              <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-tertiary)', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
                <div style={{ fontSize: 40, marginBottom: 10, opacity: 0.3 }}>🕷️</div>
                <div style={{ fontSize: 13 }}>Noch kein Crawl durchgeführt</div>
                <div style={{ fontSize: 11, marginTop: 4 }}>Klicke auf "Crawler starten" um die Website zu analysieren.</div>
              </div>
            )}
          </div>
        );
      })()}

      {/* AUDIT DETAIL MODAL */}
      {openAudit && createPortal(
        <>
          {/* Overlay — zwei separate fixed-Elemente, außerhalb des page-enter-Transform-Kontexts */}
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.6)', backdropFilter: 'blur(4px)', zIndex: 1000 }}
            onClick={() => setOpenAudit(null)} />
          <div style={{ position: 'fixed', top: 0, bottom: 0, left: 0, right: 0, zIndex: 1001, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '20px', pointerEvents: 'none' }}>
            <div style={{ maxWidth: 900, width: '100%', maxHeight: 'calc(100vh - 40px)', borderRadius: 'var(--radius-xl)', overflow: 'hidden', display: 'flex', flexDirection: 'column', pointerEvents: 'auto' }}>
              <div style={{ flex: 1, overflowY: 'auto' }}>
                <AuditReport auditData={openAudit} onClose={() => setOpenAudit(null)} />
              </div>
            </div>
          </div>
        </>,
        document.body
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
