import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
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
import { useAuth } from '../context/AuthContext';
import { useScreenSize } from '../utils/responsive';

import API_BASE_URL from '../config';

// ── CMS options ───────────────────────────────────────────────────────────────
const CMS_OPTIONS  = ['WordPress', 'Wix', 'TYPO3', 'Webflow', 'Sonstige'];
const PKG_OPTIONS  = ['kompagnon', 'starter', 'professional', 'enterprise'];
const PAY_OPTIONS  = ['offen', 'bezahlt', 'überfällig'];

// ── Edit Modal ────────────────────────────────────────────────────────────────
function EditModal({ project, token, onClose, onSaved }) {
  const [form, setForm] = useState({
    website_url:                  project.website_url    || '',
    cms_type:                     project.cms_type       || '',
    contact_name:                 project.contact_name   || '',
    contact_phone:                project.contact_phone  || '',
    contact_email:                project.contact_email  || '',
    go_live_date:                 project.go_live_date
                                    ? String(project.go_live_date).slice(0, 10)
                                    : '',
    package_type:                 project.package_type   || 'kompagnon',
    payment_status:               project.payment_status || 'offen',
    desired_pages:                project.desired_pages  || '',
    has_logo:                     !!project.has_logo,
    has_briefing:                 !!project.has_briefing,
    has_photos:                   !!project.has_photos,
    top_problems:                 project.top_problems   || '',
    industry:                     project.industry       || '',
    customer_email:               project.customer_email || '',
    email_notifications_enabled:  project.email_notifications_enabled !== false,
  });
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

  return (
    <div style={overlay} onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={panel}>
        <div style={header}>
          <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>Projektdaten bearbeiten</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text-tertiary)', lineHeight: 1 }}>×</button>
        </div>

        <div style={body}>
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
    </div>
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

  return (
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
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ProjectDetail() {
  const { id }         = useParams();
  const { token, user } = useAuth();
  const { isMobile }   = useScreenSize();
  const headers          = token ? { Authorization: `Bearer ${token}` } : {};
  const isAdmin          = user?.role === 'admin';

  const [project, setProject]         = useState(null);
  const [margin, setMargin]           = useState(null);
  const [loading, setLoading]         = useState(true);
  const [activeTab, setActiveTab]     = useState('overview');
  const [showEdit, setShowEdit]       = useState(false);
  const [showApproval, setShowApproval] = useState(false);
  const [showBriefingWizard, setShowBriefingWizard] = useState(false);
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
  const [sitemapPages, setSitemapPages] = useState([]);
  const [sitemapLoading, setSitemapLoading] = useState(false);
  const [showSitemapPlaner, setShowSitemapPlaner] = useState(false);
  const [selectedPageId, setSelectedPageId] = useState(null);
  // Mockup
  const [mockupRunning, setMockupRunning] = useState(false);
  const [mockupResult, setMockupResult] = useState(null);
  const [mockupError, setMockupError] = useState('');

  const loadProject = useCallback(async () => {
    try {
      setLoading(true);
      const [projectRes, marginRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/projects/${id}`, { headers }),
        axios.get(`${API_BASE_URL}/api/projects/${id}/margin`, { headers }),
      ]);
      setProject(projectRes.data);
      setMargin(marginRes.data);
    } catch {
      toast.error('Projekt konnte nicht geladen werden.');
    } finally {
      setLoading(false);
    }
  }, [id]); // eslint-disable-line

  useEffect(() => { loadProject(); }, [id]); // eslint-disable-line

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
        if (!selectedPageId && pages.length > 0) {
          const start = pages.find(p => p.page_type === 'startseite') || pages[0];
          setSelectedPageId(start.id);
        }
      }
    } catch { /* silent */ }
    finally { setSitemapLoading(false); }
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

  const generateMockup = async () => {
    setMockupRunning(true);
    setMockupError('');
    setMockupResult(null);
    try {
      const bRes = await fetch(`${API_BASE_URL}/api/briefings/${project.lead_id}`, { headers });
      const briefing = bRes.ok ? await bRes.json() : null;
      const selectedPage = sitemapPages.find(p => p.id === selectedPageId) || null;

      const payload = {
        company_name: project.company_name || '',
        city: briefing?.einzugsgebiet || '',
        trade: briefing?.gewerk || project.industry || '',
        usp: briefing?.usp || '',
        services: briefing?.leistungen
          ? briefing.leistungen.split(/[\n,]+/).map(s => s.trim()).filter(Boolean)
          : [],
        target_audience: briefing?.zielgruppe || '',
        ...(selectedPage ? {
          page_name: selectedPage.page_name,
          zweck: selectedPage.zweck || '',
          ziel_keyword: selectedPage.ziel_keyword || '',
          cta_text: selectedPage.cta_text || '',
        } : {}),
      };

      const res = await fetch(`${API_BASE_URL}/api/agents/${project.id}/content`, {
        method: 'POST', headers: h, body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err.detail;
        throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map(d => d.msg || JSON.stringify(d)).join(', ') : detail ? JSON.stringify(detail) : `Fehler ${res.status}`);
      }
      const data = await res.json();
      setMockupResult(data.result);

      if (selectedPage && data.result) {
        const mockupHtml = typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2);
        fetch(`${API_BASE_URL}/api/sitemap/pages/${selectedPage.id}`, {
          method: 'PUT', headers: h,
          body: JSON.stringify({ ...selectedPage, mockup_html: mockupHtml }),
        }).catch(() => {});
      }
    } catch (e) {
      setMockupError(e?.message || e?.detail || String(e) || 'Generierung fehlgeschlagen.');
    } finally {
      setMockupRunning(false);
    }
  };

  const tabs = ['overview', 'briefing', 'dateien', 'pagespeed', 'sitemap', 'mockup', 'checklists', 'crawler', 'zeit', 'kommunikation'];

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
      <ProjectCard project={project} />

      {/* ── Buttons ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <button
          onClick={() => setShowEdit(true)}
          style={{
            padding: '9px 18px', background: 'var(--bg-surface)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}
        >
          ✏️ Projektdaten bearbeiten
        </button>

        <button
          onClick={async () => {
            try {
              const res = await axios.get(`${API_BASE_URL}/api/briefings/${project.lead_id}`, { headers });
              setBriefingData(res.data);
            } catch { setBriefingData(null); }
            setShowBriefingWizard(true);
          }}
          style={{
            padding: '9px 18px', background: 'var(--bg-surface)',
            border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
            fontFamily: 'var(--font-sans)', color: 'var(--text-primary)',
            display: 'inline-flex', alignItems: 'center', gap: 6,
          }}
        >
          📋 Briefing starten
        </button>

        {isAdmin && (
          <button
            onClick={() => setShowApproval(true)}
            style={{
              padding: '9px 18px', background: '#008EAA', color: '#fff',
              border: 'none', borderRadius: 'var(--radius-md)',
              fontSize: 13, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'var(--font-sans)',
              display: 'inline-flex', alignItems: 'center', gap: 6,
            }}
          >
            📧 Freigabe anfordern
          </button>
        )}
      </div>

      {/* ── Phase Tracker ───────────────────────────────────────────────────── */}
      <div className="kc-card">
        <PhaseTracker currentPhase={project.status} />
      </div>

      {/* ── Tabs ───────────────────────────────────────────────────────────── */}
      <div className="kc-tab-nav" style={{ display: 'flex', gap: 4, background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 4, overflowX: 'auto', WebkitOverflowScrolling: 'touch', scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        {tabs.map((tab) => {
          const label =
            tab === 'overview'   ? '⊞ Übersicht'    :
            tab === 'briefing'   ? '📋 Briefing'     :
            tab === 'dateien'    ? '📎 Dateien'      :
            tab === 'pagespeed'  ? '⚡ PageSpeed'    :
            tab === 'sitemap'    ? '🗺️ Sitemap'      :
            tab === 'mockup'     ? '🎨 Mockup'       :
            tab === 'checklists' ? '✓ Checklisten'  :
            tab === 'crawler'    ? '🕷️ Crawler'      :
            tab === 'zeit'       ? '⏱ Zeiterfassung' : '💬 Kommunikation';
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{ flex: isMobile ? '0 0 auto' : 1, flexShrink: 0, padding: isMobile ? '7px 14px' : '8px 12px', borderRadius: 'var(--radius-md)', border: 'none', background: activeTab === tab ? 'var(--bg-active)' : 'transparent', color: activeTab === tab ? 'var(--brand-primary)' : 'var(--text-tertiary)', fontSize: 12, fontWeight: activeTab === tab ? 500 : 400, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', justifyContent: 'center', whiteSpace: 'nowrap', transition: 'all 0.15s' }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* ── Overview Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div className="kc-card" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 24 }}>
            <InfoBlock label="Status" value={project.status.replace('phase_', 'Phase ')} />
            <InfoBlock label="Festpreis" value={`€${project.fixed_price.toFixed(2)}`} mono />
            <InfoBlock label="Stunden geloggt" value={`${project.actual_hours.toFixed(1)}h`} mono />
            {margin && <InfoBlock label="Gesamtkosten" value={`€${margin.total_costs.toFixed(2)}`} mono />}
          </div>

          {margin && (
            <div className="kc-card" style={{ background: margin.status === 'red' ? 'var(--kc-rot-subtle)' : 'var(--bg-app)', border: margin.status === 'red' ? '1px solid var(--brand-primary)' : '1px solid var(--border-light)' }}>
              <div style={{ marginBottom: 16 }}>
                <span>Marge</span>
                <h2 style={{ fontSize: 22, margin: 0 }}>Profitabilität</h2>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 24 }}>
                <InfoBlock label="Personenstunden" value={`${margin.human_hours.toFixed(1)}h × €${project.hourly_rate}/h`} mono />
                <InfoBlock label="KI-Kosten" value={`€${margin.ai_tool_costs.toFixed(2)}`} mono />
                <InfoBlock label="Verbleibend bis 70%" value={`${margin.hours_remaining_at_target.toFixed(1)}h`} mono />
                <InfoBlock label="Marge" value={<MarginBadge marginPercent={margin.margin_percent} status={margin.status} />} raw />
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Briefing Tab ────────────────────────────────────────────────────── */}
      {activeTab === 'briefing' && project.lead_id && (
        <BriefingTab lead={{ id: project.lead_id }} isMobile={false} />
      )}

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
        if (!sitemapLoading && sitemapPages.length === 0) loadSitemapPages();
        const SITEMAP_STATUS = {
          geplant:        { bg: '#EFF6FF', text: '#1D4ED8', label: 'Geplant' },
          in_bearbeitung: { bg: '#FEF9C3', text: '#92400E', label: 'In Bearb.' },
          freigegeben:    { bg: '#FEF3C7', text: '#B45309', label: 'Freigegeben' },
          live:           { bg: '#DCFCE7', text: '#166534', label: 'Live' },
        };
        const TYPE_ICON = { startseite: '🏠', leistung: '🔧', info: 'ℹ️', vertrauen: '⭐', conversion: '📞', sonstige: '📄' };
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              <button
                onClick={() => setShowSitemapPlaner(true)}
                style={{ padding: '9px 18px', borderRadius: 8, border: 'none', background: 'var(--brand-primary)', color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                🗺️ Sitemap bearbeiten
              </button>
              <a
                href={`${API_BASE_URL}/api/sitemap/${project.lead_id}/pdf`}
                target="_blank" rel="noopener noreferrer"
                style={{ padding: '9px 18px', borderRadius: 8, border: '1.5px solid var(--border-medium)', background: 'var(--bg-surface)', color: 'var(--text-primary)', fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)', display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
              >
                📥 PDF herunterladen
              </a>
            </div>
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
              {sitemapLoading ? (
                <div style={{ padding: 32, textAlign: 'center' }}>
                  <div style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid var(--border-light)', borderTopColor: 'var(--brand-primary)', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
                </div>
              ) : sitemapPages.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-tertiary)', fontSize: 13 }}>
                  Noch keine Seiten geplant. Klicke auf „Sitemap bearbeiten" um loszulegen.
                </div>
              ) : sitemapPages.map((page, idx) => {
                const st = SITEMAP_STATUS[page.status] || SITEMAP_STATUS.geplant;
                return (
                  <div key={page.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', borderBottom: idx < sitemapPages.length - 1 ? '1px solid var(--border-light)' : 'none', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 18, flexShrink: 0 }}>{TYPE_ICON[page.page_type] || '📄'}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{page.page_name}</div>
                      {page.ziel_keyword && <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 1 }}>{page.ziel_keyword}</div>}
                    </div>
                    <span style={{ fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 10, background: st.bg, color: st.text, whiteSpace: 'nowrap', flexShrink: 0 }}>{st.label}</span>
                    <button
                      onClick={() => { setSelectedPageId(page.id); setActiveTab('mockup'); }}
                      style={{ padding: '5px 12px', borderRadius: 6, border: '1.5px solid var(--border-medium)', background: 'var(--bg-app)', color: 'var(--brand-primary)', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'var(--font-sans)', whiteSpace: 'nowrap', flexShrink: 0 }}
                    >
                      Mockup öffnen →
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })()}

      {/* ── Mockup Tab ──────────────────────────────────────────────────────── */}
      {activeTab === 'mockup' && (() => {
        if (sitemapPages.length === 0 && !sitemapLoading) loadSitemapPages();
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
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
                onClick={generateMockup}
                disabled={mockupRunning}
                style={{ padding: '10px 22px', borderRadius: 8, border: 'none', background: mockupRunning ? 'var(--bg-muted)' : 'var(--brand-primary)', color: mockupRunning ? 'var(--text-tertiary)' : '#fff', fontSize: 14, fontWeight: 600, cursor: mockupRunning ? 'not-allowed' : 'pointer', fontFamily: 'var(--font-sans)', display: 'flex', alignItems: 'center', gap: 8 }}
              >
                {mockupRunning && <span style={{ width: 12, height: 12, borderRadius: '50%', border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', animation: 'spin 0.8s linear infinite', display: 'inline-block' }} />}
                {mockupRunning ? 'Generiere Entwurf…' : '🎨 KI-Entwurf generieren'}
              </button>
              {mockupError && (
                <div style={{ background: 'var(--status-danger-bg)', border: '1px solid var(--status-danger-text)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--status-danger-text)', marginTop: 12 }}>
                  {typeof mockupError === 'string' ? mockupError : JSON.stringify(mockupError)}
                </div>
              )}
            </div>
            {mockupResult && (
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-light)', borderRadius: 'var(--radius-lg)', padding: 20 }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 14 }}>Generierter Entwurf</div>
                {typeof mockupResult === 'string' ? (
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-primary)', fontFamily: 'inherit', lineHeight: 1.7, margin: 0 }}>{mockupResult}</pre>
                ) : typeof mockupResult === 'object' ? (
                  Object.entries(mockupResult).map(([key, val]) => (
                    <div key={key} style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{key}</div>
                      <div style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{typeof val === 'string' ? val : JSON.stringify(val, null, 2)}</div>
                    </div>
                  ))
                ) : (
                  <pre style={{ fontSize: 13 }}>{JSON.stringify(mockupResult, null, 2)}</pre>
                )}
              </div>
            )}
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

      {/* ── Placeholder tabs ────────────────────────────────────────────────── */}
      {(activeTab === 'zeit' || activeTab === 'kommunikation') && (
        <div className="kc-card" style={{ textAlign: 'center', padding: 'var(--kc-space-16)', color: 'var(--text-tertiary)' }}>
          <p style={{ fontSize: 16, fontWeight: 600 }}>{activeTab === 'zeit' ? 'Zeiterfassung' : 'Kommunikation'}</p>
          <p style={{ fontSize: 13 }}>In Entwicklung</p>
        </div>
      )}

      {/* ── Edit Modal ──────────────────────────────────────────────────────── */}
      {showEdit && (
        <EditModal
          project={project}
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

      {/* ── Briefing Wizard ─────────────────────────────────────────────────── */}
      {showBriefingWizard && (
        <BriefingWizard
          leadId={project.lead_id}
          leadData={briefingData}
          onClose={() => setShowBriefingWizard(false)}
          onComplete={() => setShowBriefingWizard(false)}
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
