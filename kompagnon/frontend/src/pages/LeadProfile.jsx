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

  // DATEI NOCH NICHT FERTIG — wird in Teil 2 fortgesetzt
  // Temporärer return damit die Datei valid ist:
  return <div style={{ padding: 20, color: 'var(--text-primary)' }}>Wird geladen... (Teil 2 folgt)</div>;
}
