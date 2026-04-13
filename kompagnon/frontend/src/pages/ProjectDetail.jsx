import React, { useEffect, useState, useCallback, useRef, lazy, Suspense } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import PhaseTracker from '../components/PhaseTracker';
import MarginBadge from '../components/MarginBadge';
import ProjectCard from '../components/ProjectCard';
import WZSearch from '../components/WZSearch';
import ProjectFilesSection from '../components/ProjectFilesSection';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import PageSpeedSection from '../components/PageSpeedSection';
import KiReportPanel from '../components/KiReportPanel';
import MoodboardPanel from '../components/MoodboardPanel';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { useSwipeNavigation } from '../hooks/useTouch';
import { parseApiError } from '../utils/apiError';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';
import API_BASE_URL from '../config';
import ProzessFlow from '../components/ProzessFlow';

// Lazy-loaded: heavy components loaded on demand
const BriefingTab = lazy(() => import('../components/BriefingTab'));
const BriefingWizard = lazy(() => import('../components/BriefingWizard'));
const GrapesEditor = lazy(() => import('../components/GrapesEditor'));
const WebsiteDesigner = lazy(() => import('../components/WebsiteDesigner'));
const ContentManager = lazy(() => import('../components/ContentManager'));
const AuditReport = lazy(() => import('../components/AuditReport'));
const QAChecklist = lazy(() => import('../components/QAChecklist'));

// ── HTML builder ─────────────────────────────────────────────────────────────
const buildHtmlFromContent = (content) => {
  if (!content) return '';
  if (typeof content === 'string' && content.trim().startsWith('<')) return content;
  let data = content;
  if (typeof content === 'string') {
    try { data = JSON.parse(content); } catch { return content; }
  }
  if (typeof data !== 'object') return String(data);
  const primary = '#0d6efd';
  const services = typeof data.service_texts === 'object'
    ? Object.entries(data.service_texts).map(([k,v]) => `<div style="background:white;border-radius:8px;padding:24px;box-shadow:0 2px 8px rgba(0,0,0,0.1)"><h3 style="margin-bottom:10px">${k}</h3><p style="color:#555;line-height:1.6">${v}</p></div>`).join('')
    : '';
  const faqs = Array.isArray(data.faq_items)
    ? data.faq_items.map(i => `<div style="border-bottom:1px solid #eee;padding:18px 0"><h3 style="margin-bottom:8px">${i.question||''}</h3><p style="color:#555;line-height:1.6">${i.answer||''}</p></div>`).join('')
    : '';
  return `<!DOCTYPE html><html><head><meta charset="UTF-8"><style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}</style></head><body>
    ${data.hero_headline ? `<div style="background:${primary};color:white;padding:80px 40px;text-align:center"><h1 style="font-size:2.5rem;font-weight:700;margin-bottom:16px">${data.hero_headline}</h1>${data.hero_subline ? `<p style="font-size:1.2rem;opacity:0.9">${data.hero_subline}</p>` : ''}</div>` : ''}
    ${data.about_text ? `<div style="padding:60px 40px;max-width:1200px;margin:0 auto"><h2 style="font-size:1.8rem;margin-bottom:20px">Über uns</h2><p style="line-height:1.8;color:#555">${data.about_text}</p></div>` : ''}
    ${services ? `<div style="background:#f8f9fa;padding:60px 40px"><h2 style="text-align:center;margin-bottom:40px;font-size:1.8rem">Unsere Leistungen</h2><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;max-width:1200px;margin:0 auto">${services}</div></div>` : ''}
    ${faqs ? `<div style="padding:60px 40px;max-width:800px;margin:0 auto"><h2 style="margin-bottom:30px;font-size:1.8rem">Häufige Fragen</h2>${faqs}</div>` : ''}
    ${data.local_cta ? `<div style="background:#1a2332;color:white;padding:60px 40px;text-align:center"><h2 style="font-size:1.8rem;margin-bottom:20px">${data.local_cta}</h2><a href="#" style="display:inline-block;background:${primary};color:white;padding:14px 32px;border-radius:6px;text-decoration:none;font-weight:600">Kontakt aufnehmen</a></div>` : ''}
  </body></html>`;
};

// ── CMS options ───────────────────────────────────────────────────────────────
const CMS_OPTIONS  = ['WordPress', 'Wix', 'TYPO3', 'Webflow', 'Sonstige'];
const PKG_OPTIONS  = ['kompagnon', 'starter', 'professional', 'enterprise'];
const PAY_OPTIONS  = ['offen', 'bezahlt', 'überfällig'];

// ── Edit Modal helpers ────────────────────────────────────────────────────────
const _extractTopProblems = (audit) => {
  if (!audit?.top_issues) return '';
  try {
    let issues = typeof audit.top_issues === 'string' ? JSON.parse(audit.top_issues) : audit.top_issues;
    return Array.isArray(issues) ? issues.slice(0, 3).join('\n') : '';
  } catch { return ''; }
};

const buildInitialForm = (project, lead, latestAudit) => ({
  website_url:                  project.website_url    || lead?.website_url    || '',
  cms_type:                     project.cms_type       || '',
  contact_name:                 project.contact_name   || lead?.contact_name   || '',
  contact_phone:                project.contact_phone  || lead?.phone          || '',
  contact_email:                project.contact_email  || lead?.email          || '',
  go_live_date:                 project.go_live_date   ? String(project.go_live_date).slice(0, 10) : '',
  package_type:                 project.package_type   || 'kompagnon',
  payment_status:               project.payment_status || 'offen',
  desired_pages:                project.desired_pages  || '',
  has_logo:                     !!project.has_logo,
  has_briefing:                 !!project.has_briefing,
  has_photos:                   !!project.has_photos,
  top_problems:                 project.top_problems   || _extractTopProblems(latestAudit),
  industry:                     project.industry       || lead?.trade          || '',
  wz_code:                      project.wz_code        || lead?.wz_code        || '',
  wz_title:                     project.wz_title       || lead?.wz_title       || '',
  customer_email:               project.customer_email || lead?.email          || '',
  email_notifications_enabled:  project.email_notifications_enabled !== false,
});

// ── Phasen-Navigation ─────────────────────────────────────────────────────────
const PHASE_MENU = {
  1: { label: 'Onboarding',  tabs: [{ id: 'audits', label: '🔍 Audit' }] },
  2: { label: 'Briefing',    tabs: [{ id: 'briefing', label: '📋 Briefing' }] },
  3: { label: 'Content',     tabs: [{ id: 'sitemap', label: '🗺️ Sitemap' }] },
  4: { label: 'Technik',     tabs: [{ id: 'netlify-dns', label: '🚀 Netlify' }] },
  5: { label: 'Go Live',     tabs: [{ id: 'checklists', label: '✅ Go-Live' }] },
  6: { label: 'QM',          tabs: [{ id: 'checklists', label: '✅ QM' }] },
  7: { label: 'Post-Launch', tabs: [{ id: 'trustpilot', label: '⭐ Trustpilot' }] },
  8: { label: 'Fertig',      tabs: [{ id: 'live-data', label: '🌐 Fertig' }] },
};

// ── Lazy-Loading Fallback ──
function TabFallback() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '48px 24px', gap: 12, color: 'var(--text-tertiary)', fontSize: 13 }}>
      <div style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', flexShrink: 0 }} />
      Lade Bereich…
    </div>
  );
}

// ── GA-Status-Karte (eigenständige Komponente wegen Hooks) ──
function GaStatusCard({ leadId, headers: h, API_BASE_URL: baseUrl }) {
  const [gaData, setGaData] = React.useState(null);
  const [gaChecking, setGaChecking] = React.useState(false);

  const checkGa = async () => {
    setGaChecking(true);
    try {
      const res = await fetch(`${baseUrl}/api/branddesign/${leadId}/check-ga`, { method: 'POST', headers: h });
      if (res.ok) setGaData(await res.json());
    } catch { /* silent */ }
    finally { setGaChecking(false); }
  };

  const statusConfig = {
    'vorhanden':       { icon: '✅', color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', text: 'Google Analytics 4 vorhanden' },
    'vorhanden_alt':   { icon: '⚠️', color: '#d97706', bg: '#fff7ed', border: '#fed7aa', text: 'Altes Universal Analytics — Migration empfohlen' },
    'gtm':             { icon: '🏷️', color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe', text: 'Google Tag Manager gefunden' },
    'nicht_vorhanden': { icon: '❌', color: '#dc2626', bg: '#fef2f2', border: '#fecaca', text: 'Kein Google Analytics gefunden' },
    'unbekannt':       { icon: '❓', color: '#6b7280', bg: 'var(--bg-app)', border: 'var(--border-light)', text: 'Noch nicht geprüft' },
  };

  const status = gaData?.status || 'unbekannt';
  const cfg = statusConfig[status] || statusConfig['unbekannt'];

  return (
    <div style={{
      padding: '14px 18px', borderRadius: 10, marginBottom: 16,
      background: cfg.bg, border: `1px solid ${cfg.border}`,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      flexWrap: 'wrap', gap: 12,
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)' }}>
          Google Analytics Status
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 18 }}>{cfg.icon}</span>
          <span style={{ fontSize: 13, fontWeight: 600, color: cfg.color }}>{cfg.text}</span>
        </div>
        {gaData?.measurement_id && (
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontFamily: 'monospace', marginTop: 2 }}>
            {gaData.type}: <strong>{gaData.measurement_id}</strong>
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <button onClick={checkGa} disabled={gaChecking} style={{
          padding: '7px 16px', borderRadius: 7, border: '1px solid var(--border-light)',
          background: 'white', fontSize: 12, fontWeight: 600,
          cursor: gaChecking ? 'not-allowed' : 'pointer', color: 'var(--text-primary)',
          fontFamily: 'inherit',
        }}>
          {gaChecking ? '⏳ Prüft…' : 'GA jetzt prüfen'}
        </button>
        {status === 'nicht_vorhanden' && (
          <button disabled style={{
            padding: '7px 16px', borderRadius: 7, border: 'none',
            background: '#008eaa', color: 'white', fontSize: 12,
            fontWeight: 700, cursor: 'not-allowed', opacity: 0.5,
            fontFamily: 'inherit',
          }}>
            + GA4 einrichten (bald)
          </button>
        )}
      </div>
    </div>
  );
}

const PHASE_NAMES = ['onboarding','briefing','content','technik','go-live','qm','post-launch','fertig'];
const PHASE_LABELS = {
  'onboarding':  'Onboarding',
  'briefing':    'Report erstellen',
  'content':     'Content',
  'technik':     'Technik',
  'go-live':     'Go Live',
  'qm':          'QM',
  'post-launch': 'Post-Launch',
  'fertig':      'Fertig',
};

const SUB_TAB_MAP = {
  'unternehmen':        'overview',
  'briefing-quick':     'briefing',
  'briefing':           'briefing',
  'brand-design':       'branddesign',
  'branddesign':        'branddesign',
  'website-content':    'webcontent',
  'hosting-scan':       'hosting',
  'hosting':            'hosting',
  'hosting-form':       'hosting',
  'checkliste':         'checklists',
  'checklists':         'checklists',
  'zugangsdaten':       'zugangsdaten',
  'qa-scan':            'qa-scan',
  'design':             'design',
  'sitemap':            'sitemap',
  'content':            'content',
  'qa':                 'qa',
  'golive':             'golive',
  'postlaunch':         'postlaunch',
  'crawler':            'crawler',
  'analyse':            'analyse',
  'golive-prep':        'overview',
  'dns':                'hosting',
  'website-vergleich':  'overview',
  'ki-report':          'ki-report',
  'moodboard':          'moodboard',
};

// Maps tool tile ID → which activeSubTab value to set (for content blocks keyed on activeSubTab)
const TOOL_SUBTAB_MAP = {
  'audits':             'audit',
  'ki-report':          'ki-report',
  'moodboard':          'moodboard',
  'analyse':            'analyse',
  'crawler':            'crawler',
  'website-content':    'webcontent',
  'hosting':            'hosting-scan',
  'hosting-form':       'hosting-form',
  'preview':            'preview',
  'editor':             'editor',
  'netlify-dns':        'netlify-dns',
  'dns':                'hosting-form',
  'live-data':          'live-data',
  'trustpilot':         'trustpilot',
  'upsell':             'upsell',
  'website-vergleich':  'website-vergleich',
};

// ── Edit Modal ────────────────────────────────────────────────────────────────
function EditModal({ project, lead, latestAudit, token, onClose, onSaved }) {
  const [form, setForm] = useState(() => buildInitialForm(project, lead, latestAudit));
  const [saving, setSaving] = useState(false);

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(
        `${API_BASE_URL}/api/projects/${project.id}`,
        form,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      toast.success('Projektdaten aktualisiert');
      onSaved();
    } catch {
      toast.error('Speichern fehlgeschlagen — bitte Seite neu laden und erneut versuchen');
    } finally {
      setSaving(false);
    }
  };

  // ── styles ────────────────────────────────────────────────────────────────
  const overlay = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, padding: 16,
  };
  const panel = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    width: '100%', maxWidth: 600, maxHeight: '90vh', overflowY: 'auto',
    display: 'flex', flexDirection: 'column',
    boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
  };
  const header = {
    padding: '18px 20px', borderBottom: '1px solid var(--border-light)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    position: 'sticky', top: 0, background: 'var(--bg-surface)', zIndex: 1,
  };
  const body = { padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 };
  const footer = {
    padding: '14px 20px', borderTop: '1px solid var(--border-light)',
    display: 'flex', justifyContent: 'flex-end', gap: 8,
    position: 'sticky', bottom: 0, background: 'var(--bg-surface)',
  };
  const fieldGroup = (n = 1) => ({
    display: 'grid', gridTemplateColumns: `repeat(${n}, 1fr)`, gap: 12,
  });
  const label = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, display: 'block' };
  const input = {
    width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-medium)', background: 'var(--bg-app)',
    color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)',
    outline: 'none', boxSizing: 'border-box',
  };
  const select = { ...input, cursor: 'pointer' };
  const textarea = { ...input, resize: 'vertical', minHeight: 72 };
  const checkRow = { display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text-primary)', cursor: 'pointer' };

  const Field = ({ label: lbl, children }) => (
    <div>
      <label style={label}>{lbl}</label>
      {children}
    </div>
  );

  return createPortal(
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={panel}>
        <div style={header}>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Projektdaten bearbeiten</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
        </div>

        <div style={body}>
          {/* Info banner when pre-filled from lead */}
          {lead && (
            <div style={{ background: '#E6F1FB', color: '#185FA5', padding: '6px 12px', borderRadius: 6, fontSize: 12, marginBottom: 4 }}>
              ℹ️ Felder wurden aus der Kundenkartei vorausgefüllt.
            </div>
          )}

          {/* Website + CMS */}
          <div style={fieldGroup(2)}>
            <Field label="Website-URL">
              <input style={input} value={form.website_url} onChange={e => set('website_url', e.target.value)} placeholder="https://…" />
            </Field>
            <Field label="CMS-Typ">
              <select style={select} value={form.cms_type} onChange={e => set('cms_type', e.target.value)}>
                <option value="">– wählen –</option>
                {CMS_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
          </div>

          {/* Ansprechpartner */}
          <div style={fieldGroup(3)}>
            <Field label="Name">
              <input style={input} value={form.contact_name} onChange={e => set('contact_name', e.target.value)} placeholder="Max Mustermann" />
            </Field>
            <Field label="Telefon">
              <input style={input} value={form.contact_phone} onChange={e => set('contact_phone', e.target.value)} placeholder="+49 …" />
            </Field>
            <Field label="E-Mail">
              <input style={input} value={form.contact_email} onChange={e => set('contact_email', e.target.value)} placeholder="name@…" />
            </Field>
          </div>

          {/* Paket + Zahlung + Go-live */}
          <div style={fieldGroup(3)}>
            <Field label="Paket">
              <select style={select} value={form.package_type} onChange={e => set('package_type', e.target.value)}>
                {PKG_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Zahlungsstatus">
              <select style={select} value={form.payment_status} onChange={e => set('payment_status', e.target.value)}>
                {PAY_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </Field>
            <Field label="Go-live Datum">
              <input style={input} type="date" value={form.go_live_date} onChange={e => set('go_live_date', e.target.value)} />
            </Field>
          </div>

          {/* Branche */}
          <Field label="Branche">
            <WZSearch
              value={form.wz_code ? { code: form.wz_code, title: form.wz_title } : null}
              onChange={(entry) => {
                set('wz_code', entry?.code || '');
                set('wz_title', entry?.title || '');
                set('industry', entry?.title || '');
              }}
              placeholder="Branche suchen..."
            />
          </Field>

          {/* Gewünschte Seiten */}
          <Field label="Gewünschte Seiten (kommagetrennt)">
            <input style={input} value={form.desired_pages} onChange={e => set('desired_pages', e.target.value)} placeholder="Startseite, Über uns, Kontakt, …" />
          </Field>

          {/* Assets */}
          <div>
            <span style={label}>Assets vorhanden</span>
            <div style={{ display: 'flex', gap: 20, marginTop: 4 }}>
              {[['has_logo','Logo'], ['has_briefing','Briefing'], ['has_photos','Fotos']].map(([key, lbl]) => (
                <label key={key} style={checkRow}>
                  <input
                    type="checkbox"
                    checked={form[key]}
                    onChange={e => set(key, e.target.checked)}
                    style={{ width: 15, height: 15, accentColor: '#1D9E75', cursor: 'pointer' }}
                  />
                  {lbl}
                </label>
              ))}
            </div>
          </div>

          {/* Top-Probleme */}
          <Field label="Top-Probleme aus Audit (eine pro Zeile, max. 3)">
            <textarea style={textarea} value={form.top_problems} onChange={e => set('top_problems', e.target.value)} placeholder={"Problem 1\nProblem 2\nProblem 3"} rows={3} />
          </Field>

          {/* E-Mail-Benachrichtigungen */}
          <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: 16 }}>
            <span style={label}>E-Mail-Benachrichtigungen</span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
              <Field label="Kunden-E-Mail">
                <input
                  style={input}
                  type="email"
                  value={form.customer_email}
                  onChange={e => set('customer_email', e.target.value)}
                  placeholder="kunde@beispiel.de"
                />
              </Field>
              <label style={checkRow}>
                <input
                  type="checkbox"
                  checked={form.email_notifications_enabled}
                  onChange={e => set('email_notifications_enabled', e.target.checked)}
                  style={{ width: 15, height: 15, accentColor: '#008EAA', cursor: 'pointer' }}
                />
                E-Mail-Benachrichtigungen aktiv
              </label>
            </div>
          </div>
        </div>

        <div style={footer}>
          <button onClick={onClose} style={{ padding: '8px 16px', background: 'var(--bg-hover)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)' }}>
            Abbrechen
          </button>
          <button onClick={handleSave} disabled={saving} style={{ padding: '8px 18px', background: '#185FA5', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: saving ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}>
            {saving ? 'Speichern…' : 'Speichern'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

// ── Approval Modal ────────────────────────────────────────────────────────────
function ApprovalModal({ projectId, token, onClose }) {
  const [topic, setTopic]     = useState('');
  const [notes, setNotes]     = useState('');
  const [sending, setSending] = useState(false);
  const [result, setResult]   = useState(null); // { ok: bool, msg: str }

  const overlay = {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1000, padding: 16,
  };
  const panel = {
    background: 'var(--bg-surface)', borderRadius: 'var(--radius-lg)',
    width: '100%', maxWidth: 480,
    boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
    display: 'flex', flexDirection: 'column',
  };
  const header = {
    padding: '16px 20px', borderBottom: '1px solid var(--border-light)',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  };
  const body   = { padding: '20px', display: 'flex', flexDirection: 'column', gap: 14 };
  const footer = {
    padding: '12px 20px', borderTop: '1px solid var(--border-light)',
    display: 'flex', justifyContent: 'flex-end', gap: 8,
  };
  const labelSt = { fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4, display: 'block' };
  const inputSt  = { width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', outline: 'none', boxSizing: 'border-box' };

  const handleSend = async () => {
    if (!topic.trim()) return;
    setSending(true);
    setResult(null);
    try {
      const res = await axios.post(
        `${API_BASE_URL}/api/projects/${projectId}/request-approval`,
        { topic: topic.trim(), notes: notes.trim() },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (res.data.success) {
        setResult({ ok: true, msg: 'Freigabe-E-Mail wurde gesendet ✓' });
      } else {
        setResult({ ok: false, msg: `Fehler: ${res.data.message || 'Keine E-Mail-Adresse hinterlegt'}` });
      }
    } catch {
      setResult({ ok: false, msg: 'Fehler: Keine E-Mail-Adresse hinterlegt' });
    } finally {
      setSending(false);
    }
  };

  return createPortal(
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={panel}>
        <div style={header}>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Freigabe anfordern</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
        </div>

        <div style={body}>
          {result && (
            <div style={{
              padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 13,
              background: result.ok ? 'var(--status-success-bg)' : 'var(--status-danger-bg)',
              color:      result.ok ? 'var(--status-success-text)' : 'var(--status-danger-text)',
            }}>
              {result.msg}
            </div>
          )}

          <div>
            <label style={labelSt}>Thema der Freigabe *</label>
            <input
              style={inputSt}
              value={topic}
              onChange={e => setTopic(e.target.value)}
              placeholder="z.B. Design-Freigabe Phase 3"
            />
          </div>

          <div>
            <label style={labelSt}>Hinweise / Details (optional)</label>
            <textarea
              style={{ ...inputSt, resize: 'vertical', minHeight: 80 }}
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Bitte bis Freitag rückmelden…"
            />
          </div>
        </div>

        <div style={footer}>
          <button onClick={onClose} style={{ padding: '8px 16px', background: 'var(--bg-hover)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-secondary)' }}>
            Schließen
          </button>
          <button
            onClick={handleSend}
            disabled={sending || !topic.trim()}
            style={{ padding: '8px 18px', background: '#008EAA', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: (sending || !topic.trim()) ? 'not-allowed' : 'pointer', opacity: (sending || !topic.trim()) ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}
          >
            {sending ? 'Senden…' : 'Freigabe-E-Mail senden'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ProjectDetail() {
  const { id }         = useParams();
  const navigate       = useNavigate();
  const { token, user } = useAuth();
  const { isMobile }   = useScreenSize();
  const phaseScrollRef = useRef(null);
  const headers          = token ? { Authorization: `Bearer ${token}` } : {};
  const hdr              = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const isAdmin          = user?.role === 'admin';

  const [project, setProject]         = useState(null);
  const [lead, setLead]               = useState(null);
  const [margin, setMargin]           = useState(null);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState('overview');
  const [activeSubTab, setActiveSubTab] = useState('unternehmen');

  const scrollRef = useRef(null);
  const [showEdit, setShowEdit]       = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [showBriefingWizard, setShowBriefingWizard] = useState(false);
  const [showWebsiteDesigner, setShowWebsiteDesigner] = useState(false);
  const [showNewMessageModal, setShowNewMessageModal] = useState(false);
  const [newMessageText, setNewMessageText] = useState('');
  const [briefingData, setBriefingData] = useState(null);
  // Esc-Shortcuts für Modals
  useEscapeKey(() => setShowNewMessageModal(false), showNewMessageModal);
  useEscapeKey(() => setShowEdit(false), showEdit);
  useEscapeKey(() => setShowApproval(false), showApproval);
  useEscapeKey(() => setShowBriefingWizard(false), showBriefingWizard);

  // Swipe between tool tiles on mobile
  const ANALYSE_TOOLS = ['unternehmen', 'briefing', 'audits', 'analyse', 'zugangsdaten'];
  const currentToolIdx = ANALYSE_TOOLS.indexOf(activeSubTab);
  const swipeRef = useSwipeNavigation({
    disabled: !isMobile,
    onSwipeLeft: () => {
      const next = ANALYSE_TOOLS[currentToolIdx + 1];
      if (next) { setActiveTab(SUB_TAB_MAP[next] || next); setActiveSubTab(TOOL_SUBTAB_MAP[next] || next); }
    },
    onSwipeRight: () => {
      const prev = ANALYSE_TOOLS[currentToolIdx - 1];
      if (prev) { setActiveTab(SUB_TAB_MAP[prev] || prev); setActiveSubTab(TOOL_SUBTAB_MAP[prev] || prev); }
    },
    threshold: 60,
  });

  // Checklists (lazy audit load)
  const [latestAudit, setLatestAudit] = useState(null);
  // Crawler
  const [crawlJob, setCrawlJob] = useState(null);
  const [crawlResults, setCrawlResults] = useState([]);
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [crawlElapsed, setCrawlElapsed] = useState(0);
  const crawlIntervalRef = useRef(null);
  const [crawlSort, setCrawlSort] = useState({ col: 'crawled_at', asc: true });
  const [crawlExpandedRow, setCrawlExpandedRow] = useState(null);
  // Sitemap
  const [sitemapPages, setSitemapPages]     = useState([]);
  const [sitemapLoading, setSitemapLoading] = useState(false);
  const [sitemapLoaded, setSitemapLoaded]   = useState(false);
  const [selectedPageId, setSelectedPageId] = useState(null);
  const [editingPage, setEditingPage]       = useState(null);
  // Add page form
  const [addPageOpen, setAddPageOpen]       = useState(false);
  const [addPageForm, setAddPageForm]       = useState({ page_name: '', page_type: 'info', parent_id: '' });
  const [addPageSaving, setAddPageSaving]   = useState(false);
  // Edit page modal
  const [editPageModal, setEditPageModal]   = useState(null);
  const [editPageForm, setEditPageForm]     = useState({});
  const [editPageSaving, setEditPageSaving] = useState(false);
  const [deletingPageId, setDeletingPageId] = useState(null);
  const [draggedPageId, setDraggedPageId]   = useState(null);
  const [dragOverPageId, setDragOverPageId] = useState(null);
  // KI generation
  const [kiGenerating, setKiGenerating]     = useState(false);
  const [kiConfirm, setKiConfirm]           = useState(false);
  // Content Manager
  const [showContentManager, setShowContentManager] = useState(false);
  const [contentSummary, setContentSummary] = useState([]);
  // Website-Content Scraper
  const [scrapeStatus, setScrapeStatus]       = useState(null);
  const [scrapedPages, setScrapedPages]       = useState([]);
  const [scrapeLoaded, setScrapeLoaded]       = useState(false);
  const [scrapePolling, setScrapePolling]     = useState(false);
  const [expandedScrape, setExpandedScrape]   = useState({});
  // BrandDesign
  const [brandData, setBrandData]   = useState(null);
  const [brandEdits, setBrandEdits] = useState({});
  const [brandSaving, setBrandSaving] = useState(false);
  const [fontSuggestions, setFontSuggestions] = useState([]);
  const [loadingFonts, setLoadingFonts] = useState(false);
  const [scanRunning, setScanRunning] = useState(false);
  const [scanStep, setScanStep] = useState(-1);
  const [scanResults, setScanResults] = useState([]);
  const [scraping, setScraping]     = useState(false);
  const [analyzing, setAnalyzing]   = useState(false);
  // Design versions
  const [designVersions, setDesignVersions]       = useState([]);
  const [designVersionsLoaded, setDesignVersionsLoaded] = useState(false);
  // Hosting-Analyse
  const [hostingData, setHostingData]       = useState(null);
  const [hostingChecked, setHostingChecked] = useState(false);
  const [hostingLoaded, setHostingLoaded]   = useState(false);
  const [hostingForm, setHostingForm] = useState({
    hosting_provider: '', domain_registrar: '', nameserver1: '', nameserver2: '',
    ftp_credentials: '', wp_admin_url: '', hosting_notes: '',
  });
  const [hostingFormSaving, setHostingFormSaving] = useState(false);
  const [hostingScanning, setHostingScanning] = useState(false);
  // Screenshots before/after
  const [screenshots, setScreenshots]       = useState({ before: { data: null, date: null, url: null }, after: { data: null, date: null, url: null } });
  const [screenshotsLoaded, setScreenshotsLoaded] = useState(false);
  const [takingBefore, setTakingBefore]     = useState(false);
  const [takingAfter, setTakingAfter]       = useState(false);
  const [newWebsiteUrl, setNewWebsiteUrl]   = useState('');
  const [designPreview, setDesignPreview]         = useState(null); // { html, version_name }
  const [savingVersion, setSavingVersion]         = useState(false);
  // Design
  const [designRunning, setDesignRunning] = useState(false);
  const [designSlow, setDesignSlow] = useState(false);
  const [designResult, setDesignResult] = useState(null);
  const [designError, setDesignError] = useState('');
  const [activeDesignPage, setActiveDesignPage] = useState(null);
  const [activeContentPage, setActiveContentPage] = useState(null);
  // Audits
  const [audits, setAudits] = useState([]);
  const [openAudit, setOpenAudit] = useState(null);
  // Briefing Lead
  const [briefingLead, setBriefingLead] = useState(null);
  // Website-Content (Crawler)
  const [websiteContent, setWebsiteContent] = useState([]);
  const [contentLoading, setContentLoading] = useState(false);
  const [selectedContentPage, setSelectedContentPage] = useState(null);
  // Website Versionen (KI-generiert)
  const [versions, setVersions] = useState([]);
  const [versionsGenerating, setVersionsGenerating] = useState(false);
  const [versionsRecommendation, setVersionsRecommendation] = useState('');
  // QA-Scanner
  const [qaResult, setQaResult]   = useState(null);
  const [qaRunning, setQaRunning] = useState(false);
  const [qaError, setQaError]     = useState('');
  const [openKat, setOpenKat]     = useState(null);
  // Domain-Check
  const [domainChecking, setDomainChecking] = useState(false);
  // Netlify
  const [netlify, setNetlify] = useState(null);
  const [netlifyLoading, setNetlifyLoading] = useState(false);
  const [netlifyError, setNetlifyError] = useState(null);
  const [netlifyChecked, setNetlifyChecked] = useState(false);
  const netlifyFetchRef = useRef(false);
  const [netlifyDomain, setNetlifyDomain] = useState('');
  const [netlifyDnsGuide, setNetlifyDnsGuide] = useState(null); // { cname_target }
  const [netlifyDeploying, setNetlifyDeploying] = useState(false);
  const [netlifyDeployResult, setNetlifyDeployResult] = useState(null);
  // Nachrichten
  const [chatMessages, setChatMessages] = useState([]);
  const [chatText, setChatText] = useState('');
  const [chatChannel, setChatChannel] = useState('in_app');
  const [chatSubject, setChatSubject] = useState('');
  const [chatSending, setChatSending] = useState(false);
  // Zugangsdaten-Safe
  const [creds, setCreds]               = useState([]);
  const [credsLoading, setCredsLoading] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});
  const [credForm, setCredForm]         = useState({ label: '', username: '', password: '', url: '', notes: '' });
  const [credSaving, setCredSaving]     = useState(false);
  const [credError, setCredError]       = useState('');
  // Content-Freigaben
  const [contentFreigaben, setContentFreigaben] = useState({});
  const [approvalSending, setApprovalSending]   = useState({});
  const [approvalMsg, setApprovalMsg]           = useState({});
  // Go-Live / Abnahme
  const [abnahmeLoading, setAbnahmeLoading] = useState(false);
  const [abnahmeMsg, setAbnahmeMsg]         = useState('');
  const [abnahmeName, setAbnahmeName]       = useState('');
  const [psLoading, setPsLoading]           = useState(false);
  const [psMsg, setPsMsg]                   = useState('');
  // Post-Launch / GBP
  const [gbpData, setGbpData]           = useState(null);
  const [gbpChecked, setGbpChecked]     = useState({});
  const [gbpQrLoading, setGbpQrLoading] = useState(false);
  const [gbpQrData, setGbpQrData]       = useState(null);
  const [gbpQrError, setGbpQrError]     = useState('');

  const checkDomain = async () => {
    setDomainChecking(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${id}/domain-check`, { method: 'POST', headers });
      const d = await res.json();
      setProject(prev => ({ ...prev, domain_reachable: d.reachable, domain_status_code: d.status_code, domain_checked_at: d.checked_at }));
    } catch { /* silent */ } finally { setDomainChecking(false); }
  };

  const loadCreds = async () => {
    setCredsLoading(true);
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${id}/credentials`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (r.ok) setCreds(await r.json());
    } catch {}
    setCredsLoading(false);
  };

  useEffect(() => {
    if (activeTab === 'zugangsdaten') loadCreds();
    if (activeTab === 'postlaunch')   loadGbpData();
    if ((activeTab === 'sitemap' || activeSubTab === 'sitemap') && project?.lead_id && !sitemapLoaded) {
      loadSitemapPages();
    }
    // Load saved hosting data when tab opens
    if ((activeSubTab === 'hosting-scan' || activeSubTab === 'hosting') && !hostingChecked && project?.id) {
      setHostingChecked(true);
      setHostingScanning(true);
      fetch(`${API_BASE_URL}/api/projects/${project.id}/hosting-info`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d?.hosting_provider || d?.nameservers || d?.server_software) setHostingData(d); })
        .catch(() => {})
        .finally(() => setHostingScanning(false));
    }
  }, [activeTab, activeSubTab]); // eslint-disable-line

  const saveCred = async () => {
    if (!credForm.label.trim()) {
      setCredError('Bitte einen Namen eingeben (z.B. IONOS).');
      return;
    }
    setCredSaving(true); setCredError('');
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${id}/credentials`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
          body: JSON.stringify(credForm),
        }
      );
      if (!r.ok) {
        const d = await r.json();
        setCredError(d.detail || 'Fehler beim Speichern');
        return;
      }
      setCredForm({ label: '', username: '', password: '', url: '', notes: '' });
      await loadCreds();
    } catch { setCredError('Verbindungsfehler'); }
    finally { setCredSaving(false); }
  };

  const deleteCred = async (credId) => {
    if (!window.confirm('Zugangsdaten löschen?')) return;
    await fetch(
      `${API_BASE_URL}/api/projects/${id}/credentials/${credId}`,
      { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
    );
    await loadCreds();
  };

  const togglePw = (credId) =>
    setShowPasswords(p => ({ ...p, [credId]: !p[credId] }));

  // ── Content-Freigaben Hilfsfunktionen ───────────────────────────────────────
  const getSitemapSeiten = () => {
    const sj = project?.sitemap_json;
    if (!sj) return [];
    try { return JSON.parse(sj); } catch { return []; }
  };

  const requestApproval = async (seite) => {
    setApprovalSending(p => ({ ...p, [seite.id]: true }));
    setApprovalMsg(p => ({ ...p, [seite.id]: '' }));
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${id}/request-approval`,
        {
          method: 'POST', headers: hdr,
          body: JSON.stringify({
            seite_id: seite.id,
            topic:    `Content-Freigabe: ${seite.name}`,
            notes:    `Seite vom Typ "${seite.typ}" · Keyword: ${seite.keyword || '—'}`,
          }),
        }
      );
      const d = await r.json();
      if (r.ok) {
        setContentFreigaben(d.freigaben || {});
        setApprovalMsg(p => ({
          ...p,
          [seite.id]: d.email_sent ? '✓ E-Mail gesendet' : '✓ Gespeichert',
        }));
      } else {
        setApprovalMsg(p => ({ ...p, [seite.id]: parseApiError(d) }));
      }
    } catch {
      setApprovalMsg(p => ({ ...p, [seite.id]: 'Verbindungsfehler' }));
    }
    setApprovalSending(p => ({ ...p, [seite.id]: false }));
  };

  const confirmApproval = async (seiteId, bestaetigt) => {
    const r = await fetch(
      `${API_BASE_URL}/api/projects/${id}/confirm-approval`,
      {
        method: 'POST', headers: hdr,
        body: JSON.stringify({ seite_id: seiteId, bestaetigt }),
      }
    );
    const d = await r.json();
    if (r.ok) setContentFreigaben(d.freigaben || {});
  };

  const advanceToTechnik = async () => {
    await fetch(`${API_BASE_URL}/api/projects/${id}/phase`, {
      method: 'PATCH', headers: hdr,
      body: JSON.stringify({ new_status: 'phase_4' }),
    });
    await loadProject();
  };

  // ── Post-Launch / GBP ───────────────────────────────────────────────────────
  const loadGbpData = async () => {
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${id}/bewertungs-url`, { headers: hdr });
      if (r.ok) setGbpData(await r.json());
    } catch {}
    if (project?.gbp_checklist_json) {
      try { setGbpChecked(JSON.parse(project.gbp_checklist_json) || {}); } catch {}
    }
  };

  const loadGbpQr = async () => {
    setGbpQrLoading(true); setGbpQrError('');
    try {
      const r = await fetch(`${API_BASE_URL}/api/projects/${id}/bewertungs-qrcode`, { headers: hdr });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        setGbpQrError(d.detail || 'QR-Code konnte nicht geladen werden');
        return;
      }
      const blob = await r.blob();
      const reader = new FileReader();
      reader.onloadend = () => setGbpQrData(reader.result);
      reader.readAsDataURL(blob);
    } catch { setGbpQrError('Verbindungsfehler'); }
    finally { setGbpQrLoading(false); }
  };

  const downloadGbpQr = () => {
    if (!gbpQrData) return;
    const a = document.createElement('a');
    a.href = gbpQrData;
    a.download = `bewertungs-qr-${project?.company_name || id}.png`;
    a.click();
  };

  const toggleGbpItem = (itemId) => {
    const next = { ...gbpChecked, [itemId]: !gbpChecked[itemId] };
    setGbpChecked(next);
    fetch(`${API_BASE_URL}/api/projects/${id}/gbp-checklist`, {
      method: 'PATCH', headers: hdr,
      body: JSON.stringify({ checked: next }),
    }).catch(() => {});
  };

  // ── Go-Live Handler ─────────────────────────────────────────────────────────
  const doAbnahme = async () => {
    if (!abnahmeName.trim()) { setAbnahmeMsg('Bitte Namen eingeben'); return; }
    setAbnahmeLoading(true); setAbnahmeMsg('');
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${id}/abnahme`,
        { method: 'POST', headers: hdr, body: JSON.stringify({ name: abnahmeName }) }
      );
      const d = await r.json();
      if (r.ok) { setAbnahmeMsg(`✓ ${d.text}`); await loadProject(); }
      else      { setAbnahmeMsg(parseApiError(d)); }
    } catch { setAbnahmeMsg('Verbindungsfehler'); }
    finally { setAbnahmeLoading(false); }
  };

  const doGoLivePagespeed = async () => {
    setPsLoading(true); setPsMsg('');
    try {
      const r = await fetch(
        `${API_BASE_URL}/api/projects/${id}/go-live-pagespeed`,
        { method: 'POST', headers: hdr }
      );
      const d = await r.json();
      if (r.ok) {
        setPsMsg(`✓ Mobil: ${d.pagespeed_after_mobile ?? '—'} | Desktop: ${d.pagespeed_after_desktop ?? '—'}`);
        await loadProject();
      } else { setPsMsg(parseApiError(d)); }
    } catch { setPsMsg('Verbindungsfehler'); }
    finally { setPsLoading(false); }
  };

  const loadProject = useCallback(async () => {
    try {
      setLoading(true);
      const [projectRes, marginRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/projects/${id}`, { headers }),
        axios.get(`${API_BASE_URL}/api/projects/${id}/margin`, { headers }),
      ]);
      console.log('Projekt API:', projectRes.data);
      setProject(projectRes.data);
      setMargin(marginRes.data);
      setNewWebsiteUrl(projectRes.data.new_website_url || '');
      // content_freigaben parsen
      const cf = projectRes.data?.content_freigaben;
      if (cf) {
        try { setContentFreigaben(JSON.parse(cf)); } catch {}
      }
      // Load lead data for modal pre-fill
      if (projectRes.data.lead_id) {
        axios.get(`${API_BASE_URL}/api/leads/${projectRes.data.lead_id}`, { headers })
          .then(r => setLead(r.data))
          .catch(() => {});
      }
      // Screenshots lazy-load
      fetch(`${API_BASE_URL}/api/projects/${id}/screenshots`, { headers })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) { setScreenshots(d); setScreenshotsLoaded(true); } })
        .catch(() => {});
    } catch {
      toast.error('Projekt konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [id]); // eslint-disable-line

  useEffect(() => { loadProject(); }, [id]); // eslint-disable-line

  const loadQa = async () => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${id}/qa/result`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'no_result' || data.status === 'parse_error') {
          setQaResult(null);
          if (data.status === 'parse_error') setQaError(data.message || 'QA-Ergebnis fehlerhaft');
        } else {
          setQaResult(data);
          setQaError('');
        }
      }
    } catch {}
  };

  useEffect(() => { if (activeTab === 'qa-scan' || activeTab === 'qa') loadQa(); }, [id, activeTab]); // eslint-disable-line

  const runQa = async () => {
    setQaRunning(true); setQaError('');
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/projects/${id}/qa/run`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      );
      const d = await res.json();
      if (!res.ok) { setQaError(parseApiError(d)); return; }
      setQaResult(d);
    } catch { setQaError('Verbindungsfehler'); }
    finally { setQaRunning(false); }
  };

  const loadAudits = useCallback(async () => {
    if (!project?.lead_id) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/audit/lead/${project.lead_id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setAudits(await res.json());
    } catch (e) { console.error(e); }
  }, [project?.lead_id]); // eslint-disable-line

  useEffect(() => { if (project?.lead_id && activeSubTab === 'audit') loadAudits(); }, [project?.lead_id, activeSubTab]); // eslint-disable-line

  // Load cached scrape-full data on project mount (no network scrape)
  useEffect(() => {
    if (!project?.id) return;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/scrape-full`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && data.seo) setScrapeStatus(data);
      })
      .catch(() => {});
  }, [project?.id]); // eslint-disable-line

  // Load Netlify status ONCE when tab opens — race-condition-safe
  useEffect(() => {
    const isNetlifyTab = activeSubTab === 'netlify-dns' || activeTab === 'netlify-dns';
    if (!isNetlifyTab || !project?.id || netlifyChecked || netlifyFetchRef.current) return;
    netlifyFetchRef.current = true;
    setNetlifyLoading(true);
    setNetlifyError(null);
    let cancelled = false;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async r => {
        if (cancelled) return;
        if (r.status === 404) { setNetlify(null); setNetlifyChecked(true); return; }
        if (!r.ok) { const err = await r.json().catch(() => ({})); throw new Error(err.detail || `HTTP ${r.status}`); }
        const data = await r.json();
        if (!cancelled) { setNetlify(data); setNetlifyChecked(true); }
      })
      .catch(e => { if (!cancelled) { setNetlifyError(e.message || 'Netlify-Status konnte nicht geladen werden'); setNetlifyChecked(true); } })
      .finally(() => { if (!cancelled) { setNetlifyLoading(false); netlifyFetchRef.current = false; } });
    return () => { cancelled = true; };
  }, [activeSubTab, activeTab, project?.id, netlifyChecked]); // eslint-disable-line

  // Load website versions on project mount
  useEffect(() => {
    if (!project?.id) return;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/versions`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : [])
      .then(d => setVersions(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, [project?.id]); // eslint-disable-line

  // Load cached crawler results + website content on project mount
  useEffect(() => {
    if (!project?.lead_id) return;
    let cancelled = false;
    const h = { Authorization: `Bearer ${token}` };

    // 1. Crawler status + results from crawl_jobs / crawl_results
    fetch(`${API_BASE_URL}/api/crawler/status/${project.lead_id}`, { headers: h })
      .then(r => r.ok ? r.json() : null)
      .then(status => {
        if (cancelled || !status) return;
        if (status.status && status.status !== 'none') setCrawlJob(status);
        // Load URL list if a completed job exists
        if (status.status === 'completed' || status.total_urls > 0) {
          return fetch(`${API_BASE_URL}/api/crawler/results/${project.lead_id}`, { headers: h })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
              if (cancelled || !d) return;
              setCrawlResults(Array.isArray(d.results) ? d.results : []);
            });
        }
      })
      .catch(() => {});

    // 2. Website content from website_content_cache
    fetch(`${API_BASE_URL}/api/crawler/content/${project.lead_id}`, { headers: h })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (cancelled || !data) return;
        const items = Array.isArray(data) ? data : (data.results || []);
        if (items.length > 0) setWebsiteContent(items);
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [project?.lead_id]); // eslint-disable-line

  const loadWebsiteContent = useCallback(async () => {
    if (!project?.lead_id) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/crawler/content/${project.lead_id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setWebsiteContent(Array.isArray(data) ? data : data.results || []);
      }
    } catch (e) { console.error(e); }
  }, [project?.lead_id]); // eslint-disable-line

  const scrapeContent = async () => {
    if (!project?.lead_id) return;
    setContentLoading(true);
    try {
      // Scrape all crawler-recognised pages (text, images, files)
      await fetch(
        `${API_BASE_URL}/api/crawler/scrape-content/${project.lead_id}`,
        { method: 'POST', headers: { Authorization: `Bearer ${token}` } }
      );
      await loadWebsiteContent();
      toast.success('Website-Inhalte von allen Seiten importiert');
    } catch (e) { toast.error('Scraping fehlgeschlagen — bitte Website-URL prüfen'); }
    finally { setContentLoading(false); }
  };

  const loadBriefingLead = useCallback(async () => {
    if (!project?.lead_id || briefingLead) return;
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/leads/${project.lead_id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setBriefingLead(await res.json());
    } catch (e) { console.error(e); }
  }, [project?.lead_id, briefingLead]); // eslint-disable-line

  // Auto-load briefing lead when briefing tab is opened
  useEffect(() => {
    if (activeTab === 'briefing' && !briefingLead && project?.lead_id) {
      loadBriefingLead();
    }
  }, [activeTab, briefingLead, project?.lead_id, loadBriefingLead]); // eslint-disable-line

  // Auto-load brand data when branddesign tab is opened
  useEffect(() => {
    if (activeTab === 'branddesign' && !brandData && project?.lead_id) {
      loadBrandData();
    }
  }, [activeTab, brandData, project?.lead_id]); // eslint-disable-line

  // Auto-load briefing data on project load
  useEffect(() => {
    if (!project?.lead_id) return;
    fetch(`${API_BASE_URL}/api/briefings/${project.lead_id}`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setBriefingData(d); })
      .catch(() => {});
  }, [project?.lead_id]); // eslint-disable-line

  // Auto-load latestAudit on project load
  useEffect(() => {
    if (!project?.lead_id) return;
    fetch(`${API_BASE_URL}/api/leads/${project.lead_id}/profile`, { headers })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setLatestAudit((d.audits || [])[0] || false); })
      .catch(() => {});
  }, [project?.lead_id]); // eslint-disable-line

  // Auto-load sitemap on project load (needed for ProzessFlow step completion)
  useEffect(() => {
    if (!project?.lead_id || sitemapLoaded) return;
    loadSitemapPages();
  }, [project?.lead_id]); // eslint-disable-line

  // Auto-load brand data on project load (needed for ProzessFlow step 3 completion)
  useEffect(() => {
    if (!project?.lead_id || brandData) return;
    loadBrandData();
  }, [project?.lead_id]); // eslint-disable-line

  // Set initial tab on project load
  useEffect(() => {
    if (project) {
      setActiveTab('overview');
      setActiveSubTab('unternehmen');
    }
  }, [project?.id]); // eslint-disable-line

  if (loading || !project) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="skeleton" style={{ height: 11, width: 120, borderRadius: 4 }} />
            <div className="skeleton" style={{ height: 28, width: 260, borderRadius: 6 }} />
          </div>
          <div className="skeleton" style={{ height: 36, width: 100, borderRadius: 'var(--radius-md)' }} />
        </div>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
          <div style={{ display: 'flex', gap: 8, padding: '12px 16px', borderBottom: '1px solid var(--border-light)' }}>
            {[1,2,3,4,5,6,7,8].map(i => (
              <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5 }}>
                <div className="skeleton" style={{ width: 20, height: 20, borderRadius: '50%' }} />
                <div className="skeleton" style={{ height: 9, width: '80%', borderRadius: 3 }} />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, padding: '12px 16px', overflowX: 'hidden' }}>
            {[1,2,3,4,5].map(i => (
              <div key={i} style={{ flex: '0 0 140px', height: 80, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', padding: 10, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <div className="skeleton" style={{ width: 32, height: 32, borderRadius: 'var(--radius-sm)' }} />
                <div className="skeleton" style={{ height: 10, width: '80%', borderRadius: 3 }} />
              </div>
            ))}
          </div>
        </div>
        <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="skeleton" style={{ height: 16, width: '40%', borderRadius: 4 }} />
          {[1,2,3].map(i => (<div key={i} className="skeleton" style={{ height: 12, width: `${70 + i * 8}%`, borderRadius: 3 }} />))}
        </div>
      </div>
    );
  }

  const h = { 'Content-Type': 'application/json', ...headers };

  const loadSitemapPages = async () => {
    if (!project?.lead_id) return;
    setSitemapLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}`, { headers: h });
      if (res.ok) {
        const pages = await res.json();
        setSitemapPages(pages);
        setSitemapLoaded(true);
        if (!selectedPageId && pages.length > 0) {
          const contentPages = pages.filter(p => !p.ist_pflichtseite);
          const start = contentPages.find(p => p.page_type === 'startseite') || contentPages[0];
          if (start) setSelectedPageId(start.id);
        }
      }
    } catch { /* silent */ }
    finally { setSitemapLoading(false); }
  };

  const downloadSitemapPdf = async () => {
    if (!project?.lead_id) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/pdf`, { headers });
      if (!res.ok) throw new Error('PDF konnte nicht geladen werden');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'sitemap.pdf'; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { toast.error('PDF Fehler: ' + e.message); }
  };

  const saveOrder = async (reorderedPages) => {
    try {
      // Backend erwartet List[ReorderItem] = [{id, position, parent_id}, ...]
      // (siehe routers/sitemap.py::reorder_pages), nicht {page_ids: [...]}.
      const payload = reorderedPages.map((p, idx) => ({
        id: p.id,
        position: idx,
        parent_id: p.parent_id || null,
      }));
      await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
    } catch (e) { console.error(e); }
  };

  const movePageUp = (pageId) => {
    const nonPflicht = sitemapPages.filter(p => !p.ist_pflichtseite);
    const idx = nonPflicht.findIndex(p => p.id === pageId);
    if (idx <= 0) return;
    const reordered = [...nonPflicht];
    [reordered[idx - 1], reordered[idx]] = [reordered[idx], reordered[idx - 1]];
    const pflicht = sitemapPages.filter(p => p.ist_pflichtseite);
    const merged = [...reordered, ...pflicht];
    setSitemapPages(merged);
    saveOrder(merged);
  };

  const movePageDown = (pageId) => {
    const nonPflicht = sitemapPages.filter(p => !p.ist_pflichtseite);
    const idx = nonPflicht.findIndex(p => p.id === pageId);
    if (idx >= nonPflicht.length - 1) return;
    const reordered = [...nonPflicht];
    [reordered[idx], reordered[idx + 1]] = [reordered[idx + 1], reordered[idx]];
    const pflicht = sitemapPages.filter(p => p.ist_pflichtseite);
    const merged = [...reordered, ...pflicht];
    setSitemapPages(merged);
    saveOrder(merged);
  };

  const onDragStart = (e, pageId) => {
    setDraggedPageId(pageId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const onDragOver = (e, pageId) => {
    e.preventDefault();
    setDragOverPageId(pageId);
  };

  const onDrop = (e, targetPageId) => {
    e.preventDefault();
    if (!draggedPageId || draggedPageId === targetPageId) {
      setDraggedPageId(null); setDragOverPageId(null); return;
    }
    const reordered = [...sitemapPages];
    const fromIdx = reordered.findIndex(p => p.id === draggedPageId);
    const toIdx   = reordered.findIndex(p => p.id === targetPageId);
    const [moved] = reordered.splice(fromIdx, 1);
    reordered.splice(toIdx, 0, moved);
    setSitemapPages(reordered);
    saveOrder(reordered);
    setDraggedPageId(null); setDragOverPageId(null);
  };

  const onDragEnd = () => {
    setDraggedPageId(null); setDragOverPageId(null);
  };

  const deleteSitemapPage = async (pageId) => {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/sitemap/pages/${pageId}`,
        { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setSitemapPages(prev => prev.filter(p => p.id !== pageId));
        toast.success('Seite gelöscht');
      } else {
        toast.error('Löschen fehlgeschlagen');
      }
    } catch (e) {
      toast.error(parseApiError(e));
    } finally {
      setDeletingPageId(null);
    }
  };

  const generateKI = async () => {
    setKiConfirm(false); setKiGenerating(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/generate`, { method: 'POST', headers: h });
      if (res.ok) { const d = await res.json(); setSitemapPages(d.pages || []); setSelectedPageId(null); }
    } catch { /* silent */ }
    finally { setKiGenerating(false); }
  };

  const createSitemapPage = async () => {
    if (!addPageForm.page_name.trim()) return;
    setAddPageSaving(true);
    try {
      const body = { page_name: addPageForm.page_name, page_type: addPageForm.page_type, parent_id: addPageForm.parent_id ? Number(addPageForm.parent_id) : null, position: sitemapPages.filter(p => !p.ist_pflichtseite).length };
      const res = await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/pages`, { method: 'POST', headers: h, body: JSON.stringify(body) });
      if (res.ok) { const page = await res.json(); setSitemapPages(prev => [...prev, page]); setAddPageForm({ page_name: '', page_type: 'info', parent_id: '' }); setAddPageOpen(false); }
    } catch { /* silent */ }
    finally { setAddPageSaving(false); }
  };

  const saveEditPage = async () => {
    if (!editPageModal) return;
    setEditPageSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/sitemap/pages/${editPageModal.id}`, { method: 'PUT', headers: h, body: JSON.stringify(editPageForm) });
      if (res.ok) { const updated = await res.json(); setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p)); setEditPageModal(null); }
    } catch { /* silent */ }
    finally { setEditPageSaving(false); }
  };

  const loadLatestAudit = async () => {
    if (!project?.lead_id || latestAudit !== null) return;
    try {
      const res = await fetch(`${API_BASE_URL}/api/leads/${project.lead_id}/profile`, { headers });
      if (res.ok) {
        const data = await res.json();
        setLatestAudit((data.audits || [])[0] || false);
      }
    } catch { /* silent */ }
  };

  const loadBrandData = async () => {
    if (!project?.lead_id) return;
    const res = await fetch(`${API_BASE_URL}/api/branddesign/${project.lead_id}`, { headers });
    if (res.ok) setBrandData(await res.json());
  };

  const loadPageContext = async () => {
    const leadId = project?.lead_id;
    if (!leadId) return {};
    const [audits, pagespeed, crawler, briefing] = await Promise.allSettled([
      fetch(`${API_BASE_URL}/api/audit/lead/${leadId}`, { headers }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/leads/${leadId}/pagespeed`, { headers }).then(r => r.json()),
      // Bug 2: Der alte /api/crawler/{id}-Endpoint existiert nicht (404).
      // /content/{id} liefert ein flaches Array [{url, title, h1, ...}]
      // mit echten Page-Titles aus dem website_content_cache.
      fetch(`${API_BASE_URL}/api/crawler/content/${leadId}`, { headers }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/briefings/${leadId}`, { headers }).then(r => r.json()),
    ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : null));
    const latestAudit = Array.isArray(audits) ? audits[0] : null;
    return {
      audit_score: latestAudit?.total_score || null,
      // Bug 1: Audit-Response feldname ist top_issues, nicht top_problems.
      audit_problems: latestAudit?.top_issues || [],
      pagespeed_mobile: pagespeed?.mobile_score || null,
      crawler_pages: Array.isArray(crawler) ? crawler.length : 0,
      crawler_titles: Array.isArray(crawler)
        ? crawler.slice(0, 5).map(p => p.title || p.h1 || p.url).filter(Boolean)
        : [],
      briefing_usp: typeof briefing?.usp === 'string' ? briefing.usp : '',
      briefing_leistungen: typeof briefing?.leistungen === 'string' ? briefing.leistungen : '',
      briefing_zielgruppe: typeof briefing?.zielgruppe === 'string' ? briefing.zielgruppe : '',
    };
  };

  const generateDesign = async () => {
    setDesignRunning(true);
    setDesignSlow(false);
    setDesignError('');
    setDesignResult(null);
    const slowTimer = setTimeout(() => setDesignSlow(true), 20000);
    try {
      const bRes = await fetch(`${API_BASE_URL}/api/briefings/${project.lead_id}`, { headers });
      const briefing = bRes.ok ? await bRes.json() : null;
      const selectedPage = sitemapPages.find(p => p.id === selectedPageId) || null;
      const ctx = await loadPageContext();

      const city = briefing?.einzugsgebiet || project.city || '';
      const trade = briefing?.gewerk || project.trade || project.industry || '';

      // Bug 3: services-Fallback greift auch bei leerem Array/leerem String —
      // vorher nur bei null/undefined, was '' und [] durchrutschen liess.
      const rawLeistungen = briefing?.leistungen;
      const serviceList = Array.isArray(rawLeistungen)
        ? rawLeistungen.map(String).filter(Boolean)
        : typeof rawLeistungen === 'string' && rawLeistungen.trim()
          ? rawLeistungen.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
          : [];
      const services = serviceList.length > 0
        ? serviceList
        : [trade || 'Handwerk'].filter(Boolean);

      // Bug 2: zielgruppe kann ein Objekt (Legacy-JSON-Sektion) sein —
      // String({...}) -> "[object Object]". Analyse-Feld rausziehen.
      const extractZielgruppe = (z) => {
        if (!z) return '';
        if (typeof z === 'string') return z === '{}' ? '' : z;
        if (typeof z === 'object') {
          return z.analyse || z.beschreibung || z.text || '';
        }
        return '';
      };
      const audience = extractZielgruppe(briefing?.zielgruppe)
        || (city ? `Kunden in ${city}` : 'Lokale Kunden');

      const payload = {
        // Bug 5: lead_id muss mit, sonst greift der Backend-Autofill nicht.
        lead_id: project?.lead_id || null,
        company_name: String(project.company_name || ''),
        city: String(city),
        trade: String(trade),
        usp: String(briefing?.usp || ''),
        services,
        target_audience: audience,
        page_name: String(selectedPage?.page_name || 'Startseite'),
        zweck: String(selectedPage?.zweck || ''),
        ziel_keyword: String(selectedPage?.ziel_keyword || ''),
        cta_text: String(selectedPage?.cta_text || ''),
        ...ctx,
      };
      console.log('Design payload:', JSON.stringify(payload, null, 2));

      // Start background job — returns immediately with job_id
      const startRes = await fetch(`${API_BASE_URL}/api/agents/${project.id}/content`, {
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

      if (selectedPage && result) {
        const designHtml = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
        fetch(`${API_BASE_URL}/api/sitemap/pages/${selectedPage.id}`, {
          method: 'PUT', headers: h,
          body: JSON.stringify({ ...selectedPage, mockup_html: designHtml }),
        }).catch(() => {});
      }
    } catch (e) {
      setDesignError(e?.message || e?.detail || String(e) || 'Generierung fehlgeschlagen.');
    } finally {
      clearTimeout(slowTimer);
      setDesignRunning(false);
      setDesignSlow(false);
    }
  };

  // ── QA Helpers ───────────────────────────────────────────────────────────
  const statusFarbe = (status) => ({
    bestanden: '#1D9E75',
    warnung:   '#BA7517',
    kritisch:  '#E24B4A',
  }[status] || '#94a3b8');

  const checkIcon  = (val) => val ? '✓' : '✗';
  const checkColor = (val) => val ? '#1D9E75' : '#E24B4A';

  const QA_CHECK_LABELS = {
    ssl_aktiv:           'SSL-Zertifikat',
    https_redirect:      'HTTPS-Weiterleitung',
    favicon_vorhanden:   'Favicon vorhanden',
    robots_txt:          'robots.txt vorhanden',
    sitemap_xml:         'sitemap.xml vorhanden',
    title_vorhanden:     'Title-Tag vorhanden',
    title_laenge_ok:     'Title-Länge (10–65 Zeichen)',
    meta_desc_vorhanden: 'Meta-Description vorhanden',
    meta_desc_laenge_ok: 'Meta-Desc Länge (50–160 Zeichen)',
    h1_genau_eins:       'Genau ein H1-Tag',
    h2_vorhanden:        'H2-Tags vorhanden',
    canonical_vorhanden: 'Canonical-Tag vorhanden',
    og_tags_vorhanden:   'Open Graph Tags',
    schema_markup:       'Schema Markup (JSON-LD)',
    schema_localbusiness:'LocalBusiness Schema',
    schema_faq:          'FAQ Schema',
    mobile_viewport:     'Mobile Viewport',
    alt_texte_ok:        'Alt-Texte (≥80% der Bilder)',
    kontaktformular:     'Kontaktformular vorhanden',
    telefon_link:        'Telefon als tel:-Link',
    mailto_link:         'E-Mail als mailto:-Link',
    google_fonts_extern: 'Google Fonts NICHT extern',
    google_maps:         'Google Maps eingebettet',
    impressum_link:      'Impressum verlinkt',
    datenschutz_link:    'Datenschutz verlinkt',
    cookie_banner:       'Cookie-Consent-Banner',
    dsgvo_checkbox:      'DSGVO-Checkbox in Formular',
    hsts:                'HSTS Security Header',
    csp:                 'Content Security Policy',
    cache_control:       'Cache-Control Header',
    llm_txt:             'llm.txt vorhanden',
    faq_block:           'FAQ / Akkordeon vorhanden',
    footer_timestamp:    'Aktualisierungsdatum im Footer',
  };
  // Keys where true = bad (inverted logic)
  const QA_INVERTED = new Set(['google_fonts_extern']);

  const scoreColor = (s) =>
    s >= 80 ? '#1D9E75' : s >= 60 ? '#BA7517' : '#E24B4A';
  const scoreBg = (s) =>
    s >= 80 ? '#E1F5EE' : s >= 60 ? '#FFF7ED' : '#FFF1F1';
  const scoreBorder = (s) =>
    s >= 80 ? '#1D9E75' : s >= 60 ? '#BA7517' : '#E24B4A';

  const LST = {
    display: 'block', fontSize: 11, fontWeight: 600,
    color: '#64748b', textTransform: 'uppercase',
    letterSpacing: '.06em', marginBottom: 5,
  };
  const INP = {
    width: '100%', padding: '9px 12px',
    border: '1.5px solid var(--border-light)',
    borderRadius: 8, fontSize: 13,
    fontFamily: 'inherit', color: 'var(--text-primary)',
    background: 'var(--bg-app)',
    boxSizing: 'border-box', outline: 'none',
    marginBottom: 0,
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ marginBottom: 0 }}>
          <span>Projekt #{project.id}</span>
          <h1 style={{ fontSize: 'var(--kc-text-3xl)', margin: 0 }}>{project.company_name}</h1>
        </div>
        {margin && <MarginBadge marginPercent={margin.margin_percent} status={margin.status} />}
      </div>

      {/* ── ProjectCard ─────────────────────────────────────────────────────── */}
      <ProjectCard project={project} onDomainCheck={checkDomain} domainChecking={domainChecking} />

      {/* ── Projekt-Uebersicht — Status + Marge ── */}
      {project && (() => {
        const phaseNum  = parseInt((project.status || '').replace('phase_', '')) || 1;
        const phaseName = ['Onboarding','Briefing','Content','Technik','Go Live','QM','Post-Launch','Fertig'][phaseNum - 1] || 'Onboarding';
        const statusColor = project.status?.includes('abgeschlossen')
          ? { bg: '#f3f4f6', text: '#6b7280' }
          : project.status?.includes('pausiert')
          ? { bg: '#fef3c7', text: '#92400e' }
          : { bg: '#dcfce7', text: '#166534' };
        const statusLabel = project.status?.includes('abgeschlossen') ? 'Abgeschlossen'
          : project.status?.includes('pausiert') ? 'Pausiert' : 'Aktiv';
        const marginPct   = margin?.margin_percent ?? null;
        const marginColor = marginPct === null ? 'var(--text-tertiary)'
          : marginPct < 30 ? '#E24B4A' : marginPct < 50 ? '#BA7517' : '#1D9E75';

        return (
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
            {/* Status */}
            <div style={{ flex: '1 1 220px', padding: '12px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700, background: statusColor.bg, color: statusColor.text }}>
                  {statusLabel}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  Phase {phaseNum}/7 {phaseName}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-tertiary)' }}>
                <span>Start: {project.start_date ? new Date(project.start_date).toLocaleDateString('de-DE') : '\u2013'}</span>
                <span>Go-Live: {project.target_go_live || project.go_live_date ? new Date(project.target_go_live || project.go_live_date).toLocaleDateString('de-DE') : '\u2013'}</span>
              </div>
            </div>
            {/* Marge */}
            <div style={{ flex: '1 1 220px', padding: '12px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ display: 'flex', gap: 20, alignItems: 'baseline' }}>
                <div>
                  <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>Fixpreis</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{(project.fixed_price || 0).toFixed(0)}</div>
                </div>
                <div>
                  <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>Stunden</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{(project.actual_hours || 0).toFixed(1)}h</div>
                </div>
                <div>
                  <div style={{ fontSize: 9, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>Marge</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: marginColor, fontVariantNumeric: 'tabular-nums' }}>{marginPct !== null ? `${marginPct.toFixed(0)}%` : '\u2013'}</div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* ── Buttons ─────────────────────────────────────────────────────────── */}
      {(() => {
        const btnBase = {
          flex: 1, minWidth: 120, padding: '8px 10px', fontSize: 12,
          fontWeight: 500, borderRadius: 'var(--radius-md)', cursor: 'pointer',
          border: '1px solid var(--border-light)', background: 'var(--bg-surface)',
          color: 'var(--text-primary)', display: 'flex', alignItems: 'center',
          gap: 5, justifyContent: 'center', fontFamily: 'var(--font-sans)',
        };
        const btnApproval = {
          ...btnBase, background: 'var(--brand-primary)', color: '#fff', border: 'none',
        };
        return (
          <div style={{ display: 'flex', flexDirection: 'row', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
            {project.lead_id && (
              <button onClick={() => navigate(`/app/leads/${project.lead_id}`)} style={btnBase}>👤 Zur Kundenkartei</button>
            )}
            <button onClick={() => { loadLatestAudit(); setShowEdit(true); }} style={btnBase}>✏️ Projektdaten bearbeiten</button>
            {isAdmin && (
              <button onClick={() => setShowApproval(true)} style={btnApproval}>🖊️ Freigabe anfordern</button>
            )}
          </div>
        );
      })()}

      {/* ── ProzessFlow ─────────────────────────────────────────────────────── */}
      <ProzessFlow
        project={project}
        lead={lead || briefingLead}
        token={token}
        briefing={briefingData}
        latestAudit={latestAudit}
        onAuditUpdate={setLatestAudit}
        onSitemapReload={loadSitemapPages}
        onBrandUpdate={setBrandData}
        onCrawlUpdate={(count) => setCrawlResults(prev => prev.length >= count ? prev : Array(count).fill({}))}
        crawlPages={crawlResults?.length || 0}
        sitemapPages={sitemapPages}
        sitemapLoading={sitemapLoading}
        websiteContent={websiteContent}
        brandData={brandData}
        netlify={netlify}
        qaResult={qaResult}
      />

      {/* ── Nachrichten Modal ───────────────────────────────────────────────── */}
      {showNewMessageModal && createPortal(
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.5)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
          onClick={() => setShowNewMessageModal(false)}>
          <div onClick={e => e.stopPropagation()} style={{ background: 'var(--bg-surface)', borderRadius: 'var(--radius-xl)', padding: 28, maxWidth: 420, width: '100%', boxShadow: 'var(--shadow-xl)' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>💬 Nachricht schreiben</div>
            <textarea
              value={newMessageText}
              onChange={e => setNewMessageText(e.target.value)}
              placeholder="Nachricht eingeben..."
              style={{ width: '100%', minHeight: 100, padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', resize: 'vertical', boxSizing: 'border-box', outline: 'none' }}
            />
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <button onClick={() => setShowNewMessageModal(false)} style={{ flex: 1, padding: '10px 0', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', color: 'var(--text-primary)' }}>
                Abbrechen
              </button>
              <button disabled style={{ flex: 1, padding: '10px 0', background: 'var(--border-medium)', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'not-allowed', fontFamily: 'var(--font-sans)', color: 'var(--text-tertiary)' }}>
                Senden (bald verfügbar)
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* ── Briefing Wizard ─────────────────────────────────────────────────── */}
      {showBriefingWizard && (
        <Suspense fallback={<TabFallback />}><BriefingWizard
          leadId={project.lead_id}
          leadData={briefingData}
          onClose={() => setShowBriefingWizard(false)}
          onComplete={() => setShowBriefingWizard(false)}
        /></Suspense>
      )}

      {/* ── Content Manager ─────────────────────────────────────────────────── */}
      {showContentManager && project.lead_id && (
        <Suspense fallback={<TabFallback />}><ContentManager
          leadId={project.lead_id}
          leadName={project.company_name}
          token={token}
          onClose={() => { setShowContentManager(false); setContentSummary([]); }}
        /></Suspense>
      )}

      {/* ── GrapesJS Editor ─────────────────────────────────────────────────── */}
      {editingPage && (
        <Suspense fallback={<TabFallback />}><GrapesEditor
          key={editingPage.id}
          pageId={editingPage.id}
          pageName={editingPage.page_name}
          initialHtml={editingPage.gjs_html || editingPage.mockup_html || ''}
          onClose={() => setEditingPage(null)}
          onSave={({ html, css }) => {
            setSitemapPages(prev => prev.map(p =>
              p.id === editingPage.id
                ? { ...p, gjs_html: html, gjs_css: css || '', mockup_html: html }
                : p
            ));
            setEditingPage(null);
            toast.success(`"${editingPage.page_name}" gespeichert`);
          }}
          projectId={project.id}
          netlitySiteId={project.netlify_site_id || null}
          leadId={project.lead_id}
        /></Suspense>
      )}
    </div>
  );
}

// ── InfoBlock ─────────────────────────────────────────────────────────────────
function InfoBlock({ label, value, mono = false, raw = false }) {
  return (
    <div>
      <p style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 'var(--kc-tracking-wide)', color: 'var(--text-tertiary)', marginBottom: 4 }}>
        {label}
      </p>
      {raw ? (
        <div>{value}</div>
      ) : (
        <p style={{ fontSize: 16, fontWeight: 700, fontFamily: mono ? 'var(--font-mono)' : 'var(--font-sans)', color: 'var(--text-primary)', margin: 0 }}>
          {value}
        </p>
      )}
    </div>
  );
}
