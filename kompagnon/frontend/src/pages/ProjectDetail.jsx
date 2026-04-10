import React, { useEffect, useState, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import toast from 'react-hot-toast';
import PhaseTracker from '../components/PhaseTracker';
import MarginBadge from '../components/MarginBadge';
import ProjectCard from '../components/ProjectCard';
import BriefingTab from '../components/BriefingTab';
import BriefingWizard from '../components/BriefingWizard';
import WZSearch from '../components/WZSearch';
import ProjectFilesSection from '../components/ProjectFilesSection';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import PageSpeedSection from '../components/PageSpeedSection';
import SitemapPlaner from '../components/SitemapPlaner';
import GrapesEditor from '../components/GrapesEditor';
import KiReportPanel from '../components/KiReportPanel';
import MoodboardPanel from '../components/MoodboardPanel';
import { useEscapeKey } from '../hooks/useKeyboardShortcuts';
import { parseApiError } from '../utils/apiError';
import WebsiteDesigner from '../components/WebsiteDesigner';
import ContentManager from '../components/ContentManager';
import AuditReport from '../components/AuditReport';
import QAChecklist from '../components/QAChecklist';
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

import API_BASE_URL from '../config';

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

const PHASE_TOOLS = {
  'onboarding': [
    { id: 'null-uebersicht', label: 'Null-Übersicht',       icon: '📊', sub: 'Status · Marge · Nachrichten' },
    { id: 'audits',          label: 'Audit',                icon: '🔍', sub: 'Bericht' },
    { id: 'unternehmen',     label: 'Briefing Unternehmen', icon: '🏢', sub: 'Stammdaten' },
    { id: 'briefing',        label: 'Briefing Website',     icon: '📋', sub: 'Fragenkatalog' },
    { id: 'crawler',         label: 'Crawler',              icon: '🕷️', sub: 'URLs erfasst' },
    { id: 'website-content', label: 'Website-Content',      icon: '🌐', sub: '50 Seiten', badge: '!' },
    { id: 'hosting',         label: 'Hosting-Crawling',     icon: '🖥️', sub: 'Scan' },
    { id: 'hosting-form',    label: 'Hosting-Fragebogen',   icon: '📋', sub: 'Fragebogen' },
    { id: 'zugangsdaten',    label: 'Zugangsdaten',         icon: '🔑', sub: 'Safe' },
    { id: 'branddesign',     label: 'Brand-Design-PDF',     icon: '🎨', sub: 'Dreiseitig' },
    { id: 'pagespeed',       label: 'Page-Speed',           icon: '⚡', sub: 'Score' },
  ],
  'briefing': [
    { id: 'ki-report',       label: 'Report erstellen',     icon: '🤖', sub: 'KI-Analyse' },
  ],
  'content': [
    { id: 'moodboard',       label: 'Moodboard',            icon: '🎨', sub: 'Stilrichtung' },
    { id: 'design',          label: 'Design',               icon: '✏️', sub: 'Entwürfe' },
    { id: 'content',         label: 'Content neu',          icon: '📝', sub: 'Texte & Medien' },
    { id: 'sitemap',         label: 'Website neu',          icon: '🗺️', sub: 'Seitenstruktur' },
    { id: 'preview',         label: 'Vorschau',             icon: '👁',  sub: 'Vorschau' },
    { id: 'editor',          label: 'Editor',               icon: '🖊️', sub: 'GrapesJS' },
  ],
  'technik': [
    { id: 'netlify-dns',     label: 'Netlify / WP',         icon: '🚀', sub: 'Installieren' },
    { id: 'dns',             label: 'DNS-Einstellungen',    icon: '🌍', sub: 'Beim Kunden' },
    { id: 'qa',              label: 'QA-Checkliste',        icon: '✓',  sub: 'Go-Live-Check' },
  ],
  'go-live': [
    { id: 'checklists',      label: 'Go-Live',              icon: '🚀', sub: 'Checkliste' },
    { id: 'golive',          label: 'Abnahme & Vergleich',  icon: '✅', sub: 'Vorher/Nachher' },
  ],
  'qm': [
    { id: 'checklists',      label: 'Checkliste QM',        icon: '✅', sub: 'QA-Prüfung' },
    { id: 'qa-scan',         label: 'KI-QA-Scan',           icon: '🤖', sub: 'Qualitätsprüfung' },
  ],
  'post-launch': [
    { id: 'trustpilot',      label: 'Trustpilot',           icon: '⭐', sub: 'Bewertungen' },
    { id: 'postlaunch',      label: 'Post-Launch',          icon: '📈', sub: 'QR + GBP' },
  ],
  'fertig': [
    { id: 'live-data',          label: 'Fertige Website',   icon: '🌐', sub: 'Live' },
    { id: 'upsell',             label: 'Up-Sales',          icon: '💼', sub: 'Upsell-Produkte' },
    { id: 'website-vergleich',  label: 'Website-Vergleich', icon: '📸', sub: 'Vorher/Nachher' },
  ],
};
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
      toast.success('Projektdaten gespeichert');
      onSaved();
    } catch {
      toast.error('Speichern fehlgeschlagen');
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
  const headers          = token ? { Authorization: `Bearer ${token}` } : {};
  const hdr              = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` };
  const isAdmin          = user?.role === 'admin';

  const [project, setProject]         = useState(null);
  const [lead, setLead]               = useState(null);
  const [margin, setMargin]           = useState(null);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState('overview');
  const [activePhase, setActivePhase] = useState('onboarding');
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
  const [showSitemapPlaner, setShowSitemapPlaner] = useState(false);
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
  const [scraping, setScraping]     = useState(false);
  const [analyzing, setAnalyzing]   = useState(false);
  // Design versions
  const [designVersions, setDesignVersions]       = useState([]);
  const [designVersionsLoaded, setDesignVersionsLoaded] = useState(false);
  // Hosting-Analyse
  const [hostingData, setHostingData]       = useState(null);
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
  const [deployHtml, setDeployHtml] = useState('');
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
      // Auto domain-check im Hintergrund
      fetch(`${API_BASE_URL}/api/projects/${id}/domain-check`, { method: 'POST', headers })
        .then(r => r.ok ? r.json() : null)
        .then(d => { if (d) setProject(prev => ({ ...prev, domain_reachable: d.reachable, domain_status_code: d.status_code, domain_checked_at: d.checked_at })); })
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

  useEffect(() => { loadQa(); }, [id]); // eslint-disable-line

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

  useEffect(() => { if (project?.lead_id) loadAudits(); }, [project?.lead_id]); // eslint-disable-line

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

  // Load Netlify status ONCE when tab opens — avoids infinite render loop
  useEffect(() => {
    if (!project?.id) return;
    if (activeSubTab !== 'netlify-dns' && activeTab !== 'netlify-dns') return;
    if (netlify || netlifyLoading) return;
    setNetlifyLoading(true);
    let cancelled = false;
    fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (cancelled) return;
        // Always set — even empty result — to prevent re-trigger loop
        setNetlify(d || { connected: false, status: 'not_connected' });
        setNetlifyLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setNetlify({ connected: false, status: 'error' });
        setNetlifyLoading(false);
      });
    return () => { cancelled = true; };
  }, [project?.id, activeSubTab, activeTab]); // eslint-disable-line

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
      toast.success('Content von allen Seiten gescrapt!');
    } catch (e) { toast.error('Scraping fehlgeschlagen'); }
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

  // Sync activePhase from project status on load
  useEffect(() => {
    if (project) {
      // Map numeric phase status → string phase name
      const phaseNum = parseInt((project.status || '').replace('phase_', '')) || 1;
      const phaseName = PHASE_NAMES[phaseNum - 1] || 'onboarding';
      setActivePhase(phaseName);
      const firstTool = PHASE_TOOLS[phaseName]?.[0]?.id || 'overview';
      setActiveTab(SUB_TAB_MAP[firstTool] || firstTool);
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
      await fetch(`${API_BASE_URL}/api/sitemap/${project.lead_id}/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ page_ids: reorderedPages.map(p => p.id) }),
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
      fetch(`${API_BASE_URL}/api/crawler/${leadId}`, { headers }).then(r => r.json()),
      fetch(`${API_BASE_URL}/api/briefings/${leadId}`, { headers }).then(r => r.json()),
    ]).then(results => results.map(r => r.status === 'fulfilled' ? r.value : null));
    const latestAudit = Array.isArray(audits) ? audits[0] : null;
    return {
      audit_score: latestAudit?.total_score || null,
      audit_problems: latestAudit?.top_problems || [],
      pagespeed_mobile: pagespeed?.mobile_score || null,
      crawler_pages: Array.isArray(crawler) ? crawler.length : 0,
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
      const services = Array.isArray(briefing?.leistungen)
        ? briefing.leistungen.map(String)
        : typeof briefing?.leistungen === 'string'
          ? briefing.leistungen.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
          : (trade ? [trade] : ['Handwerk']);
      const payload = {
        company_name: String(project.company_name || ''),
        city: String(city),
        trade: String(trade),
        usp: String(briefing?.usp || ''),
        services,
        target_audience: String(briefing?.zielgruppe || (city ? `Kunden in ${city}` : 'Lokale Kunden')),
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

      {/* ── Phasen-Navigation (Ebene 1) ─────────────────────────────────────── */}
      <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        {/* Phasenleiste */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', overflowX: 'auto', scrollbarWidth: 'none' }}>
          {PHASE_NAMES.map((phaseName, idx) => {
            const currentNum = parseInt((project.status || '').replace('phase_', '')) || 1;
            const phaseNum   = idx + 1;
            const isDone     = phaseNum < currentNum;
            const isActive   = phaseName === activePhase;
            const isCurrent  = phaseNum === currentNum;
            return (
              <React.Fragment key={phaseName}>
                {idx > 0 && (
                  <div style={{ alignSelf: 'center', height: 1, width: 8, flexShrink: 0, background: isDone ? 'var(--status-success-text)' : 'var(--border-light)', opacity: 0.6 }} />
                )}
                <button onClick={() => {
                  setActivePhase(phaseName);
                  const firstTool = PHASE_TOOLS[phaseName]?.[0]?.id;
                  if (firstTool) setActiveTab(SUB_TAB_MAP[firstTool] || firstTool);
                }} style={{
                  flex: 1, minWidth: 60, padding: '8px 4px 6px', border: 'none',
                  background: 'transparent',
                  cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3,
                  borderRadius: 0, transition: 'background var(--transition-fast)',
                  opacity: isActive ? 1 : 0.65,
                }}>
                  <div style={{
                    width: 20, height: 20, borderRadius: '50%',
                    background: isDone ? 'var(--status-success-text)' : isActive ? 'var(--brand-primary)' : 'var(--border-light)',
                    color: (isDone || isActive) ? 'var(--text-inverse)' : 'var(--text-tertiary)',
                    fontSize: 10, fontWeight: 600,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0,
                  }}>{isDone ? '✓' : phaseNum}</div>
                  <span style={{
                    fontSize: 10,
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                    whiteSpace: 'nowrap',
                  }}>{PHASE_LABELS[phaseName]}</span>
                </button>
              </React.Fragment>
            );
          })}
        </div>

        {/* Werkzeug-Kacheln (Ebene 2) */}
        <div style={{
          position: 'relative', padding: '12px 0 10px',
          borderTop: '2px solid var(--border-light)',
          background: 'var(--bg-app)',
        }}>
          {/* Kontextlabel */}
          <div style={{
            position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
            background: 'var(--bg-app)', padding: '0 10px',
            fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)',
            textTransform: 'uppercase', letterSpacing: '0.08em',
            whiteSpace: 'nowrap', zIndex: 3,
          }}>
            {PHASE_LABELS[activePhase]} — Werkzeuge
          </div>
          {/* Pfeil links */}
          <button onClick={() => scrollRef.current?.scrollBy({ left: -160, behavior: 'smooth' })} style={{
            position: 'absolute', left: 0, top: 0, bottom: 0, width: 32, zIndex: 2,
            background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md) 0 0 var(--radius-md)',
            cursor: 'pointer', fontSize: 18, color: 'var(--text-secondary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>‹</button>

          {/* Scrollbarer Container */}
          <div ref={scrollRef} style={{
            display: 'flex', gap: 8, overflowX: 'auto', scrollBehavior: 'smooth',
            padding: '0 40px', scrollbarWidth: 'none', msOverflowStyle: 'none',
          }}>
            {(PHASE_TOOLS[activePhase] || []).map(tool => {
              const isActive = TOOL_SUBTAB_MAP[tool.id]
                ? activeSubTab === TOOL_SUBTAB_MAP[tool.id]
                : activeTab === (SUB_TAB_MAP[tool.id] || tool.id);
              return (
                <button
                  key={tool.id}
                  onClick={() => {
                    setActiveTab(SUB_TAB_MAP[tool.id] || tool.id);
                    setActiveSubTab(TOOL_SUBTAB_MAP[tool.id] || tool.id);
                    if (tool.id === 'unternehmen') setShowBriefingWizard(true);
                  }}
                  onMouseEnter={e => {
                    if (!isActive) {
                      e.currentTarget.style.borderTopColor = 'var(--border-medium)';
                      e.currentTarget.style.background = 'var(--bg-hover)';
                    }
                  }}
                  onMouseLeave={e => {
                    if (!isActive) {
                      e.currentTarget.style.borderTopColor = 'transparent';
                      e.currentTarget.style.background = 'var(--bg-surface)';
                    }
                  }}
                  style={{
                    flex: '0 0 140px', minWidth: 140, minHeight: 80,
                    background: isActive ? 'var(--brand-primary-light)' : 'var(--bg-surface)',
                    border: '1px solid var(--border-light)',
                    borderTop: isActive ? '3px solid var(--brand-primary)' : '3px solid transparent',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 10px 10px', cursor: 'pointer',
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                    textAlign: 'center',
                    transition: 'border-color var(--transition-fast), background var(--transition-fast)',
                    position: 'relative', fontFamily: 'var(--font-sans)',
                  }}
                >
                  {tool.badge && (
                    <span style={{
                      position: 'absolute', top: 6, right: 6,
                      background: 'var(--status-warning-text)', color: 'white',
                      fontSize: 9, fontWeight: 700, borderRadius: 'var(--radius-full)',
                      padding: '1px 5px', lineHeight: 1.4,
                    }}>{tool.badge}</span>
                  )}
                  <div style={{
                    width: 32, height: 32,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18,
                    background: isActive ? 'var(--brand-primary)' : 'var(--bg-app)',
                    borderRadius: 'var(--radius-sm)', flexShrink: 0,
                    color: isActive ? 'white' : 'var(--text-secondary)',
                    transition: 'background var(--transition-fast), color var(--transition-fast)',
                  }}>{tool.icon}</div>
                  <div style={{
                    fontSize: 11, fontWeight: isActive ? 700 : 500,
                    color: isActive ? 'var(--brand-primary-dark)' : 'var(--text-primary)',
                    lineHeight: 1.3, whiteSpace: 'nowrap', overflow: 'hidden',
                    textOverflow: 'ellipsis', maxWidth: '100%',
                  }}>{tool.label}</div>
                  <div style={{
                    fontSize: 10,
                    color: isActive ? 'var(--brand-primary)' : 'var(--text-tertiary)',
                    lineHeight: 1.2,
                  }}>{tool.sub}</div>
                </button>
              );
            })}
          </div>

          {/* Pfeil rechts */}
          <button onClick={() => scrollRef.current?.scrollBy({ left: 160, behavior: 'smooth' })} style={{
            position: 'absolute', right: 0, top: 0, bottom: 0, width: 32, zIndex: 2,
            background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
            borderRadius: '0 var(--radius-md) var(--radius-md) 0',
            cursor: 'pointer', fontSize: 18, color: 'var(--text-secondary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>›</button>
        </div>
      </div>

      {/* ── Overview Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* ── Briefing Unternehmen ─────────────────────────────────────── */}
          <div className="kc-card">
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>📋 Briefing Unternehmen</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowBriefingWizard(true)}
                style={{ padding: '8px 18px', background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                📋 Briefing ausfüllen / bearbeiten
              </button>
              <span style={{
                padding: '4px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                background: briefingLead ? '#dcfce7' : '#fef3c7',
                color: briefingLead ? '#166534' : '#92400e',
              }}>
                {briefingLead ? '✓ Briefing vorhanden' : '○ Noch nicht ausgefüllt'}
              </span>
            </div>
          </div>

          {/* ── Website-Vergleich — nur in Phase 8 → website-vergleich ── */}
          {activeSubTab === 'website-vergleich' && (() => {
            const phaseNum = parseInt((project.status || '').replace('phase_', '')) || 0;
            const isGoLiveOrLater = phaseNum >= 6;

            const takeBefore = async () => {
              setTakingBefore(true);
              try {
                const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/screenshot/before`, { method: 'POST', headers: h });
                if (res.ok) {
                  const data = await res.json();
                  setScreenshots(s => ({ ...s, before: { data: data.screenshot_url, date: new Date().toISOString(), url: project.website_url } }));
                } else toast.error('Screenshot fehlgeschlagen');
              } catch { toast.error('Screenshot fehlgeschlagen'); }
              finally { setTakingBefore(false); }
            };

            const takeAfter = async () => {
              setTakingAfter(true);
              try {
                const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/screenshot/after`, { method: 'POST', headers: h });
                if (res.ok) {
                  const data = await res.json();
                  const afterUrl = newWebsiteUrl || project.website_url;
                  setScreenshots(s => ({ ...s, after: { data: data.screenshot_url, date: new Date().toISOString(), url: afterUrl } }));
                } else toast.error('Screenshot fehlgeschlagen');
              } catch { toast.error('Screenshot fehlgeschlagen'); }
              finally { setTakingAfter(false); }
            };

            const saveNewUrl = async () => {
              try {
                await fetch(`${API_BASE_URL}/api/projects/${project.id}`, { method: 'PUT', headers: h, body: JSON.stringify({ new_website_url: newWebsiteUrl }) });
                toast.success('URL gespeichert');
              } catch { toast.error('Speichern fehlgeschlagen'); }
            };

            const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : null;

            const Placeholder = ({ icon, text }) => (
              <div style={{ height: 160, background: 'var(--bg-app)', border: '1.5px dashed var(--border-medium)', borderRadius: 8, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                {icon && <span style={{ fontSize: 28 }}>{icon}</span>}
                <span style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'center', padding: '0 16px' }}>{text}</span>
              </div>
            );

            const btnSmall = { padding: '5px 12px', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 5 };
            const Spinner = () => <span style={{ width: 10, height: 10, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />;

            return (
              <div className="kc-card">
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>📸 Website-Vergleich</div>

                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 20 }}>
                  {/* VORHER */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Vorher</span>
                        {screenshots.before?.date && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{fmtDate(screenshots.before.date)}</span>}
                      </div>
                    </div>

                    {screenshots.before?.data
                      ? <img src={screenshots.before.data} alt="Vorher-Screenshot" style={{ width: '100%', borderRadius: 8, border: '2px solid var(--border-light)', display: 'block' }} />
                      : <Placeholder icon={null} text="Noch kein Screenshot" />
                    }

                    {screenshots.before?.url && (
                      <a href={screenshots.before.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 11, color: 'var(--brand-primary)', display: 'block', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {screenshots.before.url}
                      </a>
                    )}

                    <div style={{ marginTop: 10 }}>
                      <button onClick={takeBefore} disabled={takingBefore} style={{ ...btnSmall, background: 'var(--bg-elevated)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)' }}>
                        {takingBefore ? <><Spinner /> Aufnehmen…</> : '📷 Screenshot aufnehmen'}
                      </button>
                    </div>
                  </div>

                  {/* NACHHER */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: '#1D9E75', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Nachher</span>
                        {screenshots.after?.date && <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{fmtDate(screenshots.after.date)}</span>}
                      </div>
                    </div>

                    {screenshots.after?.data
                      ? <img src={screenshots.after.data} alt="Nachher-Screenshot" style={{ width: '100%', borderRadius: 8, border: '2px solid #1D9E75', display: 'block' }} />
                      : <Placeholder icon="🚀" text={isGoLiveOrLater ? 'Noch kein Screenshot' : 'Verfügbar nach Go-Live (Phase 6)'} />
                    }

                    {screenshots.after?.url && (
                      <a href={screenshots.after.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 11, color: '#1D9E75', display: 'block', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {screenshots.after.url}
                      </a>
                    )}

                    {isGoLiveOrLater && (
                      <div style={{ marginTop: 10 }}>
                        <button onClick={takeAfter} disabled={takingAfter} style={{ ...btnSmall, background: '#1D9E75', color: '#fff' }}>
                          {takingAfter ? <><Spinner /> Aufnehmen…</> : '📷 Nachher-Screenshot aufnehmen'}
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Neue Website-URL — ab Phase 5 */}
                {phaseNum >= 5 && (
                  <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
                    <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 6 }}>
                      Neue Website-URL (falls abweichend)
                    </label>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        value={newWebsiteUrl}
                        onChange={e => setNewWebsiteUrl(e.target.value)}
                        placeholder="URL der neuen Website (falls abweichend)"
                        style={{ flex: 1, padding: '7px 10px', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none' }}
                        onKeyDown={e => e.key === 'Enter' && saveNewUrl()}
                      />
                      <button onClick={saveNewUrl} style={{ ...btnSmall, background: 'var(--brand-primary)', color: '#fff' }}>Speichern</button>
                    </div>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* ── Briefing Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'briefing' && (
        briefingLead
          ? <BriefingTab lead={briefingLead} isMobile={isMobile} />
          : <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center',
              justifyContent: 'center', padding: '48px 20px',
              color: 'var(--text-tertiary)',
            }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%',
                border: '2px solid var(--border-light)',
                borderTopColor: 'var(--brand-primary)',
                animation: 'spin 0.8s linear infinite', marginBottom: 12 }} />
              <div style={{ fontSize: 13 }}>Briefing wird geladen...</div>
              {(() => { loadBriefingLead(); return null; })()}
            </div>
      )}

      {/* ── KI-Report Tab ─────────────────────────────────────────────────────── */}
      {(activeSubTab === 'ki-report' || activeTab === 'ki-report') && (
        <KiReportPanel
          projectId={id}
          leadId={project.lead_id}
          token={token}
        />
      )}

      {/* ── Moodboard Tab ─────────────────────────────────────────────────────── */}
      {(activeSubTab === 'moodboard' || activeTab === 'moodboard') && project?.lead_id && (
        <MoodboardPanel
          projectId={id}
          leadId={project.lead_id}
          token={token}
        />
      )}

      {/* ── BrandDesign Tab ─────────────────────────────────────────────────── */}
      {activeTab === 'branddesign' && (() => {
        const lid = project.lead_id;
        if (!brandData) loadBrandData();

        const scrapeWebsite = async () => {
          setScraping(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/scrape`, { method: 'POST', headers: h });
            if (res.ok) setBrandData(await res.json());
            else toast.error('Scraping fehlgeschlagen');
          } catch { toast.error('Scraping fehlgeschlagen'); }
          finally { setScraping(false); }
        };

        const analyzeScreenshot = async () => {
          setAnalyzing(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/analyze-screenshot`, { method: 'POST', headers: h });
            if (res.ok) { setBrandData(d => ({ ...d, ...(res.ok ? {} : {}) })); await loadBrandData(); }
            else { const e = await res.json().catch(() => ({})); toast.error(parseApiError(e)); }
          } catch { toast.error('Analyse fehlgeschlagen'); }
          finally { setAnalyzing(false); }
        };

        const uploadPdf = async (e) => {
          const file = e.target.files?.[0];
          if (!file) return;
          const fd = new FormData(); fd.append('file', file);
          const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/upload-pdf`, { method: 'POST', headers, body: fd });
          if (res.ok) { toast.success('PDF hochgeladen'); await loadBrandData(); }
          else toast.error('PDF-Upload fehlgeschlagen');
          e.target.value = '';
        };

        const downloadPdf = async () => {
          const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/pdf`, { headers });
          if (!res.ok) return toast.error('PDF nicht gefunden');
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a'); a.href = url; a.download = brandData?.pdf_filename || 'brand.pdf'; a.click();
          URL.revokeObjectURL(url);
        };

        const copyColor = (color) => { navigator.clipboard.writeText(color).catch(() => {}); toast.success(`${color} kopiert`); };

        const colors = [
          { key: 'primary_color', label: 'Primär' },
          { key: 'secondary_color', label: 'Sekundär' },
        ];
        const allColors = brandData?.all_colors || [];
        const fonts = brandData?.all_fonts || [];
        const hasBrand = brandData && (brandData.primary_color || brandData.font_primary);

        const btnStyle = (active) => ({
          flex: 1, minWidth: 140, padding: '9px 14px', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)', background: active ? '#008EAA' : 'var(--bg-surface)',
          color: active ? '#fff' : 'var(--text-primary)', fontSize: 13, fontWeight: 500,
          cursor: active ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, opacity: active ? 0.7 : 1,
        });

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* GA-Status Karte */}
            <GaStatusCard leadId={lid} headers={h} API_BASE_URL={API_BASE_URL} />

            {/* Status Banner */}
            <div style={{
              padding: '12px 16px', borderRadius: 'var(--radius-lg)', fontSize: 13,
              background: hasBrand ? '#EAF4E0' : brandData?.scrape_failed ? '#FEF3DC' : 'var(--bg-surface)',
              border: `1px solid ${hasBrand ? '#3B6D11' : brandData?.scrape_failed ? '#BA7517' : 'var(--border-light)'}`,
              color: hasBrand ? '#3B6D11' : brandData?.scrape_failed ? '#BA7517' : 'var(--text-secondary)',
            }}>
              {hasBrand ? `✅ Branddesign geladen — zuletzt aktualisiert: ${brandData.scraped_at || '–'}` :
               brandData?.scrape_failed ? '⚠️ Letzter Scraping-Versuch fehlgeschlagen (403 oder Timeout)' :
               '⬜ Noch keine Markendaten vorhanden — Website scrapen oder Screenshot analysieren'}
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={scrapeWebsite} disabled={scraping} style={btnStyle(scraping)}>
                {scraping ? '⏳ Scraping…' : '🌐 Website scrapen'}
              </button>
              <button onClick={analyzeScreenshot} disabled={analyzing} style={btnStyle(analyzing)}>
                {analyzing ? '⏳ Analysiere…' : '🤖 Screenshot analysieren'}
              </button>
              <label style={{ ...btnStyle(false), cursor: 'pointer' }}>
                📄 PDF hochladen
                <input type="file" accept=".pdf" onChange={uploadPdf} style={{ display: 'none' }} />
              </label>
            </div>

            {/* Color Palette */}
            {allColors.length > 0 && (
              <div className="kc-card">
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>🎨 Farb-Palette</div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                  {allColors.map((color, i) => (
                    <div key={i} title={`${color} – klicken zum Kopieren`} onClick={() => copyColor(color)}
                      style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4, cursor: 'pointer' }}>
                      <div style={{
                        width: 44, height: 44, borderRadius: '50%', background: color,
                        border: '2px solid var(--border-light)', boxShadow: 'var(--shadow-card)',
                        transition: 'transform 0.15s',
                      }}
                        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.15)'}
                        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                      />
                      <span style={{ fontSize: 9, color: 'var(--text-tertiary)', fontFamily: 'monospace' }}>
                        {i === 0 ? 'Primär' : i === 1 ? 'Sekundär' : color}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Fonts */}
            {fonts.length > 0 && (
              <div className="kc-card">
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>🔤 Schriften</div>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                  {fonts.map((font, i) => (
                    <div key={i} style={{
                      padding: '10px 16px', background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)', fontFamily: font,
                    }}>
                      <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4, fontFamily: 'var(--font-sans)' }}>
                        {i === 0 ? 'Primär' : 'Sekundär'}
                      </div>
                      <div style={{ fontSize: 16, fontWeight: 600 }}>{font}</div>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Aa Bb Cc 123</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Design Style + Notes */}
            {(brandData?.design_style || brandData?.brand_notes) && (
              <div className="kc-card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {brandData.design_style && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>Designstil</div>
                    <span style={{
                      display: 'inline-block', padding: '4px 12px', borderRadius: 'var(--radius-full)',
                      background: '#E6F1FB', color: '#185FA5', fontSize: 13, fontWeight: 600,
                    }}>
                      🎭 {brandData.design_style}
                    </span>
                  </div>
                )}
                {brandData.brand_notes && (
                  <div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>KI-Notizen</div>
                    <div style={{
                      padding: '10px 14px', background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6,
                    }}>
                      {brandData.brand_notes}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* PDF */}
            {brandData?.pdf_filename && (
              <div className="kc-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 20 }}>📄</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{brandData.pdf_filename}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Brand Guidelines PDF</div>
                  </div>
                </div>
                <button onClick={downloadPdf} style={{
                  padding: '7px 14px', background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer',
                  fontFamily: 'var(--font-sans)', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6,
                }}>
                  ⬇️ Herunterladen
                </button>
              </div>
            )}

            {/* ── Design-Assets ─────────────────────────────────────────── */}
            <div style={{ marginTop: 8, paddingTop: 16, borderTop: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>🎨 Entdeckte Design-Assets</div>
                <button onClick={() => toast.info('Asset-Scan wird in Kürze verfügbar')} style={{
                  padding: '6px 14px', background: 'var(--bg-elevated)', color: 'var(--text-secondary)',
                  border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                  fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                }}>
                  🔍 Assets scannen
                </button>
              </div>
              {(() => {
                let assets = [];
                try { assets = project.brand_assets ? JSON.parse(project.brand_assets) : []; } catch { assets = []; }
                const typeColor = { Farbe: { bg: '#ede9fe', text: '#5b21b6' }, Logo: { bg: '#dcfce7', text: '#166534' }, Font: { bg: '#fef3c7', text: '#92400e' }, Bild: { bg: '#dbeafe', text: '#1e40af' } };
                if (!assets.length) return (
                  <div style={{ fontSize: 13, color: 'var(--text-tertiary)', fontStyle: 'italic', textAlign: 'center', padding: '20px 0' }}>Noch keine Assets gescrapt</div>
                );
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {assets.map((a, i) => {
                      const tc = typeColor[a.type] || { bg: 'var(--bg-app)', text: 'var(--text-secondary)' };
                      const isHex = /^#[0-9a-fA-F]{3,6}$/.test(a.value);
                      return (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                          <span style={{ padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: tc.bg, color: tc.text, flexShrink: 0 }}>{a.type}</span>
                          {isHex && <div style={{ width: 18, height: 18, borderRadius: 4, background: a.value, border: '1px solid var(--border-light)', flexShrink: 0 }} />}
                          <span style={{ fontSize: 12, color: 'var(--text-primary)', fontFamily: isHex ? 'monospace' : 'inherit' }}>{a.value}</span>
                        </div>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
          </div>
        );
      })()}

      {/* ── Dateien Tab ─────────────────────────────────────────────────────── */}
      {activeTab === 'dateien' && project.lead_id && (
        <ProjectFilesSection leadId={project.lead_id} />
      )}

      {/* ── PageSpeed Tab ───────────────────────────────────────────────────── */}
      {activeTab === 'pagespeed' && project.lead_id && (
        <PageSpeedSection leadId={project.lead_id} />
      )}

      {/* ── Sitemap Tab — vollständiger Sitemap-Manager ───────────────── */}
      {(activeSubTab === 'sitemap' || activeTab === 'sitemap') && project?.lead_id && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* ── HEADER-AKTIONEN ── */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                Website-Seiten
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                {sitemapPages.filter(p => !p.ist_pflichtseite).length} Inhaltsseiten ·{' '}
                {sitemapPages.filter(p => p.ist_pflichtseite).length} Pflichtseiten
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => setKiConfirm(true)}
                disabled={kiGenerating}
                style={{
                  padding: '7px 14px', borderRadius: 8, border: '1px solid var(--border-light)',
                  background: 'var(--bg-surface)', color: 'var(--text-primary)',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                }}
              >
                {kiGenerating ? '⏳ KI generiert…' : '🤖 KI-Sitemap'}
              </button>
              <button
                onClick={() => setAddPageOpen(true)}
                style={{
                  padding: '7px 14px', borderRadius: 8, border: 'none',
                  background: '#008eaa', color: 'white',
                  fontSize: 12, fontWeight: 600, cursor: 'pointer',
                }}
              >
                + Seite hinzufügen
              </button>
            </div>
          </div>

          {/* ── KI-BESTÄTIGUNG ── */}
          {kiConfirm && (
            <div style={{ background: '#fff3cd', border: '1px solid #ffc107', borderRadius: 8, padding: '12px 16px', fontSize: 13 }}>
              ⚠️ KI-Sitemap überschreibt alle bestehenden Seiten. Fortfahren?{' '}
              <button onClick={generateKI} style={{ marginLeft: 12, padding: '4px 12px', background: '#ffc107', border: 'none', borderRadius: 6, fontWeight: 700, cursor: 'pointer' }}>Ja, generieren</button>
              <button onClick={() => setKiConfirm(false)} style={{ marginLeft: 8, padding: '4px 12px', background: 'transparent', border: '1px solid #999', borderRadius: 6, cursor: 'pointer' }}>Abbrechen</button>
            </div>
          )}

          {/* ── SEITEN LISTE + DETAIL (zweispaltig) ── */}
          <div style={{ display: 'grid', gridTemplateColumns: selectedPageId ? '1fr 360px' : '1fr', gap: 16, alignItems: 'start' }}>

            {/* LINKE SPALTE: Seitenliste */}
            <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 12, overflow: 'hidden' }}>
              {/* Tabellen-Header */}
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 100px 160px 140px', gap: 8, padding: '8px 16px', background: 'var(--bg-app)', borderBottom: '0.5px solid var(--border-light)', fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '.06em' }}>
                <div>Seite</div>
                <div>Typ</div>
                <div>Ziel-Keyword</div>
                <div>Aktion</div>
              </div>

              {sitemapLoading && (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>Seiten werden geladen…</div>
              )}

              {!sitemapLoading && sitemapPages.length === 0 && (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Noch keine Seiten. Klicke auf „+ Seite hinzufügen" oder nutze die KI-Sitemap.
                </div>
              )}

              {!sitemapLoading && sitemapPages
                .slice()
                .sort((a, b) => a.position - b.position)
                .map((page, idx, arr) => {
                  const isSelected = selectedPageId === page.id;
                  const isPflicht = page.ist_pflichtseite;
                  return (
                    <div
                      key={page.id}
                      onClick={() => setSelectedPageId(isSelected ? null : page.id)}
                      draggable={!isPflicht}
                      onDragStart={(e) => onDragStart(e, page.id)}
                      onDragOver={(e) => onDragOver(e, page.id)}
                      onDrop={(e) => onDrop(e, page.id)}
                      onDragEnd={onDragEnd}
                      style={{
                        display: 'grid', gridTemplateColumns: '2fr 100px 160px 140px',
                        gap: 8, padding: '10px 16px', alignItems: 'center',
                        borderBottom: idx < arr.length - 1 ? '0.5px solid var(--border-light)' : 'none',
                        background: isSelected ? 'var(--bg-active, rgba(0,142,170,0.06))' : dragOverPageId === page.id ? 'var(--bg-hover)' : 'transparent',
                        cursor: 'pointer', transition: 'background 0.1s',
                      }}
                    >
                      {/* Name */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {!isPflicht && <span style={{ cursor: 'grab', color: 'var(--text-tertiary)', fontSize: 14 }}>⠿</span>}
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                            {isPflicht ? '🔒 ' : ''}{page.page_name}
                          </div>
                          {page.zweck && (
                            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{page.zweck}</div>
                          )}
                        </div>
                      </div>

                      {/* Typ */}
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{page.page_type}</div>

                      {/* Keyword */}
                      <div style={{ fontSize: 11, color: page.ziel_keyword ? 'var(--text-primary)' : 'var(--text-tertiary)', fontStyle: page.ziel_keyword ? 'normal' : 'italic' }}>
                        {page.ziel_keyword || '– kein Keyword –'}
                      </div>

                      {/* Aktionen */}
                      <div style={{ display: 'flex', gap: 6 }} onClick={e => e.stopPropagation()}>
                        <button
                          onClick={() => setEditingPage(page)}
                          style={{ padding: '4px 10px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'var(--bg-surface)', fontSize: 11, fontWeight: 600, cursor: 'pointer', color: 'var(--text-primary)' }}
                          title="Im GrapesJS-Editor bearbeiten"
                        >
                          🖊️ Bearbeiten
                        </button>
                        {!isPflicht && (
                          <button
                            onClick={() => {
                              if (window.confirm(`Seite "${page.page_name}" löschen?`)) deleteSitemapPage(page.id);
                            }}
                            style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'transparent', fontSize: 11, cursor: 'pointer', color: '#dc2626' }}
                            title="Seite löschen"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
            </div>

            {/* RECHTE SPALTE: Detail-Panel */}
            {selectedPageId && (() => {
              const page = sitemapPages.find(p => p.id === selectedPageId);
              if (!page) return null;
              return (
                <div style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 12, padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>
                    {page.page_name}
                  </div>

                  {/* Seitenname */}
                  {!page.ist_pflichtseite && (
                    <div>
                      <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Seitenname</label>
                      <input
                        defaultValue={page.page_name}
                        key={`name-${page.id}`}
                        onBlur={e => {
                          if (e.target.value !== page.page_name) {
                            fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, { method: 'PUT', headers: h, body: JSON.stringify({ page_name: e.target.value }) })
                              .then(r => r.ok ? r.json() : null)
                              .then(updated => { if (updated) setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p)); });
                          }
                        }}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--text-primary)', background: 'var(--bg-app)', boxSizing: 'border-box' }}
                      />
                    </div>
                  )}

                  {/* Seitentyp */}
                  {!page.ist_pflichtseite && (
                    <div>
                      <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
                      <select
                        defaultValue={page.page_type}
                        key={`type-${page.id}`}
                        onChange={e => {
                          fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, { method: 'PUT', headers: h, body: JSON.stringify({ page_type: e.target.value }) })
                            .then(r => r.ok ? r.json() : null)
                            .then(updated => { if (updated) setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p)); });
                        }}
                        style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, background: 'var(--bg-app)', color: 'var(--text-primary)', boxSizing: 'border-box' }}
                      >
                        {['info','landing','leistung','kontakt','blog','rechtlich'].map(t => (
                          <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Ziel-Keyword */}
                  <div>
                    <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Ziel-Keyword (SEO)</label>
                    <input
                      defaultValue={page.ziel_keyword}
                      key={`kw-${page.id}`}
                      placeholder="z.B. Sanitär Koblenz"
                      onBlur={e => {
                        fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, { method: 'PUT', headers: h, body: JSON.stringify({ ziel_keyword: e.target.value }) })
                          .then(r => r.ok ? r.json() : null)
                          .then(updated => { if (updated) setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p)); });
                      }}
                      style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--text-primary)', background: 'var(--bg-app)', boxSizing: 'border-box' }}
                    />
                  </div>

                  {/* Zweck / Notizen */}
                  <div>
                    <label style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.06em', color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Zweck / Notizen</label>
                    <textarea
                      defaultValue={page.zweck}
                      key={`zweck-${page.id}`}
                      rows={3}
                      placeholder="Wofür ist diese Seite? Was soll der Besucher tun?"
                      onBlur={e => {
                        fetch(`${API_BASE_URL}/api/sitemap/pages/${page.id}`, { method: 'PUT', headers: h, body: JSON.stringify({ zweck: e.target.value }) })
                          .then(r => r.ok ? r.json() : null)
                          .then(updated => { if (updated) setSitemapPages(prev => prev.map(p => p.id === updated.id ? updated : p)); });
                      }}
                      style={{ width: '100%', padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--text-primary)', background: 'var(--bg-app)', resize: 'vertical', boxSizing: 'border-box' }}
                    />
                  </div>

                  {/* Editor-Button */}
                  <button
                    onClick={() => setEditingPage(page)}
                    style={{ padding: '10px', borderRadius: 8, border: 'none', background: '#008eaa', color: 'white', fontSize: 13, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
                  >
                    🖊️ Im GrapesJS-Editor bearbeiten
                  </button>

                  {page.gjs_html && (
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', textAlign: 'center' }}>
                      ✓ Seite hat Inhalt im Editor
                    </div>
                  )}
                </div>
              );
            })()}
          </div>

          {/* ── SEITE HINZUFÜGEN FORMULAR ── */}
          {addPageOpen && (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 14, color: 'var(--text-primary)' }}>Neue Seite hinzufügen</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 150px', gap: 10, marginBottom: 12 }}>
                <input
                  placeholder="Seitenname (z.B. Leistungen)"
                  value={addPageForm.page_name}
                  onChange={e => setAddPageForm(f => ({ ...f, page_name: e.target.value }))}
                  style={{ padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, fontFamily: 'var(--font-sans)', color: 'var(--text-primary)', background: 'var(--bg-app)' }}
                />
                <select
                  value={addPageForm.page_type}
                  onChange={e => setAddPageForm(f => ({ ...f, page_type: e.target.value }))}
                  style={{ padding: '8px 10px', border: '1px solid var(--border-light)', borderRadius: 6, fontSize: 13, background: 'var(--bg-app)', color: 'var(--text-primary)' }}
                >
                  {['info','landing','leistung','kontakt','blog'].map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={createSitemapPage} disabled={addPageSaving || !addPageForm.page_name.trim()} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: '#008eaa', color: 'white', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
                  {addPageSaving ? '…' : 'Seite anlegen'}
                </button>
                <button onClick={() => setAddPageOpen(false)} style={{ padding: '8px 16px', borderRadius: 6, border: '1px solid var(--border-light)', background: 'transparent', fontSize: 12, cursor: 'pointer', color: 'var(--text-primary)' }}>
                  Abbrechen
                </button>
              </div>
            </div>
          )}

          {/* ── GRAPESJS EDITOR (fullscreen portal) ── */}
          {editingPage && (
            <GrapesEditor
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
              projectId={id}
            />
          )}
        </div>
      )}

      {/* ── Content-Freigabe-Tab ─────────────────────────────────────────────── */}
      {activeTab === 'content' && (() => {
        const seiten = getSitemapSeiten();
        const total   = seiten.length;
        const freigeg = seiten.filter(s =>
          contentFreigaben[String(s.id)]?.status === 'freigegeben'
        ).length;
        const alleFreigegeben = total > 0 && freigeg === total;

        const STATUS_CONFIG = {
          freigegeben: { label: '✓ Freigegeben', bg: '#EAF3DE', color: '#27500A' },
          angefragt:   { label: '⏳ Angefragt',  bg: '#FAEEDA', color: '#633806' },
          abgelehnt:   { label: '✗ Abgelehnt',   bg: '#FCEBEB', color: '#A32D2D' },
          default:     { label: 'Ausstehend',     bg: '#F1EFE8', color: '#444441' },
        };

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── GESAMTSTATUS ── */}
            <div style={{
              background: alleFreigegeben ? '#EAF3DE' : 'var(--bg-surface)',
              border: `0.5px solid ${alleFreigegeben ? '#97C459' : 'var(--border-light)'}`,
              borderRadius: 12, padding: '14px 18px',
              display: 'flex', alignItems: 'center',
              justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
            }}>
              <div>
                <div style={{
                  fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
                  textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 4,
                }}>
                  Content-Freigabe
                </div>
                <div style={{ fontSize: 22, fontWeight: 500, color: 'var(--text-primary)' }}>
                  {freigeg} von {total} Seiten freigegeben
                </div>
                {!alleFreigegeben && total > 0 && (
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
                    {total - freigeg} Seiten benötigen noch eine Freigabe
                  </div>
                )}
              </div>

              {/* Fortschrittsbalken */}
              <div style={{ flex: '1 1 200px' }}>
                <div style={{
                  height: 6, background: 'var(--border-light)',
                  borderRadius: 3, overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: total > 0 ? `${Math.round(freigeg / total * 100)}%` : '0%',
                    background: alleFreigegeben ? '#1D9E75' : '#008eaa',
                    borderRadius: 3, transition: 'width .4s',
                  }} />
                </div>
                <div style={{
                  fontSize: 11, color: 'var(--text-tertiary)',
                  marginTop: 4, textAlign: 'right',
                }}>
                  {total > 0 ? Math.round(freigeg / total * 100) : 0}%
                </div>
              </div>

              {alleFreigegeben && (
                <button
                  onClick={advanceToTechnik}
                  style={{
                    padding: '9px 20px', borderRadius: 8, border: 'none',
                    background: '#1D9E75', color: 'white',
                    fontSize: 13, fontWeight: 600, cursor: 'pointer',
                  }}
                >
                  Weiter zu Phase Technik →
                </button>
              )}
            </div>

            {/* ── TABELLE ── */}
            {total === 0 ? (
              <div style={{
                background: 'var(--bg-surface)',
                border: '0.5px solid var(--border-light)',
                borderRadius: 12, padding: 24,
                textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13,
              }}>
                Keine Sitemap-Seiten vorhanden.
                Bitte zuerst den Sitemap-Planer ausfüllen.
              </div>
            ) : (
              <div style={{
                background: 'var(--bg-surface)',
                border: '0.5px solid var(--border-light)',
                borderRadius: 12, overflow: 'hidden',
              }}>
                {/* Tabellen-Header */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 90px 90px 130px 180px',
                  gap: 8, padding: '8px 16px',
                  background: 'var(--bg-app)',
                  borderBottom: '0.5px solid var(--border-light)',
                  fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)',
                  textTransform: 'uppercase', letterSpacing: '.06em',
                }}>
                  <div>Seite</div>
                  <div>Typ</div>
                  <div>Keyword</div>
                  <div>Freigabe-Status</div>
                  <div>Aktion</div>
                </div>

                {seiten.map((seite, idx) => {
                  const fg     = contentFreigaben[String(seite.id)] || {};
                  const sc     = STATUS_CONFIG[fg.status] || STATUS_CONFIG.default;
                  const isSend = approvalSending[seite.id];
                  const msg    = approvalMsg[seite.id];

                  return (
                    <div key={seite.id} style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 90px 90px 130px 180px',
                      gap: 8, padding: '10px 16px', alignItems: 'center',
                      borderBottom: idx < seiten.length - 1
                        ? '0.5px solid var(--border-light)' : 'none',
                    }}>
                      {/* Seitenname */}
                      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                        {seite.order}. {seite.name}
                      </span>

                      {/* Typ */}
                      <span style={{
                        fontSize: 10, fontWeight: 600, padding: '2px 7px',
                        borderRadius: 8,
                        background: 'var(--color-background-info)',
                        color: 'var(--color-text-info)',
                      }}>
                        {seite.typ}
                      </span>

                      {/* Keyword */}
                      <span style={{
                        fontSize: 11, color: 'var(--text-tertiary)',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {seite.keyword || '—'}
                      </span>

                      {/* Status */}
                      <div>
                        <span style={{
                          fontSize: 10, fontWeight: 600, padding: '3px 9px',
                          borderRadius: 10, background: sc.bg, color: sc.color,
                          display: 'inline-block',
                        }}>
                          {sc.label}
                        </span>
                        {fg.angefragt_am && fg.status === 'angefragt' && (
                          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>
                            {fg.angefragt_am}
                          </div>
                        )}
                        {fg.freigegeben_am && fg.status === 'freigegeben' && (
                          <div style={{ fontSize: 10, color: '#27500A', marginTop: 2 }}>
                            {fg.freigegeben_am}
                          </div>
                        )}
                      </div>

                      {/* Aktion */}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        {fg.status === 'freigegeben' ? (
                          <button
                            onClick={() => confirmApproval(seite.id, false)}
                            style={{
                              padding: '5px 10px', borderRadius: 6,
                              border: '0.5px solid var(--border-light)',
                              background: 'transparent', color: 'var(--text-secondary)',
                              fontSize: 11, cursor: 'pointer',
                            }}
                          >
                            Freigabe zurückziehen
                          </button>
                        ) : (
                          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                            <button
                              onClick={() => requestApproval(seite)}
                              disabled={isSend}
                              style={{
                                padding: '5px 10px', borderRadius: 6, border: 'none',
                                background: isSend ? '#94a3b8' : '#008eaa',
                                color: 'white', fontSize: 11, fontWeight: 600,
                                cursor: isSend ? 'not-allowed' : 'pointer',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {isSend ? '⏳' : '📧 Freigabe anfragen'}
                            </button>
                            <button
                              onClick={() => confirmApproval(seite.id, true)}
                              style={{
                                padding: '5px 10px', borderRadius: 6,
                                border: '0.5px solid #97C459',
                                background: '#EAF3DE', color: '#27500A',
                                fontSize: 11, cursor: 'pointer', whiteSpace: 'nowrap',
                              }}
                            >
                              ✓ Manuell
                            </button>
                          </div>
                        )}
                        {msg && (
                          <div style={{
                            fontSize: 10,
                            color: msg.startsWith('✓') ? '#27500A' : '#A32D2D',
                          }}>
                            {msg}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Hinweis */}
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              "Freigabe anfragen" sendet eine E-Mail an {project?.email || '(keine E-Mail hinterlegt)'}.
              "Manuell" erteilt die Freigabe direkt ohne E-Mail.
            </div>
          </div>
        );
      })()}

      {/* ── Zugangsdaten-Tab ────────────────────────────────────────────────── */}
      {activeTab === 'zugangsdaten' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* FORMULAR */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '0.5px solid var(--border-light)',
            borderRadius: 12, padding: '18px 20px',
          }}>
            <div style={{
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 14,
            }}>
              Neuen Zugang hinzufügen
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div>
                <label style={LST}>Name / Anbieter *</label>
                <input
                  value={credForm.label}
                  onChange={e => setCredForm(p => ({ ...p, label: e.target.value }))}
                  placeholder="z.B. IONOS, WordPress, cPanel"
                  style={INP}
                />
              </div>
              <div>
                <label style={LST}>URL</label>
                <input
                  type="url"
                  value={credForm.url}
                  onChange={e => setCredForm(p => ({ ...p, url: e.target.value }))}
                  placeholder="https://login.ionos.de"
                  style={INP}
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 10 }}>
              <div>
                <label style={LST}>Benutzername / E-Mail</label>
                <input
                  value={credForm.username}
                  onChange={e => setCredForm(p => ({ ...p, username: e.target.value }))}
                  placeholder="benutzer@domain.de"
                  autoComplete="off"
                  style={INP}
                />
              </div>
              <div>
                <label style={LST}>Passwort</label>
                <input
                  type="password"
                  value={credForm.password}
                  onChange={e => setCredForm(p => ({ ...p, password: e.target.value }))}
                  placeholder="Passwort eingeben"
                  autoComplete="new-password"
                  style={{ ...INP, paddingRight: 36 }}
                />
              </div>
            </div>

            <div style={{ marginBottom: 14 }}>
              <label style={LST}>Notizen (optional)</label>
              <textarea
                rows={2}
                value={credForm.notes}
                onChange={e => setCredForm(p => ({ ...p, notes: e.target.value }))}
                placeholder="z.B. 2FA aktiviert, Sicherheitsfrage: ..."
                style={{ ...INP, resize: 'none' }}
              />
            </div>

            {credError && (
              <div style={{
                background: '#FFF1F1', border: '1px solid #FECACA',
                borderRadius: 7, padding: '8px 12px',
                color: '#A32D2D', fontSize: 12, marginBottom: 10,
              }}>
                {credError}
              </div>
            )}

            <button
              onClick={saveCred}
              disabled={credSaving}
              style={{
                padding: '9px 20px', borderRadius: 8, border: 'none',
                background: credSaving ? '#94a3b8' : '#008eaa',
                color: 'white', fontSize: 13, fontWeight: 600,
                cursor: credSaving ? 'not-allowed' : 'pointer',
              }}
            >
              {credSaving ? 'Wird gespeichert...' : '+ Zugangsdaten speichern'}
            </button>
          </div>

          {/* LISTE */}
          <div style={{
            background: 'var(--bg-surface)',
            border: '0.5px solid var(--border-light)',
            borderRadius: 12, overflow: 'hidden',
          }}>
            <div style={{
              padding: '10px 16px',
              borderBottom: '0.5px solid var(--border-light)',
              fontSize: 12, fontWeight: 600, color: '#64748b',
              textTransform: 'uppercase', letterSpacing: '.06em',
              display: 'flex', justifyContent: 'space-between',
            }}>
              <span>Gespeicherte Zugänge ({creds.length})</span>
            </div>

            {credsLoading ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Lädt...
              </div>
            ) : creds.length === 0 ? (
              <div style={{ padding: 20, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
                Noch keine Zugangsdaten gespeichert.
              </div>
            ) : creds.map((c, i) => (
              <div key={c.id} style={{
                padding: '12px 16px',
                borderBottom: i < creds.length - 1 ? '0.5px solid var(--border-light)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <span style={{
                    background: '#E6F1FB', color: '#0C447C',
                    padding: '2px 9px', borderRadius: 8,
                    fontSize: 11, fontWeight: 600,
                  }}>
                    🔑 {c.label}
                  </span>
                  {c.url && (
                    <a href={c.url} target="_blank" rel="noreferrer"
                       style={{ fontSize: 11, color: '#008eaa' }}>
                      {c.url.replace('https://', '').slice(0, 40)}
                    </a>
                  )}
                  <button
                    onClick={() => deleteCred(c.id)}
                    style={{
                      marginLeft: 'auto', background: 'none',
                      border: 'none', color: '#94a3b8', cursor: 'pointer',
                      fontSize: 16, padding: '0 4px',
                    }}
                    title="Löschen"
                  >
                    ×
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: 12 }}>
                  {c.username && (
                    <div>
                      <span style={{ color: '#94a3b8' }}>Benutzer: </span>
                      <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{c.username}</span>
                    </div>
                  )}
                  {c.password && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ color: '#94a3b8' }}>Passwort: </span>
                      <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                        {showPasswords[c.id] ? c.password : '••••••••'}
                      </span>
                      <button
                        onClick={() => togglePw(c.id)}
                        style={{
                          background: 'none', border: 'none',
                          cursor: 'pointer', fontSize: 14, color: '#64748b', padding: '0 2px',
                        }}
                        title={showPasswords[c.id] ? 'Verbergen' : 'Einblenden'}
                      >
                        {showPasswords[c.id] ? '🙈' : '👁'}
                      </button>
                    </div>
                  )}
                </div>

                {c.notes && (
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 5 }}>
                    📝 {c.notes}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Sicherheitshinweis */}
          <div style={{
            background: '#E6F1FB', border: '0.5px solid #B5D4F4',
            borderRadius: 8, padding: '10px 14px',
            fontSize: 11, color: '#0C447C',
          }}>
            🔒 Passwörter werden mit AES-128 Fernet-Verschlüsselung gespeichert.
            Nur Admins können Zugangsdaten abrufen.
          </div>
        </div>
      )}

      {/* ── Audit Tab ──────────────────────────────────────────────────────── */}
      {(activeSubTab === 'audit' || activeTab === 'audits') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {audits.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px 20px',
              background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
              borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)' }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🔍</div>
              <div style={{ fontSize: 13, marginBottom: 14 }}>
                {project.lead_id ? 'Noch keine Audits vorhanden' : 'Kein Lead verknüpft — bitte Projektdaten bearbeiten'}
              </div>
              {project.lead_id && (
                <a href={`/app/leads/${project.lead_id}`}
                  style={{ display: 'inline-block', padding: '8px 18px', background: 'var(--brand-primary)',
                  color: 'white', border: 'none', borderRadius: 'var(--radius-md)',
                  fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', textDecoration: 'none' }}>
                  Audit in Kundenkartei starten →
                </a>
              )}
            </div>
          ) : (
            audits.map((audit, i) => {
              const levelColors = { Bronze: '#cd7f32', Silber: '#9e9e9e', Gold: '#ffd700', Platin: '#40c4df' };
              const lc = levelColors[audit.level] || 'var(--text-tertiary)';
              return (
                <div key={audit.id} style={{
                  background: 'var(--bg-surface)',
                  border: `1px solid ${i === 0 ? 'var(--border-medium)' : 'var(--border-light)'}`,
                  borderLeft: i === 0 ? '3px solid var(--brand-primary)' : '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-lg)', padding: '14px 16px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                    <div>
                      <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginBottom: 4 }}>
                        {audit.created_at ? new Date(audit.created_at).toLocaleDateString('de-DE') : ''}
                        {i === 0 && <span style={{ marginLeft: 8, background: 'var(--brand-primary)', color: 'white', padding: '1px 6px', borderRadius: 4, fontSize: 10, fontWeight: 600 }}>AKTUELL</span>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: 28, fontWeight: 700, color: lc }}>{audit.total_score || 0}</span>
                        <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>/100</span>
                        <span style={{ fontSize: 13, fontWeight: 600, color: lc }}>{audit.level || '—'}</span>
                      </div>
                      {audit.ai_summary && (
                        <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 6, lineHeight: 1.5, maxWidth: 500 }}>
                          {audit.ai_summary.substring(0, 150)}{audit.ai_summary.length > 150 ? '…' : ''}
                        </div>
                      )}
                    </div>
                    <button onClick={() => setOpenAudit(audit)} style={{
                      padding: '7px 14px', background: 'var(--bg-elevated)',
                      border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)',
                      fontSize: 12, fontWeight: 500, cursor: 'pointer',
                      color: 'var(--text-primary)', fontFamily: 'var(--font-sans)',
                    }}>
                      📋 Bericht öffnen
                    </button>
                  </div>
                </div>
              );
            })
          )}

          {/* Audit Detail Modal */}
          {openAudit && (
            <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,28,32,0.6)',
              zIndex: 1000, display: 'flex', alignItems: 'flex-start',
              justifyContent: 'center', padding: '20px', overflowY: 'auto' }}
              onClick={() => setOpenAudit(null)}>
              <div onClick={e => e.stopPropagation()}
                style={{ maxWidth: 900, width: '100%', background: 'var(--bg-surface)',
                borderRadius: 'var(--radius-xl)', overflow: 'hidden' }}>
                <AuditReport auditData={openAudit} onClose={() => setOpenAudit(null)} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Crawler Tab ──────────────────────────────────────────────────── */}
      {(activeSubTab === 'crawler' || activeTab === 'crawler') && (
        <div style={{ maxWidth: 760 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>🕷️ Website-Crawler</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                Erfasst alle URLs der Kunden-Website
                {crawlJob?.completed_at && (
                  <span style={{ marginLeft: 8, padding: '2px 8px', background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 4, fontSize: 11, fontWeight: 500 }}>
                    📦 Gespeichert: {String(crawlJob.completed_at).replace('T', ' ').slice(0, 16)}
                  </span>
                )}
              </div>
            </div>
            <button
              disabled={crawlLoading}
              onClick={async () => {
                if (!project?.lead_id || crawlLoading) return;
                setCrawlLoading(true);
                setCrawlElapsed(0);
                let elapsed = 0;
                if (crawlIntervalRef.current) clearInterval(crawlIntervalRef.current);
                crawlIntervalRef.current = setInterval(() => { elapsed += 1; setCrawlElapsed(elapsed); }, 1000);
                try {
                  const lead = await fetch(`${API_BASE_URL}/api/leads/${project.lead_id}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json());
                  const url = lead.website_url || '';
                  if (!url) { setCrawlLoading(false); clearInterval(crawlIntervalRef.current); return; }
                  await fetch(`${API_BASE_URL}/api/crawler/start/${project.lead_id}`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ url, max_pages: 50 }),
                  });
                  const poll = setInterval(async () => {
                    const s = await fetch(`${API_BASE_URL}/api/crawler/status/${project.lead_id}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json());
                    setCrawlJob(s);
                    if (s.status === 'completed' || s.status === 'failed') {
                      clearInterval(poll);
                      clearInterval(crawlIntervalRef.current);
                      setCrawlLoading(false);
                      const res = await fetch(`${API_BASE_URL}/api/crawler/results/${project.lead_id}`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json());
                      setCrawlResults(res.results || []);
                    }
                  }, 3000);
                } catch { setCrawlLoading(false); clearInterval(crawlIntervalRef.current); }
              }}
              style={{ padding: '8px 18px', background: crawlLoading ? 'var(--border-medium)' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: crawlLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6 }}
            >{crawlLoading ? (<><div style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.7s linear infinite' }} />Analysiert…</>) : crawlResults.length > 0 ? '🔄 Neu crawlen' : 'Crawl starten'}</button>
          </div>

          {/* Progress Box */}
          {crawlLoading && (() => {
            const elapsed = crawlJob?.duration_seconds ?? crawlElapsed;
            const found = crawlJob?.total_urls || 0;
            const phase = elapsed < 5 ? { icon: '🔌', text: 'Verbindung wird aufgebaut…' }
              : elapsed < 15 ? { icon: '🏠', text: 'Startseite wird analysiert…' }
              : elapsed < 30 ? { icon: '🔗', text: `Links werden entdeckt — ${found} URLs bisher` }
              : elapsed < 45 ? { icon: '📄', text: `Unterseiten durchsucht — ${found} URLs gecrawlt` }
              : { icon: '⚡', text: `Tiefe Analyse — ${found} URLs, Abschluss in Kürze` };
            return (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: 'var(--brand-primary-light)', borderRadius: 'var(--radius-md)', fontSize: 13, color: 'var(--brand-primary-dark)', fontWeight: 500 }}>
                  <span style={{ fontSize: 18 }}>{phase.icon}</span><span>{phase.text}</span>
                </div>
                <div>
                  <div style={{ height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.min(95, (elapsed / 44) * 100)}%`, background: 'var(--brand-primary)', borderRadius: 3, transition: 'width 1s linear' }} />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 5 }}>
                    <span>{found > 0 ? `${found} URLs gefunden` : 'Suche läuft…'}</span>
                    <span>{elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`}</span>
                  </div>
                </div>
              </div>
            );
          })()}

          {crawlJob && (
            <div style={{ display: 'flex', gap: 16, marginBottom: 14 }}>
              <div style={{ padding: '8px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
                Status: <strong style={{ color: crawlJob.status === 'completed' ? 'var(--status-success-text)' : 'var(--text-primary)' }}>{crawlJob.status}</strong>
              </div>
              <div style={{ padding: '8px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
                URLs: <strong>{crawlJob.total_urls || crawlResults.length}</strong>
              </div>
              {crawlJob.duration_seconds && (
                <div style={{ padding: '8px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
                  Dauer: <strong>{crawlJob.duration_seconds}s</strong>
                </div>
              )}
            </div>
          )}
          {crawlResults.length > 0 ? (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: 'var(--bg-app)' }}>
                    <th style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-tertiary)', fontWeight: 600 }}>URL</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-tertiary)', fontWeight: 600, width: 60 }}>Status</th>
                    <th style={{ padding: '8px 12px', textAlign: 'center', color: 'var(--text-tertiary)', fontWeight: 600, width: 60 }}>Tiefe</th>
                    <th style={{ padding: '8px 12px', textAlign: 'right', color: 'var(--text-tertiary)', fontWeight: 600, width: 70 }}>Ladezeit</th>
                  </tr>
                </thead>
                <tbody>
                  {crawlResults.map((r, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--border-light)' }}>
                      <td style={{ padding: '6px 12px', color: 'var(--text-primary)', wordBreak: 'break-all' }}>
                        <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-primary)', textDecoration: 'none' }}>{r.url}</a>
                      </td>
                      <td style={{ padding: '6px 12px', textAlign: 'center', color: r.status_code === 200 ? 'var(--status-success-text)' : 'var(--status-danger-text)' }}>{r.status_code || '—'}</td>
                      <td style={{ padding: '6px 12px', textAlign: 'center', color: 'var(--text-secondary)' }}>{r.depth}</td>
                      <td style={{ padding: '6px 12px', textAlign: 'right', color: 'var(--text-secondary)' }}>{r.load_time ? `${r.load_time}s` : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : !crawlLoading && (
            <div style={{ textAlign: 'center', padding: 40, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)', fontSize: 13 }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🕷️</div>
              Noch kein Crawl durchgeführt. Klicke oben auf &quot;Crawl starten&quot;.
            </div>
          )}
        </div>
      )}

      {/* ── Hosting-Scan Tab ──────────────────────────────────────────────── */}
      {(activeSubTab === 'hosting-scan' || activeSubTab === 'hosting') && (
        <div style={{ maxWidth: 760 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>🖥️ Hosting-Analyse</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                Server, DNS, SSL und Technologien
                {hostingData?._cached && hostingData?._cache_age_minutes != null && (
                  <span style={{ marginLeft: 8, padding: '2px 8px', background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 4, fontSize: 11, fontWeight: 500 }}>
                    📦 Cache ({hostingData._cache_age_minutes} min)
                  </span>
                )}
              </div>
            </div>
            <button
              disabled={hostingScanning}
              onClick={async () => {
                if (!project?.id) return;
                setHostingScanning(true);
                try {
                  const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/hosting-scan?force=true`, {
                    method: 'POST', headers: { Authorization: `Bearer ${token}` },
                  });
                  if (res.ok) {
                    const data = await res.json();
                    setHostingData(data);
                  }
                } catch { /* ignore */ }
                setHostingScanning(false);
              }}
              style={{ padding: '8px 18px', background: hostingScanning ? 'var(--text-tertiary)' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: hostingScanning ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}
            >{hostingScanning ? 'Scannt…' : 'Hosting scannen'}</button>
          </div>
          {hostingData ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              {[
                { label: 'Server', value: hostingData.server_software || '—', icon: '🖥️' },
                { label: 'IP', value: hostingData.hosting_ip || '—', icon: '🌐' },
                { label: 'Hoster', value: hostingData.hosting_org || '—', icon: '🏢' },
                { label: 'Land', value: hostingData.hosting_country || '—', icon: '🌍' },
                { label: 'DNS', value: hostingData.dns_provider || '—', icon: '📡' },
                { label: 'Registrar', value: hostingData.domain_registrar || '—', icon: '📋' },
                { label: 'WordPress', value: hostingData.is_wordpress ? 'Ja' : 'Nein', icon: '📰' },
                { label: 'CMS', value: hostingData.cms_type || '—', icon: '⚙️' },
              ].map(item => (
                <div key={item.label} style={{ padding: '12px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>{item.icon} {item.label}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{item.value}</div>
                </div>
              ))}
              {hostingData.detected_technologies && (
                <div style={{ gridColumn: '1 / -1', padding: '12px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 6 }}>🔧 Erkannte Technologien</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(typeof hostingData.detected_technologies === 'string' ? hostingData.detected_technologies.split(',') : []).map(t => (
                      <span key={t} style={{ padding: '3px 10px', background: 'var(--brand-primary-light)', color: 'var(--brand-primary)', borderRadius: 'var(--radius-full)', fontSize: 11, fontWeight: 600 }}>{t.trim()}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : !hostingScanning && (
            <div style={{ textAlign: 'center', padding: 40, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)', fontSize: 13 }}>
              <div style={{ fontSize: 32, marginBottom: 10 }}>🖥️</div>
              Noch kein Hosting-Scan. Klicke oben auf &quot;Hosting scannen&quot;.
            </div>
          )}
        </div>
      )}

      {/* ── Website-Versionen Tab (KI-Entwürfe) ───────────────────────────── */}
      {(activeSubTab === 'design' || activeTab === 'design') && (
        <div style={{ maxWidth: 1100 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>🎨 Website-Entwürfe</div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                KI wählt 3 passende Templates basierend auf Briefing, Inspirationen und altem Content
                {versions.length > 0 && (
                  <span style={{ marginLeft: 8, padding: '2px 8px', background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 4, fontSize: 11, fontWeight: 500 }}>
                    {versions.length} Entwürfe gespeichert
                  </span>
                )}
              </div>
            </div>
            <button
              disabled={versionsGenerating}
              onClick={async () => {
                if (!project?.id) return;
                setVersionsGenerating(true);
                try {
                  const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/generate-versions`, {
                    method: 'POST', headers: { Authorization: `Bearer ${token}` },
                  });
                  if (res.ok) {
                    const d = await res.json();
                    setVersionsRecommendation(d.empfehlung || '');
                    // Reload list
                    const r2 = await fetch(`${API_BASE_URL}/api/projects/${project.id}/versions`, { headers: { Authorization: `Bearer ${token}` } });
                    if (r2.ok) setVersions(await r2.json());
                    toast.success('3 Versionen generiert');
                  } else {
                    const err = await res.json().catch(() => ({}));
                    toast.error(parseApiError(err));
                  }
                } catch (e) { toast.error(parseApiError(e)); }
                setVersionsGenerating(false);
              }}
              style={{
                padding: '10px 20px',
                background: versionsGenerating ? 'var(--text-tertiary)' : 'var(--brand-primary)',
                color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                fontSize: 13, fontWeight: 600, cursor: versionsGenerating ? 'wait' : 'pointer',
                fontFamily: 'var(--font-sans)',
              }}
            >
              {versionsGenerating ? '🤖 KI generiert…' : versions.length > 0 ? '🔄 Neu generieren' : '🤖 3 Entwürfe generieren'}
            </button>
          </div>

          {versionsRecommendation && (
            <div style={{ padding: '12px 16px', background: 'var(--status-info-bg)', border: '1px solid var(--status-info-text)', borderRadius: 'var(--radius-md)', marginBottom: 16, fontSize: 13, color: 'var(--status-info-text)', lineHeight: 1.5 }}>
              <strong>KI-Empfehlung:</strong> {versionsRecommendation}
            </div>
          )}

          {versions.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)', fontSize: 13 }}>
              <div style={{ fontSize: 36, marginBottom: 10 }}>🎨</div>
              Noch keine Entwürfe generiert. Klicke oben auf &quot;3 Entwürfe generieren&quot;.
              <div style={{ fontSize: 11, marginTop: 8 }}>
                Voraussetzung: Briefing ausgefüllt + Templates in der Bibliothek
              </div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
              {versions.map(v => {
                let reasoning = {};
                try { reasoning = JSON.parse(v.ki_reasoning || '{}'); } catch {}
                return (
                  <div key={v.id} style={{
                    background: 'var(--bg-surface)',
                    border: v.selected ? '2px solid var(--brand-primary)' : '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-lg)',
                    overflow: 'hidden',
                    display: 'flex', flexDirection: 'column',
                  }}>
                    <div style={{ padding: '10px 14px', background: 'var(--bg-app)', borderBottom: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--brand-primary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                        Version {v.version_label}
                      </div>
                      {v.selected && (
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 8px', background: 'var(--brand-primary)', color: '#fff', borderRadius: 4 }}>AUSGEWÄHLT</span>
                      )}
                    </div>
                    <div style={{ height: 260, overflow: 'hidden', position: 'relative', background: 'var(--bg-app)' }}>
                      <iframe
                        title={`preview-${v.id}`}
                        src={`${API_BASE_URL}/api/projects/${project.id}/versions/${v.id}/preview`}
                        style={{
                          width: '200%', height: '520px',
                          transform: 'scale(0.5)', transformOrigin: 'top left',
                          border: 'none', pointerEvents: 'none',
                        }}
                      />
                    </div>
                    <div style={{ padding: '14px 16px', flex: 1, display: 'flex', flexDirection: 'column' }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                        {reasoning.titel || v.template_name || `Entwurf ${v.version_label}`}
                      </div>
                      {reasoning.beschreibung && (
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 10, lineHeight: 1.5 }}>
                          {reasoning.beschreibung}
                        </div>
                      )}
                      {reasoning.optimierungen && (
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 10, lineHeight: 1.5 }}>
                          <strong>Optimierung:</strong> {reasoning.optimierungen}
                        </div>
                      )}
                      {reasoning.farb_empfehlung && (
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 10 }}>
                          <strong>Farben:</strong> {reasoning.farb_empfehlung}
                        </div>
                      )}
                      <div style={{ marginTop: 'auto', display: 'flex', gap: 8 }}>
                        <button
                          onClick={async () => {
                            try {
                              await fetch(`${API_BASE_URL}/api/projects/${project.id}/versions/${v.id}/select`, {
                                method: 'POST', headers: { Authorization: `Bearer ${token}` },
                              });
                              setVersions(vs => vs.map(x => ({ ...x, selected: x.id === v.id })));
                              toast.success(`Version ${v.version_label} ausgewählt`);
                            } catch { toast.error('Fehler'); }
                          }}
                          style={{
                            flex: 1, padding: '10px',
                            background: v.selected ? 'var(--status-success-text)' : 'var(--brand-primary)',
                            color: '#fff', border: 'none', borderRadius: 'var(--radius-md)',
                            fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)',
                          }}>
                          {v.selected ? '✓ Ausgewählt' : 'Diese Version wählen'}
                        </button>
                        <a
                          href={`${API_BASE_URL}/api/projects/${project.id}/versions/${v.id}/preview`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            padding: '10px 14px',
                            background: 'var(--bg-app)', border: '1px solid var(--border-light)',
                            color: 'var(--text-primary)', borderRadius: 'var(--radius-md)',
                            fontSize: 12, textDecoration: 'none', fontFamily: 'var(--font-sans)',
                          }}>
                          Ganz öffnen
                        </a>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ── Website-Content Tab ───────────────────────────────────────────── */}
      {(activeSubTab === 'webcontent' || activeSubTab === 'website-content') && (() => {
        const [fullAnalysis, setFullAnalysis] = [scrapeStatus, setScrapeStatus]; // reuse state slots
        const [openSections, setOpenSections] = [expandedScrape, setExpandedScrape]; // reuse
        const toggle = (key) => setOpenSections(p => ({ ...p, [key]: !p[key] }));
        const seoTitleLen = fullAnalysis?.seo?.title_length || 0;
        const seoDescLen = fullAnalysis?.seo?.meta_description_length || 0;
        const ampel = (val, lo, hi) => val === 0 ? 'var(--text-tertiary)' : val < lo ? 'var(--status-danger-text)' : val <= hi ? 'var(--status-success-text)' : 'var(--status-warning-text)';
        const sectionHead = (key, icon, label, count) => (
          <button onClick={() => toggle(key)} style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
            <span>{icon} {label} {count != null && <span style={{ fontWeight: 400, color: 'var(--text-tertiary)' }}>({count})</span>}</span>
            <span style={{ color: 'var(--text-tertiary)' }}>{openSections[key] ? '▾' : '▸'}</span>
          </button>
        );

        return (
          <div style={{ maxWidth: 760 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>🌐 Website-Content</div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                  SEO, Texte, Assets und Links
                  {fullAnalysis?._cached_at && (
                    <span style={{ marginLeft: 8, padding: '2px 8px', background: 'var(--status-info-bg)', color: 'var(--status-info-text)', borderRadius: 4, fontSize: 11, fontWeight: 500 }}>
                      📦 Cache vom {fullAnalysis._cached_at.replace('T', ' ')}
                      {fullAnalysis._cache_age_minutes != null && ` (${fullAnalysis._cache_age_minutes} min)`}
                    </span>
                  )}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button disabled={contentLoading} onClick={async () => {
                  if (!project?.id) return;
                  setContentLoading(true);
                  try {
                    const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}/scrape-full?force=true`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
                    if (res.ok) setFullAnalysis(await res.json());
                  } catch {}
                  setContentLoading(false);
                }} style={{ padding: '8px 18px', background: contentLoading ? 'var(--text-tertiary)' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: contentLoading ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }} title={fullAnalysis?._cached_at ? `Gecachte Version vom ${fullAnalysis._cached_at}` : 'Neue SEO-Analyse starten'}>
                  {contentLoading ? 'Analysiert…' : fullAnalysis?.seo ? '🔄 Neu analysieren' : '🔍 SEO-Analyse'}
                </button>
                <button disabled={contentLoading} onClick={async () => {
                  if (!project?.lead_id) return;
                  setContentLoading(true);
                  try {
                    await fetch(`${API_BASE_URL}/api/crawler/scrape-content/${project.lead_id}`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } });
                    const res = await fetch(`${API_BASE_URL}/api/crawler/content/${project.lead_id}`, { headers: { Authorization: `Bearer ${token}` } });
                    if (res.ok) setWebsiteContent(await res.json());
                  } catch {}
                  setContentLoading(false);
                }} style={{ padding: '8px 18px', background: contentLoading ? 'var(--text-tertiary)' : 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 500, cursor: contentLoading ? 'wait' : 'pointer', fontFamily: 'var(--font-sans)' }}
                  title={websiteContent.length > 0 ? `${websiteContent.length} Seiten gespeichert` : 'Alle Seiten crawlen und Inhalte extrahieren'}>
                  {websiteContent.length > 0 ? '🔄 Multi-Page neu' : 'Multi-Page Scrape'}
                </button>
              </div>
            </div>

            {/* SEO Full Analysis */}
            {fullAnalysis?.seo && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
                {/* Sektion 1: SEO */}
                {sectionHead('seo', '🔍', 'SEO-Übersicht')}
                {openSections.seo && (
                  <div style={{ padding: '14px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                      <div style={{ padding: 10, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Title</div>
                        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{fullAnalysis.seo.title || '—'}</div>
                        <div style={{ fontSize: 11, color: ampel(seoTitleLen, 30, 60), marginTop: 3 }}>{seoTitleLen} Zeichen</div>
                      </div>
                      <div style={{ padding: 10, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                        <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginBottom: 4 }}>Meta-Description</div>
                        <div style={{ fontSize: 12, color: 'var(--text-primary)', lineHeight: 1.4 }}>{fullAnalysis.seo.meta_description || '—'}</div>
                        <div style={{ fontSize: 11, color: ampel(seoDescLen, 120, 160), marginTop: 3 }}>{seoDescLen} Zeichen</div>
                      </div>
                    </div>
                    {fullAnalysis.seo.canonical_url && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>Canonical:</strong> {fullAnalysis.seo.canonical_url}</div>}
                    {fullAnalysis.seo.language && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>Sprache:</strong> {fullAnalysis.seo.language}</div>}
                    {Object.entries(fullAnalysis.seo.headings || {}).map(([lvl, items]) => items.length > 0 && (
                      <div key={lvl}><div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{lvl} ({items.length})</div>
                        {items.map((h, i) => <div key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', paddingLeft: 8 }}>• {h}</div>)}
                      </div>
                    ))}
                  </div>
                )}

                {/* Sektion 2: Text */}
                {sectionHead('text', '📝', 'Volltext', fullAnalysis.text?.word_count)}
                {openSections.text && (
                  <div style={{ padding: '14px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ display: 'flex', gap: 16, marginBottom: 10 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>{fullAnalysis.text?.word_count}</strong> Wörter</span>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>{fullAnalysis.text?.char_count}</strong> Zeichen</span>
                      <button onClick={() => { navigator.clipboard.writeText(fullAnalysis.text?.full_text || ''); }}
                        style={{ fontSize: 11, color: 'var(--brand-primary)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                        Kopieren
                      </button>
                    </div>
                    <div style={{ maxHeight: 300, overflowY: 'auto', fontSize: 12, lineHeight: 1.6, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', padding: 10, background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                      {fullAnalysis.text?.full_text || 'Kein Text'}
                    </div>
                  </div>
                )}

                {/* Sektion 3: Assets */}
                {sectionHead('assets', '📦', 'Assets', (fullAnalysis.assets?.summary?.image_count || 0) + (fullAnalysis.assets?.summary?.script_count || 0))}
                {openSections.assets && (
                  <div style={{ padding: '14px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
                    <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', marginBottom: 10 }}>
                      {[['Bilder', fullAnalysis.assets?.summary?.image_count], ['Ohne Alt', fullAnalysis.assets?.summary?.images_without_alt], ['CSS', fullAnalysis.assets?.summary?.stylesheet_count], ['JS', fullAnalysis.assets?.summary?.script_count], ['Fonts', fullAnalysis.assets?.summary?.font_count]].map(([l, v]) => (
                        <div key={l} style={{ textAlign: 'center' }}><div style={{ fontSize: 18, fontWeight: 700, color: 'var(--brand-primary)' }}>{v || 0}</div><div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{l}</div></div>
                      ))}
                    </div>
                    {(fullAnalysis.assets?.images || []).length > 0 && (
                      <div style={{ marginTop: 8 }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 6 }}>BILDER</div>
                        {fullAnalysis.assets.images.slice(0, 15).map((img, i) => (
                          <div key={i} style={{ display: 'flex', gap: 8, padding: '4px 0', borderBottom: '1px solid var(--border-light)', alignItems: 'center' }}>
                            <a href={img.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-primary)', flex: 1, wordBreak: 'break-all', fontSize: 11 }}>{img.url?.split('/').pop()}</a>
                            <span style={{ color: img.has_alt ? 'var(--status-success-text)' : 'var(--status-danger-text)', fontSize: 10, flexShrink: 0 }}>{img.has_alt ? 'Alt ✓' : 'Alt ✗'}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Sektion 4: Links */}
                {sectionHead('links', '🔗', 'Links', (fullAnalysis.links?.internal_count || 0) + (fullAnalysis.links?.external_count || 0))}
                {openSections.links && (
                  <div style={{ padding: '14px 16px', background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12 }}>
                    {(fullAnalysis.links?.internal || []).length > 0 && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 6 }}>INTERN ({fullAnalysis.links.internal_count})</div>
                        {fullAnalysis.links.internal.slice(0, 20).map((l, i) => (
                          <div key={i} style={{ padding: '3px 0' }}>
                            <a href={l.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--brand-primary)', wordBreak: 'break-all', fontSize: 11 }}>{l.url}</a>
                            {l.text && <span style={{ color: 'var(--text-tertiary)', marginLeft: 6 }}>— {l.text}</span>}
                          </div>
                        ))}
                      </div>
                    )}
                    {(fullAnalysis.links?.external || []).length > 0 && (
                      <div>
                        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 6 }}>EXTERN ({fullAnalysis.links.external_count})</div>
                        {fullAnalysis.links.external.slice(0, 15).map((l, i) => (
                          <div key={i} style={{ padding: '3px 0' }}>
                            <a href={l.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--text-secondary)', wordBreak: 'break-all', fontSize: 11 }}>{l.url}</a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Multi-Page Content (existing crawler-based) */}
            {websiteContent.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', letterSpacing: '0.06em' }}>GECRAWLTE SEITEN ({websiteContent.length})</div>
                {websiteContent.map((page, i) => (
                  <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: '14px 16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
                      <a href={page.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13, fontWeight: 600, color: 'var(--brand-primary)', textDecoration: 'none', wordBreak: 'break-all' }}>{page.url}</a>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)', flexShrink: 0, marginLeft: 10 }}>{page.word_count || 0} Wörter</span>
                    </div>
                    {page.title && <div style={{ fontSize: 12, color: 'var(--text-primary)', marginBottom: 3 }}><strong>Titel:</strong> {page.title}</div>}
                    {page.h1 && <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}><strong>H1:</strong> {page.h1}</div>}
                    {page.text_preview && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 6, lineHeight: 1.5 }}>{page.text_preview}</div>}
                  </div>
                ))}
              </div>
            )}

            {!fullAnalysis?.seo && websiteContent.length === 0 && !contentLoading && (
              <div style={{ textAlign: 'center', padding: 40, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)', fontSize: 13 }}>
                <div style={{ fontSize: 32, marginBottom: 10 }}>🌐</div>
                Klicke &quot;SEO-Analyse&quot; für die Startseite oder &quot;Multi-Page Scrape&quot; für alle Seiten.
              </div>
            )}
          </div>
        );
      })()}

      {/* ── QA-Scan Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'qa-scan' && (() => {
        const ai = qaResult?.result?.ai || {};
        const checks = qaResult?.result?.checks || {};
        const score = qaResult?.score ?? ai.gesamt_score ?? null;

        return (
          <div style={{ maxWidth: 760, padding: '0 0 40px' }}>

            {/* ── Header ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)' }}>KI-Qualitätsprüfung</div>
                {qaResult?.run_at && (
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 3 }}>
                    Zuletzt: {qaResult.run_at} Uhr
                  </div>
                )}
              </div>
              <button
                disabled={qaRunning}
                onClick={runQa}
                style={{
                  background: qaRunning ? '#94a3b8' : '#008eaa', color: 'white',
                  border: 'none', borderRadius: 8, padding: '10px 20px',
                  fontSize: 13, fontWeight: 600, cursor: qaRunning ? 'not-allowed' : 'pointer',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {qaRunning ? 'Scan läuft… (ca. 30–40 Sek.)' : 'QA-Scan starten ↺'}
              </button>
            </div>

            {qaError && (
              <div style={{ background: '#FFF1F1', border: '1px solid #FECACA', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: '#DC2626', marginBottom: 16 }}>
                {qaError}
              </div>
            )}

            {/* ── Kein Ergebnis ── */}
            {!qaResult && !qaRunning && (
              <div style={{ background: '#f8f9fa', borderRadius: 12, padding: '40px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
                <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 6 }}>Noch kein QA-Scan durchgeführt.</div>
                <div style={{ fontSize: 13 }}>Klicke „QA-Scan starten" um die Website automatisch auf 50+ Kriterien zu prüfen.</div>
              </div>
            )}

            {/* ── Ergebnis ── */}
            {qaResult && score !== null && (() => {
              const sc = Number(score);
              const bg = scoreBg(sc);
              const bc = scoreBorder(sc);
              const fc = scoreColor(sc);

              return (
                <>
                  {/* A) Gesamt-Score Banner */}
                  <div style={{ background: bg, border: `1.5px solid ${bc}`, borderRadius: 12, padding: 16, display: 'flex', alignItems: 'center', gap: 20, marginBottom: 16, flexWrap: 'wrap' }}>
                    <div style={{ width: 64, height: 64, borderRadius: '50%', background: bg, border: `3px solid ${bc}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span style={{ fontSize: 24, fontWeight: 700, color: fc, lineHeight: 1 }}>{sc}</span>
                      <span style={{ fontSize: 11, color: '#94a3b8' }}>/ 100</span>
                    </div>
                    <div>
                      {ai.golive_empfehlung
                        ? <div style={{ fontSize: 14, fontWeight: 600, color: '#1D9E75' }}>✓ Go-Live empfohlen</div>
                        : <div style={{ fontSize: 14, fontWeight: 600, color: '#E24B4A' }}>✗ Noch nicht Go-Live-bereit</div>
                      }
                      {ai.golive_begruendung && (
                        <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 4 }}>{ai.golive_begruendung}</div>
                      )}
                    </div>
                  </div>

                  {/* B) KI-Zusammenfassung */}
                  {ai.ki_zusammenfassung && (
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: '14px 18px', marginBottom: 16 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: '#008eaa', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>KI-Bewertung</div>
                      <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.65 }}>{ai.ki_zusammenfassung}</div>
                    </div>
                  )}

                  {/* C) Kritische Blocker */}
                  {!ai.golive_empfehlung && ai.kritische_blocker?.length > 0 && (
                    <div style={{ background: '#FFF1F1', borderLeft: '3px solid #E24B4A', borderRadius: 8, padding: '12px 16px', marginBottom: 16 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: '#E24B4A', marginBottom: 8 }}>⚠ Vor Go-Live zu beheben:</div>
                      <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {ai.kritische_blocker.map((b, i) => (
                          <li key={i} style={{ fontSize: 13, color: '#E24B4A', marginBottom: 4 }}>{b}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* D) Kategorie-Scores */}
                  {ai.kategorien && (
                    <div style={{ marginBottom: 20 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 10 }}>Kategorie-Bewertung</div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                        {Object.entries(ai.kategorien).map(([key, kat]) => {
                          const ks = Number(kat.score || 0);
                          const kc = scoreColor(ks);
                          const isOpen = openKat === key;
                          const katLabel = { seo: 'SEO', performance: 'Performance', mobile: 'Mobile', dsgvo: 'DSGVO', content: 'Content', technik: 'Technik' }[key] || key;
                          const badgeBg = kat.status === 'bestanden' ? '#E1F5EE' : kat.status === 'warnung' ? '#FFF7ED' : '#FFF1F1';
                          const badgeColor = statusFarbe(kat.status);
                          return (
                            <div key={key}
                              onClick={() => setOpenKat(isOpen ? null : key)}
                              style={{ background: 'var(--bg-surface)', border: '0.5px solid var(--border-light)', borderRadius: 10, padding: 14, cursor: 'pointer' }}
                            >
                              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--text-tertiary)', letterSpacing: '0.05em', marginBottom: 8 }}>{katLabel}</div>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                                <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
                                  <div style={{ width: `${ks}%`, height: '100%', background: kc, borderRadius: 3 }} />
                                </div>
                                <span style={{ fontSize: 14, fontWeight: 600, color: kc, flexShrink: 0 }}>{ks}</span>
                              </div>
                              <span style={{ fontSize: 10, fontWeight: 600, background: badgeBg, color: badgeColor, padding: '2px 7px', borderRadius: 20 }}>
                                {kat.status || '—'}
                              </span>
                              {isOpen && (
                                <div style={{ marginTop: 10, borderTop: '1px solid var(--border-light)', paddingTop: 8 }}>
                                  {kat.probleme?.length > 0 && (
                                    <>
                                      <div style={{ fontSize: 11, fontWeight: 600, color: '#E24B4A', marginBottom: 4 }}>Probleme:</div>
                                      <ul style={{ margin: '0 0 6px', paddingLeft: 16 }}>
                                        {kat.probleme.map((p, i) => <li key={i} style={{ fontSize: 11, color: '#E24B4A', marginBottom: 2 }}>{p}</li>)}
                                      </ul>
                                    </>
                                  )}
                                  {kat.punkte?.slice(0, 3).length > 0 && (
                                    <>
                                      <div style={{ fontSize: 11, fontWeight: 600, color: '#1D9E75', marginBottom: 4 }}>Bestanden:</div>
                                      <ul style={{ margin: 0, paddingLeft: 16 }}>
                                        {kat.punkte.slice(0, 3).map((p, i) => <li key={i} style={{ fontSize: 11, color: '#1D9E75', marginBottom: 2 }}>{p}</li>)}
                                      </ul>
                                    </>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* E) Einzelchecks-Tabelle */}
                  {Object.keys(checks).filter(k => typeof checks[k] === 'boolean').length > 0 && (
                    <div style={{ marginBottom: 20 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 10 }}>Technische Einzelprüfungen</div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px 20px', background: 'var(--border-light)', border: '1px solid var(--border-light)', borderRadius: 10, overflow: 'hidden' }}>
                        {Object.entries(QA_CHECK_LABELS).filter(([k]) => k in checks && typeof checks[k] === 'boolean').map(([k, label]) => {
                          const raw = checks[k];
                          const ok  = QA_INVERTED.has(k) ? !raw : raw;
                          return (
                            <div key={k} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 12px', background: 'var(--bg-surface)', gap: 8 }}>
                              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{label}</span>
                              <span style={{ fontSize: 13, fontWeight: 700, color: checkColor(ok), flexShrink: 0 }}>{checkIcon(ok)}</span>
                            </div>
                          );
                        })}
                        {checks.alt_texte_quote != null && (
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '7px 12px', background: 'var(--bg-surface)', gap: 8 }}>
                            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Alt-Texte: Bilder abgedeckt</span>
                            <span style={{ fontSize: 12, fontWeight: 600, color: checks.alt_texte_quote >= 80 ? '#1D9E75' : '#E24B4A' }}>{checks.alt_texte_quote}%</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* F) Empfehlungen */}
                  {ai.top_empfehlungen?.length > 0 && (
                    <div style={{ background: '#EFF9FB', border: '1px solid #BAE6EF', borderRadius: 10, padding: '14px 18px' }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: '#008eaa', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10 }}>Top-Empfehlungen</div>
                      <ol style={{ margin: 0, paddingLeft: 20 }}>
                        {ai.top_empfehlungen.map((r, i) => (
                          <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6, lineHeight: 1.5 }}>{r}</li>
                        ))}
                      </ol>
                    </div>
                  )}
                </>
              );
            })()}
          </div>
        );
      })()}

      {/* ── Preview Tab ────────────────────────────────────────────────────── */}
      {(activeSubTab === 'preview' || activeTab === 'preview') && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 32 }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>👁</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Website-Vorschau</div>
          {project.website_url ? (
            <a href={project.website_url} target="_blank" rel="noopener noreferrer"
              style={{ display: 'inline-block', marginTop: 8, padding: '10px 24px', background: '#0d6efd', color: '#fff', borderRadius: 8, fontWeight: 600, fontSize: 13, textDecoration: 'none' }}>
              {project.website_url} →
            </a>
          ) : (
            <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Keine Website-URL hinterlegt.</div>
          )}
        </div>
      )}

      {/* ── Editor Tab — Hinweis: Seiten werden jetzt individuell bearbeitet ── */}
      {(activeSubTab === 'editor' || activeTab === 'editor') && (
        <div style={{
          padding: 32, background: 'var(--bg-surface)',
          border: '0.5px solid var(--border-light)', borderRadius: 12,
          textAlign: 'center', display: 'flex', flexDirection: 'column',
          alignItems: 'center', gap: 16,
        }}>
          <div style={{ fontSize: 32 }}>🖊️</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
            Seiten werden jetzt individuell bearbeitet
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 480, lineHeight: 1.7 }}>
            Jede Seite hat ihren eigenen Editor. Wechsle zum Tab{' '}
            <strong>„Website neu"</strong> (Phase Content), wähle eine Seite aus
            der Liste und klicke auf <strong>„🖊️ Bearbeiten"</strong>.
            So wird jede Seite getrennt gespeichert und bleibt dem Kunden zugeordnet.
          </div>
          <button
            onClick={() => setActiveSubTab('sitemap')}
            style={{
              padding: '10px 24px', borderRadius: 8, border: 'none',
              background: '#008eaa', color: 'white',
              fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}
          >
            → Zu „Website neu" wechseln
          </button>
        </div>
      )}

      {/* ── Netlify-DNS Tab ────────────────────────────────────────────────── */}
      {(activeSubTab === 'netlify-dns' || activeTab === 'netlify-dns') && (() => {
        // NOTE: Do NOT fetch here — side effects in render cause infinite loops.
        // Status is loaded via useEffect (see loadNetlifyStatus below the tab blocks).

        const createSite = async () => {
          setNetlifyLoading(true);
          try {
            const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/create-site`, { method: 'POST', headers });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            toast.success('Netlify-Site angelegt');
            // reload status
            const s = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers });
            setNetlify(s.ok ? await s.json() : null);
          } catch (e) { toast.error(parseApiError(e)); }
          finally { setNetlifyLoading(false); }
        };

        const doDeploy = async () => {
          if (!deployHtml.trim()) { toast.error('HTML-Code fehlt'); return; }
          setNetlifyDeploying(true);
          setNetlifyDeployResult(null);
          try {
            const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/deploy`, {
              method: 'POST',
              headers: { ...headers, 'Content-Type': 'application/json' },
              body: JSON.stringify({ html: deployHtml, css: '', redirects: '' }),
            });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const d = await r.json();
            setNetlifyDeployResult(d);
            toast.success('Erfolgreich deployed');
          } catch (e) { toast.error('Deploy fehlgeschlagen: ' + e.message); }
          finally { setNetlifyDeploying(false); }
        };

        const doSetDomain = async () => {
          if (!netlifyDomain.trim()) { toast.error('Bitte Domain eingeben'); return; }
          try {
            const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/set-domain`, {
              method: 'POST',
              headers: { ...headers, 'Content-Type': 'application/json' },
              body: JSON.stringify({ domain: netlifyDomain.trim() }),
            });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const d = await r.json();
            // Neue Response enthält .guide mit records[]
            setNetlifyDnsGuide(d.guide || { cname_target: d.cname_target });
            toast.success('Domain verbunden — DNS-Guide per E-Mail gesendet');
            // Status reload
            const s = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers });
            if (s.ok) setNetlify(await s.json());
          } catch (e) { toast.error(parseApiError(e)); }
        };

        const sendDnsEmail = async () => {
          const siteUrl = netlify?.url?.replace('https://', '') || netlifyDnsGuide?.cname_target || '';
          try {
            await fetch(`${API_BASE_URL}/api/projects/${project.id}/request-approval`, {
              method: 'POST',
              headers: { ...headers, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                topic: 'DNS-Einrichtung erforderlich',
                notes: `Bitte tragen Sie folgenden CNAME-Eintrag ein:\nName: www\nZiel: ${siteUrl}\nTTL: 3600`,
              }),
            });
            toast.success('Anleitung per E-Mail gesendet');
          } catch { toast.error('E-Mail konnte nicht gesendet werden'); }
        };

        const card = { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 20, display: 'flex', flexDirection: 'column', gap: 12 };
        const cardTitle = { fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 };
        const inp = { width: '100%', padding: '8px 10px', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, background: 'var(--bg-app)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box', outline: 'none' };
        const btnBlue = { padding: '9px 20px', background: netlifyLoading ? '#94a3b8' : '#0d6efd', color: '#fff', border: 'none', borderRadius: 7, fontWeight: 600, fontSize: 13, cursor: netlifyLoading ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)' };

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── BEREICH 1: Site-Status ── */}
            <div style={card}>
              <div style={cardTitle}>🌐 Netlify-Site</div>
              {netlifyLoading && !netlify ? (
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Lade Status…</div>
              ) : !netlify ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'flex-start' }}>
                  <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Noch keine Netlify-Site angelegt.</div>
                  <button onClick={createSite} disabled={netlifyLoading} style={btnBlue}>
                    {netlifyLoading ? 'Anlegen…' : '+ Netlify-Site anlegen'}
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ background: '#dcfce7', color: '#16a34a', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>✓ Site aktiv</span>
                    {netlify.ssl ? (
                      <span style={{ background: '#dcfce7', color: '#16a34a', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>🔒 SSL aktiv</span>
                    ) : (
                      <span style={{ background: '#fef9c3', color: '#854d0e', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>⏳ SSL ausstehend</span>
                    )}
                  </div>
                  {netlify.url && (
                    <a href={netlify.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 13, color: '#0d6efd', wordBreak: 'break-all' }}>{netlify.url}</a>
                  )}
                  {netlify.netlify_last_deploy && (
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>
                      Letzter Deploy: {new Date(netlify.netlify_last_deploy).toLocaleString('de-DE')}
                    </div>
                  )}
                  <button onClick={async () => {
                    setNetlifyLoading(true);
                    const s = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers });
                    setNetlify(s.ok ? await s.json() : null);
                    setNetlifyLoading(false);
                  }} disabled={netlifyLoading} style={{ ...btnBlue, background: 'var(--bg-elevated)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', width: 'fit-content' }}>
                    🔄 Status aktualisieren
                  </button>
                </div>
              )}
            </div>

            {/* ── BEREICH: Alle Seiten exportieren / deployen ── */}
            <div style={card}>
              <div style={cardTitle}>📦 Alle Seiten — Export & Deploy</div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6, margin: '0 0 16px' }}>
                Exportiert alle im GrapesJS-Editor gespeicherten Seiten dieses Projekts.
                Jede Seite wird als eigene HTML-Datei mit korrektem URL-Pfad angelegt.
              </p>

              {sitemapPages.filter(p => p.gjs_html).length === 0 ? (
                <div style={{ padding: '12px 14px', background: '#fef9c3', borderRadius: 8, fontSize: 13, color: '#854d0e', marginBottom: 12 }}>
                  ⚠️ Noch keine Seiten mit Inhalt. Bitte zuerst Seiten im Tab „Website neu" im GrapesJS-Editor bearbeiten und speichern.
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12 }}>
                  {sitemapPages.filter(p => p.gjs_html).length} Seiten bereit:&nbsp;
                  {sitemapPages.filter(p => p.gjs_html).map(p => p.page_name).join(', ')}
                </div>
              )}

              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {/* ZIP Download */}
                <button
                  onClick={async () => {
                    try {
                      const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/export-zip`, { headers });
                      if (!r.ok) { const err = await r.json().catch(() => ({})); throw new Error(err.detail || `HTTP ${r.status}`); }
                      const blob = await r.blob();
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = r.headers.get('content-disposition')?.match(/filename="(.+)"/)?.[1] || 'website-export.zip';
                      a.click();
                      URL.revokeObjectURL(url);
                      toast.success('ZIP heruntergeladen');
                    } catch (e) { toast.error(e.message || 'Download fehlgeschlagen'); }
                  }}
                  style={{
                    padding: '10px 18px', borderRadius: 8,
                    background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                    color: 'var(--text-primary)', fontSize: 13, fontWeight: 600,
                    cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: 8,
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  ⬇️ Als ZIP herunterladen
                </button>

                {/* Multi-Page Netlify Deploy */}
                {netlify && (
                  <button
                    onClick={async () => {
                      setNetlifyDeploying(true);
                      setNetlifyDeployResult(null);
                      try {
                        const r = await fetch(
                          `${API_BASE_URL}/api/projects/${project.id}/netlify/deploy-all-pages`,
                          { method: 'POST', headers }
                        );
                        if (!r.ok) {
                          const err = await r.json().catch(() => ({}));
                          throw new Error(err.detail || `HTTP ${r.status}`);
                        }
                        const d = await r.json();
                        setNetlifyDeployResult(d);
                        toast.success(`✓ ${d.pages_count} Seiten deployed!`);
                      } catch (e) {
                        toast.error('Deploy fehlgeschlagen: ' + e.message);
                      } finally {
                        setNetlifyDeploying(false);
                      }
                    }}
                    disabled={netlifyDeploying}
                    style={{
                      padding: '10px 18px', borderRadius: 8, border: 'none',
                      background: netlifyDeploying ? '#94a3b8' : '#16a34a',
                      color: 'white', fontSize: 13, fontWeight: 600,
                      cursor: netlifyDeploying ? 'not-allowed' : 'pointer',
                      display: 'flex', alignItems: 'center', gap: 8,
                      fontFamily: 'var(--font-sans)',
                    }}
                  >
                    {netlifyDeploying ? '⏳ Deploy läuft…' : '🚀 Alle Seiten zu Netlify deployen'}
                  </button>
                )}
              </div>

              {netlifyDeployResult && netlifyDeployResult.pages_count && (
                <div style={{ marginTop: 12, padding: '10px 14px', background: '#dcfce7', borderRadius: 8, fontSize: 13, color: '#166534' }}>
                  ✓ {netlifyDeployResult.pages_count} Seiten deployed
                  {netlifyDeployResult.deploy_url && (
                    <> · <a href={netlifyDeployResult.deploy_url} target="_blank" rel="noopener noreferrer" style={{ color: '#16a34a', fontWeight: 700 }}>Live ansehen →</a></>
                  )}
                </div>
              )}
            </div>

            {/* ── BEREICH 2: Deployen (einzelne Seite / Textfeld) ── */}
            {netlify && (
              <div style={card}>
                <div style={cardTitle}>🚀 Einzelne Seite deployen (manuell)</div>
                <textarea
                  value={deployHtml}
                  onChange={e => setDeployHtml(e.target.value)}
                  rows={5}
                  placeholder="HTML aus GrapesJS einfügen..."
                  style={{ ...inp, resize: 'vertical', fontFamily: 'monospace', fontSize: 12 }}
                />
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>CSS und _redirects werden automatisch ergänzt.</div>
                <button onClick={doDeploy} disabled={netlifyDeploying} style={{ ...btnBlue, background: netlifyDeploying ? '#94a3b8' : '#0d6efd', cursor: netlifyDeploying ? 'not-allowed' : 'pointer', alignSelf: 'stretch', padding: '10px 0' }}>
                  {netlifyDeploying ? '⏳ Deploy läuft (~5 Sek.)…' : '🚀 Jetzt deployen'}
                </button>
                {netlifyDeployResult && (
                  <div style={{ background: '#dcfce7', borderRadius: 7, padding: '10px 14px', fontSize: 13 }}>
                    ✅ Deploy erfolgreich —{' '}
                    <a href={netlifyDeployResult.deploy_url} target="_blank" rel="noopener noreferrer" style={{ color: '#16a34a', fontWeight: 600 }}>
                      {netlifyDeployResult.deploy_url}
                    </a>
                    <span style={{ marginLeft: 8, color: '#166534' }}>({netlifyDeployResult.state})</span>
                  </div>
                )}
              </div>
            )}

            {/* ── BEREICH 3: Domain verbinden ── */}
            {netlify && (
              <div style={card}>
                <div style={cardTitle}>🔗 Domain verbinden</div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    value={netlifyDomain}
                    onChange={e => setNetlifyDomain(e.target.value)}
                    placeholder="www.kundenwebsite.de"
                    style={{ ...inp, flex: 1 }}
                  />
                  <button onClick={doSetDomain} style={{ ...btnBlue, whiteSpace: 'nowrap' }}>Domain verbinden</button>
                </div>

                {/* Live-Status Banner */}
                {netlify?.custom_domain && netlify?.ssl && (
                  <div style={{ marginTop: 12, padding: '14px 16px', background: 'var(--status-success-bg)', border: '1px solid var(--status-success-text)', borderRadius: 10 }}>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--status-success-text)', marginBottom: 4 }}>
                      ✓ Website ist live!
                    </div>
                    <a href={`https://${netlify.custom_domain}`} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 13, color: 'var(--brand-primary)', wordBreak: 'break-all' }}>
                      {netlify.custom_domain} öffnen →
                    </a>
                  </div>
                )}

                {/* Pending Info */}
                {netlifyDnsGuide && !netlify?.ssl && (
                  <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--status-warning-bg)', border: '1px solid var(--status-warning-text)', borderRadius: 8, fontSize: 12, color: 'var(--status-warning-text)' }}>
                    ⏳ DNS wird geprüft — System prüft alle 10 Min. automatisch. E-Mail an Kunden gesendet.
                  </div>
                )}

                {/* DNS-Guide Tabelle */}
                {netlifyDnsGuide && Array.isArray(netlifyDnsGuide.records) && netlifyDnsGuide.records.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 10 }}>
                      DNS-Einstellungen für {netlifyDnsGuide.domain}
                    </div>
                    <div style={{ background: 'var(--bg-app)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border-light)' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '70px 70px 1fr 90px', padding: '9px 14px', background: 'var(--bg-surface)', fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        <span>Typ</span><span>Name</span><span>Wert</span><span></span>
                      </div>
                      {netlifyDnsGuide.records.map((r, i) => (
                        <div key={i} style={{ display: 'grid', gridTemplateColumns: '70px 70px 1fr 90px', padding: '12px 14px', borderTop: '1px solid var(--border-light)', fontSize: 13, alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, color: 'var(--brand-primary)' }}>{r.type}</span>
                          <span style={{ fontFamily: 'monospace', color: 'var(--text-primary)' }}>{r.name}</span>
                          <span style={{ fontFamily: 'monospace', fontSize: 12, color: 'var(--text-primary)', wordBreak: 'break-all' }}>{r.value}</span>
                          <button onClick={() => { navigator.clipboard.writeText(r.value); toast.success('Kopiert'); }}
                            style={{ fontSize: 11, padding: '4px 10px', border: '1px solid var(--border-light)', borderRadius: 4, background: 'var(--bg-surface)', cursor: 'pointer', color: 'var(--text-secondary)', fontFamily: 'var(--font-sans)' }}>
                            Kopieren
                          </button>
                        </div>
                      ))}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 10, lineHeight: 1.6 }}>
                      DNS-Änderungen werden innerhalb von 1–48 Stunden aktiv. Kunde wurde per E-Mail informiert.
                    </div>
                  </div>
                )}

                {/* Legacy cname_target fallback */}
                {netlifyDnsGuide && !Array.isArray(netlifyDnsGuide.records) && netlifyDnsGuide.cname_target && (
                  <div style={{ marginTop: 12, padding: 14, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 8, fontSize: 12 }}>
                    <strong>CNAME:</strong> www → {netlifyDnsGuide.cname_target}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {/* ── Go-Live Vorbereitung Tab ────────────────────────────────────────── */}
      {activeSubTab === 'golive-prep' && activeTab === 'overview' && (
        <div className="kc-card">
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>🚀 Go-Live Vorbereitung</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>
            Vorher/Nachher-Screenshots und Website-Vergleich: Wechsle zu Übersicht → Unternehmen für den Screenshot-Bereich.
          </div>
        </div>
      )}

      {/* ── Live-Daten Tab ─────────────────────────────────────────────────── */}
      {(activeSubTab === 'live-data' || activeTab === 'live-data') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="kc-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
            <InfoBlock label="Phase" value={project.status?.replace('phase_', 'Phase ') || '—'} />
            <InfoBlock label="PageSpeed Mobile" value={project.pagespeed_mobile != null ? `${project.pagespeed_mobile}/100` : '—'} mono />
            <InfoBlock label="PageSpeed Desktop" value={project.pagespeed_desktop != null ? `${project.pagespeed_desktop}/100` : '—'} mono />
            <InfoBlock label="Domain erreichbar" value={project.domain_reachable === true ? '✅ Ja' : project.domain_reachable === false ? '❌ Nein' : '—'} />
            {project.domain_checked_at && <InfoBlock label="Zuletzt geprüft" value={new Date(project.domain_checked_at).toLocaleDateString('de-DE')} />}
          </div>
        </div>
      )}

      {/* ── Hosting-Zugangsdaten Tab ────────────────────────────────────────── */}
      {activeSubTab === 'hosting-keys' && (
        <div style={{ background: 'var(--bg-app)', border: '2px dashed var(--border-light)', borderRadius: 8, padding: 40, textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🔑</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Hosting-Zugangsdaten</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Sicher verschlüsselt — Zugangsdaten-Safe (in Entwicklung)</div>
        </div>
      )}

      {/* ── Trustpilot Tab ─────────────────────────────────────────────────── */}
      {(activeSubTab === 'trustpilot' || activeTab === 'trustpilot') && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 32 }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>⭐</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>Trustpilot-Bewertung anfragen</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 20 }}>
            Fordere deinen Kunden auf, eine Bewertung auf Trustpilot zu hinterlassen.
          </div>
          <button onClick={() => setShowApproval(true)}
            style={{ padding: '10px 28px', background: '#00b67a', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
            ⭐ Bewertungsanfrage senden
          </button>
        </div>
      )}

      {/* ── Upsell Tab ─────────────────────────────────────────────────────── */}
      {(activeSubTab === 'upsell' || activeTab === 'upsell') && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>💼 Upsell-Produkte</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
            {[
              { name: 'SEO-Retainer', price: '129€/Monat', features: ['Monatliche Keyword-Analyse', 'On-Page Optimierung', 'Monatlicher Report'] },
              { name: 'Wartungspaket', price: '49€/Monat', features: ['Updates & Sicherheit', 'Backup täglich', 'Support per Chat'] },
              { name: 'Digital Rundum', price: '249€/Monat', features: ['SEO + Wartung', 'Google Ads Management', 'Monatliches Strategie-Call'] },
            ].map(pkg => (
              <div key={pkg.name} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 10, padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>{pkg.name}</div>
                <div style={{ fontSize: 20, fontWeight: 800, color: '#0d6efd' }}>{pkg.price}</div>
                <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
                  {pkg.features.map(f => <li key={f}>{f}</li>)}
                </ul>
                <button onClick={() => setShowApproval(true)}
                  style={{ marginTop: 'auto', padding: '8px 0', background: '#0d6efd', color: '#fff', border: 'none', borderRadius: 7, fontWeight: 600, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                  Angebot senden
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Edit Modal ──────────────────────────────────────────────────────── */}
      {showEdit && (
        <EditModal
          project={project}
          lead={lead}
          latestAudit={latestAudit || null}
          token={token}
          onClose={() => setShowEdit(false)}
          onSaved={() => { setShowEdit(false); loadProject(); }}
        />
      )}

      {/* ── Approval Modal ──────────────────────────────────────────────────── */}
      {showApproval && (
        <ApprovalModal
          projectId={project.id}
          token={token}
          onClose={() => setShowApproval(false)}
        />
      )}

      {/* ── Sitemap Planer Modal ────────────────────────────────────────────── */}
      {showSitemapPlaner && project.lead_id && (
        <SitemapPlaner
          leadId={project.lead_id}
          leadData={project}
          onClose={() => { setShowSitemapPlaner(false); loadSitemapPages(); }}
        />
      )}

      {/* ── QA-Checkliste Tab ───────────────────────────────────────────────── */}
      {activeTab === 'qa' && (
        <div className="kc-card">
          <QAChecklist
            projectId={id}
            token={localStorage.getItem('kompagnon_token')}
            qaChecklistJson={project.qa_checklist_json}
            pagespeedMobile={project.pagespeed_mobile}
            pagespeedDesktop={project.pagespeed_desktop}
          />
        </div>
      )}

      {/* ── Go-Live Tab ─────────────────────────────────────────────────────── */}
      {activeTab === 'golive' && (() => {
        const psMob  = project.pagespeed_mobile         ?? null;
        const psDes  = project.pagespeed_desktop        ?? null;
        const psMobA = project.pagespeed_after_mobile   ?? null;
        const psDesA = project.pagespeed_after_desktop  ?? null;
        const diffMob = (psMob !== null && psMobA !== null) ? psMobA - psMob : null;
        const diffDes = (psDes !== null && psDesA !== null) ? psDesA - psDes : null;

        const scoreColor = (s) =>
          s === null ? 'var(--text-tertiary)' : s >= 90 ? '#1D9E75' : s >= 70 ? '#BA7517' : '#E24B4A';

        const diffColor = (d) =>
          d === null ? 'var(--text-tertiary)' : d > 0 ? '#1D9E75' : d < 0 ? '#E24B4A' : 'var(--text-secondary)';

        const diffLabel = (d) =>
          d === null ? '—' : d > 0 ? `+${d} Punkte` : d < 0 ? `${d} Punkte` : '±0 Punkte';

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* ── DIGITALE ABNAHME ── */}
            <div style={{
              background: project.abnahme_datum ? '#EAF3DE' : 'var(--bg-surface)',
              border: `0.5px solid ${project.abnahme_datum ? '#97C459' : 'var(--border-light)'}`,
              borderRadius: 12, padding: '18px 20px',
            }}>
              <div style={{
                fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
                textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 10,
              }}>
                Digitale Abnahme
              </div>

              {project.abnahme_datum ? (
                <div>
                  <div style={{ fontSize: 16, fontWeight: 500, color: '#1D9E75', marginBottom: 4 }}>
                    ✓ Abgenommen
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    am {project.abnahme_datum.replace('T', ' ')} Uhr
                    von <strong>{project.abnahme_durch}</strong>
                  </div>
                  <button
                    onClick={() => {
                      if (window.confirm('Abnahme zurücksetzen?')) {
                        fetch(`${API_BASE_URL}/api/projects/${id}/abnahme`,
                          { method: 'POST', headers: hdr, body: JSON.stringify({ name: '', reset: true }) })
                          .then(() => loadProject());
                      }
                    }}
                    style={{
                      marginTop: 10, padding: '5px 12px', borderRadius: 7,
                      border: '0.5px solid var(--border-light)',
                      background: 'transparent', color: 'var(--text-secondary)',
                      fontSize: 11, cursor: 'pointer',
                    }}
                  >
                    Abnahme zurücksetzen
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 12 }}>
                    Kunde erteilt die finale Abnahme vor dem Go-Live.
                  </div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <input
                      value={abnahmeName}
                      onChange={e => setAbnahmeName(e.target.value)}
                      placeholder="Name des Abnehmers (z.B. Thomas Becker)"
                      style={{
                        flex: '1 1 220px', padding: '8px 11px',
                        border: '1.5px solid var(--border-light)',
                        borderRadius: 8, fontSize: 13,
                        fontFamily: 'inherit', outline: 'none',
                        background: 'var(--bg-app)', color: 'var(--text-primary)',
                        minWidth: 0,
                      }}
                    />
                    <button
                      onClick={doAbnahme}
                      disabled={abnahmeLoading}
                      style={{
                        padding: '9px 18px', borderRadius: 8, border: 'none',
                        background: abnahmeLoading ? '#94a3b8' : '#1D9E75',
                        color: 'white', fontSize: 13, fontWeight: 600,
                        cursor: abnahmeLoading ? 'not-allowed' : 'pointer',
                        flexShrink: 0,
                      }}
                    >
                      {abnahmeLoading ? 'Wird gespeichert…' : '✓ Abnahme erteilen'}
                    </button>
                  </div>
                  {abnahmeMsg && (
                    <div style={{
                      marginTop: 8, fontSize: 12,
                      color: abnahmeMsg.startsWith('✓') ? '#1D9E75' : '#E24B4A',
                    }}>
                      {abnahmeMsg}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ── VORHER / NACHHER ── */}
            <div style={{
              background: 'var(--bg-surface)',
              border: '0.5px solid var(--border-light)',
              borderRadius: 12, overflow: 'hidden',
            }}>
              <div style={{
                padding: '11px 18px', background: 'var(--bg-app)',
                borderBottom: '0.5px solid var(--border-light)',
                display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                  Vorher / Nachher — PageSpeed & Screenshot
                </div>
                <button
                  onClick={doGoLivePagespeed}
                  disabled={psLoading}
                  style={{
                    padding: '6px 14px', borderRadius: 7, border: 'none',
                    background: psLoading ? '#94a3b8' : '#008eaa',
                    color: 'white', fontSize: 12, fontWeight: 600,
                    cursor: psLoading ? 'not-allowed' : 'pointer',
                  }}
                >
                  {psLoading ? '⏳ Wird gemessen…' : '⚡ Jetzt messen'}
                </button>
              </div>

              {psMsg && (
                <div style={{
                  padding: '8px 18px', fontSize: 12,
                  borderBottom: '0.5px solid var(--border-light)',
                  color:      psMsg.startsWith('✓') ? '#1D9E75' : '#E24B4A',
                  background: psMsg.startsWith('✓') ? '#EAF3DE' : '#FFF1F1',
                }}>
                  {psMsg}
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0 }}>

                {/* VORHER */}
                <div style={{ padding: '18px 20px', borderRight: '0.5px solid var(--border-light)' }}>
                  <div style={{
                    fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12,
                  }}>
                    Vorher
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginBottom: 14, flexWrap: 'wrap' }}>
                    {[['Mobil', psMob], ['Desktop', psDes]].map(([lbl, val]) => (
                      <div key={lbl}>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 2 }}>{lbl}</div>
                        <div style={{ fontSize: 32, fontWeight: 500, color: scoreColor(val) }}>{val ?? '—'}</div>
                      </div>
                    ))}
                  </div>
                  {project.screenshot_before ? (
                    <img
                      src={project.screenshot_before.startsWith('data:')
                        ? project.screenshot_before
                        : `data:image/jpeg;base64,${project.screenshot_before}`}
                      alt="Screenshot Vorher"
                      style={{ width: '100%', borderRadius: 8, border: '0.5px solid var(--border-light)', display: 'block' }}
                    />
                  ) : (
                    <div style={{
                      height: 120, border: '0.5px dashed var(--border-light)',
                      borderRadius: 8, display: 'flex', alignItems: 'center',
                      justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 12,
                    }}>
                      Kein Screenshot vorhanden
                    </div>
                  )}
                </div>

                {/* NACHHER */}
                <div style={{ padding: '18px 20px' }}>
                  <div style={{
                    fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)',
                    textTransform: 'uppercase', letterSpacing: '.06em', marginBottom: 12,
                  }}>
                    Nachher
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginBottom: 14, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                    {[['Mobil', psMobA, diffMob], ['Desktop', psDesA, diffDes]].map(([lbl, val, diff]) => (
                      <div key={lbl}>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 2 }}>{lbl}</div>
                        <div style={{ fontSize: 32, fontWeight: 500, color: scoreColor(val) }}>{val ?? '—'}</div>
                        {diff !== null && (
                          <div style={{ fontSize: 13, fontWeight: 600, color: diffColor(diff), marginTop: 2 }}>
                            {diffLabel(diff)}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  {project.screenshot_after ? (
                    <img
                      src={project.screenshot_after.startsWith('data:')
                        ? project.screenshot_after
                        : `data:image/jpeg;base64,${project.screenshot_after}`}
                      alt="Screenshot Nachher"
                      style={{ width: '100%', borderRadius: 8, border: '0.5px solid var(--border-light)', display: 'block' }}
                    />
                  ) : (
                    <div style={{
                      height: 120, border: '0.5px dashed var(--border-light)',
                      borderRadius: 8, display: 'flex', alignItems: 'center',
                      justifyContent: 'center', color: 'var(--text-tertiary)', fontSize: 12,
                    }}>
                      Noch nicht gemessen — "Jetzt messen" klicken
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Hinweis */}
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              "Jetzt messen" startet PageSpeed + Screenshot nach Go-Live.
              Werte aus "Vorher" kommen aus dem ursprünglichen Audit beim Lead.
            </div>
          </div>
        );
      })()}

      {/* ── Post-Launch Tab ─────────────────────────────────────────────────── */}
      {activeTab === 'postlaunch' && (() => {
        const GBP_ITEMS = [
          { id: 'profil_beansprucht',     label: 'Google Business Profil beansprucht' },
          { id: 'adresse_oeffnungszeiten', label: 'Adresse + Öffnungszeiten korrekt hinterlegt' },
          { id: 'fotos_5',               label: 'Mindestens 5 Fotos hochgeladen' },
          { id: 'leistungsbeschreibung', label: 'Leistungsbeschreibung vollständig ausgefüllt' },
          { id: 'erste_bewertung',       label: 'Erste Kundenbewertung eingegangen' },
          { id: 'antwort_bewertung',     label: 'Auf erste Bewertung geantwortet' },
        ];

        const gbpTotal   = GBP_ITEMS.length;
        const gbpDone    = GBP_ITEMS.filter(i => gbpChecked[i.id]).length;
        const gbpAllDone = gbpDone === gbpTotal;

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* ── QR-CODE BEWERTUNGEN ── */}
            <div style={{
              background: 'var(--bg-surface)',
              border: '0.5px solid var(--border-light)',
              borderRadius: 12, overflow: 'hidden',
            }}>
              <div style={{
                padding: '12px 18px', background: 'var(--bg-app)',
                borderBottom: '0.5px solid var(--border-light)',
                display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', flexWrap: 'wrap', gap: 10,
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    QR-Code für Google-Bewertungen
                  </div>
                  {gbpData?.rating && (
                    <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
                      ⭐ {gbpData.rating?.toFixed(1)} ({gbpData.ratings_total} Bewertungen)
                    </div>
                  )}
                </div>
                {!gbpQrData && (
                  <button
                    onClick={loadGbpQr}
                    disabled={gbpQrLoading}
                    style={{
                      padding: '7px 16px', borderRadius: 8, border: 'none',
                      background: gbpQrLoading ? '#94a3b8' : '#008eaa',
                      color: 'white', fontSize: 12, fontWeight: 600,
                      cursor: gbpQrLoading ? 'not-allowed' : 'pointer',
                    }}
                  >
                    {gbpQrLoading ? '⏳ Wird generiert…' : 'QR-Code generieren'}
                  </button>
                )}
              </div>

              <div style={{ padding: '18px 20px' }}>
                {gbpQrError && (
                  <div style={{
                    background: '#FFF1F1', border: '0.5px solid #FECACA',
                    borderRadius: 8, padding: '10px 14px',
                    fontSize: 12, color: '#A32D2D', marginBottom: 14,
                  }}>
                    ⚠ {gbpQrError}
                    {!gbpData?.available && (
                      <div style={{ marginTop: 6, fontSize: 11 }}>
                        Tipp: Zuerst GBP-Check in der Nutzerkartei durchführen
                        (Tab "Übersicht" → "Neu prüfen")
                      </div>
                    )}
                  </div>
                )}

                {gbpQrData ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 20, alignItems: 'start' }}>
                    {/* QR-Bild */}
                    <div>
                      <div style={{
                        background: 'white', border: '0.5px solid var(--border-light)',
                        borderRadius: 10, padding: 12, display: 'inline-block',
                      }}>
                        <img src={gbpQrData} alt="Bewertungs-QR-Code"
                             style={{ width: 156, height: 156, display: 'block' }} />
                      </div>
                      <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                        <button onClick={downloadGbpQr} style={{
                          flex: 1, padding: '7px 10px', borderRadius: 7,
                          border: 'none', background: '#008eaa', color: 'white',
                          fontSize: 11, fontWeight: 600, cursor: 'pointer',
                        }}>
                          ⬇ PNG laden
                        </button>
                        {gbpData?.review_url && (
                          <button
                            onClick={() => navigator.clipboard.writeText(gbpData.review_url)}
                            style={{
                              flex: 1, padding: '7px 10px', borderRadius: 7,
                              border: '0.5px solid var(--border-light)',
                              background: 'transparent', color: 'var(--text-secondary)',
                              fontSize: 11, cursor: 'pointer',
                            }}
                          >
                            📋 Link
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Infos */}
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', marginBottom: 8 }}>
                        Einsatzmöglichkeiten
                      </div>
                      {[
                        ['🖨️', 'Theke / Empfang',  'QR-Code ausdrucken und aufstellen'],
                        ['🚗', 'Fahrzeuge',         'Als Aufkleber auf Firmenfahrzeuge'],
                        ['📄', 'Rechnungen',        'Unten auf jeder Rechnung abdrucken'],
                        ['✉️', 'E-Mail-Signatur',   'Als Link in der E-Mail-Signatur'],
                        ['📱', 'WhatsApp Status',   'Link im Business-Account teilen'],
                      ].map(([icon, titel, beschr]) => (
                        <div key={titel} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-start' }}>
                          <span style={{ fontSize: 13, flexShrink: 0 }}>{icon}</span>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>{titel}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>{beschr}</div>
                          </div>
                        </div>
                      ))}
                      {gbpData?.review_url && (
                        <div style={{
                          marginTop: 12, background: 'var(--bg-app)',
                          border: '0.5px solid var(--border-light)',
                          borderRadius: 8, padding: '8px 10px',
                        }}>
                          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginBottom: 3 }}>
                            Bewertungs-Link
                          </div>
                          <div style={{ fontSize: 10, fontFamily: 'monospace', color: '#008eaa', wordBreak: 'break-all' }}>
                            {gbpData.review_url}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : !gbpQrError && !gbpQrLoading && (
                  <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-tertiary)', fontSize: 13 }}>
                    QR-Code generieren um Google-Bewertungen zu erleichtern
                  </div>
                )}
              </div>
            </div>

            {/* ── GBP-CHECKLISTE ── */}
            <div style={{
              background: gbpAllDone ? '#EAF3DE' : 'var(--bg-surface)',
              border: `0.5px solid ${gbpAllDone ? '#97C459' : 'var(--border-light)'}`,
              borderRadius: 12, overflow: 'hidden',
            }}>
              <div style={{
                padding: '11px 18px',
                background: gbpAllDone ? '#EAF3DE' : 'var(--bg-app)',
                borderBottom: '0.5px solid var(--border-light)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span>🏢</span> Google Business Optimierung
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '2px 9px', borderRadius: 10,
                  background: gbpAllDone ? '#97C459' : 'var(--border-light)',
                  color:      gbpAllDone ? '#27500A' : 'var(--text-secondary)',
                }}>
                  {gbpDone}/{gbpTotal}
                </span>
              </div>

              {GBP_ITEMS.map((item, idx) => {
                const isChecked = !!gbpChecked[item.id];
                return (
                  <div
                    key={item.id}
                    onClick={() => toggleGbpItem(item.id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 12,
                      padding: '11px 18px',
                      borderBottom: idx < GBP_ITEMS.length - 1 ? '0.5px solid var(--border-light)' : 'none',
                      cursor: 'pointer',
                      background: isChecked ? 'rgba(29,158,117,0.04)' : 'transparent',
                      transition: 'background .1s',
                    }}
                  >
                    <div style={{
                      width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                      border:     isChecked ? 'none' : '1.5px solid var(--border-medium)',
                      background: isChecked ? '#1D9E75' : 'transparent',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'all .15s',
                    }}>
                      {isChecked && (
                        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                          <path d="M1 4L3.5 6.5L9 1" stroke="white"
                                strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      )}
                    </div>
                    <span style={{
                      flex: 1, fontSize: 13,
                      color:          isChecked ? 'var(--text-secondary)' : 'var(--text-primary)',
                      textDecoration: isChecked ? 'line-through' : 'none',
                      transition: 'all .15s',
                    }}>
                      {item.label}
                    </span>
                  </div>
                );
              })}

              {gbpAllDone && (
                <div style={{
                  padding: '12px 18px', background: '#EAF3DE',
                  fontSize: 13, fontWeight: 600, color: '#1D9E75',
                  display: 'flex', alignItems: 'center', gap: 6,
                  borderTop: '0.5px solid #97C459',
                }}>
                  ✓ Google Business Profil vollständig optimiert!
                </div>
              )}
            </div>

            {/* Hinweis */}
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              QR-Code und Checkliste sind für die 30-tägige Post-Launch-Betreuung.
              Der QR-Code ist eindeutig für dieses Google Business Profil.
            </div>
          </div>
        );
      })()}

      {/* ── Placeholder-Tabs ────────────────────────────────────────────────── */}
      {activeTab === 'checklists' && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>Checklisten</p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}
      {activeTab === 'zeit' && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>Zeiterfassung</p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}
      {activeTab === 'kommunikation' && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>Kommunikation</p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}

      {/* ── Null-Übersicht Tab ──────────────────────────────────────────────── */}
      {activeTab === 'null-uebersicht' && (() => {
        const phaseNum  = parseInt((project.status || '').replace('phase_', '')) || 1;
        const phaseName = ['Onboarding','Briefing','Content','Technik','Go Live','QM','Post-Launch','Fertig'][phaseNum - 1] || 'Onboarding';
        const statusColor = project.status?.includes('abgeschlossen')
          ? { bg: '#f3f4f6', text: '#6b7280' }
          : project.status?.includes('pausiert')
          ? { bg: '#fef3c7', text: '#92400e' }
          : { bg: '#dcfce7', text: '#166534' };
        const statusLabel = project.status?.includes('abgeschlossen') ? 'Abgeschlossen'
          : project.status?.includes('pausiert') ? 'Pausiert' : 'Aktiv';
        const marginPct = margin?.margin_percent ?? null;
        const marginColor = marginPct === null ? 'var(--text-tertiary)'
          : marginPct < 30 ? '#E24B4A' : marginPct < 50 ? '#BA7517' : '#1D9E75';

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Bereich 1 — Status */}
            <div className="kc-card">
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>📊 Projektstatus</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center', marginBottom: 14 }}>
                <span style={{ padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700, background: statusColor.bg, color: statusColor.text }}>
                  {statusLabel}
                </span>
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Phase <strong>{phaseNum}</strong> von 7 · {phaseName}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 12, color: 'var(--text-secondary)' }}>
                <div>
                  <span style={{ color: 'var(--text-tertiary)' }}>Start: </span>
                  {project.start_date ? new Date(project.start_date).toLocaleDateString('de-DE') : '–'}
                </div>
                <div>
                  <span style={{ color: 'var(--text-tertiary)' }}>Go-Live: </span>
                  {project.target_go_live || project.go_live_date
                    ? new Date(project.target_go_live || project.go_live_date).toLocaleDateString('de-DE')
                    : '–'}
                </div>
              </div>
            </div>

            {/* Bereich 2 — Marge */}
            <div className="kc-card">
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>💰 Marge & Kosten</div>
              {margin ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Fixpreis</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>€{(project.fixed_price || 0).toFixed(2)}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Geleistete Stunden</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>{(project.actual_hours || 0).toFixed(1)}h</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Marge</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: marginColor, fontVariantNumeric: 'tabular-nums' }}>
                      {marginPct !== null ? `${marginPct.toFixed(1)}%` : '–'}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Gesamtkosten</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontVariantNumeric: 'tabular-nums' }}>€{(margin.total_costs || 0).toFixed(2)}</div>
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: 13, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Noch keine Stunden erfasst</div>
              )}
            </div>

            {/* Bereich 3 — Nachrichten */}
            <div className="kc-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)' }}>💬 Nachrichten</div>
                <button onClick={() => setShowNewMessageModal(true)} style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: 'var(--brand-primary)', color: '#fff',
                  border: 'none', fontSize: 18, cursor: 'pointer', lineHeight: 1,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>+</button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
                {['Erste Nachricht vom Kunden erscheint hier...', 'Interne Notiz erscheint hier...', 'Statusmeldung erscheint hier...'].map((txt, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)', opacity: 0.5 }}>
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--border-light)', flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{txt}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>vor {i + 1} Tagen</div>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-tertiary)', fontStyle: 'italic' }}>Nachrichtenfunktion wird in Kürze aktiviert</div>
            </div>
          </div>
        );
      })()}

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
        <BriefingWizard
          leadId={project.lead_id}
          leadData={briefingData}
          onClose={() => setShowBriefingWizard(false)}
          onComplete={() => setShowBriefingWizard(false)}
        />
      )}

      {/* ── Content Manager ─────────────────────────────────────────────────── */}
      {showContentManager && project.lead_id && (
        <ContentManager
          leadId={project.lead_id}
          leadName={project.company_name}
          token={token}
          onClose={() => { setShowContentManager(false); setContentSummary([]); }}
        />
      )}

      {/* ── GrapesJS Editor ─────────────────────────────────────────────────── */}
      {editingPage && (
        <GrapesEditor
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
        />
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
