import { useState, useEffect, useRef } from 'react';
import { useAudit } from '../hooks/useAudit';
import { parseApiError } from '../utils/apiError';
import { loadJson, saveJson } from '../utils/apiRequest';
import EmptyState from '../components/ui/EmptyState';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import {
  herkunftLabel, herkunftVariant, leadSourceLabel, rechtsgrundlageLabel,
} from '../utils/leadStatus';
import Button from '../components/ui/Button';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import AuditReport from '../components/AuditReport';
import BriefingTab from '../components/BriefingTab';
import BetriebVerlauf from '../components/BetriebVerlauf';
import BriefingWizard from '../components/BriefingWizard';
import WZSearch from '../components/WZSearch';
import SitemapPlaner from '../components/SitemapPlaner';
import ContentManager from '../components/ContentManager';
import OfferTab from '../components/OfferTab';
import ProjectFilesSection from '../components/ProjectFilesSection';
import AcademyCustomerSection from '../components/AcademyCustomerSection';
import PageSpeedSection from '../components/PageSpeedSection';
import API_BASE_URL from '../config';
import NewsletterDesigner from '../components/NewsletterDesigner';
import { useScreenSize } from '../utils/responsive';
import { datumKurz, datumUndZeit } from '../utils/datum';
import { befundZeilen, geprueftAmText } from '../utils/anreicherung';
import { naechsterSchritt } from '../utils/naechsterSchritt';
import { aufteilung } from '../utils/betriebReiter';
import { aufTaste } from '../utils/tastaturBedienung';
import CrawlerReiter from '../components/betrieb/CrawlerReiter';

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

// Zustellungsstörungen, wie Brevo sie meldet. Dauerhaft heißt: an diese
// Adresse kommt nichts mehr an, bis sich etwas ändert — das ist der
// Unterschied, auf den es beim Nachfassen ankommt.
const MAIL_STOERUNGEN = {
  hard_bounce:   { text: 'dauerhaft unzustellbar', dauerhaft: true },
  blocked:       { text: 'vom Empfänger abgewiesen', dauerhaft: true },
  invalid_email: { text: 'Adresse unbrauchbar', dauerhaft: true },
  spam:          { text: 'als Spam gemeldet', dauerhaft: true },
  soft_bounce:   { text: 'vorübergehend nicht zustellbar', dauerhaft: false },
  error:         { text: 'Fehler beim Versand', dauerhaft: false },
};

const LEVEL_COLORS = {
  'Homepage Standard Platin': 'var(--status-info-text)',
  'Homepage Standard Gold':   '#b8860b',
  'Homepage Standard Silber': 'var(--text-tertiary)',
  'Homepage Standard Bronze': '#cd7f32',
  'Nicht konform':            'var(--status-danger-text)',
};

const DomainBadge = ({ reachable, checkedAt, loading, onCheck }) => {
  if (loading) return <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>⏳ Prüfe...</span>;
  const date = checkedAt ? datumKurz(checkedAt, '') : '';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span style={{ padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, background: reachable === null ? 'var(--status-neutral-bg)' : reachable ? 'var(--status-success-bg)' : 'var(--status-danger-bg)', color: reachable === null ? 'var(--status-neutral-text)' : reachable ? 'var(--status-success-text)' : 'var(--status-danger-text)' }}>
        {reachable === null ? '● Nicht geprüft' : reachable ? '✓ Erreichbar' : '✗ Nicht erreichbar'}
      </span>
      {date && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{date}</span>}
      <button onClick={onCheck} title="Jetzt prüfen" style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 12, color: 'var(--text-tertiary)', padding: '0 2px' }}>🔄</button>
    </span>
  );
};

const TABS = [
  { id: 'overview',   label: 'Übersicht',   icon: '⊞' },
  { id: 'deals',      label: 'Deals',       icon: '💼' },
  { id: 'messages',   label: 'Nachrichten', icon: '💬' },
  { id: 'contact',    label: 'Kontakt',     icon: '👤' },
  { id: 'audits',     label: 'Audits',      icon: '✓' },
  { id: 'dateien',    label: 'Dateien',     icon: '📎' },
  // „Akademy" war halb deutsch, halb englisch — und trug damit als einziger
  // Reiter ein Wort, das es nicht gibt.
  { id: 'akademy',    label: 'Akademie',    icon: '🎓' },
  { id: 'offer',      label: 'Angebot',     icon: '📄' },
  { id: 'qrcode',     label: 'Zugang',      icon: '📲' },
  // Das Zeichen stand hier in der Beschriftung statt im `icon`-Feld. Gerendert
  // wird beides nebeneinander — dieser Reiter hatte dadurch einen Abstand
  // mehr als die anderen neun.
  { id: 'emails',     label: 'E-Mails',     icon: '📧' },
];

const GbpBadge = ({ lead }) => {
  if (!lead) return null;

  const claimed = lead.gbp_claimed;
  const rating  = lead.gbp_rating;
  const total   = lead.gbp_ratings_total;

  if (lead.gbp_checked_at === undefined || lead.gbp_checked_at === null) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 10px', borderRadius: 12, fontSize: 11,
        fontWeight: 500, background: '#F1EFE8', color: '#5F5E5A',
        border: '0.5px solid #D3D1C7',
      }}>
        <span>📍</span> Google Business: Nicht geprüft
      </span>
    );
  }

  if (!claimed) {
    return (
      <span
        title="Kein Google Business Profil gefunden — starkes Verkaufsargument!"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 5,
          padding: '3px 10px', borderRadius: 12, fontSize: 11,
          fontWeight: 600, background: '#FCEBEB', color: '#A32D2D',
          border: '0.5px solid #F09595', cursor: 'default',
        }}
      >
        <span>⚠</span> Google Business: Nicht eingetragen
      </span>
    );
  }

  const stars = rating ? `⭐ ${rating.toFixed(1)}` : '✓';
  const count = total  ? ` (${total} Bewertungen)` : '';

  return (
    <span
      title={`Google Place ID: ${lead.gbp_place_id || '—'}`}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 10px', borderRadius: 12, fontSize: 11,
        fontWeight: 600, background: '#EAF3DE', color: '#27500A',
        border: '0.5px solid #97C459', cursor: 'default',
      }}
    >
      {stars} Google Business{count}
    </span>
  );
};


export default function LeadProfile() {
  const { leadId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const { isMobile, width } = useScreenSize();
  const isTablet = width >= 768 && width < 1100;
  const isDesktop = width >= 1100;

  const [showNewsletter, setShowNewsletter] = useState(false);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [mehrOffen, setMehrOffen] = useState(false);
  const [domainFormOffen, setDomainFormOffen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});
  const [editingName, setEditingName] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [openAudit, setOpenAudit] = useState(null);
  const [deleteAuditId, setDeleteAuditId] = useState(null);

  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [extractResult, setExtractResult] = useState(null);
  const [qrData, setQrData] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [qrRefreshing, setQrRefreshing] = useState(false);
  // Crawler
  // Domains
  const [domains, setDomains] = useState([]);
  const [domainForm, setDomainForm] = useState({ url: '', label: '', is_primary: false });
  const [domainAdding, setDomainAdding] = useState(false);
  // Project
  const [projectId, setProjectId] = useState(null);
  const [projectData, setProjectData] = useState(null);
  const [creatingProject, setCreatingProject] = useState(false);
  const [wonModal, setWonModal] = useState(false);
  // Briefing wizard
  const [showBriefingWizard, setShowBriefingWizard] = useState(false);
  const [briefingData, setBriefingData] = useState(null);
  const [briefingLoading, setBriefingLoading] = useState(false);
  // Design tab
  const [designRunning, setDesignRunning] = useState(false);
  const [designSlow, setDesignSlow] = useState(false);
  const [designResult, setDesignResult] = useState(null);
  const [designError, setDesignError] = useState('');
  // Template assignment
  const [assignedTemplate, setAssignedTemplate] = useState(null);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [allTemplates, setAllTemplates] = useState([]);
  // Domain-Check
  const [domainLoading, setDomainLoading] = useState(false);
  // Deals
  const [companyDeals, setCompanyDeals] = useState([]);
  const [dealsLoading, setDealsLoading] = useState(false);
  // Nachrichten
  const [messages, setMessages] = useState([]);
  const [msgLoading, setMsgLoading] = useState(false);
  const [msgText, setMsgText] = useState('');
  const [msgChannel, setMsgChannel] = useState('in_app');
  const [msgSubject, setMsgSubject] = useState('');
  const [msgSending, setMsgSending] = useState(false);
  // Zustellungsstörungen: der Versand meldet Erfolg, sobald Brevo die Mail
  // annimmt — was danach beim Empfänger passiert, stand bisher nirgends.
  const [mailStoerungen, setMailStoerungen] = useState([]);
  // E-Mail-Sequenz
  const [emailLogs, setEmailLogs]       = useState([]);
  const [seqStatus, setSeqStatus]       = useState(null);
  const [emailLoading, setEmailLoading] = useState(false);

  // Kaltakquise
  const [kaltakquiseLoading, setKaltakquiseLoading] = useState(false);
  const [kaltakquiseDone,    setKaltakquiseDone]    = useState(false);
  const [kaltakquiseError,   setKaltakquiseError]   = useState('');
  const [kaltakquiseResult,  setKaltakquiseResult]  = useState(null);

  const h = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const { phase: auditPhase, progress: auditProgress, start: auditStart } = useAudit({
    leadId:      parseInt(leadId),
    websiteUrl:  profile?.lead?.website_url,
    companyName: profile?.lead?.company_name || '',
    city:        profile?.lead?.city  || '',
    headers:     h,
    autoStart:   false,
  });
  const auditRunning = auditPhase === 'running';

  useEffect(() => {
    if (auditPhase === 'done') {
      loadProfile();
      setActiveTab('audits');
    }
  }, [auditPhase]); // eslint-disable-line

  useEffect(() => { loadProfile(); loadQrCode(); loadDomains(); loadBriefing(); loadAssignedTemplate(); loadMailStoerungen(); }, [leadId]); // eslint-disable-line

  const loadMessages = async () => {
    setMsgLoading(true);
    const data = await loadJson(`${API_BASE_URL}/api/messages/${leadId}`, { headers: h }, { context: 'Nachrichten' });
    if (data) setMessages(data);
    setMsgLoading(false);
  };

  const sendMessage = async () => {
    if (!msgText.trim()) return;
    setMsgSending(true);
    // Vorher blieb der Text im Feld stehen und nichts passierte — der Nutzer
    // konnte nicht unterscheiden, ob gesendet wurde oder nicht.
    const sent = await saveJson(
      `${API_BASE_URL}/api/messages/${leadId}`,
      {
        method: 'POST', headers: h,
        body: JSON.stringify({ content: msgText.trim(), subject: msgSubject.trim() || undefined, channel: msgChannel }),
      },
      { context: 'Nachricht senden' }
    );
    if (sent) { setMsgText(''); setMsgSubject(''); await loadMessages(); }
    setMsgSending(false);
  };

  useEffect(() => {
    if (activeTab !== 'messages') return;
    loadMessages();
    const interval = setInterval(loadMessages, 30000);
    return () => clearInterval(interval);
  }, [activeTab, leadId]); // eslint-disable-line

  // Load deals for this company when deals tab opens
  useEffect(() => {
    if (activeTab !== 'deals' || !leadId) return;
    setDealsLoading(true);
    fetch(`${API_BASE_URL}/api/deals/?company_id=${leadId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : [])
      .then(d => { setCompanyDeals(Array.isArray(d) ? d : []); setDealsLoading(false); })
      .catch(() => setDealsLoading(false));
  }, [activeTab, leadId, token]);

  useEffect(() => {
    if (activeTab === 'emails') loadEmailData();
  }, [activeTab]); // eslint-disable-line

  const loadEmailData = async () => {
    setEmailLoading(true);
    const logs = await loadJson(`${API_BASE_URL}/api/leads/${leadId}/email-logs`, { headers: h }, { context: 'E-Mail-Verlauf' });
    if (logs) setEmailLogs(logs);

    if (profile?.lead) {
      setSeqStatus({
        active:    profile.lead.sequence_active,
        paused:    profile.lead.sequence_paused,
        step:      profile.lead.sequence_step || 0,
        last_sent: profile.lead.sequence_last_sent,
      });
    }
    setEmailLoading(false);
  };

  const seqAction = async (action) => {
    // Der Status wurde nie geprüft: eine abgelehnte Aktion sah nach einem
    // erfolgreichen Klick aus, weil danach einfach neu geladen wurde.
    const done = await saveJson(
      `${API_BASE_URL}/api/leads/${leadId}/sequence/${action}`,
      { method: 'POST', headers: h },
      { context: 'E-Mail-Sequenz' }
    );
    if (!done) return;
    await loadProfile();
    await loadEmailData();
  };

  const checkDomain = async () => {
    setDomainLoading(true);
    const d = await loadJson(
      `${API_BASE_URL}/api/leads/${leadId}/domain-check`,
      { method: 'POST', headers: h },
      { context: 'Domain-Prüfung', emptyOn: [] }
    );
    if (d) {
      setProfile(prev => ({ ...prev, lead: { ...prev.lead, domain_reachable: d.reachable, domain_status_code: d.status_code, domain_checked_at: d.checked_at } }));
    }
    setDomainLoading(false);
  };

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
      setProjectId(data.project_id || null);
      if (data.project_id) {
        loadJson(`${API_BASE_URL}/api/projects/${data.project_id}`, { headers: h }, { context: 'Projekt' })
          .then(p => { if (p) setProjectData(p); });
      }
      setEditData({
        company_name: lead.company_name || '',
        display_name: lead.display_name || '',
        contact_name: lead.contact_name || '',
        phone: lead.phone || '',
        mobile: lead.mobile || '',
        email: lead.email || '',
        website_url: lead.website_url || '',
        street: lead.street || '',
        house_number: lead.house_number || '',
        postal_code: lead.postal_code || '',
        city: lead.city || '',
        trade: lead.trade || '',
        wz_code: lead.wz_code || '',
        wz_title: lead.wz_title || '',
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

  const loadDomains = async () => {
    const data = await loadJson(`${API_BASE_URL}/api/leads/${leadId}/domains`, { headers: h }, { context: 'Domains' });
    if (data) setDomains(data);
  };

  const loadMailStoerungen = async () => {
    const data = await loadJson(`${API_BASE_URL}/api/mail-events/lead/${leadId}`, { headers: h }, { context: 'Zustellung' });
    if (data) setMailStoerungen(data.ereignisse || []);
  };

  const loadBriefing = async () => {
    setBriefingLoading(true);
    const data = await loadJson(`${API_BASE_URL}/api/briefings/${leadId}`, { headers: h }, { context: 'Briefing' });
    setBriefingLoading(false);
    if (data) setBriefingData(data);
    return data;
  };

  const openBriefingWizard = async () => {
    const data = await loadBriefing();
    setBriefingData(data);
    setShowBriefingWizard(true);
  };

  const loadAssignedTemplate = async () => {
    setTemplateLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/templates/lead/${leadId}`, { headers: h });
      if (res.ok) {
        const data = await res.json();
        setAssignedTemplate(data);
      } else {
        setAssignedTemplate(null);
      }
    } catch { setAssignedTemplate(null); }
    setTemplateLoading(false);
  };

  const openTemplateModal = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/templates/`, { headers: h });
      if (res.ok) setAllTemplates(await res.json());
    } catch { setAllTemplates([]); }
    setShowTemplateModal(true);
  };

  const assignTemplate = async (templateId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/templates/${templateId}/assign-lead`, {
        method: 'POST', headers: h, body: JSON.stringify({ lead_id: parseInt(leadId) }),
      });
      if (res.ok) {
        toast.success('Template zugewiesen');
        setShowTemplateModal(false);
        await loadAssignedTemplate();
      }
    } catch (e) { toast.error(parseApiError(e)); }
  };

  const generateDesign = async () => {
    setDesignRunning(true);
    setDesignSlow(false);
    setDesignError('');
    setDesignResult(null);
    const slowTimer = setTimeout(() => setDesignSlow(true), 20000);
    try {
      // Fetch briefing first
      const bRes = await fetch(`${API_BASE_URL}/api/briefings/${leadId}`, { headers: h });
      const briefing = bRes.ok ? await bRes.json() : null;

      const lead = profile?.lead;

      const payload = {
        company_name: String(lead?.display_name || lead?.company_name || ''),
        city: String(briefing?.einzugsgebiet || lead?.city || ''),
        trade: String(briefing?.gewerk || lead?.trade || ''),
        usp: String(briefing?.usp || ''),
        services: Array.isArray(briefing?.leistungen)
          ? briefing.leistungen.map(String)
          : typeof briefing?.leistungen === 'string'
            ? briefing.leistungen.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
            : [],
        target_audience: String(briefing?.zielgruppe || ''),
        page_name: 'Startseite',
        zweck: '',
        ziel_keyword: '',
        cta_text: '',
      };

      // Start background job — returns immediately with job_id
      const startRes = await fetch(`${API_BASE_URL}/api/agents/${projectId}/content`, {
        method: 'POST', headers: h, body: JSON.stringify(payload),
      });
      if (!startRes.ok) {
        const err = await startRes.json().catch(() => ({}));
        const detail = err.detail;
        throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : detail ? JSON.stringify(detail) : `Fehler ${startRes.status}`);
      }
      const { job_id } = await startRes.json();

      // Poll until done (max 120 s, every 2 s)
      let result = null;
      const deadline = Date.now() + 120_000;
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, 2000));
        const pollRes = await fetch(`${API_BASE_URL}/api/agents/jobs/${job_id}`, { headers: h });
        if (!pollRes.ok) throw new Error('Job-Status konnte nicht abgerufen werden');
        const job = await pollRes.json();
        if (job.status === 'done') {
          result = job.result_html || (typeof job.result === 'string' ? job.result : null);
          break;
        }
        if (job.status === 'error') throw new Error(job.error || 'KI-Generierung fehlgeschlagen');
      }
      if (!result) throw new Error('Zeitüberschreitung — bitte erneut versuchen');
      setDesignResult(result);
    } catch (e) {
      setDesignError(e?.message || e?.detail || String(e) || 'Generierung fehlgeschlagen.');
    } finally {
      clearTimeout(slowTimer);
      setDesignRunning(false);
      setDesignSlow(false);
    }
  };

  const addDomain = async () => {
    const url = domainForm.url.trim();
    if (!url) return;
    setDomainAdding(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${leadId}/domains`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ url, label: domainForm.label.trim(), is_primary: domainForm.is_primary }),
      });
      if (res.ok) {
        setDomainForm({ url: '', label: '', is_primary: false });
        await loadDomains();
      }
    } finally { setDomainAdding(false); }
  };

  const deleteDomain = async (domainId) => {
    await fetch(`${API_BASE_URL}/api/leads/${leadId}/domains/${domainId}`, { method: 'DELETE', headers: h });
    await loadDomains();
  };

  const fetchLatestScreenshot = async () => {
    const data = await loadJson(`${API_BASE_URL}/api/leads/${leadId}/latest-screenshot`, { headers: h }, { context: 'Screenshot' });
    if (data?.screenshot_url) {
      setProfile(prev => ({
        ...prev,
        lead: { ...prev.lead, website_screenshot: data.screenshot_url },
      }));
    }
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
    const saved = await saveJson(
      `${API_BASE_URL}/api/leads/${leadId}`,
      { method: 'PATCH', headers: h, body: JSON.stringify({ display_name: displayName }) },
      { context: 'Anzeigename speichern' }
    );
    if (!saved) return;
    setEditingName(false);
    await loadProfile();
  };

  const createProject = async () => {
    setCreatingProject(true);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/from-lead/${leadId}`,
        { method: 'POST', headers: h }
      );
      const data = await res.json();
      if (res.status === 409) {
        const projRes = await fetch(`${API_BASE_URL}/api/projects/?limit=200`, { headers: h });
        const projects = await projRes.json();
        const existing = Array.isArray(projects) ? projects.find(p => p.lead_id === parseInt(leadId)) : null;
        if (existing) navigate(`/app/projects/${existing.id}`);
        return;
      }
      if (res.status === 422) {
        const err = data?.detail?.message || 'Domain fehlt — bitte zuerst im Kundenprofil ergänzen.';
        toast ? toast.error(err) : alert(err);
        return;
      }
      if (!res.ok) throw new Error();
      setProjectId(data.id);
      setWonModal(false);
      navigate(`/app/projects/${data.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setCreatingProject(false);
    }
  };

  const updateStatus = async (status) => {
    // Ein gescheitertes PATCH lief vorher ins Leere und die Ansicht wurde
    // trotzdem neu geladen — der alte Status sah aus wie ein Anzeigefehler.
    const saved = await saveJson(
      `${API_BASE_URL}/api/leads/${leadId}`,
      { method: 'PATCH', headers: h, body: JSON.stringify({ status }) },
      { context: 'Status ändern' }
    );
    if (!saved) return;

    await loadProfile();
    if (status === 'won' && !projectId) {
      setWonModal(true);
    }
  };

  const startAudit = () => auditStart();

  const handleKaltakquise = async () => {
    const lead = profile?.lead;
    if (!lead) return;
    if (!window.confirm(
      `Kaltakquise-E-Mail an ${lead.email} senden?\n\n` +
      `KI generiert ein personalisiertes Anschreiben auf Basis des Audits ` +
      `und sendet es mit dem Audit-PDF als Anhang.`
    )) return;
    setKaltakquiseLoading(true);
    setKaltakquiseError('');
    setKaltakquiseDone(false);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${lead.id}/kaltakquise`,
        { method: 'POST', headers: h }
      );
      const data = await res.json();
      if (!res.ok) {
        if (data.status === 'no_audit') {
          setKaltakquiseError('Kein Audit vorhanden. Bitte zuerst einen Audit starten.');
        } else {
          setKaltakquiseError(data.detail || 'Fehler beim Senden');
        }
        return;
      }
      setKaltakquiseResult(data);
      setKaltakquiseDone(true);
      toast.success(`Kaltakquise-E-Mail gesendet an ${data.email_sent_to}`);
    } catch {
      setKaltakquiseError('Verbindungsfehler — bitte erneut versuchen');
    } finally {
      setKaltakquiseLoading(false);
    }
  };

  const createScreenshot = async () => {
    if (!profile?.lead?.website_url) return;
    setScreenshotLoading(true);
    const data = await loadJson(
      `${API_BASE_URL}/api/leads/${leadId}/screenshot`,
      { method: 'POST', headers: h },
      { context: 'Screenshot aufnehmen', emptyOn: [] }
    );
    if (data?.success && data.screenshot_url) {
      setProfile(prev => ({
        ...prev,
        lead: { ...prev.lead, website_screenshot: data.screenshot_url },
      }));
    }
    setScreenshotLoading(false);
  };

  const deleteAudit = async (auditId) => {
    // Ein fehlgeschlagenes Löschen schloss trotzdem den Dialog; der Eintrag war
    // nach dem Neuladen wieder da und wirkte wie ein Gespenst.
    const deleted = await saveJson(
      `${API_BASE_URL}/api/audit/${auditId}`,
      { method: 'DELETE', headers: h },
      { context: 'Audit löschen' }
    );
    if (!deleted) return;
    setDeleteAuditId(null);
    await loadProfile();
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
        <span style={{ fontSize: 14, color: 'var(--brand-primary-mid)', flexShrink: 0, marginTop: 1, width: 18, textAlign: 'center' }}>
          {icon}
        </span>
        <div>
          <div style={{ fontSize: isMobile ? 15 : 13, color: 'var(--text-primary)', lineHeight: isMobile ? 1.6 : undefined }}>{value}</div>
          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 1 }}>{label}</div>
        </div>
      </div>
    ) : null;

  // LOADING STATE
  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ background: 'var(--brand-primary)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14, opacity: 0.5 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div className="skeleton" style={{ width: 56, height: 56, borderRadius: '50%' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
            <div className="skeleton" style={{ height: 20, width: '40%', borderRadius: 4 }} />
            <div className="skeleton" style={{ height: 12, width: '25%', borderRadius: 3 }} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {[1,2,3,4,5].map(i => (<div key={i} className="skeleton" style={{ height: 32, width: 90, borderRadius: 'var(--radius-md)' }} />))}
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {[1,2].map(col => (
          <div key={col} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div className="skeleton" style={{ height: 13, width: '50%', borderRadius: 4 }} />
            {[1,2,3,4].map(i => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                <div className="skeleton" style={{ height: 9, width: '40%', borderRadius: 3 }} />
                <div className="skeleton" style={{ height: 13, width: `${50 + i * 10}%`, borderRadius: 3 }} />
              </div>
            ))}
          </div>
        ))}
      </div>
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

  // Der eine Knopf, der an dieser Stelle dran ist — siehe utils/naechsterSchritt.
  const schritt = naechsterSchritt({
    hatAudit: current_score !== null && current_score !== undefined,
    hatProjekt: Boolean(projectId),
    hatEmail: Boolean(lead.email && lead.website_url),
    status: lead.status,
  });

  // Hervorgehoben ist Gelb auf Dunkel — auf diesem Bildschirm genau einmal.
  const knopfHervorgehoben = {
    background: 'var(--kc-yellow)', color: '#000',
    border: '1px solid var(--kc-yellow)', fontWeight: 700,
  };
  const knopfRuhig = {
    background: 'rgba(255,255,255,0.15)', color: 'white',
    border: '1px solid rgba(255,255,255,0.25)', fontWeight: 500,
  };
  const knopfStil = (name) => (schritt === name ? knopfHervorgehoben : knopfRuhig);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'fadeIn 0.3s ease', maxWidth: 1200, margin: '0 auto', width: '100%', minWidth: 0, overflowX: 'hidden', padding: isMobile ? '0 4px' : undefined }}>

      {/* ZUSTELLUNG — steht über allem, weil ein Anschreiben sonst ins Leere
          geht, ohne dass es jemandem auffällt. */}
      {mailStoerungen.length > 0 && (() => {
        const neueste = mailStoerungen[0];
        const art = MAIL_STOERUNGEN[neueste.event] || { text: neueste.event, dauerhaft: false };
        return (
          <div style={{
            background: art.dauerhaft ? 'var(--status-danger-bg)' : 'var(--status-warning-bg)',
            color: art.dauerhaft ? 'var(--status-danger-text)' : 'var(--status-warning-text)',
            border: `1px solid ${art.dauerhaft ? 'var(--status-danger-text)' : 'var(--status-warning-text)'}`,
            borderRadius: 'var(--radius-lg)', padding: '12px 16px', fontSize: 13,
          }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>
              E-Mail {art.text}
              {mailStoerungen.length > 1 && ` — ${mailStoerungen.length} Meldungen`}
            </div>
            <div style={{ opacity: 0.9 }}>
              {neueste.email}
              {neueste.occurred_at && ` · ${datumUndZeit(neueste.occurred_at, '')}`}
            </div>
            {neueste.reason && (
              <div style={{ marginTop: 6, fontSize: 12, fontFamily: 'var(--font-mono, monospace)', opacity: 0.85, wordBreak: 'break-word' }}>
                {neueste.reason}
              </div>
            )}
            {neueste.sending_ip && (
              <div style={{ marginTop: 4, fontSize: 11, opacity: 0.75 }}>
                Versendet über {neueste.sending_ip}
              </div>
            )}
          </div>
        );
      })()}

      {/* HEADER */}
      <div style={{ background: 'var(--brand-primary)', borderRadius: 'var(--radius-xl)', padding: isMobile ? '12px 16px' : '24px', color: 'var(--text-on-brand)', position: 'relative', overflow: 'hidden' }}>

        {/* Der „← Zurück"-Knopf stand hier zusätzlich zur Brotkrume, die
          * oben „Betriebe › Name" zeigt und zurückführt. Zwei Wege für
          * dasselbe, und `navigate(-1)` führt anderswohin als die Brotkrume,
          * je nachdem, woher man kam (UX-24). */}

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: isMobile ? 'wrap' : 'nowrap', gap: 16 }}>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
              Betrieb
            </div>

            {editingName ? (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <input aria-label="Anzeigename des Betriebs"
                  value={displayName}
                  onChange={e => setDisplayName(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') saveDisplayName(); if (e.key === 'Escape') setEditingName(false); }}
                  autoFocus
                  style={{ ...inputStyle, background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.4)', color: 'white', fontSize: 20, fontWeight: 600, flex: 1, minWidth: 200 }}
                />
                <button aria-label="Speichern" onClick={saveDisplayName} style={{ background: 'white', color: 'var(--brand-primary)', border: 'none', borderRadius: 'var(--radius-md)', padding: '7px 14px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>✓</button>
                <button onClick={() => setEditingName(false)} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 'var(--radius-md)', color: 'white', padding: '7px 10px', fontSize: 12, cursor: 'pointer' }}>✕</button>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                {lead.favicon_url ? (
                  <img
                    src={lead.favicon_url}
                    alt=""
                    style={{ width: 32, height: 32, borderRadius: 6, objectFit: 'contain', background: '#fff', padding: 2, flexShrink: 0 }}
                    onError={e => { e.target.style.display = 'none'; }}
                  />
                ) : (
                  <div style={{ width: 32, height: 32, borderRadius: 6, background: 'rgba(255,255,255,0.2)', color: 'white', fontSize: 14, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    {(lead.display_name || lead.company_name || '?')[0].toUpperCase()}
                  </div>
                )}
                <h1 style={{ fontSize: isMobile ? 18 : 24, fontWeight: 600, color: 'white', margin: 0, letterSpacing: '-0.01em' }}>
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
              <GbpBadge lead={profile?.lead} />
            </div>
          </div>

          {current_score !== null && (
            <div style={{ background: 'rgba(255,255,255,0.12)', borderRadius: 'var(--radius-lg)', padding: '16px 20px', textAlign: 'center', flexShrink: 0, backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.2)', minWidth: 90 }}>
              <div style={{ fontSize: isMobile ? 28 : 40, fontWeight: 600, color: 'white', lineHeight: 1 }}>{current_score}</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 2 }}>/ 100</div>
              {current_level && (
                <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.75)', marginTop: 6, fontWeight: 500 }}>
                  {current_level.replace('Homepage Standard ', '')}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Genau ein Knopf ist hervorgehoben — der, den man an dieser
          * Stelle normalerweise drückt. Welcher das ist, hängt davon ab, wie
          * weit der Betrieb ist; deshalb `naechsterSchritt` statt einer
          * festen Farbe im Markup (UX-13). Drängt sich nichts auf, ist kein
          * Knopf hervorgehoben — das ist ehrlicher als einer auf Verdacht. */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap', flexDirection: isMobile ? 'column' : 'row' }}>
          <button
            onClick={startAudit}
            disabled={auditRunning}
            style={{ ...knopfStil('audit'), ...(auditRunning ? { background: 'rgba(255,255,255,0.1)', color: 'white' } : {}), borderRadius: 'var(--radius-md)', fontSize: 12, padding: '9px 14px', cursor: auditRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, width: isMobile ? '100%' : undefined, justifyContent: isMobile ? 'center' : undefined }}
          >
            {auditRunning ? (
              <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />{auditProgress || 'Läuft...'}</>
            ) : '🔍 Audit starten'}
          </button>

          {profile?.lead?.email && profile?.lead?.website_url && (
            <button
              onClick={handleKaltakquise}
              disabled={kaltakquiseLoading}
              style={{
                ...knopfStil('kaltakquise'),
                ...(kaltakquiseLoading ? { background: 'rgba(255,255,255,0.1)', color: 'white' } : {}),
                ...(kaltakquiseDone ? { background: 'var(--success)', color: 'var(--text-on-brand)' } : {}),
                borderRadius: 'var(--radius-md)',
                fontSize: 12,
                padding: '9px 14px', cursor: kaltakquiseLoading ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6,
                width: isMobile ? '100%' : undefined, justifyContent: isMobile ? 'center' : undefined,
              }}
            >
              {kaltakquiseLoading ? (
                <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />KI schreibt Anschreiben …</>
              ) : kaltakquiseDone ? '✓ Kaltakquise gesendet' : '📧 Kaltakquise starten'}
            </button>
          )}

          <button onClick={() => { setActiveTab('contact'); setEditMode(true); }} style={{ ...knopfRuhig, borderRadius: 'var(--radius-md)', fontSize: 12, padding: '7px 14px', cursor: 'pointer', fontFamily: 'var(--font-sans)', width: isMobile ? '100%' : undefined }}>
            ✏️ Bearbeiten
          </button>

          <button
            onClick={async () => {
              const enriched = await saveJson(
                `${API_BASE_URL}/api/leads/${leadId}/enrich`,
                { method: 'POST', headers: h },
                { context: 'Daten neu prüfen' }
              );
              if (enriched) await loadProfile();
            }}
            title="Firmendaten, Google Business, SSL, Impressum und PageSpeed neu abrufen"
            style={{
              ...knopfStil('stammdaten'),
              padding: '7px 14px', borderRadius: 'var(--radius-md)',
              fontSize: 12, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              width: isMobile ? '100%' : undefined,
            }}
          >
            🔄 Stammdaten neu holen
          </button>

          <button
            onClick={openBriefingWizard}
            disabled={briefingLoading}
            style={{ ...knopfRuhig, borderRadius: 'var(--radius-md)', fontSize: 12, padding: '7px 14px', cursor: briefingLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', width: isMobile ? '100%' : undefined }}
          >
            📋 Briefing starten
          </button>

          {projectId ? (
            <button onClick={() => navigate(`/app/projects/${projectId}`)} style={{ ...knopfStil('zum_projekt'), borderRadius: 'var(--radius-md)', fontSize: 12, padding: '7px 14px', cursor: 'pointer', fontFamily: 'var(--font-sans)', width: isMobile ? '100%' : undefined }}>
              📁 Zum Projekt →
            </button>
          ) : (
            <button onClick={createProject} disabled={creatingProject} style={{ ...knopfStil('projekt'), ...(creatingProject ? { background: 'rgba(255,255,255,0.1)', color: 'white' } : {}), borderRadius: 'var(--radius-md)', fontSize: 12, padding: '7px 14px', cursor: creatingProject ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6, width: isMobile ? '100%' : undefined, justifyContent: isMobile ? 'center' : undefined }}>
              {creatingProject ? <><span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Anlegen…</> : '📁 Projekt anlegen'}
            </button>
          )}

          <select aria-label="Status des Betriebs" value={lead.status} onChange={e => updateStatus(e.target.value)} style={{ background: 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.25)', borderRadius: 'var(--radius-md)', color: 'white', fontSize: 12, padding: '7px 12px', cursor: 'pointer', fontFamily: 'var(--font-sans)', outline: 'none', width: isMobile ? '100%' : undefined }}>
            <option value="new">Neu</option>
            <option value="contacted">Kontaktiert</option>
            <option value="qualified">Qualifiziert</option>
            <option value="proposal_sent">Angebot gesendet</option>
            <option value="won">Gewonnen</option>
            <option value="lost">Verloren</option>
          </select>
        </div>

        {/* Kaltakquise status messages */}
        {kaltakquiseError && (
          <div style={{ marginTop: 8, fontSize: 11, color: 'var(--status-danger-text)', padding: '6px 10px', background: 'var(--status-danger-bg)', borderRadius: 6 }}>
            {kaltakquiseError}
          </div>
        )}
        {kaltakquiseDone && kaltakquiseResult && (
          <div style={{ marginTop: 8, fontSize: 11, color: 'var(--status-success-text)', padding: '6px 10px', background: 'var(--status-success-bg)', borderRadius: 6 }}>
            ✓ Gesendet an {kaltakquiseResult.email_sent_to} · Score {kaltakquiseResult.audit_score}/100 ·{kaltakquiseResult.with_pdf ? ' mit PDF-Anhang' : ' ohne PDF'}
          </div>
        )}
      </div>

      {/* Briefing status */}
      {briefingData && briefingData.gewerk ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 12, color: 'rgba(255,255,255,0.85)', background: 'rgba(255,255,255,0.1)', borderRadius: 'var(--radius-md)', padding: '6px 12px', width: 'fit-content' }}>
          <span style={{ color: '#4ade80', fontWeight: 700 }}>✓</span>
          Briefing ausgefüllt{briefingData.updated_at ? ` · ${briefingData.updated_at.slice(0, 10).split('-').reverse().join('.')}` : ''}
          <a
            href={`${API_BASE_URL}/api/briefings/${leadId}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'rgba(255,255,255,0.7)', textDecoration: 'underline', marginLeft: 4, cursor: 'pointer' }}
          >
            PDF herunterladen
          </a>
        </div>
      ) : (
        <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)', padding: '2px 4px' }}>
          Noch kein Briefing vorhanden
        </div>
      )}

      {/* TABS — sechs oben, vier hinter „Mehr" (UX-15, entschieden 17.08.2026).
        * Zehn gleichrangige Reiter waren zehn Entscheidungen bei jedem Aufruf.
        * Nichts ist weg, es ist nur nicht mehr alles gleich laut. Welche wohin
        * gehören, steht in `utils/betriebReiter.js`. */}
      {(() => {
        const { haupt, mehr, mehrIstAktiv } = aufteilung(TABS, activeTab);
        const reiterKnopf = (tab, imMenue = false) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setMehrOffen(false); }}
            style={{
              flex: imMenue ? undefined : (isMobile ? '0 0 auto' : 1),
              flexShrink: 0, width: imMenue ? '100%' : undefined,
              padding: isMobile && !imMenue ? '7px 14px' : '8px 12px',
              borderRadius: 'var(--radius-md)', border: 'none',
              background: activeTab === tab.id ? 'var(--bg-active)' : 'transparent',
              color: activeTab === tab.id ? 'var(--brand-primary)' : 'var(--text-tertiary)',
              fontSize: 12, fontWeight: activeTab === tab.id ? 500 : 400,
              cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex',
              alignItems: 'center', justifyContent: imMenue ? 'flex-start' : 'center',
              gap: 6, whiteSpace: 'nowrap', transition: 'all 0.15s',
            }}
          >
            <span>{tab.icon}</span>{tab.label}
            {tab.id === 'messages' && (lead.unread_messages || 0) > 0 && (
              <span style={{ background: 'var(--error)', color: 'var(--text-on-brand)', borderRadius: 9999, fontSize: 10, fontWeight: 700, padding: '1px 6px', lineHeight: 1.4 }}>
                {lead.unread_messages}
              </span>
            )}
          </button>
        );

        return (
          <div className="kc-tab-nav" style={{ display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 4, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            {haupt.map(tab => reiterKnopf(tab))}

            <div style={{ position: 'relative', flex: isMobile ? '0 0 auto' : 1, flexShrink: 0 }}>
              <button
                onClick={() => setMehrOffen(o => !o)}
                aria-expanded={mehrOffen}
                style={{
                  width: '100%', padding: isMobile ? '7px 14px' : '8px 12px',
                  borderRadius: 'var(--radius-md)', border: 'none',
                  // Ist einer der untergeordneten Reiter offen, muss man das
                  // oben sehen — sonst sucht man ihn zwischen den sechs.
                  background: mehrIstAktiv ? 'var(--bg-active)' : 'transparent',
                  color: mehrIstAktiv ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                  fontSize: 12, fontWeight: mehrIstAktiv ? 500 : 400,
                  cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex',
                  alignItems: 'center', justifyContent: 'center', gap: 6, whiteSpace: 'nowrap',
                }}
              >
                Mehr {mehrOffen ? '▴' : '▾'}
              </button>

              {mehrOffen && (
                <>
                  {/* Ein Klick daneben schließt. Ohne das bleibt das Menü
                    * offen und verdeckt, was man als Nächstes anklicken will. */}
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setMehrOffen(false))}
                    onClick={() => setMehrOffen(false)}
                    style={{ position: 'fixed', inset: 0, zIndex: 19 }}
                  />
                  <div style={{ position: 'absolute', top: '100%', right: 0, marginTop: 4, zIndex: 20, minWidth: 180, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)', padding: 4, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {mehr.map(tab => reiterKnopf(tab, true))}
                  </div>
                </>
              )}
            </div>
          </div>
        );
      })()}

      {/* NACHRICHTEN TAB */}
      {/* Reiterinhalt und Verlauf nebeneinander (L-82).
        *
        * Der Verlauf steht **neben** den Reitern, nicht in einem: Wer beim
        * Anruf erst klicken muss, um zu sehen, was zuletzt geschah, sieht es
        * nicht. Auf schmalen Geraeten rutscht er darunter — dort gibt es
        * keine zweite Spalte, und ein zusammengequetschter Verlauf waere
        * schlechter als einer, der wartet. */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'minmax(0, 1fr) 300px',
        gap: 16, alignItems: 'start', minWidth: 0,
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16, minWidth: 0 }}>
      {activeTab === 'messages' && (() => {
        const fmtTime = (iso) => {
          if (!iso) return '';
          const d = new Date(iso);
          return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        };
        const fmtDay = (iso) => {
          if (!iso) return '';
          const d = new Date(iso);
          const today = new Date();
          const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
          if (d.toDateString() === today.toDateString()) return 'Heute';
          if (d.toDateString() === yesterday.toDateString()) return 'Gestern';
          return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
        };

        // Group messages by day for separators
        const grouped = [];
        let lastDay = null;
        for (const m of messages) {
          const day = fmtDay(m.created_at);
          if (day !== lastDay) { grouped.push({ type: 'sep', day }); lastDay = day; }
          grouped.push({ type: 'msg', msg: m });
        }

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0, border: '1px solid var(--border-light)', borderRadius: 12, overflow: 'hidden', background: 'var(--bg-app)' }}>

            {/* Newsletter Button */}
            <div style={{ padding: '10px 16px', borderBottom: '1px solid var(--border-light)', display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowNewsletter(true)}
                style={{ padding: '6px 14px', border: 'none', borderRadius: 6,
                         background: 'var(--brand-primary)', color: 'var(--text-on-brand)', cursor: 'pointer',
                         fontSize: 13, fontWeight: 600 }}>
                Newsletter erstellen
              </button>
            </div>

            {/* Nachrichtenverlauf */}
            <div style={{ maxHeight: 500, overflowY: 'auto', padding: '16px 16px 8px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {msgLoading && messages.length === 0 && (
                <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, padding: 32 }}>Nachrichten werden geladen…</div>
              )}
              {!msgLoading && messages.length === 0 && (
                <EmptyState icon="💬" title="Noch keine Nachrichten" description="Schreibe die erste Nachricht an den Kunden — sie erscheint direkt im Kundenportal. Nutze das Eingabefeld unten." compact />
              )}
              {grouped.map((item, i) => {
                if (item.type === 'sep') return (
                  <div key={`sep-${i}`} style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-tertiary)', fontSize: 11 }}>
                    <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
                    {item.day}
                    <div style={{ flex: 1, height: 1, background: 'var(--border-light)' }} />
                  </div>
                );
                const m = item.msg;
                const isAdmin = m.sender_role === 'admin';
                return (
                  <div key={m.id} style={{ display: 'flex', flexDirection: 'column', alignItems: isAdmin ? 'flex-end' : 'flex-start' }}>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontWeight: 600 }}>{m.sender_name || (isAdmin ? 'Admin' : lead.company_name)}</span>
                      <span>{fmtTime(m.created_at)}</span>
                      {isAdmin && (
                        <span style={{ background: m.channel === 'email' ? 'var(--status-warning-bg)' : 'var(--status-success-bg)', color: m.channel === 'email' ? 'var(--status-warning-text)' : 'var(--status-success-text)', borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 600 }}>
                          {m.channel === 'email' ? '✉️ E-Mail' : '💬 In-App'}
                        </span>
                      )}
                      {!isAdmin && !m.is_read && (
                        <span style={{ color: 'var(--status-info-text)', fontSize: 10 }}>🔵 Ungelesen</span>
                      )}
                    </div>
                    <div style={{ maxWidth: '75%', padding: '10px 14px', borderRadius: isAdmin ? '14px 14px 4px 14px' : '14px 14px 14px 4px', background: isAdmin ? 'var(--brand-primary-light)' : 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {m.content}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Eingabebereich */}
            <div style={{ borderTop: '1px solid var(--border-light)', padding: '12px 16px', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {msgChannel === 'email' && (
                <input aria-label="Betreff der E-Mail…"
                  value={msgSubject}
                  onChange={e => setMsgSubject(e.target.value)}
                  placeholder="Betreff der E-Mail…"
                  style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none' }}
                />
              )}
              <textarea aria-label="Nachricht schreiben… (Ctrl+Enter zum Senden)"
                value={msgText}
                onChange={e => setMsgText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendMessage(); }}
                placeholder="Nachricht schreiben… (Ctrl+Enter zum Senden)"
                rows={3}
                style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', resize: 'vertical', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none', width: '100%', boxSizing: 'border-box' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  {[{ id: 'in_app', label: '💬 In-App' }, { id: 'email', label: '✉️ + E-Mail' }].map(ch => (
                    <button key={ch.id} onClick={() => setMsgChannel(ch.id)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border-light)', fontSize: 12, fontWeight: msgChannel === ch.id ? 700 : 400, background: msgChannel === ch.id ? 'var(--brand-primary)' : 'var(--bg-app)', color: msgChannel === ch.id ? '#fff' : 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      {ch.label}
                    </button>
                  ))}
                </div>
                <button onClick={sendMessage} disabled={msgSending || !msgText.trim()}
                  style={{ padding: '8px 20px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: msgSending || !msgText.trim() ? 'not-allowed' : 'pointer', opacity: msgSending || !msgText.trim() ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}>
                  {msgSending ? 'Senden…' : 'Senden →'}
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {showNewsletter && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9998,
                      background: 'var(--bg-surface)' }}>
          <div style={{ position: 'absolute', top: 12, right: 16, zIndex: 9999 }}>
            <button onClick={() => setShowNewsletter(false)}
              style={{ padding: '6px 16px', border: 'none', borderRadius: 6,
                       background: 'var(--error)', color: 'var(--text-on-brand)', cursor: 'pointer' }}>
              Schliessen
            </button>
          </div>
          <NewsletterDesigner
            leadId={leadId}
            onSend={() => {
              setShowNewsletter(false);
              toast.success('Newsletter gesendet');
            }}
            onSave={() => toast.success('Entwurf gespeichert')}
          />
        </div>
      )}

      {/* ÜBERSICHT TAB */}
      {activeTab === 'overview' && (
        <>
        {/* Herkunft und Rechtsgrundlage (nur intern) — L-59.
            Hier stand eine eigene, vierte Quellenliste (SOURCE_MAP mit
            facebook/linkedin/google_ads/briefkarte/…), und der Block zeigte
            sich nur, wenn `utm_source` oder `kampagne_quelle` gesetzt war —
            also bei den wenigsten Betrieben. Die Quelle, die tatsächlich
            geführt wird (`lead_source`), stand gar nicht da, und die
            Rechtsgrundlage nirgends im ganzen System.

            Jetzt eine Liste (`utils/leadStatus.js`, gespiegelt von
            `services/lead_quellen.py`) und immer sichtbar: Eine ungeführte
            Quelle oder eine offene Rechtsgrundlage soll auffallen, nicht
            verschwinden. */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap',
          padding: '8px 14px', background: 'var(--bg-surface)',
          border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
          fontSize: 12, marginBottom: 12, width: 'fit-content', maxWidth: '100%',
        }}>
          <span style={{ color: 'var(--text-tertiary)' }}>Quelle:</span>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
            {leadSourceLabel(lead.lead_source)}
          </span>
          <Badge variant={herkunftVariant(lead.datenherkunft)}>
            {herkunftLabel(lead.datenherkunft)}
          </Badge>
          <Badge variant={lead.rechtsgrundlage ? 'info' : 'warning'}>
            {rechtsgrundlageLabel(lead.rechtsgrundlage)}
          </Badge>
          {(lead.utm_campaign || lead.kampagne_quelle) && (
            <span style={{ color: 'var(--text-tertiary)', fontSize: 11 }}>
              · {lead.utm_campaign || lead.kampagne_quelle}
            </span>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: isDesktop ? '340px 1fr' : isTablet ? '280px 1fr' : '1fr', gap: 16, alignItems: 'flex-start', minWidth: 0, width: '100%', overflowX: 'hidden' }}>

          {/* Linke Spalte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>

            {/* Screenshot */}
            <Card padding="sm" style={{ overflow: 'hidden', maxHeight: isMobile ? 200 : 'none', width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ background: 'var(--bg-app)', padding: '7px 10px', display: 'flex', alignItems: 'center', gap: 5, borderBottom: '1px solid var(--border-light)', margin: '-12px -12px 0' }}>
                {['#ef4444','#f59e0b','#22c55e'].map(c => (
                  <div key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c }} />
                ))}
                <div style={{ flex: 1, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', border: '1px solid var(--border-light)' }}>
                  {lead.website_url || 'Keine Website'}
                </div>
                {lead.website_url && (
                  <a href={lead.website_url.startsWith('http') ? lead.website_url : 'https://' + lead.website_url} target="_blank" rel="noopener noreferrer" aria-label="Website des Betriebs in neuem Tab oeffnen" style={{ fontSize: 12, color: 'var(--text-tertiary)', flexShrink: 0 }}>↗</a>
                )}
                <button onClick={createScreenshot} disabled={screenshotLoading} style={{ background: 'none', border: 'none', color: 'var(--text-tertiary)', cursor: screenshotLoading ? 'wait' : 'pointer', fontSize: 12, padding: '1px 4px', flexShrink: 0 }} title="Screenshot aktualisieren">
                  {screenshotLoading ? '⏳' : '🔄'}
                </button>
              </div>

              <div style={{ padding: '4px 10px 6px' }}>
                <DomainBadge reachable={lead.domain_reachable ?? null} checkedAt={lead.domain_checked_at} loading={domainLoading} onCheck={checkDomain} />
              </div>

              <div style={{ margin: '0 -12px', position: 'relative', minHeight: 160, overflow: 'hidden' }}>
                {screenshotLoading ? (
                  <div style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', gap: 10 }}>
                    <div style={{ width: 28, height: 28, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                    <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Screenshot wird erstellt...</span>
                  </div>
                ) : lead.website_screenshot ? (
                  <>
                    <img src={lead.website_screenshot} alt="Website" style={{ width: '100%', maxHeight: isMobile ? '150px' : '300px', objectFit: 'cover', objectPosition: 'top', display: 'block', borderRadius: 0 }} />
                    {current_score !== null && (
                      <div style={{ position: 'absolute', bottom: 8, right: 8, background: 'rgba(15,28,32,0.85)', backdropFilter: 'blur(6px)', borderRadius: 'var(--radius-md)', padding: '4px 10px' }}>
                        <span style={{ fontSize: 13, fontWeight: 600, color: levelColor }}>{current_score}/100</span>
                      </div>
                    )}
                  </>
                ) : (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(createScreenshot)} onClick={createScreenshot} style={{ height: 160, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-app)', cursor: lead.website_url ? 'pointer' : 'default', gap: 8 }}
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
              <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
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
              <Card padding="sm" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
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
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, minWidth: 0 }}>

            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kontaktdaten</span>
                <button onClick={() => { setActiveTab('contact'); setEditMode(true); }} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Bearbeiten →</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: isMobile || isTablet ? '1fr' : '1fr 1fr', gap: '0 16px' }}>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('✉️', lead.email, 'E-Mail')}
                {fieldRow('🌐', lead.website_url?.replace(/^https?:\/\//, ''), 'Website')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 10 }}>
                  <span style={{ fontSize: 14, color: 'var(--brand-primary-mid)', flexShrink: 0, marginTop: 1, width: 18, textAlign: 'center' }}>👤</span>
                  <div>
                    <div style={{ fontSize: 13, color: lead.geschaeftsfuehrer ? 'var(--text-primary)' : 'var(--text-tertiary)' }}>{lead.geschaeftsfuehrer || '–'}</div>
                    {/* „(auto)" sagte, woher der Wert kommt — das interessiert die
                      * Maschine, nicht den Menschen davor (UX-25). */}
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 1 }}>Geschäftsführer</div>
                  </div>
                </div>
                {fieldRow('📍', [lead.street && `${lead.street} ${lead.house_number || ''}`.trim(), [lead.postal_code, lead.city].filter(Boolean).join(' ')].filter(Boolean).join(', '), 'Adresse')}
              </div>
              {/* Die technische Prüfung stand bis zum 17.08.2026 als Zeile
                * „[Auto-Enrichment] SSL: OK | …" in den Notizen — im Feld für
                * das, was ein Mensch schreibt, und bei jedem Lauf erneut
                * davorgesetzt. Sie hat jetzt einen eigenen Platz (UX-06).
                * „nicht geprüft" steht ausdrücklich da: Es ist nicht dasselbe
                * wie „fehlt". */}
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 6 }}>
                  Technische Prüfung
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {befundZeilen(profile.anreicherung).map(({ schluessel, beschriftung, wert, art }) => (
                    <span key={schluessel} style={{
                      fontSize: 11, padding: '3px 8px', borderRadius: 'var(--radius-sm)',
                      background: art === 'gut' ? 'var(--status-success-bg)'
                        : art === 'fehlt' ? 'var(--status-danger-bg)' : 'var(--bg-app)',
                      color: art === 'gut' ? 'var(--status-success-text)'
                        : art === 'fehlt' ? 'var(--status-danger-text)' : 'var(--text-tertiary)',
                    }}>
                      {beschriftung}: {wert}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 5 }}>
                  {geprueftAmText(profile.anreicherung)}
                </div>
              </div>

              {lead.notes && (
                <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, fontStyle: 'italic' }}>
                  {lead.notes}
                </div>
              )}
            </Card>

            {/* ── Weitere Domains ── */}
            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>
                Weitere Domains
              </div>

              {/* Domain list */}
              {domains.length === 0 ? (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', padding: '8px 0', textAlign: 'center' }}>
                  Keine weiteren Domains
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
                  {domains.map(d => (
                    <div key={d.id} style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '7px 10px', borderRadius: 'var(--radius-md)',
                      background: d.is_primary ? 'var(--bg-active)' : 'var(--bg-app)',
                      border: `1px solid ${d.is_primary ? 'var(--brand-primary)' : 'var(--border-light)'}`,
                    }}>
                      {d.is_primary && (
                        <span title="Primär" style={{ fontSize: 13, flexShrink: 0 }}>⭐</span>
                      )}
                      <a
                        href={d.url.startsWith('http') ? d.url : 'https://' + d.url}
                        target="_blank" rel="noopener noreferrer"
                        style={{
                          fontSize: 12, flex: 1, minWidth: 0,
                          color: d.is_primary ? 'var(--brand-primary)' : 'var(--text-secondary)',
                          fontWeight: d.is_primary ? 500 : 400,
                          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          textDecoration: 'none',
                        }}
                        onMouseEnter={e => e.currentTarget.style.textDecoration = 'underline'}
                        onMouseLeave={e => e.currentTarget.style.textDecoration = 'none'}
                      >
                        {d.url.replace(/^https?:\/\//, '')}
                      </a>
                      {d.label && (
                        <span style={{
                          fontSize: 10, padding: '1px 7px', borderRadius: 'var(--radius-full)',
                          background: 'var(--bg-surface)', color: 'var(--text-tertiary)',
                          border: '1px solid var(--border-light)', flexShrink: 0,
                        }}>
                          {d.label}
                        </span>
                      )}
                      <button
                        onClick={() => deleteDomain(d.id)}
                        title="Löschen"
                        style={{
                          background: 'none', border: 'none', cursor: 'pointer', padding: '2px 4px',
                          color: 'var(--text-tertiary)', borderRadius: 'var(--radius-sm)', fontSize: 13, flexShrink: 0,
                          lineHeight: 1, transition: 'color 0.1s',
                        }}
                        onMouseEnter={e => e.currentTarget.style.color = 'var(--status-danger-text)'}
                        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-tertiary)'}
                      >
                        🗑
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Das Formular stand immer offen und nahm auf der Übersicht
                * Platz weg — bei den meisten Betrieben gibt es gar keine
                * zweite Domain. Jetzt erst auf Verlangen (UX-26). */}
              {!domainFormOffen && (
                <button
                  onClick={() => setDomainFormOffen(true)}
                  style={{ marginTop: domains.length ? 10 : 0, padding: '6px 10px', fontSize: 12,
                    background: 'none', border: '1px dashed var(--border-medium)',
                    borderRadius: 'var(--radius-md)', color: 'var(--text-secondary)',
                    cursor: 'pointer', width: '100%', fontFamily: 'var(--font-sans)' }}
                >
                  + Domain hinzufügen
                </button>
              )}

              {domainFormOffen && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, paddingTop: domains.length ? 10 : 0, borderTop: domains.length ? '1px solid var(--border-light)' : 'none' }}>
                <input aria-label="Adresse der Domain"
                  value={domainForm.url}
                  onChange={e => setDomainForm(f => ({ ...f, url: e.target.value }))}
                  onKeyDown={e => e.key === 'Enter' && addDomain()}
                  placeholder="https://shop.firma.de"
                  style={{
                    padding: '7px 10px', fontSize: 12,
                    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-app)', color: 'var(--text-primary)',
                    fontFamily: 'var(--font-sans)', outline: 'none',
                  }}
                />
                <input aria-label="Label (z.B. Shop, Karriere)"
                  value={domainForm.label}
                  onChange={e => setDomainForm(f => ({ ...f, label: e.target.value }))}
                  placeholder="Label (z.B. Shop, Karriere)"
                  style={{
                    padding: '7px 10px', fontSize: 12,
                    border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-app)', color: 'var(--text-primary)',
                    fontFamily: 'var(--font-sans)', outline: 'none',
                  }}
                />
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={domainForm.is_primary}
                      onChange={e => setDomainForm(f => ({ ...f, is_primary: e.target.checked }))}
                      style={{ cursor: 'pointer' }}
                    />
                    Als primär markieren
                  </label>
                  <button
                    onClick={addDomain}
                    disabled={!domainForm.url.trim() || domainAdding}
                    style={{
                      padding: '6px 14px', fontSize: 12, fontWeight: 600,
                      background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                      border: 'none', borderRadius: 'var(--radius-md)',
                      cursor: domainForm.url.trim() && !domainAdding ? 'pointer' : 'not-allowed',
                      opacity: domainForm.url.trim() && !domainAdding ? 1 : 0.5,
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    {domainAdding ? '…' : 'Hinzufügen'}
                  </button>
                </div>
              </div>
              )}
            </Card>

            {latestAudit && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Letzter Audit</span>
                  <button onClick={() => setActiveTab('audits')} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Alle anzeigen →</button>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                  <div style={{ width: 48, height: 48, borderRadius: 'var(--radius-md)', background: `${levelColor}18`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <span style={{ fontSize: 18, fontWeight: 700, color: levelColor }}>{latestAudit.total_score}</span>
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{current_level}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>{datumKurz(latestAudit.created_at, 'Datum unbekannt')}</div>
                  </div>
                </div>
                {latestAudit.ai_summary && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                    {latestAudit.ai_summary.substring(0, 200)}{latestAudit.ai_summary.length > 200 ? '...' : ''}
                  </div>
                )}
                {/* Sah aus wie deaktiviert. Gemessen: `--brand-primary-mid`
                  * auf `--bg-active` ergibt im Hellmodus **3.39** — unter der
                  * Schwelle für Text. (Im Dunkelmodus waren es 5.62; die
                  * Arbeitsliste vermutete es umgekehrt.) Mit
                  * `--brand-primary` sind es 8.16, und mit Halbfett und
                  * sichtbarem Rand sieht der Knopf aus wie einer (UX-18). */}
                <button onClick={() => setOpenAudit(latestAudit)} style={{ marginTop: 10, width: '100%', padding: '9px', background: 'var(--bg-active)', border: '1px solid var(--brand-primary-mid)', borderRadius: 'var(--radius-md)', color: 'var(--brand-primary)', fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Vollständigen Bericht anzeigen
                </button>
              </Card>
            )}

            {/* ── Projekt ── */}
            {projectData && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Projekt</span>
                  <button onClick={() => navigate(`/app/projects/${projectId}`)} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Öffnen →
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {fieldRow('🔄', projectData.status?.replace('phase_', 'Phase ') || '–', 'Phase')}
                  {fieldRow('📦', projectData.package_type || '–', 'Paket')}
                  {fieldRow('💳', projectData.payment_status || '–', 'Zahlung')}
                  {fieldRow('📅', projectData.go_live_date || '–', 'Go-Live')}
                </div>
                <button
                  onClick={() => navigate(`/app/projects/${projectId}`)}
                  style={{ marginTop: 10, width: '100%', padding: '7px', background: 'var(--bg-active)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', color: 'var(--brand-primary-mid)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
                >
                  📁 Zum Projekt
                </button>
              </Card>
            )}

            {(lead.vat_id || lead.register_number || lead.register_court) && (
              <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 12 }}>Rechtliches</div>
                {fieldRow('🏛️', lead.vat_id, 'USt-IdNr.')}
                {fieldRow('📋', lead.register_number, 'Handelsreg.-Nr.')}
                {fieldRow('⚖️', lead.register_court, 'Handelsregister')}
              </Card>
            )}

            {/* QR-Code */}
            <Card padding="md" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>Kunden-Zugang</span>
                <button onClick={() => setActiveTab('qrcode')} style={{ fontSize: 11, color: 'var(--brand-primary-mid)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Details →</button>
              </div>
              {qrLoading ? (
                <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: 24, height: 24, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite' }} />
                </div>
              ) : qrData ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); })} style={{ background: 'white', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: 8, flexShrink: 0, cursor: 'pointer' }}
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
                        style={{ padding: '5px 10px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        ⬇ PNG
                      </button>
                      <button onClick={() => navigator.clipboard.writeText(qrData.portal_url)}
                        style={{ padding: '5px 10px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        📋 Link
                      </button>
                      {lead.email && (
                        <a href={`mailto:${lead.email}?subject=Ihr persönlicher Zugang&body=Ihr Zugangslink:%0D%0A${qrData.portal_url}`}
                          aria-label="Zugangslink per E-Mail senden" style={{ padding: '5px 10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-sm)', fontSize: 11, textDecoration: 'none', fontFamily: 'var(--font-sans)' }}>
                          ✉️
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <button onClick={loadQrCode} style={{ padding: '8px 16px', background: 'var(--bg-active)', color: 'var(--brand-primary-mid)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    QR-Code generieren
                  </button>
                </div>
              )}
            </Card>
          </div>
        </div>
        </>
      )}

      {/* KONTAKT TAB */}
      {activeTab === 'contact' && (
        <Card padding="md">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontSize: 15, fontWeight: 500, color: 'var(--text-primary)', margin: 0 }}>Kontakt & Betrieb</h2>
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
                  <div style={sectionLabel}>Betrieb</div>
                </div>

                {[
                  ['Firmenname', 'company_name', 'Mustermann GmbH'],
                  ['Gesellschaftsform', 'legal_form', 'GmbH, UG, GmbH & Co. KG'],
                  ['Vorname Geschäftsführer', 'ceo_first_name', 'Max'],
                  ['Nachname Geschäftsführer', 'ceo_last_name', 'Mustermann'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}
                <div>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Gewerk / Branche</div>
                  <WZSearch
                    value={editData.wz_code ? { code: editData.wz_code, title: editData.wz_title } : null}
                    onChange={(entry) => setEditData(p => ({
                      ...p,
                      wz_code: entry?.code || '',
                      wz_title: entry?.title || '',
                      trade: entry?.title || '',
                    }))}
                    placeholder="Branche suchen..."
                  />
                </div>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Adresse</div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Straße</div>
                    <input aria-label="Musterstraße" value={editData.street || ''} onChange={e => setEditData(p => ({...p, street: e.target.value}))} placeholder="Musterstraße" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Nr.</div>
                    <input aria-label="12a" value={editData.house_number || ''} onChange={e => setEditData(p => ({...p, house_number: e.target.value}))} placeholder="12a" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>PLZ</div>
                    <input aria-label="Postleitzahl" value={editData.postal_code || ''} onChange={e => setEditData(p => ({...p, postal_code: e.target.value}))} placeholder="56070" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>Ort</div>
                    <input aria-label="Koblenz" value={editData.city || ''} onChange={e => setEditData(p => ({...p, city: e.target.value}))} placeholder="Koblenz" style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                </div>

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={sectionLabel}>Kontakt</div>
                </div>

                {[
                  ['Ansprechpartner', 'contact_name', 'Max Mustermann'],
                  ['Telefon', 'phone', '+49 261 123456'],
                  ['Mobilfunknummer', 'mobile', '+49 170 1234567'],
                  ['E-Mail', 'email', 'info@firma.de'],
                  ['Website', 'website_url', 'www.firma.de'],
                ].map(([label, field, ph]) => (
                  <div key={field}>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5 }}>{label}</div>
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
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
                    <input aria-label={ph} value={editData[field] || ''} onChange={e => setEditData(p => ({...p, [field]: e.target.value}))} placeholder={ph} style={inputStyle}
                      onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
                      onBlur={e => e.target.style.borderColor = 'var(--border-medium)'} />
                  </div>
                ))}

                <div style={{ gridColumn: isMobile ? '1' : '1 / -1' }}>
                  <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 5, marginTop: 8 }}>Notizen</div>
                  <textarea aria-label="Interne Notizen..." value={editData.notes || ''} onChange={e => setEditData(p => ({...p, notes: e.target.value}))} placeholder="Interne Notizen..." rows={3}
                    style={{ ...inputStyle, resize: 'vertical', minHeight: 70 }}
                    onFocus={e => e.target.style.borderColor = 'var(--brand-primary-mid)'}
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
                <div style={sectionLabel}>Betrieb</div>
                {fieldRow('🏢', [lead.company_name, lead.legal_form].filter(Boolean).join(' '), 'Firma')}
                {fieldRow('👔', [lead.ceo_first_name, lead.ceo_last_name].filter(Boolean).join(' '), 'Geschäftsführer')}
                {fieldRow('🔧', lead.trade, 'Gewerk')}
              </div>
              <div>
                <div style={sectionLabel}>Kontakt</div>
                {fieldRow('👤', lead.contact_name, 'Ansprechpartner')}
                {fieldRow('📞', lead.phone, 'Telefon')}
                {fieldRow('📱', lead.mobile, 'Mobilfunknummer')}
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
              <button onClick={startAudit} style={{ marginTop: 14, padding: '8px 18px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
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

      {/* DEALS TAB */}
      {activeTab === 'deals' && (
        <div style={{ maxWidth: 900 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>💼 Deals</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                {companyDeals.length} Deal{companyDeals.length !== 1 ? 's' : ''} · Gesamt{' '}
                {companyDeals.reduce((s, d) => s + (d.total_value || 0), 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
              </div>
            </div>
            <a
              href="/app/deals"
              style={{
                padding: '9px 18px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600,
                textDecoration: 'none', fontFamily: 'var(--font-sans)',
              }}
            >
              Zur Deal-Pipeline →
            </a>
          </div>

          {dealsLoading && (
            <div style={{ color: 'var(--text-tertiary)', fontSize: 13, padding: 20 }}>Deals werden geladen…</div>
          )}

          {!dealsLoading && companyDeals.length === 0 && (
            <div style={{ textAlign: 'center', padding: 48, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>💼</div>
              <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
                Noch keine Deals für diesen Betrieb.
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>
                Lege einen neuen Deal in der <a href="/app/deals" style={{ color: 'var(--brand-primary-mid)' }}>Deal-Pipeline</a> an.
              </div>
            </div>
          )}

          {companyDeals.map(deal => (
            <div key={deal.id} style={{
              padding: '14px 18px', borderRadius: 'var(--radius-lg)', marginBottom: 10,
              background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{deal.title}</div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
                  {deal.created_at?.slice(0, 10)}
                </div>
              </div>
              <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: '3px 10px', borderRadius: 4,
                  background: deal.status === 'gewonnen' ? 'var(--status-success-bg)'
                    : deal.status === 'verloren' ? 'var(--status-danger-bg)' : 'var(--status-info-bg)',
                  color: deal.status === 'gewonnen' ? 'var(--status-success-text)'
                    : deal.status === 'verloren' ? 'var(--status-danger-text)' : 'var(--status-info-text)',
                  textTransform: 'capitalize',
                }}>
                  {deal.status?.replace('_', ' ')}
                </span>
                <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--brand-primary)', minWidth: 110, textAlign: 'right' }}>
                  {Number(deal.total_value || 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* DATEIEN TAB */}
      {activeTab === 'dateien' && <ProjectFilesSection leadId={lead.id} />}

      {/* PAGESPEED TAB */}
      {activeTab === 'pagespeed' && <PageSpeedSection leadId={lead.id} />}

      {/* AKADEMY TAB */}
      {activeTab === 'akademy' && <AcademyCustomerSection leadId={lead.id} />}

      {/* DESIGN TAB */}
      {activeTab === 'design' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>
              KI-Website-Entwurf generieren
            </div>

            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              Generiert automatisch Textentwürfe für die Website auf Basis der Briefing-Daten.
              {!briefingData?.gewerk && ' Noch kein Briefing ausgefüllt – Basisdaten des Leads werden verwendet.'}
            </div>

            {/* Template assignment */}
            <div style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 8, padding: '12px 14px', marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>Design-Template</div>
              {templateLoading ? (
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Lade Template-Info...</div>
              ) : assignedTemplate ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 500 }}>📐 {assignedTemplate.name}</span>
                  <button onClick={openTemplateModal} style={{ fontSize: 11, padding: '3px 10px', background: 'var(--bg-surface)', border: '1px solid var(--border-medium)', borderRadius: 6, cursor: 'pointer', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)' }}>
                    wechseln
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Kein Template zugewiesen</span>
                  <button onClick={openTemplateModal} style={{ fontSize: 11, padding: '4px 12px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 6, cursor: 'pointer', fontFamily: 'var(--font-sans)', fontWeight: 600 }}>
                    Template zuweisen
                  </button>
                </div>
              )}
              {assignedTemplate && (
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4 }}>
                  Die KI nutzt dieses Template als Designgrundlage für den Entwurf.
                </div>
              )}
            </div>

            {!projectId && (
              <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#92660A', marginBottom: 12 }}>
                Für den KI-Entwurf wird ein Projekt benötigt. Bitte zuerst ein Projekt anlegen.
              </div>
            )}
            <button
              onClick={generateDesign}
              disabled={designRunning || !projectId}
              style={{
                padding: '10px 22px', borderRadius: 8, border: 'none',
                background: designRunning || !projectId ? 'var(--bg-muted)' : 'var(--brand-primary)',
                color: designRunning || !projectId ? 'var(--text-tertiary)' : '#fff',
                fontSize: 14, fontWeight: 600, cursor: designRunning || !projectId ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              {designRunning && <span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />}
              {designRunning ? 'Generiere Entwurf…' : '🎨 KI-Entwurf generieren'}
            </button>
            {designSlow && (
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#F59E0B', display: 'inline-block', flexShrink: 0 }} />
                Claude denkt gründlich nach — das kann bis zu 55 Sekunden dauern…
              </div>
            )}
            {designError && (
              <div style={{ background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-text)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--status-danger-text)', marginTop: 12 }}>
                {typeof designError === 'string' ? designError : JSON.stringify(designError)}
              </div>
            )}
          </div>
          {designResult && (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>Generierter Entwurf</div>
              {typeof designResult === 'string' ? (
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'inherit', lineHeight: 1.7, margin: 0 }}>{designResult}</pre>
              ) : (
                Object.entries(designResult).map(([key, val]) => (
                  <div key={key} style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{key}</div>
                    <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{typeof val === 'string' ? val : JSON.stringify(val, null, 2)}</div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
        </div>

        <BetriebVerlauf leadId={lead.id} token={token} />
      </div>

      {/* TEMPLATE SELECTION MODAL */}
      {showTemplateModal && createPortal(
        <div role="button" tabIndex={0} onKeyDown={aufTaste(e => e.target === e.currentTarget && setShowTemplateModal(false))} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={e => e.target === e.currentTarget && setShowTemplateModal(false)}>
          <div style={{ background: '#fff', borderRadius: 12, padding: 24, width: '100%', maxWidth: 600, maxHeight: '80vh', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ fontWeight: 700, fontSize: 17 }}>🗂️ Template auswählen</div>
            {allTemplates.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#888' }}>
                <div style={{ fontSize: 32, marginBottom: 8 }}>🗂️</div>
                <div>Noch keine Templates vorhanden.</div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 12 }}>
                {allTemplates.map(tpl => (
                  <div role="button" tabIndex={0} onKeyDown={aufTaste(() => assignTemplate(tpl.id))} key={tpl.id} onClick={() => assignTemplate(tpl.id)} style={{ border: `2px solid ${assignedTemplate?.id === tpl.id ? 'var(--brand-primary)' : '#e0e0e0'}`, borderRadius: 8, padding: 14, cursor: 'pointer', background: assignedTemplate?.id === tpl.id ? 'var(--bg-active)' : '#fff', transition: 'border-color 0.15s' }}
                    onMouseEnter={e => { if (assignedTemplate?.id !== tpl.id) e.currentTarget.style.borderColor = 'var(--brand-primary)'; }}
                    onMouseLeave={e => { if (assignedTemplate?.id !== tpl.id) e.currentTarget.style.borderColor = '#e0e0e0'; }}
                  >
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>{tpl.name}</div>
                    <span style={{ fontSize: 10, padding: '2px 7px', borderRadius: 8, background: tpl.source === 'url' ? '#e3f2fd' : '#e8f5e9', color: tpl.source === 'url' ? '#1565c0' : '#2e7d32', fontWeight: 600 }}>
                      {tpl.source === 'url' ? '🌐 URL' : '📁 ZIP'}
                    </span>
                    {tpl.created_at && <div style={{ fontSize: 10, color: '#aaa', marginTop: 6 }}>{new Date(tpl.created_at).toLocaleDateString('de-DE')}</div>}
                  </div>
                ))}
              </div>
            )}
            <button onClick={() => setShowTemplateModal(false)} style={{ padding: '9px', background: '#f5f5f5', color: '#555', border: 'none', borderRadius: 8, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
          </div>
        </div>,
        document.body
      )}

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
                    <div style={{ fontSize: 10, color: 'var(--brand-primary-mid)', fontFamily: 'var(--font-mono)', wordBreak: 'break-all', lineHeight: 1.4 }}>{qrData.portal_url}</div>
                  </div>
                  {lead.email && (
                    <div style={{ background: 'var(--status-info-bg)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: '8px 10px', marginBottom: 12, fontSize: 11, color: 'var(--status-info-text)', lineHeight: 1.5 }}>
                      🔐 Zugang via Domain <strong>@{lead.email.split('@')[1]}</strong>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    <button onClick={() => { const a = document.createElement('a'); a.href = `data:image/png;base64,${qrData.qr_code_base64}`; a.download = `qr-${lead.company_name || leadId}.png`; a.click(); }}
                      style={{ flex: 1, padding: 8, background: 'var(--brand-primary)', color: 'var(--text-on-brand)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
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
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-active)', color: 'var(--brand-primary-mid)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, flexShrink: 0 }}>{item.icon}</div>
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
                    style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 500, textDecoration: 'none' }}>
                    ✉️ Per E-Mail senden
                  </a>
                )}
              </Card>
            </div>
          </div>
        );
      })()}

      {/* CRAWLER TAB */}
      {/* CRAWLER TAB — eigene Komponente seit dem 22.08.2026 (L-25):
        * Der Zweig haelt seinen Zustand selbst, deshalb liess er sich
        * ohne Requisitenkette herausloesen. */}
      {activeTab === 'crawler' && (
        <CrawlerReiter leadId={leadId} lead={lead} token={token} />
      )}

      {/* E-MAILS TAB */}
      {activeTab === 'emails' && (
        <div style={{ padding: '20px 0' }}>

          {/* SEQUENZ-STEUERUNG */}
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 12,
            border: '0.5px solid var(--border-light)',
            padding: '16px 20px', marginBottom: 16,
          }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em',
              marginBottom: 12,
            }}>
              E-Mail-Sequenz (Tag 1 · 3 · 7)
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <span style={{
                padding: '3px 10px', borderRadius: 10, fontSize: 12, fontWeight: 600,
                background: seqStatus?.active && !seqStatus?.paused
                  ? '#E1F5EE' : seqStatus?.paused ? '#FAEEDA' : '#F1EFE8',
                color: seqStatus?.active && !seqStatus?.paused
                  ? '#085041' : seqStatus?.paused ? '#633806' : '#444441',
              }}>
                {seqStatus?.active && !seqStatus?.paused
                  ? `Aktiv — Schritt ${seqStatus.step} von 3`
                  : seqStatus?.paused ? 'Pausiert'
                  : 'Inaktiv'}
              </span>
              {seqStatus?.last_sent && (
                <span style={{ fontSize: 11, color: '#94a3b8' }}>
                  Letzter Versand: {new Date(seqStatus.last_sent).toLocaleDateString('de-DE')}
                </span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {!seqStatus?.active && (
                <button
                  onClick={() => seqAction('start')}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: 'none',
                    background: 'var(--success)', color: 'var(--text-on-brand)',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>
                  Sequenz starten
                </button>
              )}
              {seqStatus?.active && !seqStatus?.paused && (
                <button
                  onClick={() => seqAction('pause')}
                  style={{
                    padding: '8px 14px', borderRadius: 8,
                    border: '1px solid #e2e8f0', background: 'transparent',
                    color: '#64748b', fontSize: 12, cursor: 'pointer',
                  }}>
                  Pausieren
                </button>
              )}
              {seqStatus?.paused && (
                <button
                  onClick={() => seqAction('start')}
                  style={{
                    padding: '8px 14px', borderRadius: 8, border: 'none',
                    background: 'var(--brand-primary)', color: 'var(--text-on-brand)',
                    fontSize: 12, fontWeight: 600, cursor: 'pointer',
                  }}>
                  Fortsetzen
                </button>
              )}
              {seqStatus?.active && (
                <button
                  onClick={() => seqAction('stop')}
                  style={{
                    padding: '8px 14px', borderRadius: 8,
                    border: '1px solid #FECACA', background: '#FFF1F1',
                    color: '#A32D2D', fontSize: 12, cursor: 'pointer',
                  }}>
                  Stoppen
                </button>
              )}
            </div>
          </div>

          {/* E-MAIL-PROTOKOLL */}
          <div style={{
            background: 'var(--bg-surface)', borderRadius: 12,
            border: '0.5px solid var(--border-light)',
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '12px 16px',
              borderBottom: '0.5px solid var(--border-light)',
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em',
            }}>
              Gesendete E-Mails ({emailLogs.length})
            </div>

            {emailLoading ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Lädt...
              </div>
            ) : emailLogs.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Noch keine E-Mails gesendet.
              </div>
            ) : emailLogs.map((log, i) => (
              <div key={i} style={{
                padding: '10px 16px',
                borderBottom: i < emailLogs.length - 1 ? '0.5px solid var(--border-light)' : 'none',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                <span style={{
                  fontSize: 10, fontWeight: 600, padding: '2px 7px',
                  borderRadius: 8,
                  background: log.status === 'sent' ? '#EAF3DE' : '#FFF1F1',
                  color: log.status === 'sent' ? '#27500A' : '#A32D2D',
                  flexShrink: 0,
                }}>
                  {log.status === 'sent' ? '✓ Gesendet' : '✗ Fehler'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 13, color: 'var(--text-primary)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {log.subject}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 1 }}>
                    {log.template_key} ·{' '}
                    {log.sent_at
                      ? new Date(log.sent_at).toLocaleDateString('de-DE', {
                          day: '2-digit', month: '2-digit', year: 'numeric',
                          hour: '2-digit', minute: '2-digit',
                        })
                      : '—'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AUDIT DETAIL MODAL */}
      {openAudit && createPortal(
        <>
          {/* Overlay — zwei separate fixed-Elemente, außerhalb des page-enter-Transform-Kontexts */}
          <div role="button" tabIndex={0} onKeyDown={aufTaste(() => setOpenAudit(null))} style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.6)', backdropFilter: 'blur(4px)', zIndex: 1000 }}
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
      {deleteAuditId && createPortal(
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setDeleteAuditId(null)}>
          <div role="button" tabIndex={0} onKeyDown={aufTaste(e => e.stopPropagation())} onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 380, width: '100%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'var(--status-danger-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, margin: '0 auto 14px' }}>🗑️</div>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>Audit löschen?</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 20, lineHeight: 1.5 }}>Dieser Audit-Eintrag wird dauerhaft gelöscht und kann nicht wiederhergestellt werden.</p>
            <div style={{ display: 'flex', gap: 10 }}>
              <Button variant="secondary" fullWidth onClick={() => setDeleteAuditId(null)}>Abbrechen</Button>
              <Button variant="danger" fullWidth onClick={() => deleteAudit(deleteAuditId)}>Löschen</Button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* GEWONNEN MODAL */}
      {wonModal && createPortal(
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setWonModal(false)}>
          <div role="button" tabIndex={0} onKeyDown={aufTaste(e => e.stopPropagation())} onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 400, width: '100%', textAlign: 'center', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' }}>
            <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#EAF4E0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24, margin: '0 auto 16px' }}>🎉</div>
            <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Glückwunsch!</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, lineHeight: 1.6 }}>
              <strong>{lead.display_name || lead.company_name}</strong> wurde als gewonnen markiert.
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 24, lineHeight: 1.6 }}>
              Möchtest du jetzt ein Projekt anlegen?
            </p>
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={() => setWonModal(false)} style={{ flex: 1, padding: '10px 16px', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-secondary)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                Nein, danke
              </button>
              <button onClick={createProject} disabled={creatingProject} style={{ flex: 1, padding: '10px 16px', border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--brand-primary)', color: 'var(--text-on-brand)', fontSize: 13, fontWeight: 600, cursor: creatingProject ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                {creatingProject ? <><span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />Anlegen…</> : '📁 Ja, Projekt anlegen'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* BRIEFING WIZARD MODAL */}
      {showBriefingWizard && profile?.lead && (
        <BriefingWizard
          leadId={Number(leadId)}
          leadData={briefingData}
          onClose={() => setShowBriefingWizard(false)}
          onComplete={async () => {
            setShowBriefingWizard(false);
            await loadBriefing();
          }}
        />
      )}

    </div>
  );
}
