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
import ProjectFilesSection from '../components/ProjectFilesSection';
import HomepageChecklist from '../components/HomepageChecklist';
import SecurityChecklist from '../components/SecurityChecklist';
import PageSpeedSection from '../components/PageSpeedSection';
import SitemapPlaner from '../components/SitemapPlaner';
import GrapesEditor from '../components/GrapesEditor';
import ContentManager from '../components/ContentManager';
import AuditReport from '../components/AuditReport';
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

const PHASE_TOOLS = {
  'onboarding': [
    { id: 'null-uebersicht', label: 'Null-Übersicht',       icon: '📊', sub: 'Status · Marge · Nachrichten' },
    { id: 'audits',          label: 'Audit',                icon: '🔍', sub: 'Bericht' },
    { id: 'unternehmen',     label: 'Briefing Unternehmen', icon: '🏢', sub: 'Stammdaten' },
    { id: 'crawler',         label: 'Crawler',              icon: '🕷️', sub: 'URLs erfasst' },
    { id: 'website-content', label: 'Website-Content',      icon: '🌐', sub: '50 Seiten', badge: '!' },
    { id: 'hosting',         label: 'Hosting-Crawling',     icon: '🖥️', sub: 'Scan' },
    { id: 'hosting-form',    label: 'Hosting-Fragebogen',   icon: '📋', sub: 'Fragebogen' },
    { id: 'branddesign',     label: 'Brand-Design-PDF',     icon: '🎨', sub: 'Dreiseitig' },
    { id: 'pagespeed',       label: 'Page-Speed',           icon: '⚡', sub: 'Score' },
  ],
  'briefing': [
    { id: 'briefing',        label: 'Briefing-Webseite',    icon: '📋', sub: 'Fragenkatalog' },
  ],
  'content': [
    { id: 'sitemap',         label: 'Website neu',          icon: '🗺️', sub: 'Seitenstruktur' },
    { id: 'content',         label: 'Content neu',          icon: '📝', sub: 'Texte & Medien' },
    { id: 'design',          label: 'Design',               icon: '🎨', sub: 'Entwürfe' },
    { id: 'preview',         label: 'Vorschau',             icon: '👁',  sub: 'Vorschau' },
    { id: 'editor',          label: 'Editor',               icon: '🖊️', sub: 'GrapesJS' },
  ],
  'technik': [
    { id: 'netlify-dns',     label: 'Netlify / WP',         icon: '🚀', sub: 'Installieren' },
    { id: 'dns',             label: 'DNS-Einstellungen',    icon: '🌍', sub: 'Beim Kunden' },
  ],
  'go-live': [
    { id: 'checklists',      label: 'Go-Live',              icon: '🚀', sub: 'Checkliste' },
  ],
  'qm': [
    { id: 'checklists',      label: 'Checkliste QM',        icon: '✅', sub: 'QA-Prüfung' },
  ],
  'post-launch': [
    { id: 'trustpilot',      label: 'Trustpilot',           icon: '⭐', sub: 'Bewertungen' },
  ],
  'fertig': [
    { id: 'live-data',       label: 'Fertige Website',      icon: '🌐', sub: 'Live' },
    { id: 'upsell',          label: 'Up-Sales',             icon: '💼', sub: 'Upsell-Produkte' },
  ],
};
const PHASE_NAMES = ['onboarding','briefing','content','technik','go-live','qm','post-launch','fertig'];
const PHASE_LABELS = {
  'onboarding':  'Onboarding',
  'briefing':    'Briefing',
  'content':     'Content',
  'technik':     'Technik',
  'go-live':     'Go Live',
  'qm':          'QM',
  'post-launch': 'Post-Launch',
  'fertig':      'Fertig',
};

const SUB_TAB_MAP = {
  'unternehmen':     'overview',
  'briefing-quick':  'briefing',
  'briefing':        'briefing',
  'brand-design':    'branddesign',
  'branddesign':     'branddesign',
  'website-content': 'webcontent',
  'hosting-scan':    'hosting',
  'hosting':         'hosting',
  'hosting-form':    'hosting',
  'checkliste':      'checklists',
  'checklists':      'checklists',
  'design':          'design',
  'sitemap':         'sitemap',
  'content':         'content',
  'crawler':         'crawler',
  'golive-prep':     'overview',
  'dns':             'hosting',
};

// Maps tool tile ID → which activeSubTab value to set (for content blocks keyed on activeSubTab)
const TOOL_SUBTAB_MAP = {
  'audits':      'audit',
  'preview':     'preview',
  'editor':      'editor',
  'netlify-dns': 'netlify-dns',
  'dns':         'hosting-form',
  'live-data':   'live-data',
  'trustpilot':  'trustpilot',
  'upsell':      'upsell',
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
            <input style={input} value={form.industry} onChange={e => set('industry', e.target.value)} placeholder="z.B. Gastronomie" />
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
  const [showNewMessageModal, setShowNewMessageModal] = useState(false);
  const [newMessageText, setNewMessageText] = useState('');
  const [briefingData, setBriefingData] = useState(null);
  // Checklists (lazy audit load)
  const [latestAudit, setLatestAudit] = useState(null);
  // Crawler
  const [crawlJob, setCrawlJob] = useState(null);
  const [crawlResults, setCrawlResults] = useState([]);
  const [crawlLoading, setCrawlLoading] = useState(false);
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

  const checkDomain = async () => {
    setDomainChecking(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/projects/${id}/domain-check`, { method: 'POST', headers });
      const d = await res.json();
      setProject(prev => ({ ...prev, domain_reachable: d.reachable, domain_status_code: d.status_code, domain_checked_at: d.checked_at }));
    } catch { /* silent */ } finally { setDomainChecking(false); }
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="skeleton" style={{ height: 40, width: 300 }} />
        <div className="skeleton" style={{ height: 60 }} />
        <div className="skeleton" style={{ height: 200 }} />
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
      toast.error('Fehler: ' + e.message);
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
      briefing_usp: briefing?.usp || '',
      briefing_leistungen: briefing?.leistungen || '',
      briefing_zielgruppe: briefing?.zielgruppe || '',
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
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
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
                  <div style={{ alignSelf: 'center', height: 2, width: 12, flexShrink: 0, background: isDone ? '#1D9E75' : 'var(--border-light)' }} />
                )}
                <button onClick={() => {
                  setActivePhase(phaseName);
                  const firstTool = PHASE_TOOLS[phaseName]?.[0]?.id;
                  if (firstTool) setActiveTab(SUB_TAB_MAP[firstTool] || firstTool);
                }} style={{
                  flex: 1, minWidth: 70, padding: '10px 4px 8px', border: 'none',
                  borderBottom: isActive ? '3px solid #185FA5' : '3px solid transparent',
                  background: isActive ? '#E6F1FB' : 'transparent',
                  cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
                  borderRadius: 0, transition: 'all 0.15s',
                }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: '50%',
                    background: isDone ? '#1D9E75' : isCurrent ? '#185FA5' : '#e2e8f0',
                    color: (isDone || isCurrent) ? '#fff' : '#64748b',
                    fontSize: 11, fontWeight: 600,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>{isDone ? '✓' : phaseNum}</div>
                  <span style={{
                    fontSize: 11,
                    fontWeight: isActive ? 600 : 400,
                    color: isActive ? '#185FA5' : isDone ? '#1D9E75' : '#64748b',
                    whiteSpace: 'nowrap',
                  }}>{PHASE_LABELS[phaseName]}</span>
                </button>
              </React.Fragment>
            );
          })}
        </div>

        {/* Werkzeug-Kacheln (Ebene 2) */}
        <div style={{ position: 'relative', padding: '10px 0 8px' }}>
          {/* Pfeil links */}
          <button onClick={() => scrollRef.current?.scrollBy({ left: -140, behavior: 'smooth' })} style={{
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
                <div key={tool.id} onClick={() => {
                  setActiveTab(SUB_TAB_MAP[tool.id] || tool.id);
                  setActiveSubTab(TOOL_SUBTAB_MAP[tool.id] || tool.id);
                  if (tool.id === 'unternehmen') setShowBriefingWizard(true);
                }} style={{
                  flex: '0 0 120px', minWidth: 120,
                  background: isActive ? 'var(--brand-primary-light)' : 'var(--bg-surface)',
                  border: isActive
                    ? '1.5px solid var(--brand-primary)'
                    : '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '12px 10px', cursor: 'pointer', textAlign: 'center',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
                  position: 'relative',
                }}>
                  {tool.badge && (
                    <span style={{
                      position: 'absolute', top: 6, right: 6,
                      background: '#E24B4A', color: 'white',
                      fontSize: 9, fontWeight: 600, borderRadius: 99, padding: '1px 5px',
                    }}>{tool.badge}</span>
                  )}
                  <div style={{
                    width: 38, height: 38, borderRadius: 8, fontSize: 18,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    background: isActive ? 'var(--brand-primary-mid)' : 'var(--bg-app)',
                  }}>{tool.icon}</div>
                  <div style={{
                    fontSize: 11, fontWeight: 500,
                    color: isActive ? 'var(--brand-primary-dark)' : 'var(--text-primary)',
                  }}>{tool.label}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{tool.sub}</div>
                </div>
              );
            })}
          </div>

          {/* Pfeil rechts */}
          <button onClick={() => scrollRef.current?.scrollBy({ left: 140, behavior: 'smooth' })} style={{
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

          {/* ── Website-Vergleich ─────────────────────────────────────────── */}
          {(() => {
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
          } catch { toast.error('Fehler beim Scraping'); }
          finally { setScraping(false); }
        };

        const analyzeScreenshot = async () => {
          setAnalyzing(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/branddesign/${lid}/analyze-screenshot`, { method: 'POST', headers: h });
            if (res.ok) { setBrandData(d => ({ ...d, ...(res.ok ? {} : {}) })); await loadBrandData(); }
            else { const e = await res.json().catch(() => ({})); toast.error(e.detail || 'Analyse fehlgeschlagen'); }
          } catch { toast.error('Fehler bei der Analyse'); }
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

      {/* ── Sitemap Tab ─────────────────────────────────────────────────────── */}
      {activeTab === 'sitemap' && (() => {
        if (!sitemapLoaded && !sitemapLoading) loadSitemapPages();
        const ST = {
          geplant:        { bg: '#EFF6FF', text: '#1D4ED8', label: 'Geplant' },
          in_bearbeitung: { bg: '#FEF9C3', text: '#92400E', label: 'In Bearb.' },
          freigegeben:    { bg: '#FEF3C7', text: '#B45309', label: 'Freigegeben' },
          live:           { bg: '#DCFCE7', text: '#166534', label: 'Live' },
        };
        const TI = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', sonstige: '📄' };
        const PAGE_TYPES = [
          { v: 'startseite', l: 'Startseite' }, { v: 'leistung', l: 'Leistung' },
          { v: 'info', l: 'Info' }, { v: 'vertrauen', l: 'Vertrauen' },
          { v: 'conversion', l: 'Conversion' }, { v: 'sonstige', l: 'Sonstige' },
        ];
        const inp = { width: '100%', padding: '7px 10px', fontSize: 13, border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', boxSizing: 'border-box' };
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Actions */}
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button onClick={() => setAddPageOpen(o => !o)}
                style={{ padding: '8px 16px', background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                ➕ Seite hinzufügen
              </button>
              <button onClick={() => setKiConfirm(true)} disabled={kiGenerating || !project.lead_id}
                style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: kiGenerating ? 0.6 : 1 }}>
                {kiGenerating ? '⏳ Generiere…' : '🤖 KI-Vorlage laden'}
              </button>
              <button onClick={downloadSitemapPdf}
                style={{ padding: '8px 16px', background: 'var(--bg-surface)', color: 'var(--text-primary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                📄 PDF herunterladen
              </button>
            </div>

            {/* KI confirm */}
            {kiConfirm && (
              <div style={{ background: '#FFF9E6', border: '1px solid #F5D87A', borderRadius: 'var(--radius-md)', padding: '12px 16px', fontSize: 13, color: '#92660A', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <span style={{ flex: 1 }}>⚠️ KI-Vorlage überschreibt alle Nicht-Pflicht-Seiten.</span>
                <button onClick={generateKI} style={{ padding: '6px 14px', background: '#d97706', color: '#fff', border: 'none', borderRadius: 6, fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Ja, generieren</button>
                <button onClick={() => setKiConfirm(false)} style={{ padding: '6px 14px', background: 'var(--bg-surface)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>Abbrechen</button>
              </div>
            )}

            {/* Add page form */}
            {addPageOpen && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Neue Seite anlegen</div>
                <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr 1fr', gap: 10 }}>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Seitenname *</label>
                    <input value={addPageForm.page_name} onChange={e => setAddPageForm(f => ({ ...f, page_name: e.target.value }))} placeholder="z.B. Leistungen" style={inp} />
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
                    <select value={addPageForm.page_type} onChange={e => setAddPageForm(f => ({ ...f, page_type: e.target.value }))} style={inp}>
                      {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Übergeordnete Seite</label>
                    <select value={addPageForm.parent_id} onChange={e => setAddPageForm(f => ({ ...f, parent_id: e.target.value }))} style={inp}>
                      <option value="">– Keine –</option>
                      {sitemapPages.filter(p => !p.ist_pflichtseite).map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
                    </select>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={createSitemapPage} disabled={addPageSaving || !addPageForm.page_name.trim()}
                    style={{ padding: '7px 16px', background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: addPageSaving ? 0.6 : 1 }}>
                    {addPageSaving ? 'Speichert…' : '💾 Anlegen'}
                  </button>
                  <button onClick={() => setAddPageOpen(false)}
                    style={{ padding: '7px 14px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 6, fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                    Abbrechen
                  </button>
                </div>
              </div>
            )}

            {/* Page list */}
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {sitemapLoading ? (
                <div style={{ padding: 32, textAlign: 'center' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
                </div>
              ) : sitemapPages.filter(p => !p.ist_pflichtseite).length === 0 ? (
                <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>
                  <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.3 }}>🗺️</div>
                  <div style={{ fontSize: 13 }}>Noch keine Seiten geplant.</div>
                </div>
              ) : (
                <>
                  {sitemapPages.filter(p => !p.ist_pflichtseite).map((page, index) => {
                    const st = ST[page.status] || ST.geplant;
                    const isDragOver = dragOverPageId === page.id;
                    return (
                      <div
                        key={page.id}
                        draggable
                        onDragStart={e => onDragStart(e, page.id)}
                        onDragOver={e => onDragOver(e, page.id)}
                        onDrop={e => onDrop(e, page.id)}
                        onDragEnd={onDragEnd}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
                          borderBottom: '1px solid var(--border-light)', flexWrap: 'wrap',
                          background: isDragOver ? 'var(--bg-hover)' : 'transparent',
                          borderTop: isDragOver ? '2px solid var(--brand-primary)' : '2px solid transparent',
                          transition: 'background 0.1s',
                        }}
                      >
                        <span style={{ cursor: 'grab', color: 'var(--text-tertiary)', fontSize: 14, marginRight: 2, userSelect: 'none' }}>⠿</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, marginRight: 4 }}>
                          <button onClick={() => movePageUp(page.id)} disabled={index === 0}
                            style={{ background: 'none', border: 'none', cursor: index === 0 ? 'default' : 'pointer',
                              fontSize: 12, color: index === 0 ? 'var(--border-light)' : 'var(--text-tertiary)',
                              padding: '1px 4px', lineHeight: 1 }}>▲</button>
                          <button onClick={() => movePageDown(page.id)}
                            disabled={index === sitemapPages.filter(p => !p.ist_pflichtseite).length - 1}
                            style={{ background: 'none', border: 'none',
                              cursor: index === sitemapPages.filter(p => !p.ist_pflichtseite).length - 1 ? 'default' : 'pointer',
                              fontSize: 12,
                              color: index === sitemapPages.filter(p => !p.ist_pflichtseite).length - 1 ? 'var(--border-light)' : 'var(--text-tertiary)',
                              padding: '1px 4px', lineHeight: 1 }}>▼</button>
                        </div>
                        <span style={{ fontSize: 17, flexShrink: 0 }}>{TI[page.page_type] || '📄'}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{page.page_name}</div>
                          {page.ziel_keyword && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{page.ziel_keyword}</div>}
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text, whiteSpace: 'nowrap', flexShrink: 0 }}>{st.label}</span>
                        {(() => {
                          const ab = (bg, color) => ({
                            padding: '4px 10px', fontSize: 11, fontWeight: 500,
                            background: bg, color: color, border: 'none',
                            borderRadius: 'var(--radius-md)', cursor: 'pointer', whiteSpace: 'nowrap',
                            fontFamily: 'var(--font-sans)', flexShrink: 0,
                          });
                          const openEditModal = (p) => { setEditPageModal(p); setEditPageForm({ page_name: p.page_name, page_type: p.page_type, ziel_keyword: p.ziel_keyword || '', zweck: p.zweck || '', cta_text: p.cta_text || '', status: p.status || 'geplant' }); };
                          const goToDesign = (p) => { setActiveTab('design'); setActiveDesignPage(p); setSelectedPageId(p.id); };
                          const goToContent = (p) => { setActiveTab('content'); setActiveContentPage(p); };
                          const previewPage = (p) => {
                            if (p.mockup_html) {
                              const w = window.open('', '_blank');
                              w.document.write(p.mockup_html); w.document.close();
                            } else toast.info('Noch kein Design vorhanden — zuerst Design generieren');
                          };
                          return (
                            <>
                              <button onClick={() => openEditModal(page)} style={ab('var(--bg-elevated)', 'var(--text-primary)')}>✏️ Bearbeiten</button>
                              <button onClick={() => goToDesign(page)} style={ab('var(--brand-primary)', '#fff')}>🎨 Design</button>
                              <button onClick={() => goToContent(page)} style={ab('#059669', '#fff')}>📝 Content</button>
                              <button onClick={() => previewPage(page)} style={ab('#7c3aed', '#fff')}>👁 Vorschau</button>
                              <button onClick={() => setEditingPage(page)} style={ab('#1a2332', '#fff')}>🖊️ Editor</button>
                              <button
                                onClick={() => setDeletingPageId(page.id)}
                                title="Seite löschen"
                                style={{
                                  padding: '4px 8px', fontSize: 11,
                                  background: 'var(--status-danger-bg)',
                                  color: 'var(--status-danger-text)',
                                  border: 'none', borderRadius: 'var(--radius-md)',
                                  cursor: 'pointer', flexShrink: 0,
                                }}
                              >
                                🗑️
                              </button>
                            </>
                          );
                        })()}
                      </div>
                    );
                  })}
                  {sitemapPages.filter(p => p.ist_pflichtseite).map((page, idx, arr) => {
                    const st = ST[page.status] || ST.geplant;
                    return (
                      <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', borderBottom: idx < arr.length - 1 ? '1px solid var(--border-light)' : 'none', background: 'var(--bg-app)' }}>
                        <span style={{ fontSize: 15, flexShrink: 0, color: 'var(--text-tertiary)' }}>🔒</span>
                        <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: 'var(--text-tertiary)' }}>{page.page_name}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: '#F3F4F6', color: '#6B7280' }}>⚖️ Pflicht</span>
                        <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 10, background: st.bg, color: st.text }}>{st.label}</span>
                      </div>
                    );
                  })}
                  <div style={{ padding: '8px 14px', fontSize: 11, color: 'var(--text-tertiary)', borderTop: '1px solid var(--border-light)' }}>
                    4 Pflichtseiten werden von KOMPAGNON rechtskonform befüllt.
                  </div>
                </>
              )}
            </div>

            {/* Edit page modal */}
            {editPageModal && createPortal(
              <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 1000, display: 'flex', alignItems: isMobile ? 'flex-end' : 'center', justifyContent: 'center', padding: isMobile ? 0 : 20 }}
                onClick={e => e.target === e.currentTarget && setEditPageModal(null)}>
                <div style={{ background: 'var(--bg-surface)', borderRadius: isMobile ? '16px 16px 0 0' : 'var(--radius-xl)', padding: 24, width: '100%', maxWidth: 480, maxHeight: isMobile ? '92vh' : '85vh', overflowY: 'auto' }}
                  onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                    <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Seite bearbeiten</span>
                    <button onClick={() => setEditPageModal(null)} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)' }}>×</button>
                  </div>
                  {[
                    { k: 'page_name', label: 'Seitenname', type: 'text' },
                    { k: 'ziel_keyword', label: 'Ziel-Keyword', type: 'text' },
                    { k: 'zweck', label: 'Zweck / Beschreibung', type: 'textarea' },
                    { k: 'cta_text', label: 'CTA-Text', type: 'text' },
                  ].map(f => (
                    <div key={f.k} style={{ marginBottom: 12 }}>
                      <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>{f.label}</label>
                      {f.type === 'textarea'
                        ? <textarea value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} rows={3} style={{ ...inp, resize: 'vertical' }} />
                        : <input type="text" value={editPageForm[f.k] || ''} onChange={e => setEditPageForm(p => ({ ...p, [f.k]: e.target.value }))} style={inp} />
                      }
                    </div>
                  ))}
                  <div style={{ marginBottom: 12 }}>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Typ</label>
                    <select value={editPageForm.page_type || 'info'} onChange={e => setEditPageForm(p => ({ ...p, page_type: e.target.value }))} style={inp}>
                      {PAGE_TYPES.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}
                    </select>
                  </div>
                  <div style={{ marginBottom: 20 }}>
                    <label style={{ fontSize: 11, color: 'var(--text-tertiary)', display: 'block', marginBottom: 4 }}>Status</label>
                    <select value={editPageForm.status || 'geplant'} onChange={e => setEditPageForm(p => ({ ...p, status: e.target.value }))} style={inp}>
                      <option value="geplant">Geplant</option>
                      <option value="in_bearbeitung">In Bearbeitung</option>
                      <option value="freigegeben">Freigegeben</option>
                      <option value="live">Live</option>
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={saveEditPage} disabled={editPageSaving}
                      style={{ flex: 1, padding: '10px', background: 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', opacity: editPageSaving ? 0.6 : 1 }}>
                      {editPageSaving ? 'Speichert…' : '💾 Speichern'}
                    </button>
                    <button onClick={() => setEditPageModal(null)}
                      style={{ flex: 1, padding: '10px', background: 'var(--bg-app)', color: 'var(--text-secondary)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', fontSize: 13, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      Abbrechen
                    </button>
                  </div>
                </div>
              </div>,
              document.body
            )}

            {/* Delete confirmation modal */}
            {deletingPageId && createPortal(
              <div style={{
                position: 'fixed', inset: 0,
                background: 'rgba(15,28,32,0.5)',
                zIndex: 1000, display: 'flex',
                alignItems: 'center', justifyContent: 'center',
                padding: 20,
              }} onClick={() => setDeletingPageId(null)}>
                <div onClick={e => e.stopPropagation()} style={{
                  background: 'var(--bg-surface)',
                  borderRadius: 'var(--radius-xl)',
                  padding: 28, maxWidth: 360, width: '100%',
                  textAlign: 'center',
                  boxShadow: 'var(--shadow-xl)',
                }}>
                  <div style={{ fontSize: 32, marginBottom: 12 }}>🗑️</div>
                  <h3 style={{ fontSize: 15, fontWeight: 700,
                    color: 'var(--text-primary)', marginBottom: 8 }}>
                    Seite löschen?
                  </h3>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)',
                    marginBottom: 20, lineHeight: 1.5 }}>
                    Diese Seite wird dauerhaft aus der Sitemap entfernt.
                    Diese Aktion kann nicht rückgängig gemacht werden.
                  </p>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <button onClick={() => setDeletingPageId(null)} style={{
                      flex: 1, padding: '10px 0',
                      background: 'var(--bg-app)',
                      border: '1px solid var(--border-light)',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 13, cursor: 'pointer',
                      fontFamily: 'var(--font-sans)',
                      color: 'var(--text-primary)',
                    }}>
                      Abbrechen
                    </button>
                    <button onClick={() => deleteSitemapPage(deletingPageId)} style={{
                      flex: 1, padding: '10px 0',
                      background: 'var(--status-danger-text)',
                      border: 'none',
                      borderRadius: 'var(--radius-md)',
                      fontSize: 13, fontWeight: 600,
                      cursor: 'pointer',
                      fontFamily: 'var(--font-sans)',
                      color: 'white',
                    }}>
                      Löschen
                    </button>
                  </div>
                </div>
              </div>,
              document.body
            )}
          </div>
        );
      })()}

      {/* ── Design Tab ──────────────────────────────────────────────────────── */}
      {/* ── Content Tab ──────────────────────────────────────────────────────── */}
      {activeTab === 'content' && (() => {
        const totalSlots = contentSummary.reduce((a, p) => a + (p.sections?.length || 0) + (p.media?.length || 0), 0);
        const doneSlots  = contentSummary.reduce((a, p) => a + (p.sections?.filter(s => s.status === 'freigegeben').length || 0) + (p.media?.filter(m => m.status === 'freigegeben').length || 0), 0);
        const pending    = totalSlots - doneSlots;
        const allDone    = totalSlots > 0 && pending === 0;

        if (contentSummary.length === 0 && project.lead_id) {
          fetch(`${API_BASE_URL}/api/content/${project.lead_id}`, { headers })
            .then(r => r.json()).then(d => setContentSummary(Array.isArray(d) ? d.filter(p => !p.ist_pflichtseite) : []));
        }

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {contentSummary.length > 0 && (
              <div style={{ padding: '10px 16px', borderRadius: 8, background: allDone ? '#D1FAE5' : '#FFFBEB', border: `1px solid ${allDone ? '#A7F3D0' : '#FDE68A'}`, fontSize: 13, color: allDone ? '#065F46' : '#92400E' }}>
                {allDone ? '✅ Alle Inhalte freigegeben — Design-Designer kann gestartet werden' : `⚠️ ${pending} Inhalt${pending !== 1 ? 'e' : ''} noch ausstehend — Design-Designer erst nach Freigabe empfohlen`}
              </div>
            )}

            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowContentManager(true)}
                style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}
              >
                📝 Content bearbeiten
              </button>
            </div>

            {contentSummary.length > 0 && (() => {
              const total = contentSummary.reduce((a, p) => a + (p.sections?.length || 0) + (p.media?.length || 0), 0);
              const done  = contentSummary.reduce((a, p) => a + (p.sections?.filter(s => s.status === 'freigegeben').length || 0) + (p.media?.filter(m => m.status === 'freigegeben').length || 0), 0);
              const pct   = total > 0 ? Math.round(done / total * 100) : 0;
              return (
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 8, marginBottom: 8 }}>
                  <div style={{ flex: 1, height: 6, background: 'var(--border-light)', borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: pct === 100 ? '#22C55E' : 'var(--brand-primary)', transition: 'width 0.4s ease', borderRadius: 3 }} />
                  </div>
                  <span style={{ fontSize: 12, fontWeight: 600, color: pct === 100 ? '#065F46' : 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{done}/{total} freigegeben ({pct}%)</span>
                </div>
              );
            })()}

            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {contentSummary.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Noch keine Content-Slots. Erst Sitemap anlegen, dann hier befüllen.
                </div>
              ) : (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px 100px 80px', gap: 0, borderBottom: '2px solid var(--border-light)', padding: '8px 16px' }}>
                    {['Seite', 'Text-Slots', 'Medien', 'Ampel'].map(l => (
                      <span key={l} style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{l}</span>
                    ))}
                  </div>
                  {contentSummary.map(page => {
                    const secTotal = page.sections?.length || 0;
                    const secDone  = page.sections?.filter(s => s.status === 'freigegeben').length || 0;
                    const medTotal = page.media?.length || 0;
                    const medDone  = page.media?.filter(m => m.status === 'freigegeben').length || 0;
                    const allFree  = secTotal + medTotal > 0 && secDone + medDone === secTotal + medTotal;
                    const partial  = secDone + medDone > 0;
                    return (
                      <div key={page.sitemap_page_id} style={{ display: 'grid', gridTemplateColumns: '1fr 120px 100px 80px', gap: 0, padding: '10px 16px', borderBottom: '1px solid var(--border-light)', alignItems: 'center' }}>
                        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>{page.page_name}</span>
                        <span style={{ fontSize: 12, color: secDone === secTotal && secTotal > 0 ? '#065F46' : 'var(--text-secondary)' }}>{secDone}/{secTotal} freigegeben</span>
                        <span style={{ fontSize: 12, color: medDone === medTotal && medTotal > 0 ? '#065F46' : 'var(--text-secondary)' }}>{medDone}/{medTotal}</span>
                        <span style={{ width: 14, height: 14, borderRadius: '50%', background: allFree ? '#22C55E' : partial ? '#F59E0B' : '#EF4444', display: 'inline-block' }} />
                      </div>
                    );
                  })}
                </>
              )}
            </div>
          </div>
        );
      })()}

      {activeTab === 'design' && (() => {
        if (sitemapPages.length === 0 && !sitemapLoading) loadSitemapPages();

        // Load saved versions once
        if (!designVersionsLoaded && project.lead_id) {
          setDesignVersionsLoaded(true);
          fetch(`${API_BASE_URL}/api/designs/${project.lead_id}`, { headers: h })
            .then(r => r.ok ? r.json() : [])
            .then(data => setDesignVersions(Array.isArray(data) ? data : []))
            .catch(() => {});
        }

        const saveCurrentVersion = async () => {
          if (!designResult || !project.lead_id) return;
          const selectedPage = sitemapPages.find(p => p.id === selectedPageId);
          const pageName = selectedPage?.page_name || 'Startseite';
          const versionName = `${pageName} – ${new Date().toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })}`;
          setSavingVersion(true);
          try {
            const html = buildHtmlFromContent(designResult);
            const res = await fetch(`${API_BASE_URL}/api/designs/${project.lead_id}`, {
              method: 'POST', headers: h,
              body: JSON.stringify({
                sitemap_page_id: selectedPageId || null,
                page_name: pageName,
                version_name: versionName,
                html_content: html,
              }),
            });
            if (res.ok) {
              toast.success('Version gespeichert');
              // Reload versions list
              fetch(`${API_BASE_URL}/api/designs/${project.lead_id}`, { headers: h })
                .then(r => r.ok ? r.json() : [])
                .then(data => setDesignVersions(Array.isArray(data) ? data : []));
            }
          } catch { toast.error('Fehler beim Speichern'); }
          finally { setSavingVersion(false); }
        };

        const loadVersion = async (versionId) => {
          const res = await fetch(`${API_BASE_URL}/api/designs/${project.lead_id}/${versionId}`, { headers: h });
          if (res.ok) {
            const data = await res.json();
            setDesignPreview({ html: data.html_content, version_name: data.version_name });
          }
        };

        const deleteVersion = async (versionId) => {
          if (!window.confirm('Version löschen?')) return;
          await fetch(`${API_BASE_URL}/api/designs/version/${versionId}`, { method: 'DELETE', headers: h });
          setDesignVersions(prev => prev.filter(v => v.id !== versionId));
          if (designPreview) setDesignPreview(null);
        };

        const activeHtml = designPreview ? designPreview.html : (designResult ? buildHtmlFromContent(designResult) : null);

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* ── Generator ── */}
            <div className="kc-card">
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 6 }}>KI-Website-Entwurf generieren</div>

              {sitemapPages.length > 0 && (
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 6 }}>
                    Welche Seite gestalten?
                  </label>
                  <select
                    value={selectedPageId || ''}
                    onChange={e => setSelectedPageId(Number(e.target.value) || null)}
                    style={{ width: '100%', maxWidth: 360, padding: '8px 10px', fontSize: 13, borderRadius: 8, border: '1.5px solid var(--border-medium)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontFamily: 'var(--font-sans)', cursor: 'pointer' }}
                  >
                    <option value="">– Keine Seite ausgewählt –</option>
                    {sitemapPages.map(p => <option key={p.id} value={p.id}>{p.page_name}</option>)}
                  </select>
                  {selectedPageId && (() => {
                    const pg = sitemapPages.find(p => p.id === selectedPageId);
                    if (!pg) return null;
                    return (
                      <div style={{ marginTop: 10, padding: '10px 14px', background: 'var(--bg-app)', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13 }}>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{pg.page_name}</span>
                        {pg.ziel_keyword && <span style={{ color: 'var(--text-tertiary)', marginLeft: 10 }}>🔑 {pg.ziel_keyword}</span>}
                        {pg.zweck && <div style={{ color: 'var(--text-secondary)', marginTop: 4, fontSize: 12 }}>{pg.zweck}</div>}
                      </div>
                    );
                  })()}
                </div>
              )}

              <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                Generiert Textentwürfe für die Website auf Basis der Briefing- und Sitemap-Daten.
              </div>
              <button
                onClick={generateDesign}
                disabled={designRunning}
                style={{ padding: '10px 22px', borderRadius: 8, border: 'none', background: designRunning ? 'var(--bg-muted)' : 'var(--brand-primary)', color: designRunning ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 600, cursor: designRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}
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

            {/* ── Aktuelle Vorschau (neu generiert oder aus Version geladen) ── */}
            {activeHtml && (
              <div className="kc-card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid var(--border-light)' }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {designPreview ? `📂 ${designPreview.version_name}` : '✨ Aktueller Entwurf'}
                  </span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {designPreview && (
                      <button onClick={() => setDesignPreview(null)}
                        style={{ fontSize: 12, padding: '4px 10px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                        ✕ Schließen
                      </button>
                    )}
                    {designResult && !designPreview && (
                      <button onClick={saveCurrentVersion} disabled={savingVersion}
                        style={{ fontSize: 12, padding: '4px 10px', background: '#008EAA', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: '#fff', fontWeight: 600 }}>
                        {savingVersion ? '…' : '💾 Version speichern'}
                      </button>
                    )}
                    <button onClick={() => { const w = window.open('', '_blank'); w.document.write(activeHtml); w.document.close(); }}
                      style={{ fontSize: 12, padding: '4px 10px', background: 'var(--bg-elevated)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                      Im Browser öffnen ↗
                    </button>
                  </div>
                </div>
                <iframe
                  srcDoc={activeHtml}
                  style={{ width: '100%', height: 600, border: 'none', background: '#fff', display: 'block' }}
                  title="Website Vorschau"
                  sandbox="allow-same-origin"
                />
              </div>
            )}

            {/* ── Gespeicherte Versionen ── */}
            <div className="kc-card">
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
                📂 Gespeicherte Entwürfe
                {designVersions.length > 0 && (
                  <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 500, background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 99, padding: '1px 8px', color: 'var(--text-tertiary)' }}>
                    {designVersions.length}
                  </span>
                )}
              </div>

              {designVersions.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-tertiary)', fontSize: 13, border: '1.5px dashed var(--border-medium)', borderRadius: 'var(--radius-lg)' }}>
                  Noch keine Versionen gespeichert — generiere einen Entwurf und klicke "💾 Version speichern"
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {designVersions.map(v => {
                    const isActive = designPreview && designPreview.version_name === v.version_name;
                    return (
                      <div key={v.id} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
                        padding: '10px 14px', borderRadius: 'var(--radius-md)',
                        background: isActive ? '#EAF4E0' : 'var(--bg-app)',
                        border: `1px solid ${isActive ? '#3B6D11' : 'var(--border-light)'}`,
                      }}>
                        <div style={{ minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {v.version_name || v.page_name}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                            {v.page_name} · {v.created_at}
                            {v.created_by && ` · ${v.created_by}`}
                          </div>
                        </div>
                        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                          <button onClick={() => loadVersion(v.id)}
                            style={{ fontSize: 12, padding: '4px 10px', background: isActive ? '#3B6D11' : 'var(--bg-surface)', border: `1px solid ${isActive ? '#3B6D11' : 'var(--border-light)'}`, borderRadius: 'var(--radius-md)', cursor: 'pointer', color: isActive ? '#fff' : 'var(--brand-primary)', fontWeight: 600 }}>
                            {isActive ? '✓ Aktiv' : '👁 Laden'}
                          </button>
                          <button onClick={() => deleteVersion(v.id)}
                            style={{ fontSize: 12, padding: '4px 8px', background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-text)', borderRadius: 'var(--radius-md)', cursor: 'pointer', color: 'var(--status-danger-text)' }}>
                            🗑
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          </div>
        );
      })()}

      {/* ── Checklisten Tab ─────────────────────────────────────────────────── */}
      {activeTab === 'checklists' && (() => {
        if (latestAudit === null) loadLatestAudit();
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <HomepageChecklist auditData={latestAudit || null} />
            <SecurityChecklist auditData={latestAudit || null} />
          </div>
        );
      })()}

      {/* ── Crawler Tab ─────────────────────────────────────────────────────── */}
      {activeTab === 'crawler' && (() => {
        const leadId = project.lead_id;
        const websiteUrl = project.website_url;

        const loadCrawlStatus = () => {
          fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers })
            .then(r => r.json()).then(d => {
              setCrawlJob(d);
              if (d.status === 'completed') {
                fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers })
                  .then(r => r.json()).then(res => setCrawlResults(res.results || []));
              }
            }).catch(console.error);
        };
        const startCrawl = () => {
          if (!websiteUrl) return;
          setCrawlLoading(true);
          fetch(`${API_BASE_URL}/api/crawler/start/${leadId}`, {
            method: 'POST', headers: h,
            body: JSON.stringify({ url: websiteUrl, max_pages: 50 }),
          }).then(r => r.json()).then(d => {
            setCrawlJob(d);
            setCrawlResults([]);
            const interval = setInterval(() => {
              fetch(`${API_BASE_URL}/api/crawler/status/${leadId}`, { headers })
                .then(r => r.json()).then(status => {
                  setCrawlJob(status);
                  if (status.status === 'completed' || status.status === 'failed') {
                    clearInterval(interval);
                    setCrawlLoading(false);
                    if (status.status === 'completed') {
                      fetch(`${API_BASE_URL}/api/crawler/results/${leadId}`, { headers })
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
          const va = a[crawlSort.col] ?? ''; const vb = b[crawlSort.col] ?? '';
          return crawlSort.asc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
        });
        const statusGroups = { '2xx': 0, '3xx': 0, '4xx+': 0 };
        crawlResults.forEach(r => {
          if (!r.status_code) return;
          if (r.status_code < 300) statusGroups['2xx']++;
          else if (r.status_code < 400) statusGroups['3xx']++;
          else statusGroups['4xx+']++;
        });
        const ThSort = ({ col, label: lbl }) => (
          <th onClick={() => setCrawlSort(p => ({ col, asc: p.col === col ? !p.asc : true }))} style={{ padding: '8px 12px', fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'left', cursor: 'pointer', borderBottom: '1px solid var(--border-light)', userSelect: 'none', whiteSpace: 'nowrap' }}>
            {lbl} {crawlSort.col === col ? (crawlSort.asc ? '↑' : '↓') : ''}
          </th>
        );

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>🕷️ Website-Crawler</div>
              <button onClick={startCrawl} disabled={crawlLoading || crawlJob?.status === 'running' || !websiteUrl} style={{ padding: '8px 18px', background: '#16a34a', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontSize: 12, fontWeight: 700, cursor: (crawlLoading || crawlJob?.status === 'running' || !websiteUrl) ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', opacity: (crawlLoading || crawlJob?.status === 'running') ? 0.7 : 1 }} title={!websiteUrl ? 'Website-URL im Projekt hinterlegen' : undefined}>
                {crawlJob?.status === 'running' ? '⏳ Läuft…' : '▶ Crawler starten'}
              </button>
            </div>
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
            {crawlResults.length > 0 && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 16 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>URLs nach Status-Code</div>
                <div style={{ display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden', marginBottom: 10 }}>
                  {statusGroups['2xx'] > 0 && <div style={{ flex: statusGroups['2xx'], background: '#16a34a', minWidth: 2 }} />}
                  {statusGroups['3xx'] > 0 && <div style={{ flex: statusGroups['3xx'], background: '#f59e0b', minWidth: 2 }} />}
                  {statusGroups['4xx+'] > 0 && <div style={{ flex: statusGroups['4xx+'], background: '#dc2626', minWidth: 2 }} />}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 11, color: 'var(--text-secondary)' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#16a34a', display: 'inline-block' }} />{statusGroups['2xx']} OK</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#f59e0b', display: 'inline-block' }} />{statusGroups['3xx']} Redirect</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><span style={{ width: 10, height: 10, borderRadius: 2, background: '#dc2626', display: 'inline-block' }} />{statusGroups['4xx+']} Fehler</span>
                </div>
              </div>
            )}
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
                      const hints = [];
                      if (sc === 301 || sc === 302) hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '⚠️ Weiterleitung erkannt. Prüfe ob die Ziel-URL direkt verlinkt werden kann.' });
                      else if (sc === 404) hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht gefunden. Dieser Link sollte entfernt oder korrigiert werden.' });
                      else if (sc === 500) hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Serverfehler. Diese Seite hat ein technisches Problem.' });
                      else if (!sc || sc === 0) hints.push({ bg: 'var(--status-danger-bg)', border: '#fecaca', text: '🔴 Seite nicht erreichbar. Timeout nach 10 Sekunden.' });
                      if (lt != null && lt > 3.0) hints.push({ bg: '#fff7ed', border: '#fed7aa', text: '🟠 Ladezeit über 3 Sekunden. Bilder komprimieren oder Caching aktivieren.' });
                      else if (lt != null && lt > 1.5) hints.push({ bg: 'var(--status-warning-bg)', border: '#fde68a', text: '🟡 Ladezeit erhöht. Performance-Optimierung empfohlen.' });
                      if (hints.length === 0 && sc >= 200 && sc < 300 && lt != null && lt <= 1.5) hints.push({ bg: 'var(--status-success-bg)', border: '#bbf7d0', text: '✅ Alles in Ordnung.' });
                      return (
                        <React.Fragment key={rowKey}>
                          <tr onClick={() => setCrawlExpandedRow(isExpanded ? null : rowKey)} style={{ borderTop: '1px solid var(--border-light)', cursor: 'pointer', background: isExpanded ? 'var(--bg-app)' : 'transparent' }}
                            onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = 'var(--bg-hover)'; }}
                            onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = 'transparent'; }}>
                            <td style={{ padding: '7px 12px', color: 'var(--text-tertiary)', whiteSpace: 'nowrap' }}>{r.crawled_at || '—'}</td>
                            <td style={{ padding: '7px 12px' }}><span style={{ background: scBg, color: scColor, fontWeight: 700, borderRadius: 4, padding: '2px 7px' }}>{sc || '—'}</span></td>
                            <td style={{ padding: '7px 12px', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>{lt != null ? `${lt}s` : '—'}</td>
                            <td style={{ padding: '7px 12px', maxWidth: 400 }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                                <a href={r.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ color: 'var(--brand-primary)', textDecoration: 'none', fontSize: 11, wordBreak: 'break-all' }}>{r.url}</a>
                                <span style={{ flexShrink: 0, fontSize: 10, color: 'var(--text-tertiary)', transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>▼</span>
                              </div>
                            </td>
                          </tr>
                          {isExpanded && (
                            <tr style={{ background: 'var(--bg-app)' }}>
                              <td colSpan={4} style={{ padding: '0 12px 10px 12px' }}>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                  {hints.length === 0
                                    ? <div style={{ padding: '8px 12px', background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)' }}>Keine Empfehlung verfügbar.</div>
                                    : hints.map((hint, hi) => (
                                      <div key={hi} style={{ padding: '9px 13px', background: hint.bg, border: `1px solid ${hint.border}`, borderRadius: 'var(--radius-md)', fontSize: 12, lineHeight: 1.5, color: 'var(--text-primary)' }}>{hint.text}</div>
                                    ))
                                  }
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
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

      {/* ── Website-Content Tab ─────────────────────────────────────────────── */}
      {activeTab === 'webcontent' && (() => {
        if (!websiteContent.length && !contentLoading) loadWebsiteContent();

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* ── Seiten-Liste (Crawler) ─────────────────────────────────── */}
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
                  Website-Content — {websiteContent.length} Seiten
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                  Content der gecrawlten Seiten: Titel, Meta, H1, H2, Textvorschau
                </div>
              </div>
              <button onClick={scrapeContent} disabled={contentLoading} style={{
                padding: '8px 16px', background: 'var(--brand-primary)', color: 'white',
                border: 'none', borderRadius: 'var(--radius-md)', fontSize: 13,
                fontWeight: 600, cursor: contentLoading ? 'not-allowed' : 'pointer',
                fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 6,
                opacity: contentLoading ? 0.7 : 1,
              }}>
                {contentLoading ? '⏳ Scrapt...' : '🔍 Content scannen'}
              </button>
            </div>

            {websiteContent.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 20px',
                background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                borderRadius: 'var(--radius-lg)', color: 'var(--text-tertiary)' }}>
                <div style={{ fontSize: 32, marginBottom: 10 }}>📄</div>
                <div style={{ fontSize: 13, marginBottom: 6 }}>Noch kein Content gescrapt</div>
                <div style={{ fontSize: 11 }}>Zuerst Crawler starten, dann "Content scannen" klicken</div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                {/* Seitenliste links */}
                <div style={{ width: 280, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 600, overflowY: 'auto' }}>
                  {websiteContent.map((page, i) => (
                    <button key={i} onClick={() => setSelectedContentPage(page)} style={{
                      padding: '10px 12px', textAlign: 'left', border: '1px solid',
                      borderColor: selectedContentPage?.url === page.url ? 'var(--brand-primary)' : 'var(--border-light)',
                      background: selectedContentPage?.url === page.url ? 'var(--brand-primary-light)' : 'var(--bg-surface)',
                      borderRadius: 'var(--radius-md)', cursor: 'pointer', width: '100%',
                      fontFamily: 'var(--font-sans)',
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {page.title || page.h1 || page.url}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2,
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {page.url}
                      </div>
                      {page.word_count && (
                        <div style={{ fontSize: 10, color: 'var(--brand-primary)', marginTop: 2 }}>
                          {page.word_count} Wörter
                        </div>
                      )}
                    </button>
                  ))}
                </div>

                {/* Detail rechts */}
                {selectedContentPage ? (
                  <div style={{ flex: 1, background: 'var(--bg-surface)', border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-lg)', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
                    <div>
                      <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>URL</div>
                      <a href={selectedContentPage.url} target="_blank" rel="noreferrer"
                        style={{ fontSize: 12, color: 'var(--brand-primary)', wordBreak: 'break-all' }}>
                        {selectedContentPage.url}
                      </a>
                    </div>
                    {selectedContentPage.title && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>Title Tag</div>
                        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{selectedContentPage.title}</div>
                      </div>
                    )}
                    {selectedContentPage.meta_description && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>Meta Description</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{selectedContentPage.meta_description}</div>
                      </div>
                    )}
                    {selectedContentPage.h1 && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>H1</div>
                        <div style={{ fontSize: 15, color: 'var(--text-primary)', fontWeight: 700 }}>{selectedContentPage.h1}</div>
                      </div>
                    )}
                    {selectedContentPage.h2s?.length > 0 && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 8 }}>H2 Überschriften</div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {(typeof selectedContentPage.h2s === 'string' ? JSON.parse(selectedContentPage.h2s) : selectedContentPage.h2s).map((h2, j) => (
                            <div key={j} style={{ padding: '6px 10px', background: 'var(--bg-app)',
                              borderRadius: 'var(--radius-md)', fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
                              {h2}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedContentPage.text_preview && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>Textvorschau</div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7,
                          padding: '10px 14px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)' }}>
                          {selectedContentPage.text_preview}
                        </div>
                      </div>
                    )}
                    {selectedContentPage.full_text && (
                      <div>
                        <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 4 }}>Volltext</div>
                        <div style={{ maxHeight: 300, overflowY: 'auto', fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7,
                          padding: '10px 14px', background: 'var(--bg-app)', borderRadius: 'var(--radius-md)',
                          whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {selectedContentPage.full_text}
                        </div>
                      </div>
                    )}
                    {(() => {
                      const imgs = Array.isArray(selectedContentPage.images) ? selectedContentPage.images
                        : (typeof selectedContentPage.images === 'string' ? (() => { try { return JSON.parse(selectedContentPage.images); } catch { return []; } })() : []);
                      return imgs.length > 0 && (
                        <div>
                          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 6 }}>Bilder ({imgs.length})</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxHeight: 200, overflowY: 'auto' }}>
                            {imgs.map((url, j) => (
                              <a key={j} href={url} target="_blank" rel="noreferrer"
                                style={{ fontSize: 11, color: 'var(--brand-primary)', wordBreak: 'break-all', lineHeight: 1.5 }}>
                                {url}
                              </a>
                            ))}
                          </div>
                        </div>
                      );
                    })()}
                    {(() => {
                      const files = Array.isArray(selectedContentPage.files) ? selectedContentPage.files
                        : (typeof selectedContentPage.files === 'string' ? (() => { try { return JSON.parse(selectedContentPage.files); } catch { return []; } })() : []);
                      return files.length > 0 && (
                        <div>
                          <div style={{ fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 6 }}>Dateien ({files.length})</div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                            {files.map((url, j) => (
                              <a key={j} href={url} target="_blank" rel="noreferrer"
                                style={{ fontSize: 11, color: 'var(--brand-primary)', wordBreak: 'break-all', lineHeight: 1.5 }}>
                                {url}
                              </a>
                            ))}
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                ) : (
                  <div style={{ flex: 1, textAlign: 'center', padding: '60px 20px',
                    color: 'var(--text-tertiary)', fontSize: 12 }}>
                    ← Seite auswählen um Content zu sehen
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {/* ── Hosting Fragebogen ──────────────────────────────────────────────── */}
      {activeTab === 'hosting' && activeSubTab === 'hosting-form' && (() => {
        const setF = (key, val) => setHostingForm(f => ({ ...f, [key]: val }));
        const inp = { width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)', background: 'var(--bg-app)', color: 'var(--text-primary)', fontSize: 13, fontFamily: 'var(--font-sans)', boxSizing: 'border-box', outline: 'none' };

        const save = async () => {
          setHostingFormSaving(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/projects/${project.id}`, {
              method: 'PUT',
              headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
              body: JSON.stringify({
                hosting_provider: hostingForm.hosting_provider,
                domain_registrar: hostingForm.domain_registrar,
                nameserver1:      hostingForm.nameserver1,
                nameserver2:      hostingForm.nameserver2,
                ftp_credentials:  hostingForm.ftp_credentials,
                wp_admin_url:     hostingForm.wp_admin_url,
                hosting_notes:    hostingForm.hosting_notes,
              }),
            });
            if (res.ok) toast.success('Zugangsdaten gespeichert');
            else toast.error('Speichern fehlgeschlagen');
          } catch (e) { toast.error('Fehler: ' + e.message); }
          finally { setHostingFormSaving(false); }
        };

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>🔑 Hosting & Zugangsdaten</div>
            {[
              { label: 'Hoster / Provider',     key: 'hosting_provider', type: 'input',    placeholder: 'z.B. IONOS, Strato, All-Inkl.' },
              { label: 'Domain-Registrar',       key: 'domain_registrar', type: 'input',    placeholder: 'z.B. united-domains.de' },
              { label: 'Nameserver 1',           key: 'nameserver1',      type: 'input',    placeholder: 'ns1.example.com' },
              { label: 'Nameserver 2',           key: 'nameserver2',      type: 'input',    placeholder: 'ns2.example.com' },
              { label: 'FTP/SFTP Zugangsdaten',  key: 'ftp_credentials',  type: 'textarea', placeholder: 'Host · Benutzer · Passwort' },
              { label: 'WordPress-Admin URL',    key: 'wp_admin_url',     type: 'input',    placeholder: 'https://example.com/wp-admin' },
              { label: 'Hinweise',               key: 'hosting_notes',    type: 'textarea', placeholder: 'Weitere Informationen...' },
            ].map(f => (
              <div key={f.key}>
                <label style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', display: 'block', marginBottom: 4 }}>{f.label}</label>
                {f.type === 'textarea' ? (
                  <textarea value={hostingForm[f.key]} onChange={e => setF(f.key, e.target.value)} placeholder={f.placeholder}
                    style={{ ...inp, resize: 'vertical', minHeight: 80 }} />
                ) : (
                  <input value={hostingForm[f.key]} onChange={e => setF(f.key, e.target.value)} placeholder={f.placeholder} style={inp} />
                )}
              </div>
            ))}
            <button onClick={save} disabled={hostingFormSaving} style={{
              alignSelf: 'flex-start', padding: '10px 24px',
              background: hostingFormSaving ? 'var(--border-medium)' : 'var(--brand-primary)',
              color: hostingFormSaving ? 'var(--text-tertiary)' : '#fff',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 13, fontWeight: 600,
              cursor: hostingFormSaving ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-sans)',
            }}>
              {hostingFormSaving ? 'Speichert…' : '💾 Speichern'}
            </button>
          </div>
        );
      })()}

      {/* ── Hosting-Analyse ─────────────────────────────────────────────────── */}
      {activeTab === 'hosting' && activeSubTab !== 'hosting-form' && (() => {
        const token = localStorage.getItem('kompagnon_token');
        const authH = token ? { Authorization: `Bearer ${token}` } : {};

        if (!hostingLoaded) {
          fetch(`${API_BASE_URL}/api/projects/${project.id}/hosting-info`, { headers: authH })
            .then(r => r.ok ? r.json() : null)
            .then(d => { setHostingData(d); setHostingLoaded(true); })
            .catch(() => setHostingLoaded(true));
        }

        const scan = async () => {
          setHostingScanning(true);
          try {
            const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/hosting-scan`, { method: 'POST', headers: authH });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const d = await r.json();
            setHostingData(d);
            toast.success('Hosting-Analyse abgeschlossen');
          } catch (e) {
            toast.error('Scan fehlgeschlagen: ' + e.message);
          } finally {
            setHostingScanning(false);
          }
        };

        const fmtDate = (s) => {
          if (!s) return null;
          return new Date(s).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
        };

        const timeAgo = (iso) => {
          if (!iso) return null;
          const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
          if (diff < 60) return `vor ${diff} Sek.`;
          if (diff < 3600) return `vor ${Math.floor(diff / 60)} Min.`;
          if (diff < 86400) return `vor ${Math.floor(diff / 3600)} Std.`;
          return fmtDate(iso);
        };

        const expiresWarn = (dateStr) => {
          if (!dateStr) return null;
          const days = Math.floor((new Date(dateStr) - Date.now()) / 86400000);
          return days < 30 ? 'danger' : 'success';
        };

        const card = { background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 12, padding: '20px 22px' };
        const lbl = { fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 };
        const val = { fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 4 };
        const sub = { fontSize: 12, color: 'var(--text-tertiary)' };

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Header + Button */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>🖥️ Hosting-Analyse</h2>
                {(hostingData?.hosting_checked_at || hostingData?.checked_at) && (
                  <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    Zuletzt gescannt: {timeAgo(hostingData.hosting_checked_at || hostingData.checked_at)}
                  </div>
                )}
              </div>
              <button
                onClick={scan}
                disabled={hostingScanning}
                style={{ padding: '9px 20px', background: hostingScanning ? '#94a3b8' : 'var(--brand-primary)', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: hostingScanning ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
              >
                {hostingScanning
                  ? <><span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} /> Scanning…</>
                  : (hostingData?.hosting_checked_at || hostingData?.checked_at) ? '🔄 Erneut scannen' : '🔍 Hosting scannen'}
              </button>
            </div>

            {!hostingLoaded ? (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>Lade…</div>
            ) : !(hostingData?.hosting_checked_at || hostingData?.checked_at) ? (
              <div style={{ textAlign: 'center', padding: 48, background: 'var(--bg-surface)', borderRadius: 12, border: '1px dashed var(--border-light)', color: 'var(--text-tertiary)' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🖥️</div>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Noch kein Scan durchgeführt</div>
                <div style={{ fontSize: 13 }}>Klicke auf "Hosting scannen" um Hosting, DNS und WHOIS zu analysieren.</div>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>

                {/* Block 1: Hosting-Anbieter */}
                <div style={card}>
                  <div style={lbl}>🖥 Hosting-Anbieter</div>
                  <div style={val}>{hostingData.hosting_provider || '–'}</div>
                  {hostingData.hosting_org && <div style={sub}>{hostingData.hosting_org}</div>}
                  <div style={{ ...sub, marginTop: 6 }}>
                    {[hostingData.hosting_ip, hostingData.hosting_country].filter(Boolean).join(' · ') || '–'}
                  </div>
                </div>

                {/* Block 2: DNS & Nameserver */}
                <div style={card}>
                  <div style={lbl}>🌐 DNS & Nameserver</div>
                  <div style={val}>{hostingData.dns_provider || 'Unbekannt'}</div>
                  {hostingData.nameservers && (
                    <ul style={{ margin: '6px 0 0', paddingLeft: 16, ...sub }}>
                      {hostingData.nameservers.split(',').slice(0, 3).map((ns, i) => (
                        <li key={i}>{ns.trim()}</li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Block 3: Domain-Registrar */}
                <div style={card}>
                  <div style={lbl}>📋 Domain-Registrar</div>
                  <div style={val}>{hostingData.domain_registrar || '–'}</div>
                  {hostingData.domain_created && (
                    <div style={sub}>Registriert: {fmtDate(hostingData.domain_created)}</div>
                  )}
                  {hostingData.domain_expires && (
                    <div style={{ ...sub, marginTop: 4, color: expiresWarn(hostingData.domain_expires) === 'danger' ? '#dc2626' : '#16a34a', fontWeight: 600 }}>
                      Läuft ab: {fmtDate(hostingData.domain_expires)}
                      {expiresWarn(hostingData.domain_expires) === 'danger' && ' ⚠️'}
                    </div>
                  )}
                </div>

                {/* Block 4: CMS & Technologie */}
                <div style={card}>
                  <div style={lbl}>⚙️ CMS & Technologie</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                    {hostingData.is_wordpress ? (
                      <span style={{ background: '#2271b1', color: '#fff', borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>WordPress</span>
                    ) : (
                      <span style={{ background: '#f1f5f9', color: '#94a3b8', borderRadius: 6, padding: '3px 10px', fontSize: 12 }}>Kein WordPress erkannt</span>
                    )}
                    {hostingData.wordpress_hosting && (
                      <span style={{ background: '#dcfce7', color: '#166534', borderRadius: 6, padding: '3px 10px', fontSize: 12, fontWeight: 700 }}>{hostingData.wordpress_hosting}</span>
                    )}
                  </div>
                  {hostingData.server_software && <div style={sub}>{hostingData.server_software}</div>}
                </div>

                {/* Block 5: Erkannte Technologien */}
                {hostingData.detected_technologies && (
                  <div style={{ ...card, gridColumn: '1 / -1' }}>
                    <div style={lbl}>🔍 Erkannte Technologien & Tools</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                      {hostingData.detected_technologies.split(',').filter(Boolean).map(tech => (
                        <span key={tech} style={{ background: 'var(--bg-app)', border: '1px solid var(--border-light)', borderRadius: 6, padding: '4px 10px', fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
                          {tech.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
          </div>
        );
      })()}

      {/* ── Zeiterfassung Placeholder ───────────────────────────────────────── */}
      {activeTab === 'zeit' && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>Zeiterfassung</p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}

      {/* ── Nachrichten Tab ─────────────────────────────────────────────────── */}
      {activeTab === 'kommunikation' && (() => {
        const leadId = project.lead_id;
        const hdr = token ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` } : { 'Content-Type': 'application/json' };

        const loadChat = async () => {
          if (!leadId) return;
          try {
            const res = await fetch(`${API_BASE_URL}/api/messages/${leadId}`, { headers: hdr });
            if (res.ok) setChatMessages(await res.json());
          } catch { /* silent */ }
        };

        const sendChat = async () => {
          if (!chatText.trim() || chatSending || !leadId) return;
          setChatSending(true);
          try {
            const res = await fetch(`${API_BASE_URL}/api/messages/${leadId}`, {
              method: 'POST', headers: hdr,
              body: JSON.stringify({ content: chatText.trim(), subject: chatSubject.trim() || undefined, channel: chatChannel }),
            });
            if (res.ok) { setChatText(''); setChatSubject(''); await loadChat(); }
          } catch { /* silent */ } finally { setChatSending(false); }
        };

        if (chatMessages.length === 0 && leadId) loadChat();

        const fmtTime = (iso) => iso ? new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) : '';
        const fmtDay = (iso) => {
          if (!iso) return '';
          const d = new Date(iso);
          const today = new Date(); const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1);
          if (d.toDateString() === today.toDateString()) return 'Heute';
          if (d.toDateString() === yesterday.toDateString()) return 'Gestern';
          return d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
        };

        const grouped = [];
        let lastDay = null;
        for (const m of chatMessages) {
          const day = fmtDay(m.created_at);
          if (day !== lastDay) { grouped.push({ type: 'sep', day }); lastDay = day; }
          grouped.push({ type: 'msg', msg: m });
        }

        if (!leadId) return (
          <div className="kc-card" style={{ textAlign: 'center', padding: 40, color: 'var(--text-tertiary)' }}>
            <p>Kein Kunde mit diesem Projekt verknüpft.</p>
            <p style={{ fontSize: 13 }}>Verknüpfe zuerst einen Lead über "Projektdaten bearbeiten".</p>
          </div>
        );

        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0, border: '1px solid var(--border-light)', borderRadius: 12, overflow: 'hidden', background: 'var(--bg-app)' }}>
            {/* Verlauf */}
            <div style={{ maxHeight: 500, overflowY: 'auto', padding: '16px 16px 8px', display: 'flex', flexDirection: 'column', gap: 12 }}>
              {chatMessages.length === 0 && (
                <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13, padding: 32 }}>Noch keine Nachrichten. Schreib die erste Nachricht!</div>
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
                      <span style={{ fontWeight: 600 }}>{m.sender_name || (isAdmin ? 'Admin' : 'Kunde')}</span>
                      <span>{fmtTime(m.created_at)}</span>
                      {isAdmin && (
                        <span style={{ background: m.channel === 'email' ? '#fef3c7' : '#dcfce7', color: m.channel === 'email' ? '#92400e' : '#166534', borderRadius: 4, padding: '1px 6px', fontSize: 10, fontWeight: 600 }}>
                          {m.channel === 'email' ? '✉️ E-Mail' : '💬 In-App'}
                        </span>
                      )}
                      {!isAdmin && !m.is_read && <span style={{ color: '#3b82f6', fontSize: 10 }}>🔵 Ungelesen</span>}
                    </div>
                    <div style={{ maxWidth: '75%', padding: '10px 14px', borderRadius: isAdmin ? '14px 14px 4px 14px' : '14px 14px 14px 4px', background: isAdmin ? '#E6F1FB' : 'var(--bg-surface)', border: '1px solid var(--border-light)', fontSize: 13, lineHeight: 1.6, color: 'var(--text-primary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {m.content}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Eingabe */}
            <div style={{ borderTop: '1px solid var(--border-light)', padding: '12px 16px', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {chatChannel === 'email' && (
                <input value={chatSubject} onChange={e => setChatSubject(e.target.value)} placeholder="Betreff der E-Mail…"
                  style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none' }} />
              )}
              <textarea value={chatText} onChange={e => setChatText(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendChat(); }}
                placeholder="Nachricht schreiben… (Ctrl+Enter zum Senden)" rows={3}
                style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border-light)', fontSize: 13, fontFamily: 'var(--font-sans)', resize: 'vertical', background: 'var(--bg-app)', color: 'var(--text-primary)', outline: 'none', width: '100%', boxSizing: 'border-box' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <div style={{ display: 'flex', gap: 4 }}>
                  {[{ id: 'in_app', label: '💬 In-App' }, { id: 'email', label: '✉️ + E-Mail' }].map(ch => (
                    <button key={ch.id} onClick={() => setChatChannel(ch.id)}
                      style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid var(--border-light)', fontSize: 12, fontWeight: chatChannel === ch.id ? 700 : 400, background: chatChannel === ch.id ? 'var(--brand-primary)' : 'var(--bg-app)', color: chatChannel === ch.id ? '#fff' : 'var(--text-secondary)', cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      {ch.label}
                    </button>
                  ))}
                </div>
                <button onClick={sendChat} disabled={chatSending || !chatText.trim()}
                  style={{ padding: '8px 20px', background: '#0d6efd', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: chatSending || !chatText.trim() ? 'not-allowed' : 'pointer', opacity: chatSending || !chatText.trim() ? 0.6 : 1, fontFamily: 'var(--font-sans)' }}>
                  {chatSending ? 'Senden…' : 'Senden →'}
                </button>
              </div>
            </div>
          </div>
        );
      })()}

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

      {/* ── Editor Tab ─────────────────────────────────────────────────────── */}
      {(activeSubTab === 'editor' || activeTab === 'editor') && (
        <div style={{ background: 'var(--bg-app)', border: '2px dashed var(--border-light)', borderRadius: 8, padding: 40, textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>✏️</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>GrapesJS Editor</div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)' }}>Seite aus dem Sitemap-Planer auswählen, um den Editor zu öffnen.</div>
        </div>
      )}

      {/* ── Netlify-DNS Tab ────────────────────────────────────────────────── */}
      {(activeSubTab === 'netlify-dns' || activeTab === 'netlify-dns') && (() => {
        // Load status on first open
        if (!netlify && !netlifyLoading) {
          setNetlifyLoading(true);
          fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers })
            .then(r => r.ok ? r.json() : null)
            .then(d => { setNetlify(d); setNetlifyLoading(false); })
            .catch(() => setNetlifyLoading(false));
        }

        const createSite = async () => {
          setNetlifyLoading(true);
          try {
            const r = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/create-site`, { method: 'POST', headers });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            toast.success('Netlify-Site angelegt');
            // reload status
            const s = await fetch(`${API_BASE_URL}/api/projects/${project.id}/netlify/status`, { headers });
            setNetlify(s.ok ? await s.json() : null);
          } catch (e) { toast.error('Fehler: ' + e.message); }
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
            setNetlifyDnsGuide({ cname_target: d.cname_target || netlify?.url?.replace('https://', '') || '' });
            toast.success('Domain verbunden');
          } catch (e) { toast.error('Fehler: ' + e.message); }
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

            {/* ── BEREICH 2: Deployen ── */}
            {netlify && (
              <div style={card}>
                <div style={cardTitle}>🚀 Deployen</div>
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

                {netlifyDnsGuide && (
                  <div style={{ background: '#E6F1FB', border: '1px solid #93c5fd', borderRadius: 8, padding: 16, marginTop: 4 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: '#185FA5', marginBottom: 10 }}>
                      DNS-Eintrag beim Domain-Anbieter setzen:
                    </div>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <tbody>
                        {[
                          ['Typ',  'CNAME'],
                          ['Name', 'www'],
                          ['Ziel', netlifyDnsGuide.cname_target],
                          ['TTL',  '3600'],
                        ].map(([k, v]) => (
                          <tr key={k}>
                            <td style={{ padding: '4px 12px 4px 0', color: '#185FA5', fontWeight: 600, whiteSpace: 'nowrap' }}>{k}</td>
                            <td style={{ padding: '4px 0', color: '#1e3a5f', fontFamily: 'monospace' }}>{v}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <button onClick={sendDnsEmail} style={{ marginTop: 12, padding: '7px 16px', background: '#185FA5', color: '#fff', border: 'none', borderRadius: 6, fontWeight: 600, fontSize: 12, cursor: 'pointer', fontFamily: 'var(--font-sans)' }}>
                      ✉️ Anleitung per E-Mail senden
                    </button>
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
          pageId={editingPage.id}
          pageName={editingPage.page_name}
          initialHtml={editingPage.mockup_html || ''}
          onClose={() => setEditingPage(null)}
          onSave={({ html }) => {
            setSitemapPages(prev => prev.map(p =>
              p.id === editingPage.id ? { ...p, mockup_html: html } : p
            ));
            setEditingPage(null);
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
